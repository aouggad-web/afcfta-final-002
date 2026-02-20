from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from services.crawl_orchestrator import get_orchestrator
from crawlers.all_countries_registry import AFRICAN_COUNTRIES_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["Crawl Orchestration"])


class CrawlStartRequest(BaseModel):
    country_codes: Optional[List[str]] = None
    priority: Optional[str] = None
    region: Optional[str] = None
    block: Optional[str] = None
    force_generic: bool = False


@router.post("/start")
async def start_crawl(request: CrawlStartRequest):
    orchestrator = get_orchestrator()

    try:
        job = await orchestrator.start_crawl(
            country_codes=request.country_codes or [],
            priority=request.priority,
            region=request.region,
            block=request.block,
            force_generic=request.force_generic,
        )
        return {
            "message": f"Crawl job {job.job_id} started for {len(job.country_codes)} countries",
            "job": job.summary,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
):
    orchestrator = get_orchestrator()
    return {
        "jobs": orchestrator.list_jobs(status=status, limit=limit),
        "stats": orchestrator.get_stats(),
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job.to_dict()


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    orchestrator = get_orchestrator()
    success = orchestrator.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or not cancellable")
    return {"message": f"Job {job_id} cancelled", "job": orchestrator.get_job(job_id).summary}


@router.get("/registry")
async def get_registry():
    from crawlers.scraper_factory import ScraperFactory

    stats = ScraperFactory.get_registry_stats()
    return {
        "total_countries": stats["total_countries"],
        "specific_scrapers": stats["specific_scrapers"],
        "using_generic": stats["using_generic"],
        "coverage_percentage": round(stats["coverage_percentage"], 1),
        "registered_countries": stats["registered_countries"],
    }


@router.get("/countries")
async def list_crawl_countries(
    priority: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    block: Optional[str] = Query(None),
):
    from crawlers.all_countries_registry import (
        get_priority_countries,
        get_countries_by_region,
        get_countries_by_block,
        Priority,
        Region,
        RegionalBlock,
    )

    try:
        if priority:
            p = Priority[priority.upper()]
            codes = get_priority_countries(p)
        elif region:
            r = Region[region.upper().replace(" ", "_")]
            codes = get_countries_by_region(r)
        elif block:
            b = RegionalBlock[block.upper()]
            codes = get_countries_by_block(b)
        else:
            codes = list(AFRICAN_COUNTRIES_REGISTRY.keys())
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")

    countries = []
    for code in codes:
        config = AFRICAN_COUNTRIES_REGISTRY.get(code, {})
        countries.append({
            "iso3": code,
            "iso2": config.get("iso2", ""),
            "name_en": config.get("name_en", ""),
            "name_fr": config.get("name_fr", ""),
            "region": config.get("region", "").value if hasattr(config.get("region", ""), "value") else "",
            "priority": config.get("priority", "").value if hasattr(config.get("priority", ""), "value") else "",
            "customs_url": config.get("customs_url", ""),
        })

    return {"count": len(countries), "countries": countries}


@router.get("/notifications/stats")
async def get_notification_stats():
    orchestrator = get_orchestrator()
    if orchestrator.notification_manager:
        return orchestrator.notification_manager.get_stats()
    return {"message": "No notification channels configured", "channels": []}
