"""
Redis Cache Service for ZLECAf Application
===========================================
Provides caching layer for API responses to improve performance.

Cache TTLs:
- Statistics: 1 hour (data changes infrequently)
- Search results: 30 minutes
- Tariff calculations: 15 minutes
- Country data: 2 hours
- Regulatory details: 1 hour
"""

import hashlib
import json
import os
import time
from datetime import timedelta
from functools import wraps
from typing import Any, Optional, Union

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"

# Cache TTLs in seconds
CACHE_TTL = {
    "statistics": 3600,  # 1 hour
    "countries": 7200,  # 2 hours
    "search": 1800,  # 30 minutes
    "calculation": 900,  # 15 minutes
    "regulatory": 3600,  # 1 hour
    "oec_data": 86400,  # 24 hours (annual trade data changes rarely)
    "default": 600,  # 10 minutes
}

# Global Redis client (type hinted with a forward reference so it is safe
# even when the redis package is not installed)
_redis_client: "Optional[Any]" = None

# ---------------------------------------------------------------------------
# In-memory fallback cache
# ---------------------------------------------------------------------------
# When Redis is unavailable (dev, sandbox, deployments without Redis), this
# process-local TTL store keeps caching working so we don't hammer upstream
# APIs (e.g. OEC) on every request. It also retains the last value past expiry
# to enable "stale-on-error" serving when the upstream source is down/rate-limited.
_MEMORY_STORE: "dict[str, tuple]" = {}  # key -> (value, expiry_epoch)
_MEMORY_MAX_ENTRIES = 2000

# Injectable clock (tests can override) — returns epoch seconds.
_now = time.time


def _mem_set(key: str, value: Any, ttl_seconds: int) -> None:
    """Store a value in the in-memory cache with a TTL (seconds)."""
    # Cheap capacity guard: drop expired entries, then oldest if still full.
    if len(_MEMORY_STORE) >= _MEMORY_MAX_ENTRIES:
        now = _now()
        expired = [k for k, (_, exp) in _MEMORY_STORE.items() if exp < now]
        for k in expired:
            _MEMORY_STORE.pop(k, None)
        if len(_MEMORY_STORE) >= _MEMORY_MAX_ENTRIES:
            # Evict the entry closest to expiry.
            oldest = min(_MEMORY_STORE, key=lambda k: _MEMORY_STORE[k][1])
            _MEMORY_STORE.pop(oldest, None)
    _MEMORY_STORE[key] = (value, _now() + ttl_seconds)


def _mem_get(key: str, allow_stale: bool = False) -> Optional[Any]:
    """Read from the in-memory cache. With allow_stale, ignore expiry."""
    item = _MEMORY_STORE.get(key)
    if item is None:
        return None
    value, expiry = item
    if allow_stale or _now() < expiry:
        return value
    return None


def get_redis_client() -> "Optional[Any]":
    """Get or create Redis client singleton."""
    global _redis_client

    if not REDIS_AVAILABLE or not CACHE_ENABLED:
        return None

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL, decode_responses=True, socket_connect_timeout=2, socket_timeout=2
            )
            # Test connection
            _redis_client.ping()
            print(f"✓ Redis cache connected: {REDIS_URL}")
        except Exception as e:
            print(f"⚠ Redis connection failed: {e}")
            _redis_client = None

    return _redis_client


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from prefix and arguments."""
    key_parts = [prefix]

    # Add positional args
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")

    # Create hash for long keys
    key_str = ":".join(key_parts)
    if len(key_str) > 200:
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]
        key_str = f"{prefix}:{key_hash}"

    return f"zlecaf:{key_str}"


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache (Redis if available, else in-memory)."""
    if not CACHE_ENABLED:
        return None

    client = get_redis_client()
    if client:
        try:
            value = client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    # No Redis → in-memory fallback
    return _mem_get(key)


def cache_get_stale(key: str) -> Optional[Any]:
    """
    Get a cached value even if expired (stale-on-error).

    Used to keep serving the last known good value when the upstream source
    is down or rate-limited. Only the in-memory backend retains expired
    entries; Redis evicts on TTL, so this returns its live value there.
    """
    if not CACHE_ENABLED:
        return None

    client = get_redis_client()
    if client:
        try:
            value = client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get(stale) error: {e}")
            return None

    return _mem_get(key, allow_stale=True)


def cache_set(key: str, value: Any, ttl_type: str = "default") -> bool:
    """Set value in cache with TTL (Redis if available, else in-memory)."""
    if not CACHE_ENABLED:
        return False

    ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
    client = get_redis_client()
    if client:
        try:
            client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    # No Redis → in-memory fallback
    _mem_set(key, value, ttl)
    return True


def cache_delete(key: str) -> bool:
    """Delete a key from cache (Redis if available, else in-memory)."""
    client = get_redis_client()
    if not client:
        # In-memory fallback so invalidation works without Redis too.
        return _MEMORY_STORE.pop(key, None) is not None

    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern (Redis if available, else in-memory)."""
    client = get_redis_client()
    if not client:
        # In-memory fallback: match the same zlecaf:-prefixed key space.
        prefix = f"zlecaf:{pattern}".rstrip("*")
        keys = [k for k in list(_MEMORY_STORE) if k.startswith(prefix)]
        for k in keys:
            _MEMORY_STORE.pop(k, None)
        return len(keys)

    try:
        keys = client.keys(f"zlecaf:{pattern}")
        if keys:
            return client.delete(*keys)
    except Exception as e:
        print(f"Cache delete pattern error: {e}")

    return 0


def cache_stats() -> dict:
    """Get cache statistics."""
    client = get_redis_client()
    if not client:
        return {"status": "unavailable", "enabled": CACHE_ENABLED}

    try:
        info = client.info("memory")
        keys_count = client.dbsize()

        return {
            "status": "connected",
            "enabled": CACHE_ENABLED,
            "keys_count": keys_count,
            "used_memory": info.get("used_memory_human", "N/A"),
            "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
            "ttl_config": CACHE_TTL,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def cached(ttl_type: str = "default", key_prefix: str = None):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl_type="statistics", key_prefix="stats")
        async def get_statistics():
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call the function
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                cache_set(cache_key, result, ttl_type)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call the function
            result = func(*args, **kwargs)

            # Store in cache
            if result is not None:
                cache_set(cache_key, result, ttl_type)

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Initialize Redis on module load
get_redis_client()
