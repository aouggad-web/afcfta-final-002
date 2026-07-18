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
from pathlib import Path
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
    "oec_index": 86400,  # 24 hours (multi-country trader indices — expensive to rebuild)
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


# ---------------------------------------------------------------------------
# Disk-backed persistent tier (Redis-less deployments and cold starts)
# ---------------------------------------------------------------------------
# The in-memory store above is process-local and empty on every restart — in
# an environment without Redis provisioned (dev, sandbox, or a Redis outage),
# every container/worker restart previously meant re-hitting upstream APIs
# (OEC in particular) from a cold cache, even for data fetched minutes
# earlier. This tier persists cache entries as one JSON file per key under
# ``CACHE_DIR``, so a cold start (or a Redis-less deployment) can still serve
# from disk instead of the network — reducing OEC call volume and exposure to
# its rate limits/outages. Best-effort: any I/O error degrades silently back
# to the in-memory/network path, never raises.
_DISK_CACHE_ENABLED = os.environ.get("DISK_CACHE_ENABLED", "true").lower() == "true"
_DISK_CACHE_DIR = Path(
    os.environ.get("CACHE_DIR") or (Path(__file__).resolve().parent.parent / "data" / "_cache")
)


def _disk_path(key: str) -> Path:
    # Filenames must be filesystem-safe and bounded in length regardless of
    # key content — hash the full key rather than sanitizing it.
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return _DISK_CACHE_DIR / f"{digest}.json"


def _disk_set(key: str, value: Any, ttl_seconds: int) -> bool:
    if not _DISK_CACHE_ENABLED:
        return False
    try:
        _DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _disk_path(key)
        payload = json.dumps({"expiry": _now() + ttl_seconds, "value": value}, default=str)
        # Atomic write: a crash mid-write must never leave a corrupt cache file.
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.replace(path)
        return True
    except OSError:
        return False


def _disk_get(key: str, allow_stale: bool = False) -> Optional[Any]:
    if not _DISK_CACHE_ENABLED:
        return None
    try:
        path = _disk_path(key)
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if allow_stale or _now() < record.get("expiry", 0):
        return record.get("value")
    return None


def _disk_delete(key: str) -> bool:
    try:
        path = _disk_path(key)
        if path.exists():
            path.unlink()
            return True
    except OSError:
        pass
    return False


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

    # No Redis → in-memory fallback, then disk (cold start: repopulate memory
    # from disk so the next read is fast and doesn't touch the filesystem).
    value = _mem_get(key)
    if value is not None:
        return value
    value = _disk_get(key)
    if value is not None:
        _MEMORY_STORE[key] = (value, _now() + 1)  # short in-memory grace only
    return value


def cache_get_stale(key: str) -> Optional[Any]:
    """
    Get a cached value even if expired (stale-on-error).

    Used to keep serving the last known good value when the upstream source
    is down or rate-limited. Only the in-memory/disk backends retain expired
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

    value = _mem_get(key, allow_stale=True)
    if value is not None:
        return value
    # Disk tier also serves stale: a fresh process (empty in-memory store)
    # that just restarted during an upstream outage should still be able to
    # serve the last known-good value instead of an empty error.
    return _disk_get(key, allow_stale=True)


def cache_set(key: str, value: Any, ttl_type: str = "default") -> bool:
    """Set value in cache with TTL (Redis if available, else in-memory + disk)."""
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

    # No Redis → in-memory (fast reads) + disk (survives process restarts).
    _mem_set(key, value, ttl)
    _disk_set(key, value, ttl)
    return True


def cache_delete(key: str) -> bool:
    """Delete a key from cache (Redis if available, else in-memory + disk)."""
    client = get_redis_client()
    if not client:
        # In-memory + disk fallback so invalidation works without Redis too.
        removed_mem = _MEMORY_STORE.pop(key, None) is not None
        removed_disk = _disk_delete(key)
        return removed_mem or removed_disk

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
        # No Redis doesn't mean no caching: the in-memory + disk fallback tiers
        # are still active (this is the normal state in dev/sandbox and any
        # deployment without Redis provisioned) — report them as such rather
        # than a misleading "unavailable".
        disk_files = 0
        if _DISK_CACHE_ENABLED:
            try:
                disk_files = sum(1 for _ in _DISK_CACHE_DIR.glob("*.json"))
            except OSError:
                disk_files = 0
        return {
            "status": "fallback (memory + disk)",
            "enabled": CACHE_ENABLED,
            "memory_keys_count": len(_MEMORY_STORE),
            "disk_keys_count": disk_files,
            "disk_cache_enabled": _DISK_CACHE_ENABLED,
            "disk_cache_dir": str(_DISK_CACHE_DIR),
            "ttl_config": CACHE_TTL,
        }

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
