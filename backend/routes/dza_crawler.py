"""
DZA Crawler API – Routes for managing Algeria tariff crawl sessions
and the collected data lifecycle.

Endpoints:
    POST /api/dza-crawler/start          Start a new crawl session
    GET  /api/dza-crawler/status         Status of the latest (or given) session
    GET  /api/dza-crawler/stats          Overall crawling statistics
    POST /api/dza-crawler/stop           Stop the current crawl session

    GET  /api/dza-data/freshness         Check age of published data
    POST /api/dza-data/refresh           Trigger data refresh (alias for start)
    GET  /api/dza-data/export            Export collected data
    GET  /api/dza-data/validate          Run quality checks on stored data
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from config.crawler_config import get_crawler_config
from services.crawlers.crawler_manager import get_crawler_manager
from services.crawlers.data_validator import DataValidator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router definition
# ---------------------------------------------------------------------------

router = APIRouter(tags=["DZA Crawler"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class StartCrawlRequest(BaseModel):
    max_workers: Optional[int] = None
    rate_limit_delay: Optional[float] = None
    max_pages: Optional[int] = None


class RefreshRequest(BaseModel):
    force: bool = False


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _latest_published_file() -> Optional[Path]:
    cfg = get_crawler_config()
    files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)
    return files[0] if files else None


def _load_published_lines() -> List[Dict[str, Any]]:
    f = _latest_published_file()
    if not f:
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data.get("tariff_lines", [])
    except Exception as exc:
        logger.error(f"Failed to load published data: {exc}")
        return []


# ---------------------------------------------------------------------------
# Crawler management endpoints
# ---------------------------------------------------------------------------

@router.post("/dza-crawler/start", summary="Start DZA tariff crawl session")
async def start_dza_crawl(request: StartCrawlRequest, background_tasks: BackgroundTasks):
    """
    Launch a new async crawl session against douane.gov.dz.
    The crawl runs in the background; use /status to monitor progress.
    """
    manager = get_crawler_manager()

    overrides: Dict[str, Any] = {}
    if request.max_workers is not None:
        overrides["max_workers"] = request.max_workers
    if request.rate_limit_delay is not None:
        overrides["rate_limit_delay"] = request.rate_limit_delay
    if request.max_pages is not None:
        overrides["max_pages"] = request.max_pages

    session = manager.start_session(config_overrides=overrides if overrides else None)
    return {
        "message": "DZA crawl session started",
        "session_id": session.session_id,
        "status": session.status,
    }


@router.get("/dza-crawler/status", summary="Check crawl session status")
async def get_dza_crawl_status(session_id: Optional[str] = Query(None)):
    """
    Return the status of the latest crawl session (or a specific one by ID).
    """
    manager = get_crawler_manager()

    if session_id:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")
    else:
        session = manager.get_active_session()
        if not session:
            return {"message": "No crawl sessions found", "sessions": []}

    return session.summary


@router.get("/dza-crawler/stats", summary="Get overall crawling statistics")
async def get_dza_crawl_stats():
    """Return aggregate statistics across all crawl sessions."""
    manager = get_crawler_manager()
    return {
        "manager_stats": manager.get_stats(),
        "sessions": manager.get_all_sessions(),
    }


@router.post("/dza-crawler/stop", summary="Stop the active crawl session")
async def stop_dza_crawl(session_id: Optional[str] = Query(None)):
    """Request a graceful stop of the current (or specified) crawl session."""
    manager = get_crawler_manager()

    if session_id:
        success = manager.stop_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")
        return {"message": f"Stop requested for session {session_id}"}

    session = manager.get_active_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active crawl session found")

    manager.stop_session(session.session_id)
    return {"message": f"Stop requested for session {session.session_id}"}


# ---------------------------------------------------------------------------
# Data management endpoints
# ---------------------------------------------------------------------------

@router.get("/dza-data/freshness", summary="Check data age")
async def dza_data_freshness():
    """Return the age and metadata of the most recent published DZA dataset."""
    f = _latest_published_file()
    if not f:
        return {
            "has_data": False,
            "message": "No published DZA data found. Run /api/dza-crawler/start to collect data.",
        }

    stat = f.stat()
    file_ts = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - file_ts).total_seconds() / 3600

    try:
        meta = json.loads(f.read_text(encoding="utf-8"))
        total_lines = meta.get("total_lines", 0)
    except Exception:
        total_lines = 0

    return {
        "has_data": True,
        "file": f.name,
        "last_updated": file_ts.isoformat(),
        "age_hours": round(age_hours, 2),
        "is_fresh": age_hours < 24,
        "total_lines": total_lines,
    }


@router.post("/dza-data/refresh", summary="Trigger data refresh")
async def dza_data_refresh(request: RefreshRequest, background_tasks: BackgroundTasks):
    """
    Trigger a new crawl session to refresh DZA tariff data.
    Alias for POST /dza-crawler/start.
    """
    manager = get_crawler_manager()
    session = manager.start_session()
    return {
        "message": "DZA data refresh started",
        "session_id": session.session_id,
    }


@router.get("/dza-data/export", summary="Export collected data")
async def dza_data_export(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: Optional[int] = Query(None, ge=1, le=100_000),
):
    """
    Export the latest published DZA tariff lines.

    Supported formats: ``json`` (default), ``csv``.
    """
    lines = _load_published_lines()
    if not lines:
        raise HTTPException(
            status_code=404,
            detail="No published DZA data found. Run /api/dza-data/refresh first.",
        )

    if limit:
        lines = lines[:limit]

    if format == "csv":
        import csv
        import io

        output = io.StringIO()
        if lines:
            fieldnames = [
                "hs10_code", "hs6_code", "description_fr",
                "unit", "dd", "tva", "prct", "tcs", "daps", "tic",
                "confidence_score", "source_url",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for ln in lines:
                taxes = ln.get("taxes", {})
                flat = {
                    "hs10_code": ln.get("hs10_code", ""),
                    "hs6_code": ln.get("hs6_code", ""),
                    "description_fr": ln.get("description_fr", ""),
                    "unit": ln.get("unit", ""),
                    "dd": taxes.get("dd", ""),
                    "tva": taxes.get("tva", ""),
                    "prct": taxes.get("prct", ""),
                    "tcs": taxes.get("tcs", ""),
                    "daps": taxes.get("daps", ""),
                    "tic": taxes.get("tic", ""),
                    "confidence_score": ln.get("confidence_score", ""),
                    "source_url": ln.get("source_url", ""),
                }
                writer.writerow(flat)

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dza_tariffs.csv"},
        )

    return {
        "country": "DZA",
        "total": len(lines),
        "tariff_lines": lines,
    }


@router.get("/dza-data/validate", summary="Run quality checks on stored data")
async def dza_data_validate():
    """
    Run the DataValidator against the latest published DZA dataset
    and return a full quality report.
    """
    lines = _load_published_lines()
    if not lines:
        raise HTTPException(
            status_code=404,
            detail="No published DZA data found. Run /api/dza-data/refresh first.",
        )

    from config.crawler_config import get_quality_config
    qcfg = get_quality_config()
    validator = DataValidator(
        min_confidence_score=qcfg.min_confidence_score,
        min_vat_coverage=qcfg.min_vat_coverage,
        min_hs10_coverage=qcfg.min_hs10_coverage,
        strict_mode=qcfg.strict_mode,
    )
    report = validator.validate(lines)
    return {"country": "DZA", "validation_report": report}
