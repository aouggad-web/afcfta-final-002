"""
Redis Cache Service for Gemini API calls optimization
Caches AI responses to reduce API calls and improve performance

Fallback: When Redis is unavailable (connection refused), a JSON file cache
under backend/data/ai_cache/ is used automatically so the cache survives
server restarts without requiring Redis.
"""
import os
import redis
import json
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from functools import wraps

logger = logging.getLogger(__name__)

# Cache TTL configurations (in seconds)
CACHE_TTL = {
    "gemini_analysis": 6 * 60 * 60,       # 6 hours for trade analysis
    "gemini_profile": 24 * 60 * 60,        # 24 hours for country profiles
    "gemini_summary": 24 * 60 * 60,        # 24 hours for summaries
    "gemini_value_chains": 12 * 60 * 60,   # 12 hours for value chains
    "gemini_product": 12 * 60 * 60,        # 12 hours for product analysis
    "oec_data": 24 * 60 * 60,              # 24 hours for OEC data
    "default": 6 * 60 * 60                 # 6 hours default
}

# Default directory for JSON file cache
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "ai_cache"


class JsonFileCacheService:
    """
    Persistent JSON file cache that survives server restarts.
    Used as a fallback when Redis is unavailable.

    Each cache entry is stored as a separate JSON file named by its cache key.
    A lightweight index file (index.json) tracks TTL expiry without loading all files.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or _DEFAULT_CACHE_DIR)
        self._ensure_dir()

    def _ensure_dir(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"JsonFileCache: cannot create cache dir {self.cache_dir}: {e}")

    def _key_to_filename(self, key: str) -> Path:
        safe = key.replace(":", "_")
        return self.cache_dir / f"{safe}.json"

    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"zlecaf:{prefix}:{param_hash}"

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._generate_cache_key(prefix, params)
        filepath = self._key_to_filename(key)
        if not filepath.exists():
            logger.debug(f"JsonFileCache MISS for {key}")
            return None
        try:
            with filepath.open("r", encoding="utf-8") as f:
                entry = json.load(f)
            expires_at = entry.get("_file_cache_expires_at", 0)
            if expires_at and time.time() > expires_at:
                filepath.unlink(missing_ok=True)
                logger.debug(f"JsonFileCache EXPIRED for {key}")
                return None
            logger.debug(f"JsonFileCache HIT for {key}")
            return entry.get("data")
        except Exception as e:
            logger.error(f"JsonFileCache read error for {key}: {e}")
            return None

    def set(
        self,
        prefix: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        ttl_type: str = "default"
    ) -> bool:
        key = self._generate_cache_key(prefix, params)
        filepath = self._key_to_filename(key)
        ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
        cached_data = {
            **data,
            "_cache_metadata": {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": ttl,
                "cache_type": ttl_type,
                "from_cache": True,
                "backend": "json_file"
            }
        }
        entry = {
            "_file_cache_expires_at": time.time() + ttl,
            "data": cached_data
        }
        try:
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, default=str)
            logger.debug(f"JsonFileCache SET for {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"JsonFileCache write error for {key}: {e}")
            return False

    def invalidate(self, prefix: str, params: Dict[str, Any]) -> bool:
        key = self._generate_cache_key(prefix, params)
        filepath = self._key_to_filename(key)
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"JsonFileCache invalidated: {key}")
            return True
        except Exception as e:
            logger.error(f"JsonFileCache invalidate error for {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Remove all cache files whose name contains the pattern."""
        deleted = 0
        try:
            safe_pattern = pattern.replace(":", "_")
            for filepath in self.cache_dir.glob("*.json"):
                if safe_pattern in filepath.name or pattern == "*":
                    filepath.unlink(missing_ok=True)
                    deleted += 1
            logger.info(f"JsonFileCache invalidated {deleted} files matching '{pattern}'")
        except Exception as e:
            logger.error(f"JsonFileCache invalidate_pattern error: {e}")
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        try:
            files = list(self.cache_dir.glob("*.json"))
            now = time.time()
            active = 0
            expired = 0
            for f in files:
                try:
                    entry = json.loads(f.read_text(encoding="utf-8"))
                    if entry.get("_file_cache_expires_at", 0) > now:
                        active += 1
                    else:
                        expired += 1
                except Exception:
                    pass
            return {
                "status": "active",
                "backend": "json_file",
                "cache_dir": str(self.cache_dir),
                "total_files": len(files),
                "active_entries": active,
                "expired_entries": expired
            }
        except Exception as e:
            return {"status": "error", "backend": "json_file", "error": str(e)}

    def clear_all(self) -> int:
        return self.invalidate_pattern("*")


class RedisCacheService:
    """
    Redis-based caching service for expensive API calls.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self._connected = False

    def _get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client with lazy initialization"""
        if self._client is None:
            try:
                app_env = os.environ.get("APP_ENV", "development")
                if app_env != "development":
                    parsed = urlparse(self.redis_url)
                    if not parsed.password:
                        logger.warning(
                            "Redis URL contains no password — configure a password for "
                            "production use (set REDIS_URL=redis://:password@host:port)"
                        )

                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
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
        if self._client is None:
            self._get_client()
        return self._connected

    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"zlecaf:{prefix}:{param_hash}"

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return None
        try:
            key = self._generate_cache_key(prefix, params)
            cached = client.get(key)
            if cached:
                logger.debug(f"Cache HIT for {key}")
                return json.loads(cached)
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
        client = self._get_client()
        if not client:
            return False
        try:
            key = self._generate_cache_key(prefix, params)
            ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
            cached_data = {
                **data,
                "_cache_metadata": {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "ttl_seconds": ttl,
                    "cache_type": ttl_type,
                    "from_cache": True,
                    "backend": "redis"
                }
            }
            client.setex(key, ttl, json.dumps(cached_data, default=str))
            logger.debug(f"Cache SET for {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def invalidate(self, prefix: str, params: Dict[str, Any]) -> bool:
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
        client = self._get_client()
        if not client:
            return {"status": "disconnected"}
        try:
            info = client.info("stats")
            keys_count = len(client.keys("zlecaf:*"))
            return {
                "status": "connected",
                "backend": "redis",
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
        return self.invalidate_pattern("*")


class HybridCacheService:
    """
    Tries Redis first; falls back to JSON file cache when Redis is unavailable.
    This ensures cached AI responses survive server restarts even without Redis.
    """

    def __init__(self):
        self._redis = RedisCacheService()
        self._file = JsonFileCacheService()

    def _use_redis(self) -> bool:
        return self._redis.is_connected

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self._use_redis():
            result = self._redis.get(prefix, params)
            if result is not None:
                return result
        return self._file.get(prefix, params)

    def set(
        self,
        prefix: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        ttl_type: str = "default"
    ) -> bool:
        redis_ok = False
        if self._use_redis():
            redis_ok = self._redis.set(prefix, params, data, ttl_type)
        file_ok = self._file.set(prefix, params, data, ttl_type)
        return redis_ok or file_ok

    def invalidate(self, prefix: str, params: Dict[str, Any]) -> bool:
        r = self._redis.invalidate(prefix, params) if self._use_redis() else False
        f = self._file.invalidate(prefix, params)
        return r or f

    def invalidate_pattern(self, pattern: str) -> int:
        r = self._redis.invalidate_pattern(pattern) if self._use_redis() else 0
        f = self._file.invalidate_pattern(pattern)
        return r + f

    def get_stats(self) -> Dict[str, Any]:
        redis_stats = self._redis.get_stats()
        file_stats = self._file.get_stats()
        return {
            "redis": redis_stats,
            "json_file": file_stats,
            "active_backend": "redis" if self._use_redis() else "json_file"
        }

    def clear_all(self) -> int:
        r = self._redis.clear_all() if self._use_redis() else 0
        f = self._file.clear_all()
        return r + f

    @property
    def is_connected(self) -> bool:
        return self._redis.is_connected


# Singleton instance — used by gemini_trade_service and routes
cache_service = HybridCacheService()


def cached_gemini_call(cache_type: str = "gemini_analysis"):
    """
    Decorator for caching Gemini API calls.

    Usage:
        @cached_gemini_call("gemini_profile")
        async def get_country_profile(country: str, lang: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_params = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cached = cache_service.get(cache_type, cache_params)
            if cached:
                return cached
            result = await func(*args, **kwargs)
            if result and not result.get("error"):
                cache_service.set(cache_type, cache_params, result, cache_type)
            return result
        return wrapper
    return decorator


def get_data_freshness(cached_at: Optional[str]) -> Dict[str, Any]:
    """
    Calculate data freshness information.
    Returns human-readable freshness indicators.
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
            "is_fresh": age_seconds < 3600,
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
