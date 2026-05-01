"""
HS6 Database Routes - Optimized for Data-Driven Search.
Uses the TariffSearchEngine to provide complete and accurate tariff data.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import logging
import json
import os
from search.hs_code_search import get_search_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hs6")


def load_algeria_nomenclature():
    """Load Algeria nomenclature map for extended sub-position search"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        file_path = os.path.join(data_dir, 'DZA_nomenclature_map.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Algeria nomenclature: {e}")
    return None

@router.get("/smart-search")
async def smart_search_hs6(
    q: str = Query(..., min_length=2),
    language: str = Query(default="fr"),
    country_code: Optional[str] = Query(default=None),
    include_sub_positions: bool = Query(default=False),
    limit: int = Query(default=20),
):
    """
    Smart HS6 search powered by the optimized TariffSearchEngine.
    Provides complete denominations (buffered) and real-time data loading.
    Special handling for DZA (Algeria) with nomenclature_map lookup for extended codes.
    """
    try:
        # Special case for long numeric codes (potentially Algeria extended sub-positions)
        # Check Algeria nomenclature if query is a long numeric code (8+ digits)
        if q.isdigit() and len(q) >= 8:
            dza_nomenclature = load_algeria_nomenclature()
            if dza_nomenclature and q in dza_nomenclature:
                # Found exact match in Algeria nomenclature
                logger.info(f"Found {q} in Algeria nomenclature_map")
                return {
                    "query": q,
                    "results": [{
                        "code": q,
                        "description": dza_nomenclature[q],
                        "country": "DZA",
                        "duty_rate_pct": 0.0,
                        "unit": "",
                        "chapter": q[:2],
                        "match_type": "exact_nomenclature",
                        "source": "algeria_nomenclature_map"
                    }],
                    "total": 1,
                    "source": "algeria_nomenclature_map"
                }
        
        engine = get_search_engine()
        # The new engine provides a unified search method
        raw_results = engine.search(query=q, country=country_code, limit=limit)
        
        # Map results to the format expected by the frontend
        results = []
        for r in raw_results:
            results.append({
                "code": str(r.get("hs_code", "")),
                "description": r.get("description", ""),
                "country": r.get("country", ""),
                "duty_rate_pct": r.get("duty_rate_pct"),
                "unit": r.get("unit", ""),
                "chapter": str(r.get("hs_code", ""))[:2],
                "match_type": "hybrid"
            })

        return {
            "query": q,
            "results": results,
            "total": len(results),
            "source": "optimized_tariff_engine"
        }
    except Exception as e:
        logger.error(f"Smart search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{hs_code}")
async def get_hs6_info(hs_code: str, language: str = Query(default="fr")):
    """Get detailed info for a specific HS code using the optimized engine."""
    engine = get_search_engine()
    # Search for exact code
    res = engine.search(query=hs_code, limit=1)
    if res:
        r = res[0]
        return {
            "code": str(r.get("hs_code")),
            "description": r.get("description"),
            "found": True
        }
    return {"code": hs_code, "found": False, "description": f"HS {hs_code} not found"}
