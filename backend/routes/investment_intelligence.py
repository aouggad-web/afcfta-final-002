"""
Investment Intelligence API Routes for North Africa.

Provides decision support endpoints for market entry and
trade strategy analysis across DZA, MAR, EGY, TUN.

Endpoints:
  GET  /api/investment/north-africa/freshness        # Data freshness
  GET  /api/investment/north-africa/agreements       # Preferential agreements matrix
  POST /api/investment/north-africa/market-entry     # Market entry recommendations
  GET  /api/investment/north-africa/dataset          # Regional dataset export
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investment/north-africa", tags=["Investment Intelligence"])


# ==================== Request Models ====================

class MarketEntryRequest(BaseModel):
    sector: str = Field(..., description="Industry sector (automotive, textiles, ict, etc.)")
    origin_country: str = Field(default="INTL", description="Investor's home country")
    target_market_size: str = Field(
        default="large",
        description="Target market size: large | medium | small",
    )
    priority: str = Field(
        default="eu_access",
        description="Priority: eu_access | us_access | regional_hub | cost",
    )


# ==================== Helper ====================

def _get_intel():
    from services.regional_intelligence_service import get_regional_intelligence
    return get_regional_intelligence()


# ==================== Endpoints ====================

@router.get("/freshness")
async def get_data_freshness():
    """
    Get data freshness status for all North African country datasets.

    Reports the age and size of the latest published tariff data
    for DZA, MAR, EGY, and TUN.
    """
    try:
        intel = _get_intel()
        report = intel.get_data_freshness()
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Data freshness check failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/agreements")
async def get_preferential_agreements_matrix():
    """
    Get the cross-country preferential trade agreement matrix.

    Shows which North African countries (DZA/MAR/EGY/TUN) have
    preferential agreements with external markets (EU, US, COMESA, etc.)
    and identifies the best country per destination market.
    """
    try:
        intel = _get_intel()
        return intel.get_preferential_agreements_matrix()
    except Exception as exc:
        logger.error(f"Agreements matrix failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/market-entry")
async def recommend_market_entry(request: MarketEntryRequest):
    """
    Get data-driven market entry recommendations for North Africa.

    Ranks DZA, MAR, EGY, TUN by suitability for the given sector
    and strategic priority (EU access, US access, regional hub, cost).
    """
    try:
        intel = _get_intel()
        result = intel.recommend_market_entry(
            sector=request.sector,
            origin_country=request.origin_country,
            target_market_size=request.target_market_size,
            priority=request.priority,
        )
        return result
    except Exception as exc:
        logger.error(f"Market entry recommendation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dataset")
async def get_regional_dataset(
    countries: Optional[str] = Query(
        None,
        description="Comma-separated ISO3 codes (e.g. DZA,MAR). Defaults to all.",
    )
):
    """
    Get an aggregated summary of the regional North Africa tariff dataset.

    Returns metadata (record counts, freshness, sources) for available
    published data across the selected countries.
    """
    try:
        include = [c.strip().upper() for c in countries.split(",")] if countries else None
        intel = _get_intel()
        result = intel.export_regional_dataset(include_countries=include)
        return result
    except Exception as exc:
        logger.error(f"Regional dataset export failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
