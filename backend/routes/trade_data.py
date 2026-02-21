"""
Trade Data API Routes
Endpoints for accessing UN COMTRADE, WTO, and smart data source selection
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from services.data_source_selector import data_source_selector
from services.comtrade_service import comtrade_service
from services.wto_service import wto_service

router = APIRouter(prefix="/api", tags=["Trade Data"])


@router.get("/trade-data/latest")
async def get_latest_trade_data(
    reporter: str = Query(..., description="Reporter country ISO3 code"),
    partner: str = Query(..., description="Partner country ISO3 code"),
    hs_code: Optional[str] = Query(None, description="HS product code")
):
    """
    Get the latest available trade data using smart source selection
    
    This endpoint automatically selects the best data source based on:
    - Data freshness
    - API availability
    - Coverage
    """
    result = data_source_selector.get_latest_trade_data(reporter, partner, hs_code)
    
    if not result.get("data"):
        raise HTTPException(
            status_code=404,
            detail="No trade data available from any source"
        )
    
    return result


@router.get("/trade-data/compare-sources")
async def compare_data_sources(
    countries: List[str] = Query(..., description="List of ISO3 country codes")
):
    """
    Compare all data sources to determine which has the most recent data
    
    This is useful for understanding which data source to prioritize
    """
    comparison = data_source_selector.compare_data_sources(countries)
    return comparison


@router.get("/trade-data/comtrade/{reporter}/{partner}")
async def get_comtrade_data(
    reporter: str,
    partner: str,
    period: str = Query(..., description="Year (YYYY) or Month (YYYYMM)"),
    hs_code: Optional[str] = None
):
    """
    Get UN COMTRADE bilateral trade data directly
    """
    data = comtrade_service.get_bilateral_trade(reporter, partner, period, hs_code)
    
    if not data:
        raise HTTPException(status_code=404, detail="No COMTRADE data available")
    
    return data


@router.get("/trade-data/wto/{reporter}/{partner}")
async def get_wto_data(
    reporter: str,
    partner: str,
    product_code: Optional[str] = None
):
    """
    Get WTO tariff and trade data directly
    """
    data = wto_service.get_tariff_data(reporter, partner, product_code)
    
    if not data:
        raise HTTPException(status_code=404, detail="No WTO data available")
    
    return data
