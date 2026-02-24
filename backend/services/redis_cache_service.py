"""
Redis Cache Service for Gemini API calls optimization
Caches AI responses to reduce API calls and improve performance
"""
import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from functools import wraps

logger = logging.getLogger(__name__)

# Cache TTL configurations (in seconds)
CACHE_TTL = {
    "gemini_analysis": 6 * 60 * 60,      # 6 hours for trade analysis
    "gemini_profile": 24 * 60 * 60,       # 24 hours for country profiles
    "gemini_summary": 6 * 60 * 60,        # 6 hours for summaries
    "gemini_value_chains": 6 * 60 * 60,   # 6 hours for value chains
    "gemini_product": 12 * 60 * 60,       # 12 hours for product analysis
    "oec_data": 24 * 60 * 60,             # 24 hours for OEC data
    "default": 6 * 60 * 60                # 6 hours default
}


class RedisCacheService:
    """
    Redis-based caching service for expensive API calls
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    def _get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client with lazy initialization"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self._client.ping()
                self._connected = True
                logger.info("Redis cache connected successfully")
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self._client = None
                self._connected = False
            except Exception as e:
                logger.error(f"Unexpected Redis error: {e}")
                self._client = None
                self._connected = False
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if self._client is None:
            self._get_client()
        return self._connected
    
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key based on parameters"""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"zlecaf:{prefix}:{param_hash}"
    
    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached data if available
        Returns None if not cached or expired
        """
        client = self._get_client()
        if not client:
            return None
        
        try:
            key = self._generate_cache_key(prefix, params)
            cached = client.get(key)
            
            if cached:
                data = json.loads(cached)
                logger.debug(f"Cache HIT for {key}")
                return data
            
            logger.debug(f"Cache MISS for {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self, 
        prefix: str, 
        params: Dict[str, Any], 
        data: Dict[str, Any],
        ttl_type: str = "default"
    ) -> bool:
        """
        Cache data with appropriate TTL
        Adds metadata about cache time
        """
        client = self._get_client()
        if not client:
            return False
        
        try:
            key = self._generate_cache_key(prefix, params)
            ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
            
            # Add cache metadata
            cached_data = {
                **data,
                "_cache_metadata": {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "ttl_seconds": ttl,
                    "cache_type": ttl_type,
                    "from_cache": True
                }
            }
            
            client.setex(key, ttl, json.dumps(cached_data, default=str))
            logger.debug(f"Cache SET for {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(self, prefix: str, params: Dict[str, Any]) -> bool:
        """Invalidate a specific cache entry"""
        client = self._get_client()
        if not client:
            return False
        
        try:
            key = self._generate_cache_key(prefix, params)
            client.delete(key)
            logger.info(f"Cache invalidated: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern"""
        client = self._get_client()
        if not client:
            return 0
        
        try:
            keys = client.keys(f"zlecaf:{pattern}:*")
            if keys:
                deleted = client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        client = self._get_client()
        if not client:
            return {"status": "disconnected"}
        
        try:
            info = client.info("stats")
            keys_count = len(client.keys("zlecaf:*"))
            
            return {
                "status": "connected",
                "total_zlecaf_keys": keys_count,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def clear_all(self) -> int:
        """Clear all ZLECAf cache entries (use with caution)"""
        return self.invalidate_pattern("*")


# Singleton instance
cache_service = RedisCacheService()


def cached_gemini_call(cache_type: str = "gemini_analysis"):
    """
    Decorator for caching Gemini API calls
    
    Usage:
        @cached_gemini_call("gemini_profile")
        async def get_country_profile(country: str, lang: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache params from function arguments
            cache_params = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            
            # Try to get from cache
            cached = cache_service.get(cache_type, cache_params)
            if cached:
                return cached
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result if it's valid
            if result and not result.get("error"):
                cache_service.set(cache_type, cache_params, result, cache_type)
            
            return result
        
        return wrapper
    return decorator


def get_data_freshness(cached_at: Optional[str]) -> Dict[str, Any]:
    """
    Calculate data freshness information
    Returns human-readable freshness indicators
    """
    if not cached_at:
        return {
            "is_fresh": True,
            "from_cache": False,
            "age_seconds": 0,
            "age_human": "Données en direct",
            "age_human_en": "Live data"
        }
    
    try:
        cached_time = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = now - cached_time
        age_seconds = int(age.total_seconds())
        
        # Human-readable age
        if age_seconds < 60:
            age_human = "Il y a quelques secondes"
            age_human_en = "A few seconds ago"
        elif age_seconds < 3600:
            minutes = age_seconds // 60
            age_human = f"Il y a {minutes} min"
            age_human_en = f"{minutes} min ago"
        elif age_seconds < 86400:
            hours = age_seconds // 3600
            age_human = f"Il y a {hours}h"
            age_human_en = f"{hours}h ago"
        else:
            days = age_seconds // 86400
            age_human = f"Il y a {days}j"
            age_human_en = f"{days}d ago"
        
        return {
            "is_fresh": age_seconds < 3600,  # Less than 1 hour = fresh
            "from_cache": True,
            "age_seconds": age_seconds,
            "age_human": age_human,
            "age_human_en": age_human_en,
            "cached_at": cached_at
        }
    except Exception as e:
        logger.error(f"Error calculating freshness: {e}")
        return {
            "is_fresh": True,
            "from_cache": False,
            "age_seconds": 0,
            "age_human": "Données en direct",
            "age_human_en": "Live data"
        }
