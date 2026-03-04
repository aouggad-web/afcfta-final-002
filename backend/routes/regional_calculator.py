"""
Regional Calculator API Routes for North Africa.

Provides advanced tariff calculation endpoints leveraging the
EnhancedCalculatorV3 with regional North African intelligence.

Endpoints:
  POST /api/enhanced-calculator/regional-route    # Best path analysis
  GET  /api/enhanced-calculator/investment-map    # Regional opportunities
  POST /api/enhanced-calculator/supply-chain      # Multi-country optimization
  GET  /api/enhanced-calculator/preferential      # Preferential agreements
  POST /api/enhanced-calculator/country-taxes     # Single country calculation
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-calculator", tags=["Regional Calculator"])


# ==================== Request Models ====================

class RegionalRouteRequest(BaseModel):
    hs_code: str = Field(..., description="HS tariff code (6-10 digits)")
    cif_value: float = Field(..., gt=0, description="CIF value in USD")
    target_market: str = Field(default="NORTH_AFRICA", description="Target market")
    dd_rates: Optional[Dict[str, float]] = Field(
        None, description="Known DD rates per country {ISO3: rate_pct}"
    )


class CountryTaxRequest(BaseModel):
    country_code: str = Field(..., description="ISO3 country code (DZA/MAR/EGY/TUN)")
    hs_code: str = Field(..., description="HS tariff code")
    cif_value: float = Field(..., gt=0, description="CIF value in USD")
    dd_rate: Optional[float] = Field(None, ge=0, le=300, description="Override DD rate %")
    apply_vat: bool = Field(default=True, description="Include VAT in calculation")


class SupplyChainRequest(BaseModel):
    hs_codes: List[str] = Field(..., description="List of HS codes for components")
    production_country: str = Field(default="INTL", description="Production country")
    target_countries: Optional[List[str]] = Field(
        None, description="Countries to compare (defaults to all North Africa)"
    )
    unit_value: float = Field(default=1000.0, gt=0, description="Per-unit CIF value USD")


class PreferentialRequest(BaseModel):
    hs_code: str
    origin_country: str = Field(..., description="ISO3 origin country")
    destination: str = Field(..., description="Destination market (EU/US/COMESA/ARAB)")


# ==================== Helper ====================

def _get_calculator():
    from services.enhanced_calculator_v3 import get_enhanced_calculator
    return get_enhanced_calculator()


# ==================== Endpoints ====================

@router.post("/regional-route")
async def find_best_route(request: RegionalRouteRequest):
    """
    Find the optimal trade route across North African countries.

    Compares total landed costs (DD + VAT) across DZA, MAR, EGY, TUN
    and ranks countries by lowest total cost.
    """
    calculator = _get_calculator()
    try:
        result = calculator.find_best_route(
            hs_code=request.hs_code,
            cif_value=request.cif_value,
            target_market=request.target_market,
            dd_rates=request.dd_rates,
        )
        return result
    except Exception as exc:
        logger.error(f"Regional route calculation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/country-taxes")
async def calculate_country_taxes(request: CountryTaxRequest):
    """
    Calculate import tax breakdown for a specific North African country.

    Returns DD, VAT, and total landed cost for a given HS code and CIF value.
    """
    calculator = _get_calculator()
    supported = ["DZA", "MAR", "EGY", "TUN"]
    if request.country_code.upper() not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported country. Must be one of: {supported}",
        )

    try:
        result = calculator.calculate_country_taxes(
            country_code=request.country_code.upper(),
            hs_code=request.hs_code,
            cif_value=request.cif_value,
            dd_rate=request.dd_rate,
            apply_vat=request.apply_vat,
        )
        return result
    except Exception as exc:
        logger.error(f"Country tax calculation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/investment-map")
async def get_investment_map():
    """
    Get the North African regional investment opportunity map.

    Provides comparative analysis of DZA, MAR, EGY, TUN including:
    - Market size and population
    - Strategic position and port access
    - Trade agreements count and key markets
    - Special economic zones
    - Investment attractiveness scores
    """
    try:
        from services.regional_intelligence_service import get_regional_intelligence
        intel = get_regional_intelligence()
        return intel.build_investment_map()
    except Exception as exc:
        logger.error(f"Investment map failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/supply-chain")
async def optimize_supply_chain(request: SupplyChainRequest):
    """
    Multi-country supply chain optimization analysis.

    Compares total tax burden across North African countries for a
    set of HS codes, helping identify the optimal production base.
    """
    calculator = _get_calculator()
    try:
        result = calculator.compare_regional_supply_chain(
            hs_codes=request.hs_codes,
            production_country=request.production_country,
            target_countries=request.target_countries,
            unit_value=request.unit_value,
        )
        return result
    except Exception as exc:
        logger.error(f"Supply chain optimization failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/preferential")
async def get_preferential_rates(request: PreferentialRequest):
    """
    Get preferential trade agreement rates for a specific trade lane.

    Identifies applicable agreements (EU, US/QIZ, COMESA, Agadir, GAFTA)
    for the given origin country and destination market.
    """
    calculator = _get_calculator()
    try:
        rates = calculator.get_preferential_rates(
            hs_code=request.hs_code,
            origin_country=request.origin_country.upper(),
            destination=request.destination,
        )
        return {
            "hs_code": request.hs_code,
            "origin": request.origin_country.upper(),
            "destination": request.destination,
            "applicable_agreements": rates,
            "count": len(rates),
        }
    except Exception as exc:
        logger.error(f"Preferential rates lookup failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/free-zones")
async def get_free_zone_opportunities(
    hs_code: str = Query(..., description="HS tariff code"),
    cif_value: float = Query(1000.0, gt=0, description="CIF value in USD"),
):
    """
    Identify free zone arbitrage opportunities across North Africa.

    Returns special economic zones in DZA/MAR/EGY/TUN that may offer
    reduced or zero customs duties for the given HS code.
    """
    calculator = _get_calculator()
    try:
        opportunities = calculator.analyze_free_zone_arbitrage(
            hs_code=hs_code,
            cif_value=cif_value,
        )
        return {
            "hs_code": hs_code,
            "cif_value": cif_value,
            "opportunities": opportunities,
            "total_zones": len(opportunities),
        }
    except Exception as exc:
        logger.error(f"Free zone analysis failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
