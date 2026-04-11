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

import os
import json
import hashlib
from typing import Optional, Any, Union
from datetime import timedelta
from functools import wraps

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
    "statistics": 3600,        # 1 hour
    "countries": 7200,         # 2 hours
    "search": 1800,            # 30 minutes
    "calculation": 900,        # 15 minutes
    "regulatory": 3600,        # 1 hour
    "default": 600             # 10 minutes
}

# Global Redis client (type hinted with a forward reference so it is safe
# even when the redis package is not installed)
_redis_client: "Optional[Any]" = None


def get_redis_client() -> "Optional[Any]":
    """Get or create Redis client singleton."""
    global _redis_client
    
    if not REDIS_AVAILABLE or not CACHE_ENABLED:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
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
    """Get value from cache."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"Cache get error: {e}")
    
    return None


def cache_set(key: str, value: Any, ttl_type: str = "default") -> bool:
    """Set value in cache with TTL."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern."""
    client = get_redis_client()
    if not client:
        return 0
    
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
            "ttl_config": CACHE_TTL
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
