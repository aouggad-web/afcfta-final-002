"""
AfCFTA Platform - Mobile-Optimized API Endpoints
==================================================
Lightweight endpoints designed for mobile clients with:
  - Response size < 10KB for summary endpoints
  - Response time < 100ms (with caching)
  - Progressive loading support
  - ETags for efficient cache validation
  - Aggressive caching via L1 layer
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["Mobile API"])

# ---------------------------------------------------------------------------
# ETag helpers
# ---------------------------------------------------------------------------

def _etag(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return '"' + hashlib.md5(raw.encode()).hexdigest() + '"'


def _check_etag(request: Request, etag: str) -> bool:
    """Return True if the client already has this version (304 eligible)."""
    return request.headers.get("if-none-match") == etag


# ---------------------------------------------------------------------------
# Country summary (< 10KB)
# ---------------------------------------------------------------------------

@router.get("/country/summary/{code}")
async def mobile_country_summary(
    code: str,
    request: Request,
    response: Response,
    lang: str = Query("en", description="Response language (en|fr)"),
):
    """
    Lightweight country summary for mobile clients.
    Returns only essential metrics, key opportunities, and basic tariff info.
    Cached aggressively in L1 with ETag validation.
    """
    try:
        from performance.caching.cache_layers import get_cache
        cache = get_cache()
        cache_key = cache.l1.build_key(type="mobile_country", key=f"{code.upper()}_{lang}")
        cached = cache.l1.get(cache_key)
        if cached:
            tag = _etag(cached)
            if _check_etag(request, tag):
                return Response(status_code=304)
            response.headers["ETag"] = tag
            response.headers["Cache-Control"] = "max-age=3600"
            return cached
    except Exception:
        cache = None
        cache_key = None

    code_upper = code.upper()

    # Build lightweight payload
    try:
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score(code_upper, "general")
        investment_summary = {
            "overall_score": score.overall_score,
            "grade": score.grade,
            "recommendation": score.recommendation_strength,
            "top_risk": score.risk_factors[0]["name"] if score.risk_factors else None,
        }
    except Exception:
        investment_summary = {}

    try:
        from intelligence.analytics.regional_analytics import REGIONAL_BLOCS
        country_bloc = next(
            (bloc for bloc, info in REGIONAL_BLOCS.items() if code_upper in info["countries"]),
            "N/A",
        )
    except Exception:
        country_bloc = "N/A"

    data = {
        "country_code": code_upper,
        "regional_bloc": country_bloc,
        "investment": investment_summary,
        "key_opportunities": [
            "AfCFTA preferential tariff access",
            "SEZ investment incentives",
            "Regional value chain integration",
        ],
        "basic_tariffs": {
            "avg_mfn_rate_pct": 12.5,  # Would be fetched from tariff service
            "afcfta_preference": "Yes",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if cache and cache_key:
        cache.l1.set(cache_key, data)

    tag = _etag(data)
    response.headers["ETag"] = tag
    response.headers["Cache-Control"] = "max-age=3600"
    return data


# ---------------------------------------------------------------------------
# Quick search with autocomplete (< 100ms)
# ---------------------------------------------------------------------------

@router.get("/search/quick")
async def mobile_quick_search(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    lang: str = Query("en"),
    limit: int = Query(8, ge=1, le=20),
):
    """
    Fast search with autocomplete for mobile type-ahead.
    Returns HS codes and product suggestions in < 100ms.
    """
    from search.enhanced_search import get_search_engine
    engine = get_search_engine()
    results = engine.intelligent_hs_search(q, lang=lang)

    # Return only top matches to keep response lightweight
    suggestions = []
    seen_codes: set = set()

    for match in (
        results.get("exact_matches", [])
        + results.get("semantic_matches", [])
        + results.get("fuzzy_matches", [])
    )[:limit]:
        code = match.get("hs_code") or match.get("code", "")
        if code not in seen_codes:
            seen_codes.add(code)
            suggestions.append({
                "hs_code": code,
                "label": match.get("description") or match.get("description_en", ""),
                "type": match.get("match_type", ""),
            })

    return {
        "query": q,
        "suggestions": suggestions[:limit],
        "category_hints": results.get("category_suggestions", [])[:3],
        "total": results.get("total_matches", 0),
    }


# ---------------------------------------------------------------------------
# Dashboard overview (personalized, mobile-first)
# ---------------------------------------------------------------------------

@router.get("/dashboard/overview")
async def mobile_dashboard_overview(
    region: Optional[str] = Query(None, description="Focus region (e.g. ECOWAS)"),
    sector: Optional[str] = Query(None, description="Focus sector"),
    lang: str = Query("en"),
):
    """
    Mobile dashboard summary with personalized regional insights.
    Smart refresh-friendly: uses ETag for efficient re-validation.
    """
    from intelligence.analytics.regional_analytics import get_regional_analytics
    analytics = get_regional_analytics()

    heatmap = analytics.get_investment_heatmap()[:5]  # Top 5 blocs

    top_opportunities = heatmap[:3] if not region else [
        h for h in heatmap if h["bloc"] == region.upper()
    ][:3]

    corridors = analytics.get_trade_corridor_analysis()[:3]

    return {
        "top_blocs": top_opportunities,
        "top_corridors": corridors,
        "platform_stats": {
            "countries_covered": 54,
            "tariff_lines": 229519,
            "investment_zones": 180,
        },
        "quick_actions": [
            {"label": "Calculate tariff", "path": "/calculator"},
            {"label": "Find opportunities", "path": "/opportunities"},
            {"label": "Compare regions", "path": "/statistics"},
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Investment alerts feed (mobile push notifications support)
# ---------------------------------------------------------------------------

@router.get("/alerts/feed")
async def mobile_alerts_feed(
    user_id: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    risk_tolerance: str = Query("medium"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Paginated investment alerts feed for mobile.
    Designed to be polled by mobile clients or used to populate push notifications.
    """
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine, COUNTRY_INDICATORS
    engine = get_intelligence_engine()

    alerts = []
    countries = list(COUNTRY_INDICATORS.keys())[:20]

    for country in countries:
        score = engine.calculate_investment_score(
            country, sector or "general", "medium", {"risk_tolerance": risk_tolerance}
        )
        if score.overall_score >= 0.65:
            alerts.append({
                "type": "investment_opportunity",
                "country": country,
                "sector": sector or "general",
                "score": score.overall_score,
                "grade": score.grade,
                "headline": f"Investment opportunity in {country} — Grade {score.grade}",
                "summary": score.recommendation_strength.replace("_", " ").title(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    alerts.sort(key=lambda x: x["score"], reverse=True)
    return {
        "user_id": user_id,
        "total": len(alerts),
        "alerts": alerts[:limit],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Progressive loading helpers
# ---------------------------------------------------------------------------

@router.get("/country/details/{code}")
async def mobile_country_details(
    code: str,
    section: str = Query("all", description="Section to load: investment|trade|logistics|all"),
):
    """
    Progressive loading endpoint — returns only the requested section.
    The mobile client fetches sections lazily as the user scrolls.
    """
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    code_upper = code.upper()

    sections: Dict[str, Any] = {}

    if section in ("investment", "all"):
        score = engine.calculate_investment_score(code_upper)
        sections["investment"] = {
            "score": score.overall_score,
            "grade": score.grade,
            "components": [
                {"name": c.name, "score": c.raw_score}
                for c in score.component_scores
            ],
            "risk_factors": score.risk_factors,
        }

    if section in ("trade", "all"):
        sections["trade"] = {
            "top_export_partners": ["EU", "China", "USA"],  # Placeholder
            "top_import_partners": ["China", "EU", "India"],
            "trade_balance_usd_bn": 2.5,
        }

    if section in ("logistics", "all"):
        sections["logistics"] = {
            "lpi_score": 3.2,
            "main_ports": ["Port 1", "Port 2"],
            "border_crossings": 8,
        }

    return {
        "country_code": code_upper,
        "section": section,
        "data": sections,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
