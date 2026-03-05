"""
AfCFTA API v2 – enhanced endpoints for comprehensive search, bulk operations,
analytics, AI recommendations and mobile quick-lookup.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Internal imports (backend/ is on sys.path)
# ---------------------------------------------------------------------------
try:
    from ai.recommendation_engine import PersonalizedRecommendationEngine  # type: ignore
    _RECOMMENDATION_ENGINE: Any = PersonalizedRecommendationEngine()
    _REC_AVAILABLE = True
except Exception:
    _RECOMMENDATION_ENGINE = None
    _REC_AVAILABLE = False

try:
    from ai.scoring_algorithms import InvestmentScoringEngine  # type: ignore
    _SCORER: Any = InvestmentScoringEngine()
    _SCORING_AVAILABLE = True
except Exception:
    _SCORER = None
    _SCORING_AVAILABLE = False

from analytics.regional_intelligence import RegionalAnalyticsEngine  # type: ignore
from analytics.dashboard_generator import DashboardGenerator  # type: ignore
from search.hs_code_search import AdvancedHSCodeSearch  # type: ignore
from search.investment_search import InvestmentOpportunitySearch  # type: ignore

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_regional_engine = RegionalAnalyticsEngine()
_dashboard_gen = DashboardGenerator()
_hs_search = AdvancedHSCodeSearch()
_inv_search = InvestmentOpportunitySearch()

router = APIRouter(prefix="/v2")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SearchFilters(BaseModel):
    countries: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    hs_chapters: list[int] = Field(default_factory=list)


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class ComprehensiveSearchRequest(BaseModel):
    query: str
    filters: SearchFilters = Field(default_factory=SearchFilters)
    pagination: Pagination = Field(default_factory=Pagination)


class ProductItem(BaseModel):
    hs_code: str
    description: str


class RouteItem(BaseModel):
    origin: str
    destination: str


class BulkTariffRequest(BaseModel):
    products: list[ProductItem]
    routes: list[RouteItem]


class OpportunityItem(BaseModel):
    country: str
    sector: str


class InvestmentCriteria(BaseModel):
    risk_tolerance: str = "medium"
    min_roi: float = 0.0


class BulkInvestmentRequest(BaseModel):
    opportunities: list[OpportunityItem]
    criteria: InvestmentCriteria = Field(default_factory=InvestmentCriteria)


class UserProfile(BaseModel):
    sectors: list[str] = Field(default_factory=list)
    risk_tolerance: str = "medium"
    budget_usd: float = 1_000_000
    countries: list[str] = Field(default_factory=list)
    time_horizon_years: int = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TARIFF_RATES: dict[str, dict[str, float]] = {
    "default": {"within_ecowas": 0.0, "within_sadc": 0.0, "within_eac": 0.0, "mfn": 10.0},
    "01": {"within_ecowas": 0.0, "within_sadc": 0.0, "within_eac": 0.0, "mfn": 5.0},
    "09": {"within_ecowas": 0.0, "within_sadc": 0.0, "within_eac": 0.0, "mfn": 5.0},
    "10": {"within_ecowas": 5.0, "within_sadc": 2.5, "within_eac": 0.0, "mfn": 10.0},
    "27": {"within_ecowas": 5.0, "within_sadc": 0.0, "within_eac": 5.0, "mfn": 5.0},
    "84": {"within_ecowas": 0.0, "within_sadc": 0.0, "within_eac": 0.0, "mfn": 5.0},
    "85": {"within_ecowas": 0.0, "within_sadc": 0.0, "within_eac": 0.0, "mfn": 7.5},
    "87": {"within_ecowas": 20.0, "within_sadc": 25.0, "within_eac": 25.0, "mfn": 35.0},
}


def _estimate_tariff(hs_code: str, origin: str, destination: str) -> dict[str, Any]:
    chapter = hs_code[:2] if len(hs_code) >= 2 else "00"
    rates = _TARIFF_RATES.get(chapter, _TARIFF_RATES["default"])
    return {
        "hs_code": hs_code,
        "origin": origin,
        "destination": destination,
        "applied_rate_pct": rates["mfn"],
        "afcfta_preferential_rate_pct": 0.0,
        "mfn_rate_pct": rates["mfn"],
        "duty_regime": "AfCFTA preferential (estimated)",
        "note": "Indicative estimate – verify with official tariff schedule",
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/search/comprehensive", summary="Multi-dimensional comprehensive search")
async def comprehensive_search(request: ComprehensiveSearchRequest) -> dict[str, Any]:
    """Search across products (HS codes), countries and investment opportunities."""
    start = time.perf_counter()

    # HS code / product search
    products = _hs_search.fuzzy_search(request.query, limit=10)
    if request.filters.hs_chapters:
        products = [p for p in products if p.get("chapter") in request.filters.hs_chapters]

    # Country filter applied to investment search
    inv_criteria: dict[str, Any] = {}
    if request.filters.countries:
        inv_criteria["geographic"] = {"country": request.filters.countries[0]}
    if request.filters.sectors:
        inv_criteria["sectoral"] = {"primary": request.filters.sectors[0]}

    investment_opportunities = _inv_search.search(inv_criteria) if inv_criteria else _inv_search.search({})

    # Country matches (simple substring on query)
    country_matches = [
        c for c in [
            "Nigeria", "Kenya", "South Africa", "Ethiopia", "Egypt",
            "Ghana", "Morocco", "Tanzania", "Senegal", "Côte d'Ivoire",
        ]
        if request.query.lower() in c.lower()
    ]

    # Pagination
    page = request.pagination.page
    limit = request.pagination.limit
    offset = (page - 1) * limit
    paginated_products = products[offset: offset + limit]

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "query": request.query,
        "products": paginated_products,
        "countries": country_matches,
        "investment_opportunities": investment_opportunities[:limit],
        "total_count": len(products) + len(investment_opportunities),
        "execution_time_ms": elapsed_ms,
        "pagination": {"page": page, "limit": limit},
    }


@router.post("/bulk/tariff-calculations", summary="Bulk tariff calculation")
async def bulk_tariff_calculations(request: BulkTariffRequest) -> dict[str, Any]:
    """Calculate tariffs for multiple product-route combinations in one call."""
    if not request.products:
        raise HTTPException(status_code=400, detail="At least one product required")
    if not request.routes:
        raise HTTPException(status_code=400, detail="At least one route required")

    batch_id = str(uuid.uuid4())
    results = []
    for product in request.products:
        for route in request.routes:
            result = _estimate_tariff(product.hs_code, route.origin, route.destination)
            result["product_description"] = product.description
            results.append(result)

    return {
        "batch_id": batch_id,
        "status": "completed",
        "results": results,
        "processed": len(results),
        "total": len(request.products) * len(request.routes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/bulk/investment-analysis", summary="Batch investment opportunity analysis")
async def bulk_investment_analysis(request: BulkInvestmentRequest) -> dict[str, Any]:
    """Score and rank a batch of investment opportunities against investor criteria."""
    _risk_map = {"low": 1, "medium": 2, "high": 3}
    max_risk = _risk_map.get(request.criteria.risk_tolerance, 2)

    scored: list[dict[str, Any]] = []
    for opp in request.opportunities:
        matches = _inv_search.search(
            {
                "geographic": {"country": opp.country},
                "sectoral": {"primary": opp.sector},
                "financial": {
                    "risk_tolerance": request.criteria.risk_tolerance,
                    "roi_min": request.criteria.min_roi,
                },
            }
        )
        for match in matches:
            risk_val = _risk_map.get(match.get("risk_tolerance", "medium"), 2)
            roi = match.get("roi_pct", 0)
            # Simple composite score: roi_weight=0.6, risk_penalty=0.4
            score = round(roi * 0.6 - risk_val * 0.4 * 2, 2)
            scored.append({**match, "composite_score": score, "meets_criteria": risk_val <= max_risk and roi >= request.criteria.min_roi})

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return {
        "opportunities": scored,
        "total_analysed": len(request.opportunities),
        "qualifying_count": sum(1 for o in scored if o["meets_criteria"]),
        "criteria_applied": request.criteria.model_dump(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/analytics/dashboard", summary="Executive analytics dashboard")
async def analytics_dashboard(
    region: Optional[str] = Query(default=None, description="Filter by region (e.g. ECOWAS, EAC)"),
    timeframe: str = Query(default="2024"),
) -> dict[str, Any]:
    """Return aggregated dashboard metrics for AfCFTA regional performance."""
    regions_filter = [region] if (region and isinstance(region, str)) else None
    regional = _regional_engine.get_regional_dashboard(regions=regions_filter, timeframe=timeframe)
    kpis = _dashboard_gen.generate_kpi_metrics()
    flows = _dashboard_gen.generate_investment_flow_data(timeframe=timeframe)
    summary = _dashboard_gen.generate_executive_summary()

    return {
        "regional_performance": regional,
        "investment_flows": flows,
        "trade_opportunities": summary,
        "kpis": kpis,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/ai/recommendations", summary="AI-powered investment recommendations")
async def ai_recommendations(profile: UserProfile) -> dict[str, Any]:
    """Return personalised investment recommendations based on the user's profile."""
    if _REC_AVAILABLE and _RECOMMENDATION_ENGINE is not None:
        try:
            raw_profile = {
                "sectors": profile.sectors,
                "risk_tolerance": profile.risk_tolerance,
                "budget_usd": profile.budget_usd,
                "countries": profile.countries,
                "time_horizon_years": profile.time_horizon_years,
            }
            recs = _RECOMMENDATION_ENGINE.generate_recommendations(
                investor_profile=raw_profile,
                top_n=5,
            )
            recs_list = [r.to_dict() if hasattr(r, "to_dict") else r for r in recs]
            return {
                "recommendations": recs_list,
                "engine": "recommendation_engine_v2",
                "profile_used": raw_profile,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            # Fall through to heuristic fallback
            pass

    # Heuristic fallback
    criteria: dict[str, Any] = {
        "financial": {
            "risk_tolerance": profile.risk_tolerance,
            "roi_min": 10.0,
            "investment_size_max": int(profile.budget_usd),
        }
    }
    if profile.sectors:
        criteria["sectoral"] = {"primary": profile.sectors[0]}
    if profile.countries:
        criteria["geographic"] = {"country": profile.countries[0]}

    results = _inv_search.search(criteria)
    return {
        "recommendations": results[:5],
        "engine": "heuristic_fallback",
        "profile_used": profile.model_dump(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/mobile/quick-lookup", summary="Mobile-optimised quick tariff lookup")
async def mobile_quick_lookup(
    hs_code: Optional[str] = Query(default=None, description="HS code to look up"),
    country: Optional[str] = Query(default=None, description="Destination country"),
) -> dict[str, Any]:
    """Lightweight endpoint optimised for mobile clients – returns minimal tariff info."""
    if not hs_code and not country:
        raise HTTPException(status_code=400, detail="Provide at least hs_code or country")

    result: dict[str, Any] = {"query": {"hs_code": hs_code, "country": country}}

    if hs_code:
        matches = _hs_search.fuzzy_search(hs_code, limit=3)
        result["hs_info"] = matches[0] if matches else None
        chapter = hs_code[:2] if len(hs_code) >= 2 else "00"
        rates = _TARIFF_RATES.get(chapter, _TARIFF_RATES["default"])
        result["tariff_summary"] = {
            "mfn_rate_pct": rates["mfn"],
            "afcfta_rate_pct": 0.0,
            "note": "Indicative – verify with official schedule",
        }

    if country:
        opps = _inv_search.get_by_country(country)
        result["investment_snapshot"] = {
            "country": country,
            "opportunity_count": len(opps),
            "top_sectors": list({o["sector"] for o in opps})[:3],
        }

    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    return result
