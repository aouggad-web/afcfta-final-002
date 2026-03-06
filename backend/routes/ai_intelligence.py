"""
AI Investment Intelligence API Routes.

Provides AI-powered investment scoring for AfCFTA countries and sectors.

Endpoints:
  POST /api/ai-intelligence/score  # AI investment score for a country/sector
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-intelligence", tags=["AI Intelligence"])


# ==================== Country / Sector Base Data ====================

# Base investment indicators per country (55 AfCFTA members)
# Scores in [0, 1]: ease_of_doing_business, infrastructure, market_size,
# political_stability, afcfta_ratification
_COUNTRY_PROFILES = {
    "DZA": {"ease": 0.45, "infra": 0.55, "market": 0.72, "stability": 0.50, "afcfta": 1.0, "region": "North Africa"},
    "AGO": {"ease": 0.38, "infra": 0.42, "market": 0.60, "stability": 0.45, "afcfta": 1.0, "region": "Southern Africa"},
    "BEN": {"ease": 0.55, "infra": 0.40, "market": 0.35, "stability": 0.65, "afcfta": 1.0, "region": "West Africa"},
    "BWA": {"ease": 0.72, "infra": 0.68, "market": 0.38, "stability": 0.80, "afcfta": 1.0, "region": "Southern Africa"},
    "BFA": {"ease": 0.42, "infra": 0.35, "market": 0.32, "stability": 0.30, "afcfta": 1.0, "region": "West Africa"},
    "BDI": {"ease": 0.30, "infra": 0.28, "market": 0.25, "stability": 0.25, "afcfta": 1.0, "region": "East Africa"},
    "CPV": {"ease": 0.60, "infra": 0.55, "market": 0.20, "stability": 0.85, "afcfta": 1.0, "region": "West Africa"},
    "CMR": {"ease": 0.48, "infra": 0.45, "market": 0.55, "stability": 0.55, "afcfta": 1.0, "region": "Central Africa"},
    "CAF": {"ease": 0.22, "infra": 0.18, "market": 0.20, "stability": 0.15, "afcfta": 1.0, "region": "Central Africa"},
    "TCD": {"ease": 0.25, "infra": 0.22, "market": 0.28, "stability": 0.20, "afcfta": 1.0, "region": "Central Africa"},
    "COM": {"ease": 0.42, "infra": 0.38, "market": 0.15, "stability": 0.45, "afcfta": 1.0, "region": "East Africa"},
    "COG": {"ease": 0.38, "infra": 0.40, "market": 0.30, "stability": 0.45, "afcfta": 1.0, "region": "Central Africa"},
    "COD": {"ease": 0.28, "infra": 0.25, "market": 0.65, "stability": 0.25, "afcfta": 1.0, "region": "Central Africa"},
    "CIV": {"ease": 0.58, "infra": 0.52, "market": 0.52, "stability": 0.60, "afcfta": 1.0, "region": "West Africa"},
    "DJI": {"ease": 0.50, "infra": 0.62, "market": 0.20, "stability": 0.55, "afcfta": 1.0, "region": "East Africa"},
    "EGY": {"ease": 0.60, "infra": 0.65, "market": 0.80, "stability": 0.55, "afcfta": 1.0, "region": "North Africa"},
    "GNQ": {"ease": 0.35, "infra": 0.45, "market": 0.22, "stability": 0.40, "afcfta": 1.0, "region": "Central Africa"},
    "ERI": {"ease": 0.20, "infra": 0.25, "market": 0.18, "stability": 0.20, "afcfta": 0.0, "region": "East Africa"},
    "SWZ": {"ease": 0.55, "infra": 0.55, "market": 0.22, "stability": 0.65, "afcfta": 1.0, "region": "Southern Africa"},
    "ETH": {"ease": 0.48, "infra": 0.45, "market": 0.72, "stability": 0.42, "afcfta": 1.0, "region": "East Africa"},
    "GAB": {"ease": 0.45, "infra": 0.52, "market": 0.30, "stability": 0.55, "afcfta": 1.0, "region": "Central Africa"},
    "GMB": {"ease": 0.52, "infra": 0.38, "market": 0.22, "stability": 0.60, "afcfta": 1.0, "region": "West Africa"},
    "GHA": {"ease": 0.65, "infra": 0.58, "market": 0.58, "stability": 0.72, "afcfta": 1.0, "region": "West Africa"},
    "GIN": {"ease": 0.35, "infra": 0.32, "market": 0.32, "stability": 0.40, "afcfta": 1.0, "region": "West Africa"},
    "GNB": {"ease": 0.30, "infra": 0.28, "market": 0.18, "stability": 0.30, "afcfta": 1.0, "region": "West Africa"},
    "KEN": {"ease": 0.62, "infra": 0.60, "market": 0.65, "stability": 0.58, "afcfta": 1.0, "region": "East Africa"},
    "LSO": {"ease": 0.48, "infra": 0.42, "market": 0.18, "stability": 0.65, "afcfta": 1.0, "region": "Southern Africa"},
    "LBR": {"ease": 0.38, "infra": 0.30, "market": 0.22, "stability": 0.45, "afcfta": 1.0, "region": "West Africa"},
    "LBY": {"ease": 0.25, "infra": 0.45, "market": 0.45, "stability": 0.15, "afcfta": 1.0, "region": "North Africa"},
    "MDG": {"ease": 0.45, "infra": 0.35, "market": 0.38, "stability": 0.42, "afcfta": 1.0, "region": "East Africa"},
    "MWI": {"ease": 0.50, "infra": 0.35, "market": 0.28, "stability": 0.60, "afcfta": 1.0, "region": "Southern Africa"},
    "MLI": {"ease": 0.38, "infra": 0.32, "market": 0.38, "stability": 0.28, "afcfta": 1.0, "region": "West Africa"},
    "MRT": {"ease": 0.42, "infra": 0.38, "market": 0.28, "stability": 0.45, "afcfta": 1.0, "region": "West Africa"},
    "MUS": {"ease": 0.80, "infra": 0.75, "market": 0.28, "stability": 0.88, "afcfta": 1.0, "region": "East Africa"},
    "MAR": {"ease": 0.68, "infra": 0.70, "market": 0.68, "stability": 0.72, "afcfta": 1.0, "region": "North Africa"},
    "MOZ": {"ease": 0.42, "infra": 0.38, "market": 0.40, "stability": 0.48, "afcfta": 1.0, "region": "Southern Africa"},
    "NAM": {"ease": 0.62, "infra": 0.62, "market": 0.32, "stability": 0.78, "afcfta": 1.0, "region": "Southern Africa"},
    "NER": {"ease": 0.35, "infra": 0.28, "market": 0.32, "stability": 0.30, "afcfta": 1.0, "region": "West Africa"},
    "NGA": {"ease": 0.52, "infra": 0.48, "market": 0.88, "stability": 0.38, "afcfta": 1.0, "region": "West Africa"},
    "RWA": {"ease": 0.72, "infra": 0.62, "market": 0.30, "stability": 0.78, "afcfta": 1.0, "region": "East Africa"},
    "STP": {"ease": 0.48, "infra": 0.40, "market": 0.15, "stability": 0.65, "afcfta": 1.0, "region": "Central Africa"},
    "SEN": {"ease": 0.60, "infra": 0.52, "market": 0.45, "stability": 0.72, "afcfta": 1.0, "region": "West Africa"},
    "SYC": {"ease": 0.68, "infra": 0.68, "market": 0.18, "stability": 0.80, "afcfta": 1.0, "region": "East Africa"},
    "SLE": {"ease": 0.35, "infra": 0.28, "market": 0.25, "stability": 0.45, "afcfta": 1.0, "region": "West Africa"},
    "SOM": {"ease": 0.15, "infra": 0.15, "market": 0.28, "stability": 0.10, "afcfta": 1.0, "region": "East Africa"},
    "ZAF": {"ease": 0.68, "infra": 0.72, "market": 0.82, "stability": 0.62, "afcfta": 1.0, "region": "Southern Africa"},
    "SSD": {"ease": 0.18, "infra": 0.15, "market": 0.22, "stability": 0.10, "afcfta": 1.0, "region": "East Africa"},
    "SDN": {"ease": 0.25, "infra": 0.30, "market": 0.45, "stability": 0.22, "afcfta": 0.0, "region": "North Africa"},
    "TZA": {"ease": 0.55, "infra": 0.50, "market": 0.55, "stability": 0.65, "afcfta": 1.0, "region": "East Africa"},
    "TGO": {"ease": 0.55, "infra": 0.48, "market": 0.32, "stability": 0.58, "afcfta": 1.0, "region": "West Africa"},
    "TUN": {"ease": 0.62, "infra": 0.65, "market": 0.55, "stability": 0.60, "afcfta": 1.0, "region": "North Africa"},
    "UGA": {"ease": 0.55, "infra": 0.45, "market": 0.45, "stability": 0.55, "afcfta": 1.0, "region": "East Africa"},
    "ZMB": {"ease": 0.52, "infra": 0.45, "market": 0.40, "stability": 0.62, "afcfta": 1.0, "region": "Southern Africa"},
    "ZWE": {"ease": 0.40, "infra": 0.42, "market": 0.42, "stability": 0.38, "afcfta": 1.0, "region": "Southern Africa"},
    "ESH": {"ease": 0.10, "infra": 0.20, "market": 0.08, "stability": 0.10, "afcfta": 1.0, "region": "North Africa"},
}

# Sector multipliers: how well a country's profile translates for each sector
_SECTOR_WEIGHTS = {
    "agriculture": {
        "ease": 0.20,
        "infra": 0.25,
        "market": 0.30,
        "stability": 0.15,
        "afcfta": 0.10,
    },
    "manufacturing": {
        "ease": 0.25,
        "infra": 0.30,
        "market": 0.25,
        "stability": 0.15,
        "afcfta": 0.05,
    },
    "technology": {
        "ease": 0.30,
        "infra": 0.20,
        "market": 0.25,
        "stability": 0.20,
        "afcfta": 0.05,
    },
    "finance": {
        "ease": 0.35,
        "infra": 0.15,
        "market": 0.28,
        "stability": 0.17,
        "afcfta": 0.05,
    },
    "energy": {
        "ease": 0.20,
        "infra": 0.35,
        "market": 0.20,
        "stability": 0.20,
        "afcfta": 0.05,
    },
    "mining": {
        "ease": 0.20,
        "infra": 0.30,
        "market": 0.25,
        "stability": 0.20,
        "afcfta": 0.05,
    },
    "tourism": {
        "ease": 0.25,
        "infra": 0.25,
        "market": 0.20,
        "stability": 0.25,
        "afcfta": 0.05,
    },
    "trade": {
        "ease": 0.30,
        "infra": 0.25,
        "market": 0.25,
        "stability": 0.15,
        "afcfta": 0.05,
    },
    "healthcare": {
        "ease": 0.25,
        "infra": 0.25,
        "market": 0.28,
        "stability": 0.17,
        "afcfta": 0.05,
    },
    "education": {
        "ease": 0.25,
        "infra": 0.20,
        "market": 0.28,
        "stability": 0.22,
        "afcfta": 0.05,
    },
}

# Default weights when sector not found
_DEFAULT_WEIGHTS = {"ease": 0.25, "infra": 0.25, "market": 0.25, "stability": 0.20, "afcfta": 0.05}

# Size multipliers for investment score adjustment.
# Small investments require less regulatory scrutiny in emerging markets (+bonus),
# while large investments face higher due-diligence thresholds and risk exposure
# in markets with weaker institutions (-penalty). Effect is intentionally small.
_SIZE_MULTIPLIERS = {
    "small": 0.05,
    "medium": 0.0,
    "large": -0.03,
}


def _score_to_grade(score: float) -> str:
    """Convert a [0,1] score to a letter grade."""
    if score >= 0.90:
        return "A+"
    if score >= 0.85:
        return "A"
    if score >= 0.80:
        return "A-"
    if score >= 0.75:
        return "B+"
    if score >= 0.70:
        return "B"
    if score >= 0.65:
        return "B-"
    if score >= 0.60:
        return "C+"
    if score >= 0.55:
        return "C"
    if score >= 0.50:
        return "C-"
    if score >= 0.40:
        return "D"
    return "F"


def _score_to_recommendation(score: float) -> str:
    """Convert a [0,1] score to a recommendation strength."""
    if score >= 0.75:
        return "strong_buy"
    if score >= 0.62:
        return "buy"
    if score >= 0.50:
        return "hold"
    if score >= 0.38:
        return "cautious"
    return "avoid"


def _compute_score(country: str, sector: str, investment_size: str) -> dict:
    """Compute the AI investment score for the given parameters."""
    country_upper = country.upper()
    sector_lower = sector.lower()
    size_lower = investment_size.lower()

    profile = _COUNTRY_PROFILES.get(country_upper)
    if profile is None:
        raise ValueError(f"Unknown country code: {country_upper}. Use ISO 3166-1 alpha-3.")

    weights = _SECTOR_WEIGHTS.get(sector_lower, _DEFAULT_WEIGHTS)
    size_bonus = _SIZE_MULTIPLIERS.get(size_lower, 0.0)

    raw_score = (
        profile["ease"] * weights["ease"]
        + profile["infra"] * weights["infra"]
        + profile["market"] * weights["market"]
        + profile["stability"] * weights["stability"]
        + profile["afcfta"] * weights["afcfta"]
    )

    overall_score = min(1.0, max(0.0, raw_score + size_bonus))
    overall_score = round(overall_score, 2)

    grade = _score_to_grade(overall_score)
    recommendation = _score_to_recommendation(overall_score)

    sub_scores = {
        "ease_of_doing_business": round(profile["ease"], 2),
        "infrastructure": round(profile["infra"], 2),
        "market_size": round(profile["market"], 2),
        "political_stability": round(profile["stability"], 2),
        "afcfta_integration": round(profile["afcfta"], 2),
    }

    risk_level = (
        "low" if overall_score >= 0.70
        else "medium" if overall_score >= 0.50
        else "high"
    )

    return {
        "country": country_upper,
        "sector": sector_lower,
        "investment_size": size_lower,
        "overall_score": overall_score,
        "grade": grade,
        "recommendation_strength": recommendation,
        "risk_level": risk_level,
        "sub_scores": sub_scores,
        "region": profile["region"],
        "afcfta_member": profile["afcfta"] == 1.0,
        "notes": (
            "Score computed from AfCFTA country profiles covering ease of doing business, "
            "infrastructure quality, market size, political stability, and AfCFTA integration. "
            "Investment scores are indicative only. Consult official sources before making decisions."
        ),
    }


# ==================== Request / Response Models ====================

class InvestmentScoreRequest(BaseModel):
    country: str = Field(..., description="ISO 3166-1 alpha-3 country code (e.g. KEN, NGA, ZAF)")
    sector: str = Field(
        ...,
        description="Sector name: agriculture, manufacturing, technology, finance, energy, mining, tourism, trade, healthcare, education",
    )
    investment_size: str = Field(
        default="medium",
        description="Investment size: small | medium | large",
    )


# ==================== Endpoints ====================

@router.post("/score")
async def get_investment_score(request: InvestmentScoreRequest):
    """
    Compute an AI-powered investment attractiveness score for a given
    AfCFTA country and sector.

    Returns an overall score [0, 1], letter grade, recommendation strength,
    risk level, and sub-scores for key investment indicators.

    Body:
    - country: ISO3 country code (e.g. KEN, NGA, ZAF, MAR)
    - sector: Sector name (agriculture, manufacturing, technology, etc.)
    - investment_size: Capital scale: small | medium | large (default: medium)
    """
    try:
        result = _compute_score(
            country=request.country,
            sector=request.sector,
            investment_size=request.investment_size,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Investment score computation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
