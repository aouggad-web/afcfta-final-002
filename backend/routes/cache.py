"""
Cache Management API
====================
Endpoints for cache monitoring and management.
"""

from fastapi import APIRouter, HTTPException
from services.cache_service import (
    cache_stats, 
    cache_delete_pattern, 
    cache_get, 
    cache_set,
    get_redis_client,
    CACHE_TTL
)

router = APIRouter(prefix="/cache")


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics and configuration.
    
    Returns:
    - status: connected/unavailable/error
    - keys_count: number of cached keys
    - used_memory: current memory usage
    - ttl_config: TTL settings for different cache types
    """
    return cache_stats()


@router.get("/health")
async def cache_health():
    """Check if Redis cache is healthy."""
    client = get_redis_client()
    if not client:
        return {
            "healthy": False,
            "message": "Redis not available"
        }
    
    try:
        client.ping()
        return {
            "healthy": True,
            "message": "Redis is responding"
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": str(e)
        }


@router.delete("/clear")
async def clear_all_cache():
    """
    Clear all cached data.
    Use with caution - will remove all cached responses.
    """
    deleted = cache_delete_pattern("*")
    return {
        "success": True,
        "keys_deleted": deleted,
        "message": f"Cleared {deleted} cached keys"
    }


@router.delete("/clear/{prefix}")
async def clear_cache_by_prefix(prefix: str):
    """
    Clear cached data by prefix.
    
    Available prefixes:
    - statistics: Clear statistics cache
    - search: Clear search results cache
    - calculation: Clear tariff calculations cache
    - regulatory: Clear regulatory data cache
    - countries: Clear countries data cache
    """
    deleted = cache_delete_pattern(f"{prefix}:*")
    return {
        "success": True,
        "prefix": prefix,
        "keys_deleted": deleted,
        "message": f"Cleared {deleted} keys with prefix '{prefix}'"
    }


@router.get("/keys")
async def list_cache_keys(pattern: str = "*", limit: int = 100):
    """
    List cached keys matching a pattern.
    
    Args:
    - pattern: Redis key pattern (default: *)
    - limit: Maximum keys to return (default: 100)
    """
    client = get_redis_client()
    if not client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        keys = client.keys(f"zlecaf:{pattern}")
        keys = keys[:limit]
        
        # Get TTL for each key
        keys_with_ttl = []
        for key in keys:
            ttl = client.ttl(key)
            keys_with_ttl.append({
                "key": key,
                "ttl_seconds": ttl if ttl > 0 else "no expiry"
            })
        
        return {
            "total_matching": len(keys),
            "showing": len(keys_with_ttl),
            "keys": keys_with_ttl
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_cache_config():
    """Get cache configuration (TTLs)."""
    return {
        "ttl_config": CACHE_TTL,
        "description": {
            "statistics": "Statistics data (changes infrequently)",
            "countries": "Country lists and metadata",
            "search": "Search results",
            "calculation": "Tariff calculations",
            "regulatory": "Regulatory engine data",
            "default": "Default TTL for other data"
        }
    }
