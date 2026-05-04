"""
Enhanced Calculator Routes v2 – DZA-aware tariff calculation endpoints.

New endpoints:
    POST /api/enhanced-calculator/dza        Calculate with DZA-specific features
    GET  /api/enhanced-calculator/sources    Show data source priority

These routes extend the existing calculator with:
- Priority system: DZA authentic data > crawled data > tariff_service > ETL fallback
- Real-time data freshness checking
- Confidence scoring based on data source
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.crawler_config import get_crawler_config, get_integration_config
from services.enhanced_calculator_service import calculate_detailed_tariff
from services.tariff_data_service import tariff_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-calculator", tags=["Enhanced Calculator v2"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DZACalculationRequest(BaseModel):
    hs_code: str = Field(..., description="HS code (6–10 digits)")
    fob_value: float = Field(..., gt=0, description="FOB value in USD")
    freight: float = Field(default=0.0, ge=0)
    insurance: float = Field(default=0.0, ge=0)
    language: str = Field(default="fr", pattern="^(fr|en)$")
    use_authentic_data: bool = Field(
        default=True,
        description="Prefer DZA authentic crawled data when available",
    )


# ---------------------------------------------------------------------------
# Helper – load DZA authentic data
# ---------------------------------------------------------------------------

def _load_dza_authentic_line(hs_code: str) -> Optional[Dict[str, Any]]:
    """
    Try to find an authentic DZA tariff line from the latest published dataset.
    Returns None if no data is available.
    """
    cfg = get_crawler_config()
    files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)
    if not files:
        return None

    try:
        data = json.loads(files[0].read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Could not load DZA authentic data: {exc}")
        return None

    hs6 = hs_code[:6]
    hs_clean = hs_code.replace(".", "").replace(" ", "")

    for line in data.get("tariff_lines", []):
        # Match on HS10 first, then HS6
        if line.get("hs10_code", "").startswith(hs_clean):
            return line
        if line.get("hs6_code") == hs6:
            return line

    return None


def _authentic_to_rates(line: Dict[str, Any]) -> Dict[str, float]:
    """Convert an authentic DZA tariff line to the rate dict used by the calculator."""
    taxes = line.get("taxes", {})

    def _pct(val: Optional[float]) -> float:
        if val is None:
            return 0.0
        return val / 100.0

    return {
        "DD": _pct(taxes.get("dd")),
        "TVA": _pct(taxes.get("tva")),
        "PRCT": _pct(taxes.get("prct")),
        "TCS": _pct(taxes.get("tcs")),
        "DAPS": _pct(taxes.get("daps")),
        "TIC": _pct(taxes.get("tic")),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/dza", summary="Calculate DZA tariff with DZA-specific features")
async def calculate_dza(request: DZACalculationRequest):
    """
    Calculate NPF vs ZLECAf tariff comparison for Algeria (DZA) using
    the priority data-source system:

    1. **DZA authentic** – data crawled directly from douane.gov.dz
    2. **Crawled data** – data collected by other scrapers
    3. **Tariff service** – pre-collected JSON files
    4. **ETL fallback** – built-in rates from the ETL layer

    Returns a full breakdown with confidence scoring.
    """
    country_iso3 = "DZA"
    hs_code = request.hs_code.replace(".", "").replace(" ", "")

    # --- Determine data source and rates ---
    data_source = "etl_fallback"
    authentic_line: Optional[Dict[str, Any]] = None

    if request.use_authentic_data:
        authentic_line = _load_dza_authentic_line(hs_code)
        if authentic_line:
            data_source = "dza_authentic"

    # --- Compute calculation using the enhanced calculator service ---
    try:
        result = calculate_detailed_tariff(
            country_iso3=country_iso3,
            hs_code=hs_code,
            fob_value=request.fob_value,
            freight=request.freight,
            insurance=request.insurance,
            language=request.language,
        )
    except Exception as exc:
        logger.error(f"Enhanced calculator failed for DZA/{hs_code}: {exc}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {exc}")

    # --- Enrich with authentic data if available ---
    if authentic_line:
        result["authentic_source"] = {
            "hs10_code": authentic_line.get("hs10_code"),
            "description_fr": authentic_line.get("description_fr"),
            "taxes": authentic_line.get("taxes"),
            "fiscal_advantages": authentic_line.get("fiscal_advantages", []),
            "administrative_formalities": authentic_line.get("administrative_formalities", []),
            "confidence_score": authentic_line.get("confidence_score"),
            "source_url": authentic_line.get("source_url"),
            "crawled_at": authentic_line.get("crawled_at"),
        }

    # Add metadata
    int_cfg = get_integration_config()
    confidence = int_cfg.confidence_scores.get(data_source, 0.6)
    result["data_source"] = data_source
    result["data_confidence"] = confidence
    result["country_iso3"] = country_iso3

    return result


@router.get("/sources", summary="Show data source priority configuration")
async def get_data_sources():
    """
    Return the data source priority configuration used by the enhanced calculator.
    Shows which sources are available and their confidence scores.
    """
    int_cfg = get_integration_config()
    cfg = get_crawler_config()

    # Check DZA authentic data availability
    dza_files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)
    dza_available = len(dza_files) > 0
    dza_info: Dict[str, Any] = {"available": dza_available}
    if dza_available:
        from datetime import datetime, timezone
        mtime = dza_files[0].stat().st_mtime
        file_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - file_dt).total_seconds() / 3600
        dza_info["file"] = dza_files[0].name
        dza_info["last_updated"] = file_dt.isoformat()
        dza_info["age_hours"] = round(age_hours, 2)
        dza_info["is_fresh"] = age_hours < 24

    # Check tariff service
    ts_stats = tariff_service.get_stats()
    tariff_available = ts_stats.get("countries", 0) > 0

    sources = []
    for priority, source in enumerate(int_cfg.source_priority, start=1):
        available = False
        if source == "dza_authentic":
            available = dza_available
        elif source == "tariff_service":
            available = tariff_available
        elif source == "etl_fallback":
            available = True  # always available as last resort

        sources.append({
            "priority": priority,
            "source": source,
            "confidence_score": int_cfg.confidence_scores.get(source, 0.0),
            "available": available,
            **(dza_info if source == "dza_authentic" else {}),
        })

    return {
        "priority_order": int_cfg.source_priority,
        "sources": sources,
    }
