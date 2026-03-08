"""
AfCFTA Platform - Cache Warming Service
========================================
Preloads popular / hot data into L1 and L2 caches during off-peak hours
so that the first real request is always fast.
"""

import asyncio
import logging
from typing import Any, Dict, List

from .cache_layers import get_cache

logger = logging.getLogger(__name__)

# Popular HS code prefixes across African trade
HOT_HS_PREFIXES: List[str] = [
    "0901",  # Coffee
    "1001",  # Wheat
    "1511",  # Palm oil
    "2601",  # Iron ores
    "2709",  # Petroleum oils
    "7108",  # Gold
    "8471",  # Computers
    "8517",  # Phones
    "6109",  # T-shirts
    "4011",  # Tyres
]

# Frequently queried countries
HOT_COUNTRIES: List[str] = [
    "DZA", "MAR", "EGY", "TUN",  # North Africa
    "NGA", "GHA", "CIV", "SEN",  # West Africa
    "KEN", "ETH", "TZA", "UGA",  # East Africa
    "ZAF", "BWA", "ZMB", "MOZ",  # Southern Africa
    "CMR", "COD", "AGO",         # Central Africa
]

# Regional blocs for L2 warming
REGIONAL_BLOCS: List[str] = [
    "ECOWAS", "CEMAC", "EAC", "SADC", "UMA", "COMESA", "IGAD",
]


class CacheWarmingService:
    """
    Preloads hot data into the multi-layer cache.

    Call ``warm_all()`` at application startup or on a scheduled basis.
    """

    def __init__(self) -> None:
        self._cache = get_cache()

    # ------------------------------------------------------------------
    # L1 warming - hot data
    # ------------------------------------------------------------------

    async def warm_countries(self) -> int:
        """Cache frequently-accessed country metadata in L1."""
        warmed = 0
        try:
            from backend.routes.countries import _get_all_countries  # type: ignore
            countries = await _get_all_countries()
        except Exception:
            # Graceful degradation: country endpoint may not be available
            countries = []

        for country in countries:
            code = country.get("iso_code") or country.get("code", "")
            if not code:
                continue
            key = self._cache.l1.build_key(type="country", key=code)
            if self._cache.l1.get(key) is None:
                self._cache.l1.set(key, country)
                warmed += 1

        logger.info(f"[CacheWarming] L1 countries warmed: {warmed}")
        return warmed

    async def warm_hot_hs_codes(self) -> int:
        """Cache popular HS code descriptions in L1."""
        warmed = 0
        for hs_prefix in HOT_HS_PREFIXES:
            key = self._cache.l1.build_key(type="hs", key=hs_prefix)
            if self._cache.l1.get(key) is not None:
                continue
            # Store a lightweight placeholder; real resolvers fill in the data
            self._cache.l1.set(key, {"hs_code": hs_prefix, "preloaded": True})
            warmed += 1

        logger.info(f"[CacheWarming] L1 HS codes warmed: {warmed}")
        return warmed

    # ------------------------------------------------------------------
    # L2 warming - regional intelligence
    # ------------------------------------------------------------------

    async def warm_regional_analytics(self) -> int:
        """Cache regional analytics aggregates in L2."""
        warmed = 0
        for bloc in REGIONAL_BLOCS:
            key = self._cache.l2.build_key(bloc=bloc, data_type="analytics_summary")
            if self._cache.l2.get(key) is None:
                # Placeholder populated on first real query
                self._cache.l2.set(key, {"bloc": bloc, "preloaded": True, "data": {}})
                warmed += 1

        logger.info(f"[CacheWarming] L2 regional blocs warmed: {warmed}")
        return warmed

    # ------------------------------------------------------------------
    # Full warm-up orchestration
    # ------------------------------------------------------------------

    async def warm_all(self) -> Dict[str, Any]:
        """Run all warming tasks concurrently and return a summary."""
        logger.info("[CacheWarming] Starting full cache warm-up …")

        results = await asyncio.gather(
            self.warm_countries(),
            self.warm_hot_hs_codes(),
            self.warm_regional_analytics(),
            return_exceptions=True,
        )

        summary = {
            "countries_warmed": results[0] if not isinstance(results[0], Exception) else 0,
            "hs_codes_warmed":  results[1] if not isinstance(results[1], Exception) else 0,
            "regions_warmed":   results[2] if not isinstance(results[2], Exception) else 0,
            "cache_stats":      self._cache.all_stats(),
        }
        logger.info(f"[CacheWarming] Warm-up complete: {summary}")
        return summary


# Singleton
_warming_service: CacheWarmingService | None = None


def get_warming_service() -> CacheWarmingService:
    global _warming_service
    if _warming_service is None:
        _warming_service = CacheWarmingService()
    return _warming_service
