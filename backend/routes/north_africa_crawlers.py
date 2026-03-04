"""
North Africa Crawlers API Routes.

Provides endpoints to manage crawling operations for:
- DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)

Endpoints:
  POST /api/crawlers/north-africa/start-all     # All 4 countries
  POST /api/crawlers/north-africa/start         # Selected countries
  GET  /api/crawlers/north-africa/status        # Regional dashboard
  GET  /api/crawlers/north-africa/jobs          # List jobs
  GET  /api/crawlers/north-africa/jobs/{id}     # Job detail
  POST /api/crawlers/north-africa/jobs/{id}/cancel
  POST /api/crawlers/north-africa/sync          # Cross-validate data
  GET  /api/crawlers/north-africa/countries     # Supported countries info
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawlers/north-africa", tags=["North Africa Crawlers"])


# ==================== Request Models ====================

class NorthAfricaCrawlRequest(BaseModel):
    countries: Optional[List[str]] = None
    max_per_chapter: Optional[int] = None
    max_headings: Optional[int] = None
    max_positions: Optional[int] = None
    resume: bool = True


# ==================== Helper ====================

def _get_orchestrator():
    from services.crawlers.regional_orchestrator import get_north_africa_orchestrator
    return get_north_africa_orchestrator()


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
        from services.regional_intelligence_service import get_regional_intelligence
        intel = get_regional_intelligence()
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
