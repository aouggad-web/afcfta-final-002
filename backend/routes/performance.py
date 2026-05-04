"""
AfCFTA Platform - Performance Monitoring API Routes
====================================================
Exposes cache statistics, performance metrics, and cache management.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance Monitoring"])


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get statistics for all four Redis cache layers (L1-L4).
    Includes connection status, TTL configuration, and memory usage.
    """
    try:
        from performance.caching.cache_layers import get_cache
        return get_cache().all_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/cache/warm")
async def warm_cache():
    """
    Trigger a full cache warm-up cycle.
    Preloads hot data (countries, HS codes) into L1 and
    regional analytics into L2.
    """
    try:
        from performance.caching.cache_warming import get_warming_service
        import asyncio
        service = get_warming_service()
        summary = await service.warm_all()
        return {"status": "completed", "summary": summary}
    except Exception as exc:
        logger.error(f"Cache warming error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/cache/country/{country_code}")
async def invalidate_country_cache(country_code: str):
    """
    Invalidate all cached data for a specific country across all layers.
    Use this after updating country-specific data.
    """
    try:
        from performance.caching.cache_layers import get_cache
        result = get_cache().invalidate_country(country_code.upper())
        return {"invalidated": result, "country": country_code.upper()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/cache/region/{bloc}")
async def invalidate_region_cache(bloc: str):
    """
    Invalidate regional intelligence cache for a specific bloc.
    Use this after updating regional data.
    """
    try:
        from performance.caching.cache_layers import get_cache
        result = get_cache().invalidate_region(bloc.upper())
        return {"invalidated": result, "bloc": bloc.upper()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/metrics")
async def get_performance_metrics():
    """
    Get in-process performance metrics:
    - Cache hit/miss rates per operation
    - Query latency percentiles (p50, p95, p99)
    - Slow query log (queries > 500ms)
    """
    try:
        from performance.monitoring.performance_metrics import get_metrics
        return get_metrics().summary()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/metrics/slow-queries")
async def get_slow_queries():
    """Return the 200 most recent slow queries (> 500ms)."""
    try:
        from performance.monitoring.performance_metrics import get_metrics
        return {"slow_queries": get_metrics().slow_queries()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
