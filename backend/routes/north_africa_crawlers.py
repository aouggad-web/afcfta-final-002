"""
North Africa Crawlers API Routes.

Provides endpoints to manage crawling operations for:
- DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)

Endpoints:
  POST /api/crawlers/north-africa/start-all               # All 4 countries
  POST /api/crawlers/north-africa/start                   # Selected countries
  GET  /api/crawlers/north-africa/status                  # Regional dashboard
  GET  /api/crawlers/north-africa/jobs                    # List jobs
  GET  /api/crawlers/north-africa/jobs/{id}               # Job detail
  POST /api/crawlers/north-africa/jobs/{id}/cancel
  POST /api/crawlers/north-africa/sync                    # Cross-validate data
  GET  /api/crawlers/north-africa/countries               # Supported countries info
  POST /api/crawlers/north-africa/optimal-route           # Trade route optimization
  POST /api/crawlers/north-africa/investment-analysis     # Investment location analysis
  GET  /api/crawlers/north-africa/preferential-matrix/{hs_code}  # Per-HS agreement matrix
  GET  /api/crawlers/north-africa/trade-flows             # Regional trade flow data
  POST /api/crawlers/north-africa/opportunity-map         # Sectoral opportunity map
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawlers/north-africa", tags=["North Africa Crawlers"])


# ==================== Request Models ====================

class NorthAfricaCrawlRequest(BaseModel):
    countries: Optional[List[str]] = None
    max_per_chapter: Optional[int] = None
    max_headings: Optional[int] = None
    max_positions: Optional[int] = None
    resume: bool = True


class OptimalRouteRequest(BaseModel):
    hs_code: str = Field(..., description="HS tariff code (6-10 digits)")
    origin_region: str = Field(
        default="sub_saharan_africa",
        description="Origin macro-region (sub_saharan_africa, asia, americas, europe, mena)",
    )
    target_market: str = Field(
        default="europe",
        description="Target destination market (europe, us, mena, africa, comesa)",
    )
    annual_volume: float = Field(
        default=1_000_000,
        gt=0,
        description="Annual shipment value in USD",
    )
    preferences: Optional[List[str]] = Field(
        default=None,
        description=(
            "Ordered list of preferences for ranking: "
            "lowest_cost, fastest_clearance, most_reliable"
        ),
    )


class InvestmentAnalysisRequest(BaseModel):
    industry: str = Field(
        ...,
        description="Industry/sector (automotive, textile, agriculture, renewable_energy, ict, etc.)",
    )
    target_markets: Optional[List[str]] = Field(
        default=None,
        description="Target export markets (eu, us, africa, mena, arab)",
    )
    investment_size: float = Field(
        default=10_000_000,
        gt=0,
        description="Capital investment size in USD",
    )
    employment_target: int = Field(
        default=100,
        ge=1,
        description="Target number of employees",
    )


class OpportunityMapRequest(BaseModel):
    sectors: Optional[List[str]] = Field(
        default=None,
        description="Sectors to analyze (automotive, textile, agriculture, renewable_energy, ict)",
    )


# ==================== Helper ====================

def _get_orchestrator():
    from services.crawlers.regional_orchestrator import get_north_africa_orchestrator
    return get_north_africa_orchestrator()


def _get_intelligence():
    from services.regional_intelligence_service import get_regional_intelligence
    return get_regional_intelligence()


# ==================== Endpoints ====================

@router.post("/start-all")
async def start_all_crawl(options: Optional[NorthAfricaCrawlRequest] = None):
    """
    Start tariff data crawling for all four North African countries
    (DZA, MAR, EGY, TUN) in parallel.
    """
    orchestrator = _get_orchestrator()
    opts = options.dict(exclude_none=True) if options else {}

    try:
        job = await orchestrator.start_regional_crawl(options=opts)
        return {
            "message": (
                f"North Africa regional crawl job {job.job_id} started "
                f"for {len(job.countries)} countries: {job.countries}"
            ),
            "job": job.summary,
        }
    except Exception as exc:
        logger.error(f"Failed to start North Africa crawl: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/start")
async def start_selective_crawl(request: NorthAfricaCrawlRequest):
    """
    Start tariff data crawling for selected North African countries.

    Body:
    - countries: List of ISO3 codes (DZA / MAR / EGY / TUN)
    - max_per_chapter: Optional chapter limit (for testing)
    - max_headings: Optional heading limit for DZA
    - max_positions: Optional position limit for EGY
    """
    orchestrator = _get_orchestrator()
    opts = request.dict(exclude_none=True)
    countries = opts.pop("countries", None)

    try:
        job = await orchestrator.start_regional_crawl(countries=countries, options=opts)
        return {
            "message": (
                f"North Africa crawl job {job.job_id} started "
                f"for: {job.countries}"
            ),
            "job": job.summary,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to start selective crawl: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
async def get_regional_status():
    """
    Get the North African regional crawler dashboard status.

    Returns system status, active jobs, and overall metrics.
    """
    orchestrator = _get_orchestrator()
    status = orchestrator.get_regional_status()

    # Enrich with data freshness
    try:
        intel = _get_intelligence()
        freshness = intel.get_data_freshness()
        status["data_freshness"] = freshness.to_dict()
    except Exception as exc:
        logger.warning(f"Could not load data freshness: {exc}")
        status["data_freshness"] = None

    return status


@router.get("/jobs")
async def list_jobs(limit: int = Query(20, ge=1, le=100)):
    """List North Africa crawl jobs, newest first."""
    orchestrator = _get_orchestrator()
    return {
        "jobs": orchestrator.list_jobs(limit=limit),
        "total": len(orchestrator.jobs),
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get detailed status of a specific North Africa crawl job."""
    orchestrator = _get_orchestrator()
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job.summary


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running North Africa crawl job."""
    orchestrator = _get_orchestrator()
    success = orchestrator.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found or not cancellable",
        )
    job = orchestrator.get_job(job_id)
    return {"message": f"Job {job_id} cancelled", "job": job.summary if job else {}}


@router.post("/sync")
async def sync_and_validate():
    """
    Trigger cross-country data validation (sync) across North Africa.

    Compares rates for shared HS codes and reports inconsistencies.
    """
    try:
        from services.crawlers.cross_validator import NorthAfricaCrossValidator
        validator = NorthAfricaCrossValidator()
        result = validator.validate()
        return {
            "message": "North Africa cross-validation completed",
            "validation": result.to_dict(),
        }
    except Exception as exc:
        logger.error(f"Cross-validation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/countries")
async def get_supported_countries():
    """
    Get information about all supported North African countries
    and their crawler configurations.
    """
    from config.crawler_configs.dza_config import DZA_CONFIG
    from config.crawler_configs.mar_config import MAR_CONFIG
    from config.crawler_configs.egy_config import EGY_CONFIG
    from config.crawler_configs.tun_config import TUN_CONFIG

    configs = {
        "DZA": DZA_CONFIG,
        "MAR": MAR_CONFIG,
        "EGY": EGY_CONFIG,
        "TUN": TUN_CONFIG,
    }

    countries = []
    for code, cfg in configs.items():
        countries.append({
            "iso3": code,
            "country_name": cfg["country_name"],
            "country_name_fr": cfg["country_name_fr"],
            "primary_source": cfg["primary_source"],
            "nomenclature": cfg["nomenclature"],
            "hs_level": cfg["hs_level"],
            "tax_codes": list(cfg["tax_structure"].keys()),
            "preferential_agreements": cfg.get("preferential_agreements", []),
            "crawl_settings": cfg.get("crawl_settings", {}),
        })

    return {
        "total_countries": len(countries),
        "region": "North Africa",
        "countries": countries,
    }


# ==================== Advanced Regional Intelligence Endpoints ====================


@router.post("/optimal-route")
async def find_optimal_trade_route(request: OptimalRouteRequest):
    """
    Find the optimal North African transit/processing country for a trade lane.

    Ranks DZA, MAR, EGY, TUN by combined cost/clearance/reliability score
    based on the stated origin region, target market, and preferences.

    Body:
    - hs_code: HS tariff code (6-10 digits)
    - origin_region: sub_saharan_africa | asia | americas | europe | mena
    - target_market: europe | us | mena | africa | comesa
    - annual_volume: Annual shipment value in USD
    - preferences: Ordered list of [lowest_cost, fastest_clearance, most_reliable]
    """
    try:
        intel = _get_intelligence()
        result = intel.optimal_trade_route(
            hs_code=request.hs_code,
            origin_region=request.origin_region,
            target_market=request.target_market,
            annual_volume=request.annual_volume,
            preferences=request.preferences,
        )
        return result
    except Exception as exc:
        logger.error(f"Optimal route analysis failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/investment-analysis")
async def investment_location_analysis(request: InvestmentAnalysisRequest):
    """
    Analyze investment opportunities across DZA, MAR, EGY, TUN for a sector.

    Scores each country on sector capabilities, market access, regulatory
    environment, and cost efficiency to recommend the best investment location.

    Body:
    - industry: Sector name (automotive, textile, agriculture, ict, etc.)
    - target_markets: Target export markets (eu, us, africa, mena, arab)
    - investment_size: Capital investment in USD
    - employment_target: Target number of employees
    """
    try:
        intel = _get_intelligence()
        result = intel.investment_analysis(
            industry=request.industry,
            target_markets=request.target_markets,
            investment_size=request.investment_size,
            employment_target=request.employment_target,
        )
        return result
    except Exception as exc:
        logger.error(f"Investment analysis failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/preferential-matrix/{hs_code}")
async def get_preferential_matrix(hs_code: str):
    """
    Get the full preferential trade agreement matrix for a specific HS code.

    Returns per-country applicable trade agreements with indicative rates
    and market access details for the given HS code chapter.

    Path parameter:
    - hs_code: HS tariff code (6-10 digits)
    """
    try:
        intel = _get_intelligence()
        result = intel.get_preferential_matrix_by_hs(hs_code=hs_code)
        return result
    except Exception as exc:
        logger.error(f"Preferential matrix lookup failed for {hs_code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trade-flows")
async def get_regional_trade_flows():
    """
    Get regional trade flow intelligence across North African countries.

    Returns:
    - Intra-regional trade metrics (DZA-MAR, DZA-TUN, EGY-TUN, MAR-TUN, MAR-EGY)
    - EU-bound trade advantages (MAR, TUN, EGY)
    - MENA hub positioning (EGY Suez Canal, MAR Atlantic)
    - Africa gateway corridors (DZA Sahel, EGY COMESA, MAR West Africa)
    """
    try:
        intel = _get_intelligence()
        return intel.get_trade_flows()
    except Exception as exc:
        logger.error(f"Trade flows query failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/opportunity-map")
async def get_opportunity_map(request: OpportunityMapRequest):
    """
    Generate a sectoral investment opportunity map across North Africa.

    Scores all four countries across cost structure, market access,
    regulatory environment, and infrastructure quality for each sector.

    Body:
    - sectors: List of sectors to analyze
               (automotive, textile, agriculture, renewable_energy, ict)
               Defaults to all four major sectors if not specified.
    """
    try:
        intel = _get_intelligence()
        result = intel.get_opportunity_map(sectors=request.sectors)
        return result
    except Exception as exc:
        logger.error(f"Opportunity map generation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

