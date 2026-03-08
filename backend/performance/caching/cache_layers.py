"""
AfCFTA Platform - Multi-Layer Redis Caching Architecture
=========================================================
Implements L1-L4 caching strategy:
  L1 (hot_data):      TTL 1h  - Frequent tariff lookups, popular HS codes, active countries
  L2 (regional_intel): TTL 24h - Regional comparisons, investment scores, corridor data
  L3 (calculations):   TTL 6h  - Complex calculations, bulk operations, AI recommendations
  L4 (realtime):       TTL 5m  - Live updates, notifications, system status
"""

import os
import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# Cache Layer Configuration
# =============================================================================

CACHE_LAYERS: Dict[str, Dict[str, Any]] = {
    "L1_hot_data": {
        "ttl": 3600,
        "pattern": "hot:{type}:{key}",
        "use_cases": [
            "frequent_tariff_lookups",
            "popular_hs_codes",
            "active_countries",
        ],
        "db": 0,
    },
    "L2_regional_intel": {
        "ttl": 86400,
        "pattern": "region:{bloc}:{data_type}",
        "use_cases": [
            "regional_comparisons",
            "investment_scores",
            "corridor_data",
        ],
        "db": 1,
    },
    "L3_calculations": {
        "ttl": 21600,
        "pattern": "calc:{hash}",
        "use_cases": [
            "complex_calculations",
            "bulk_operations",
            "ai_recommendations",
        ],
        "db": 2,
    },
    "L4_realtime": {
        "ttl": 300,
        "pattern": "live:{channel}:{timestamp}",
        "use_cases": [
            "live_updates",
            "notifications",
            "system_status",
        ],
        "db": 3,
    },
}


class CacheLayer:
    """Single Redis cache layer with connection management."""

    def __init__(self, layer_name: str, config: Dict[str, Any]) -> None:
        self.name = layer_name
        self.ttl = config["ttl"]
        self.pattern = config["pattern"]
        self.db = config.get("db", 0)
        self._client: Optional["redis.Redis"] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Optional["redis.Redis"]:
        if not REDIS_AVAILABLE:
            return None
        if self._client is None:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
            try:
                self._client = redis.from_url(
                    redis_url,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                self._client.ping()
                logger.info(f"[{self.name}] Redis DB{self.db} connected")
            except Exception as exc:
                logger.warning(f"[{self.name}] Redis unavailable: {exc}")
                self._client = None
        return self._client

    @staticmethod
    def _make_hash(data: Any) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_key(self, **kwargs: Any) -> str:
        """Build a cache key from the layer pattern and supplied kwargs."""
        key = self.pattern
        for k, v in kwargs.items():
            key = key.replace(f"{{{k}}}", str(v))
        # Replace any remaining placeholders with a hash of remaining values
        remaining = {k: v for k, v in kwargs.items() if f"{{{k}}}" in self.pattern}
        if "{" in key:
            key = key.split("{")[0] + self._make_hash(remaining)
        return f"afcfta:{self.name.lower()}:{key}"

    def get(self, key: str) -> Optional[Any]:
        client = self._get_client()
        if client is None:
            return None
        try:
            raw = client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning(f"[{self.name}] GET failed for {key}: {exc}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            client.setex(key, ttl or self.ttl, json.dumps(value, default=str))
            return True
        except Exception as exc:
            logger.warning(f"[{self.name}] SET failed for {key}: {exc}")
            return False

    def delete(self, key: str) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            client.delete(key)
            return True
        except Exception as exc:
            logger.warning(f"[{self.name}] DELETE failed for {key}: {exc}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern."""
        client = self._get_client()
        if client is None:
            return 0
        try:
            keys = list(client.scan_iter(pattern))
            if keys:
                client.delete(*keys)
            return len(keys)
        except Exception as exc:
            logger.warning(f"[{self.name}] Pattern invalidation failed: {exc}")
            return 0

    def stats(self) -> Dict[str, Any]:
        """Return layer statistics."""
        client = self._get_client()
        if client is None:
            return {"connected": False, "layer": self.name}
        try:
            info = client.info("memory")
            return {
                "connected": True,
                "layer": self.name,
                "ttl": self.ttl,
                "db": self.db,
                "used_memory_human": info.get("used_memory_human", "N/A"),
            }
        except Exception:
            return {"connected": False, "layer": self.name}


# =============================================================================
# Multi-Layer Cache Manager
# =============================================================================

class MultiLayerCache:
    """
    Unified interface for all four cache layers.

    Usage::

        cache = MultiLayerCache()

        # Store and retrieve hot data (L1)
        cache.l1.set(cache.l1.build_key(type="tariff", key="DZ-0901"), data)

        # Store calculation result (L3)
        cache.l3.set(cache.l3.build_key(hash=calc_hash), result)
    """

    def __init__(self) -> None:
        self.l1 = CacheLayer("L1_hot_data",       CACHE_LAYERS["L1_hot_data"])
        self.l2 = CacheLayer("L2_regional_intel",  CACHE_LAYERS["L2_regional_intel"])
        self.l3 = CacheLayer("L3_calculations",    CACHE_LAYERS["L3_calculations"])
        self.l4 = CacheLayer("L4_realtime",        CACHE_LAYERS["L4_realtime"])

    def all_stats(self) -> Dict[str, Any]:
        return {
            "L1_hot_data":      self.l1.stats(),
            "L2_regional_intel": self.l2.stats(),
            "L3_calculations":  self.l3.stats(),
            "L4_realtime":      self.l4.stats(),
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }

    def invalidate_country(self, country_code: str) -> Dict[str, int]:
        """Invalidate all cached data for a given country across all layers."""
        pattern = f"afcfta:*:{country_code}*"
        return {
            "L1": self.l1.invalidate_pattern(pattern),
            "L2": self.l2.invalidate_pattern(pattern),
            "L3": self.l3.invalidate_pattern(pattern),
            "L4": self.l4.invalidate_pattern(pattern),
        }

    def invalidate_region(self, regional_bloc: str) -> Dict[str, int]:
        """Invalidate regional intelligence cache for a given bloc."""
        pattern = f"afcfta:l2_regional_intel:*{regional_bloc}*"
        return {
            "L2": self.l2.invalidate_pattern(pattern),
        }


# =============================================================================
# Decorator helpers
# =============================================================================

def cache_with_layer(layer: CacheLayer, key_func: Callable[..., str]):
    """
    Decorator: cache the result of an async function using the given cache layer.

    ``key_func`` receives the same arguments as the decorated function and must
    return a string cache key.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs)
            cached = layer.get(key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            layer.set(key, result)
            return result
        return wrapper
    return decorator


# Singleton instance
_cache: Optional[MultiLayerCache] = None


def get_cache() -> MultiLayerCache:
    """Get the singleton MultiLayerCache instance."""
    global _cache
    if _cache is None:
        _cache = MultiLayerCache()
    return _cache
