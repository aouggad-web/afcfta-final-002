"""
AfCFTA API v2 – enhanced endpoints for bulk operations,
analytics and AI recommendations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from analytics.dashboard_generator import DashboardGenerator  # type: ignore
from analytics.regional_intelligence import RegionalAnalyticsEngine  # type: ignore
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from search.investment_search import InvestmentOpportunitySearch  # type: ignore

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

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_regional_engine = RegionalAnalyticsEngine()
_dashboard_gen = DashboardGenerator()
_inv_search = InvestmentOpportunitySearch()

router = APIRouter(prefix="/v2")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


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

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/bulk/investment-analysis", summary="Batch investment opportunity analysis"
)
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
            scored.append(
                {
                    **match,
                    "composite_score": score,
                    "meets_criteria": risk_val <= max_risk
                    and roi >= request.criteria.min_roi,
                }
            )

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
    region: Optional[str] = Query(
        default=None, description="Filter by region (e.g. ECOWAS, EAC)"
    ),
    timeframe: str = Query(default="2024"),
) -> dict[str, Any]:
    """Return aggregated dashboard metrics for AfCFTA regional performance."""
    regions_filter = [region] if region else None
    regional = _regional_engine.get_regional_dashboard(
        regions=regions_filter, timeframe=timeframe
    )
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
                "risk_tolerance": profile.risk_tolerance,
                "sector_preferences": profile.sectors,
                "investment_size": profile.budget_usd,
                "geographic_preferences": profile.countries,
                "time_horizon_years": profile.time_horizon_years,
            }
            recs = _RECOMMENDATION_ENGINE.generate_recommendations(
                user_profile=raw_profile,
                limit=5,
            )
            recs_list = [r.to_dict() if hasattr(r, "to_dict") else r for r in recs]
            return {
                "recommendations": recs_list,
                "engine": "recommendation_engine_v2",
                "profile_used": raw_profile,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception:
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


