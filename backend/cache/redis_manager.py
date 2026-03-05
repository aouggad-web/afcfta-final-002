"""
Enhanced Redis Cache Manager with 4-layer caching strategy.

L1 – Hot data      (TTL: 5 min)   – real-time tariff lookups
L2 – Warm data     (TTL: 1 hour)  – country profiles, HS summaries
L3 – Cold data     (TTL: 24 hours)– analytics dashboards, bulk results
L4 – Persistent    (TTL: 7 days)  – reference data, HS catalogue

Gracefully falls back to an in-process dict cache when Redis is unavailable.
"""

import json
import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_LAYER_TTL: dict[str, int] = {
    "L1": 5 * 60,
    "L2": 60 * 60,
    "L3": 24 * 60 * 60,
    "L4": 7 * 24 * 60 * 60,
}

_DEFAULT_LAYER = "L2"


class _InMemoryFallback:
    """Simple TTL-aware in-memory dict used when Redis is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ex: int = 0) -> None:
        expires_at = time.time() + ex if ex else 0.0
        self._store[key] = (value, expires_at)

    def delete_pattern(self, pattern: str) -> int:
        prefix = pattern.rstrip("*")
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def info(self) -> dict[str, Any]:
        return {"used_memory_human": "N/A (in-memory fallback)", "connected_clients": 0}


class RedisManager:
    """
    4-layer Redis cache manager.

    Usage::

        cache = RedisManager()
        cache.set("my_key", {"data": 1}, layer="L1")
        value = cache.get("my_key", layer="L1")
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 1,
    ) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._client: Any = None
        self._fallback = _InMemoryFallback()
        self._use_redis = False
        self._hits = 0
        self._misses = 0
        self._connect()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        try:
            import redis  # type: ignore

            client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            client.ping()
            self._client = client
            self._use_redis = True
            logger.info("RedisManager: connected to Redis at %s:%s db=%s", self._host, self._port, self._db)
        except Exception as exc:
            logger.warning("RedisManager: Redis unavailable (%s). Using in-memory fallback.", exc)
            self._use_redis = False

    def _backend(self):
        return self._client if self._use_redis else self._fallback

    @staticmethod
    def _ttl(layer: str) -> int:
        return _LAYER_TTL.get(layer, _LAYER_TTL[_DEFAULT_LAYER])

    @staticmethod
    def _prefixed(key: str, layer: str) -> str:
        return f"afcfta:{layer}:{key}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, layer: str = _DEFAULT_LAYER) -> Optional[Any]:
        full_key = self._prefixed(key, layer)
        try:
            raw = self._backend().get(full_key)
            if raw is None:
                self._misses += 1
                return None
            self._hits += 1
            return json.loads(raw)
        except Exception as exc:
            logger.debug("RedisManager.get error: %s", exc)
            self._misses += 1
            return None

    def set(self, key: str, value: Any, layer: str = _DEFAULT_LAYER) -> bool:
        full_key = self._prefixed(key, layer)
        ttl = self._ttl(layer)
        try:
            serialised = json.dumps(value, default=str)
            self._backend().set(full_key, serialised, ex=ttl)
            return True
        except Exception as exc:
            logger.debug("RedisManager.set error: %s", exc)
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        try:
            if self._use_redis:
                keys = list(self._client.scan_iter(f"afcfta:*{pattern}*"))
                if keys:
                    return self._client.delete(*keys)
                return 0
            return self._fallback.delete_pattern(pattern)
        except Exception as exc:
            logger.debug("RedisManager.invalidate_pattern error: %s", exc)
            return 0

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = round(self._hits / total, 4) if total else 0.0
        backend_info: dict[str, Any] = {}
        try:
            if self._use_redis:
                info = self._client.info("memory")
                backend_info = {
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "connected_clients": self._client.info("clients").get("connected_clients", 0),
                }
            else:
                backend_info = self._fallback.info()
        except Exception:
            pass

        return {
            "backend": "redis" if self._use_redis else "in_memory_fallback",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "layers": list(_LAYER_TTL.keys()),
            "layer_ttls_seconds": _LAYER_TTL,
            "backend_info": backend_info,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def make_key(*parts: str) -> str:
        """Build a cache key from arbitrary parts, hashing if too long."""
        raw = ":".join(str(p) for p in parts)
        if len(raw) > 200:
            return hashlib.sha256(raw.encode()).hexdigest()
        return raw


# Module-level singleton
cache_manager = RedisManager()
