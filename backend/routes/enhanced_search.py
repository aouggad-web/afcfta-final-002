"""
AfCFTA Platform - Enhanced Search API Routes
=============================================
Intelligent HS code search and advanced investment opportunity filtering.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-search", tags=["Enhanced Search & Filtering"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class InvestmentSearchRequest(BaseModel):
    countries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    investment_size: str = Field(default="medium")
    risk_tolerance: str = Field(default="medium")
    required_incentives: Optional[List[str]] = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search_engine():
    from search.enhanced_search import get_search_engine
    return get_search_engine()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/hs-codes")
async def search_hs_codes(
    q: str = Query(..., min_length=2, description="Search query (code or description)"),
    lang: str = Query("en", description="Response language: en | fr"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Intelligent HS code search with exact, fuzzy, and semantic matching.
    Supports numeric codes (e.g. '0901') and natural language ('coffee').
    Results are cached in L1 for 1 hour.
    """
    try:
        engine = _search_engine()
        results = engine.intelligent_hs_search(q, lang=lang)

        # Apply limit to each category
        results["exact_matches"] = results["exact_matches"][:limit]
        results["fuzzy_matches"] = results["fuzzy_matches"][:limit]
        results["semantic_matches"] = results["semantic_matches"][:limit]

        return results
    except Exception as exc:
        logger.error(f"HS search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/investment-opportunities")
async def search_investment_opportunities(request: InvestmentSearchRequest):
    """
    Advanced investment opportunity search with multi-criteria filtering.

    Supports geographic, sector, investment size, and risk-level filtering.
    Returns scored and ranked opportunities with facets for the UI filter panel.
    """
    try:
        engine = _search_engine()
        criteria: Dict[str, Any] = {
            "countries": request.countries or [],
            "regions": request.regions or [],
            "sectors": request.sectors or ["general"],
            "investment_size": request.investment_size,
            "risk_tolerance": request.risk_tolerance,
            "required_incentives": request.required_incentives or [],
            "min_score": request.min_score,
        }
        result = engine.investment_opportunity_search(criteria)

        # Paginate
        all_opps = result.get("opportunities", [])
        start = (request.page - 1) * request.per_page
        end = start + request.per_page
        result["opportunities"] = all_opps[start:end]
        result["pagination"] = {
            "page": request.page,
            "per_page": request.per_page,
            "total_count": result["total_count"],
            "total_pages": -(-result["total_count"] // request.per_page),
        }
        return result
    except Exception as exc:
        logger.error(f"Investment search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    type: str = Query("all", description="all | hs_code | country | sector"),
    limit: int = Query(8, ge=1, le=20),
):
    """
    Fast autocomplete for search inputs.
    Combines HS code suggestions with country and sector lookups.
    """
    suggestions = []

    if type in ("all", "hs_code") and len(q) >= 2:
        engine = _search_engine()
        hs_results = engine.intelligent_hs_search(q)
        for match in (
            hs_results.get("exact_matches", [])[:3]
            + hs_results.get("semantic_matches", [])[:3]
        ):
            suggestions.append({
                "type": "hs_code",
                "value": match.get("hs_code", ""),
                "label": match.get("description") or match.get("description_en", ""),
            })

    if type in ("all", "sector"):
        sectors = [
            "agriculture", "manufacturing", "ict", "energy",
            "finance", "tourism", "logistics", "mining", "textiles", "automotive",
        ]
        q_lower = q.lower()
        suggestions += [
            {"type": "sector", "value": s, "label": s.title()}
            for s in sectors if q_lower in s
        ]

    return {"query": q, "suggestions": suggestions[:limit]}


@router.get("/filters/options")
async def get_filter_options():
    """Return all available filter options for the search UI."""
    from intelligence.analytics.regional_analytics import REGIONAL_BLOCS
    from intelligence.ai_engine.investment_scoring import COUNTRY_INDICATORS

    return {
        "geographic_filters": {
            "countries": list(COUNTRY_INDICATORS.keys()),
            "regional_blocs": list(REGIONAL_BLOCS.keys()),
        },
        "investment_filters": {
            "investment_sizes": ["sme", "medium", "large"],
            "risk_tolerances": ["low", "medium", "high"],
            "sectors": [
                "agriculture", "manufacturing", "ict", "energy",
                "finance", "tourism", "logistics", "mining", "textiles", "automotive",
            ],
        },
        "score_range": {"min": 0.0, "max": 1.0, "step": 0.05},
    }
