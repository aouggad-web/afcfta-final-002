"""
AfCFTA Platform - AI Investment Intelligence API Routes
=========================================================
Exposes the InvestmentIntelligenceEngine via REST endpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-intelligence", tags=["AI Investment Intelligence"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class InvestmentScoreRequest(BaseModel):
    country: str = Field(..., description="ISO 3-letter country code (e.g. MAR)")
    sector: str = Field(default="general", description="Industry sector")
    investment_size: str = Field(default="medium", description="sme | medium | large")
    risk_tolerance: str = Field(default="medium", description="low | medium | high")


class RecommendationRequest(BaseModel):
    sector: str = Field(default="general")
    risk_tolerance: str = Field(default="medium")
    preferred_regions: List[str] = Field(default_factory=list)
    investment_size_pref: str = Field(default="medium")
    limit: int = Field(default=10, ge=1, le=50)


class TradeFlowRequest(BaseModel):
    origin_country: str
    destination_country: str
    product_category: str
    timeframe_months: int = Field(default=12, ge=1, le=60)


class BulkScoreRequest(BaseModel):
    countries: List[str] = Field(..., min_length=1, max_length=54)
    sector: str = Field(default="general")
    investment_size: str = Field(default="medium")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engine():
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    return get_intelligence_engine()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/score")
async def get_investment_score(request: InvestmentScoreRequest):
    """
    Calculate comprehensive AI-powered investment score for a country/sector pair.
    Scores are cached in the L3 layer (6-hour TTL).
    """
    try:
        engine = _engine()
        score = engine.calculate_investment_score(
            country=request.country.upper(),
            sector=request.sector,
            investment_size=request.investment_size,
            user_profile={"risk_tolerance": request.risk_tolerance},
        )
        return score.to_dict()
    except Exception as exc:
        logger.error(f"Investment score error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Generate AI-powered personalised investment recommendations.
    Returns top opportunities ranked by composite investment score.
    """
    try:
        engine = _engine()
        user_profile = {
            "sector": request.sector,
            "risk_tolerance": request.risk_tolerance,
            "preferred_regions": request.preferred_regions,
            "investment_size_pref": request.investment_size_pref,
        }
        recs = engine.get_personalized_recommendations(user_profile, limit=request.limit)
        return {
            "total": len(recs),
            "recommendations": [r.to_dict() for r in recs],
            "user_profile": user_profile,
        }
    except Exception as exc:
        logger.error(f"Recommendations error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/predict-trade-flows")
async def predict_trade_flows(request: TradeFlowRequest):
    """
    Predict future trade flows between two countries for a product category.
    Uses trend-extrapolation with economic indicators.
    """
    try:
        engine = _engine()
        prediction = engine.predict_trade_flows(
            origin_country=request.origin_country.upper(),
            destination_country=request.destination_country.upper(),
            product_category=request.product_category,
            timeframe_months=request.timeframe_months,
        )
        return prediction.to_dict()
    except Exception as exc:
        logger.error(f"Trade flow prediction error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/risk-assessment/{country}")
async def get_risk_assessment(
    country: str,
    sector: str = Query("general"),
    investment_size: str = Query("medium"),
):
    """
    Get comprehensive risk assessment for a country/sector.
    Covers political, regulatory, infrastructure, corruption, and currency risks.
    """
    try:
        engine = _engine()
        return engine.assess_risk(country.upper(), sector, investment_size)
    except Exception as exc:
        logger.error(f"Risk assessment error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/bulk-score")
async def bulk_investment_score(request: BulkScoreRequest):
    """
    Calculate investment scores for multiple countries in a single request.
    Suitable for building country comparison tables.
    """
    try:
        engine = _engine()
        results = []
        for country in request.countries:
            score = engine.calculate_investment_score(
                country.upper(), request.sector, request.investment_size
            )
            results.append(score.to_dict())

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        return {
            "sector": request.sector,
            "investment_size": request.investment_size,
            "total_countries": len(results),
            "scores": results,
        }
    except Exception as exc:
        logger.error(f"Bulk score error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/scoring-algorithm")
async def get_scoring_algorithm():
    """Return the scoring algorithm weights and component definitions."""
    from intelligence.ai_engine.investment_scoring import SCORING_ALGORITHM
    return {
        "algorithm": SCORING_ALGORITHM,
        "description": (
            "Multi-factor investment scoring with 6 dimensions: "
            "market_access (25%), investment_climate (20%), "
            "infrastructure_quality (15%), incentive_packages (15%), "
            "market_potential (15%), cost_competitiveness (10%)"
        ),
    }
