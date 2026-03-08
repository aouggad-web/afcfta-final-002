"""
SADC Regional Intelligence API Routes
=======================================
Provides REST endpoints for the Southern African Development Community (SADC)
regional intelligence and tariff system.

Endpoints:
  GET  /api/regions/sadc/overview                        # Regional overview
  GET  /api/regions/sadc/countries                       # All 16 country profiles
  GET  /api/regions/sadc/trade-statistics                # Trade statistics
  GET  /api/regions/sadc/investment-zones                # All SEZs
  GET  /api/regions/sacu/customs-union                   # SACU framework
  GET  /api/regions/sacu/revenue-sharing                 # Revenue sharing detail
  GET  /api/countries/sadc/{country_code}/tariffs        # Country tariff data
  GET  /api/countries/sadc/{country_code}/investment     # Country investment zones
  GET  /api/countries/sadc/{country_code}/sectors        # Country sector strengths
  GET  /api/countries/sadc/{country_code}/mining         # Country mining profile
  GET  /api/mining/sadc/overview                         # Full mining intelligence
  GET  /api/mining/sadc/minerals                         # Mineral list
  GET  /api/mining/sadc/minerals/{mineral}               # Mineral profile
  GET  /api/mining/sadc/value-chain/{mineral}            # Value-chain analysis
  GET  /api/mining/sadc/beneficiation                    # Beneficiation opportunities
  GET  /api/mining/sadc/export-routes/{country_code}     # Mineral export routes
  GET  /api/trade-corridors/sadc                         # All transport corridors
  GET  /api/trade-corridors/sadc/{country_code}          # Country-specific corridors
  GET  /api/analysis/sadc-vs-eac                         # Cross-regional comparison
  GET  /api/analysis/sadc-vs-cemac                       # Cross-regional comparison
  POST /api/regions/sadc/investment-recommendation       # Investment location ranking
  GET  /api/regions/sadc/freshness                       # Data freshness status
  GET  /api/regions/sadc/protocols                       # Trade protocols
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["SADC Intelligence"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class InvestmentRecommendationRequest(BaseModel):
    sector: str = Field(..., description="Target industry sector (e.g. mining, textiles, financial_services)")
    priority: str = Field(
        default="infrastructure",
        description="Ranking priority: infrastructure | tax_incentives | market_access | stability",
    )


class SACUImportCostRequest(BaseModel):
    cif_value: float = Field(..., gt=0, description="CIF value in ZAR")
    hs_chapter: str = Field(..., description="HS chapter (2-digit, e.g. '87')")
    destination: str = Field(..., description="ISO3 destination country within SADC")
    origin: str = Field(default="INTL", description="ISO3 origin country ('INTL' for non-SADC)")


# ---------------------------------------------------------------------------
# Service accessor (lazy import)
# ---------------------------------------------------------------------------

def _get_sadc():
    from services.sadc_intelligence_service import get_sadc_intelligence
    return get_sadc_intelligence()


def _get_mining():
    from services.mining_sector_service import get_mining_service
    return get_mining_service()


# ---------------------------------------------------------------------------
# Regional overview endpoints
# ---------------------------------------------------------------------------

@router.get("/regions/sadc/overview")
async def get_sadc_overview():
    """
    High-level SADC regional overview.

    Returns key statistics, country groupings (SACU, LDC, dual-membership),
    and organisation metadata.
    """
    try:
        return _get_sadc().get_regional_overview()
    except Exception as exc:
        logger.error(f"SADC overview failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sadc/countries")
async def get_sadc_countries():
    """
    Return metadata for all 16 SADC member states.
    """
    try:
        from crawlers.countries.sadc.sadc_constants import SADC_COUNTRIES
        return {"countries": SADC_COUNTRIES, "total": len(SADC_COUNTRIES)}
    except Exception as exc:
        logger.error(f"SADC countries failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sadc/trade-statistics")
async def get_sadc_trade_statistics():
    """Return SADC regional trade statistics."""
    try:
        return _get_sadc().get_trade_statistics()
    except Exception as exc:
        logger.error(f"SADC trade statistics failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sadc/investment-zones")
async def get_all_sadc_investment_zones(
    country_code: Optional[str] = Query(None, description="Filter by ISO3 country code")
):
    """
    Return investment zone (SEZ) data for SADC.

    Optionally filter by country_code.
    """
    try:
        return _get_sadc().get_investment_zones(country_code=country_code)
    except Exception as exc:
        logger.error(f"SADC investment zones failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sadc/freshness")
async def get_sadc_data_freshness():
    """
    Check data freshness for all 16 SADC country tariff datasets.
    """
    try:
        report = _get_sadc().get_data_freshness()
        return report.to_dict()
    except Exception as exc:
        logger.error(f"SADC data freshness failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sadc/protocols")
async def get_sadc_trade_protocols(
    protocol: Optional[str] = Query(None, description="Specific protocol key (e.g. sadc_trade_protocol)")
):
    """Return SADC trade agreements and protocols."""
    try:
        return _get_sadc().get_trade_protocols(protocol=protocol)
    except Exception as exc:
        logger.error(f"SADC protocols failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# SACU endpoints
# ---------------------------------------------------------------------------

@router.get("/regions/sacu/customs-union")
async def get_sacu_framework():
    """
    Return the SACU Customs Union framework details including revenue sharing,
    CET bands, and institutional overview.
    """
    try:
        return _get_sadc().get_sacu_framework()
    except Exception as exc:
        logger.error(f"SACU framework failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/regions/sacu/revenue-sharing")
async def get_sacu_revenue_sharing():
    """Return detailed SACU revenue sharing formula and country allocations."""
    try:
        data = _get_sadc().get_sacu_framework()
        return {
            "revenue_sharing_formula": data.get("framework", {}).get("revenue_sharing", {}),
            "country_shares": data.get("revenue_shares", {}),
        }
    except Exception as exc:
        logger.error(f"SACU revenue sharing failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/regions/sacu/import-cost")
async def calculate_sacu_import_cost(request: SACUImportCostRequest):
    """
    Calculate total landed cost for an import at a SACU port of entry.

    Applies SACU CET, SADC preferences (if applicable), and VAT.
    """
    try:
        return _get_sadc().calculate_sacu_import_cost(
            cif_value=request.cif_value,
            hs_chapter=request.hs_chapter,
            destination=request.destination,
            origin=request.origin,
        )
    except Exception as exc:
        logger.error(f"SACU import cost calculation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Country-specific endpoints
# ---------------------------------------------------------------------------

@router.get("/countries/sadc/{country_code}/tariffs")
async def get_sadc_country_tariffs(country_code: str):
    """
    Return tariff data for a specific SADC country.

    Loads from the crawled data file; run the SADC member scraper to populate.
    """
    try:
        data = _get_sadc().get_country_tariff_data(country_code.upper())
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Country tariffs failed for {country_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/countries/sadc/{country_code}/investment")
async def get_sadc_country_investment(country_code: str):
    """Return investment zone data for a specific SADC country."""
    try:
        data = _get_sadc().get_investment_zones(country_code=country_code.upper())
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Country investment failed for {country_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/countries/sadc/{country_code}/sectors")
async def get_sadc_country_sectors(country_code: str):
    """Return sector strengths for a specific SADC country."""
    from services.sadc_intelligence_service import SECTOR_STRENGTHS, COUNTRY_NAMES, SADC_COUNTRY_LIST
    code = country_code.upper()
    if code not in SADC_COUNTRY_LIST:
        raise HTTPException(status_code=404, detail=f"{code} is not a SADC member state")
    return {
        "country_code": code,
        "country_name": COUNTRY_NAMES.get(code, code),
        "sector_strengths": SECTOR_STRENGTHS.get(code, []),
    }


@router.get("/countries/sadc/{country_code}/mining")
async def get_sadc_country_mining(country_code: str):
    """Return mining profile for a specific SADC country."""
    try:
        return _get_mining().get_country_mining_profile(country_code.upper())
    except Exception as exc:
        logger.error(f"Country mining profile failed for {country_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Mining sector endpoints
# ---------------------------------------------------------------------------

@router.get("/mining/sadc/overview")
async def get_sadc_mining_overview():
    """Return full SADC mining sector intelligence."""
    try:
        return _get_mining().intelligence
    except Exception as exc:
        logger.error(f"Mining overview failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mining/sadc/minerals")
async def list_sadc_minerals():
    """List all minerals covered by the SADC mining intelligence system."""
    try:
        return {"minerals": _get_mining().list_minerals()}
    except Exception as exc:
        logger.error(f"Mineral list failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mining/sadc/minerals/{mineral}")
async def get_sadc_mineral_profile(mineral: str):
    """Return detailed profile for a specific mineral."""
    try:
        data = _get_mining().get_mineral_profile(mineral.lower())
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Mineral profile failed for {mineral}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mining/sadc/value-chain/{mineral}")
async def get_sadc_value_chain(mineral: str):
    """Return value-chain analysis for a mineral."""
    try:
        data = _get_mining().get_value_chain(mineral.lower())
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Value chain failed for {mineral}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mining/sadc/beneficiation")
async def get_sadc_beneficiation_opportunities():
    """Return top beneficiation opportunities across SADC."""
    try:
        return {"opportunities": _get_mining().get_beneficiation_opportunities()}
    except Exception as exc:
        logger.error(f"Beneficiation opportunities failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mining/sadc/export-routes/{country_code}")
async def get_sadc_mineral_export_routes(country_code: str):
    """Return recommended mineral export routes for a producing country."""
    try:
        return _get_mining().get_mineral_export_routes(country_code.upper())
    except Exception as exc:
        logger.error(f"Export routes failed for {country_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Transport corridor endpoints
# ---------------------------------------------------------------------------

@router.get("/trade-corridors/sadc")
async def get_sadc_corridors():
    """Return all SADC transport corridors and major port data."""
    try:
        return _get_sadc().get_transport_corridors()
    except Exception as exc:
        logger.error(f"SADC corridors failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trade-corridors/sadc/{country_code}")
async def get_sadc_country_corridors(country_code: str):
    """Return transport corridors and ports relevant to a specific SADC country."""
    try:
        return _get_sadc().get_transport_corridors(country_code=country_code.upper())
    except Exception as exc:
        logger.error(f"Country corridors failed for {country_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Cross-regional analysis endpoints
# ---------------------------------------------------------------------------

@router.get("/analysis/sadc-vs-eac")
async def get_sadc_vs_eac():
    """Compare SADC and EAC regional blocs (structure, trade, dual-members)."""
    try:
        return _get_sadc().compare_sadc_eac()
    except Exception as exc:
        logger.error(f"SADC vs EAC comparison failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analysis/sadc-vs-cemac")
async def get_sadc_vs_cemac():
    """Compare SADC and CEMAC regional blocs."""
    try:
        return _get_sadc().compare_sadc_cemac()
    except Exception as exc:
        logger.error(f"SADC vs CEMAC comparison failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Investment recommendation endpoint
# ---------------------------------------------------------------------------

@router.post("/regions/sadc/investment-recommendation")
async def get_investment_recommendation(request: InvestmentRecommendationRequest):
    """
    Rank SADC countries for investment in a given sector.

    Returns countries sorted by suitability score for the specified sector and
    priority (infrastructure, tax_incentives, market_access, stability).
    """
    try:
        recommendations = _get_sadc().recommend_investment_location(
            sector=request.sector,
            priority=request.priority,
        )
        return {
            "sector": request.sector,
            "priority": request.priority,
            "rankings": recommendations,
        }
    except Exception as exc:
        logger.error(f"Investment recommendation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
