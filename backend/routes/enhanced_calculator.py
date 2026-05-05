"""
Enhanced Calculator Routes v2 – DZA-aware tariff calculation endpoints.

Endpoints:
    POST /api/enhanced-calculator/dza        Calculate with DZA-specific features
    GET  /api/enhanced-calculator/sources    Show data source priority

Priority system:
    dza_authentic > dza_enriched > tariff_service > etl_fallback
Each source carries a confidence score read from `config.crawler_config`.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.crawler_config import get_crawler_config, get_integration_config
from services.enhanced_calculator_service import calculate_detailed_tariff
from services.tariff_data_service import tariff_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-calculator", tags=["Enhanced Calculator v2"])


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


def _build_dza_enriched_line(sub: Dict[str, Any], extracted_at: str = "") -> Dict[str, Any]:
    hs10 = str(sub.get("hs_code", "")).replace(".", "").replace(" ", "")
    description = sub.get("description") or sub.get("name", "")

    return {
        "hs10_code": hs10,
        "hs6_code": hs10[:6],
        "description_fr": description,
        "taxes": {
            "dd": sub.get("dd_rate", 0.0),
            "tva": sub.get("tva_rate", 0.0),
            "prct": sub.get("prct_rate", 0.0),
            "tcs": sub.get("tcs_rate", 0.0),
            "daps": sub.get("daps_rate", 0.0),
            "tic": 0.0,
        },
        "fiscal_advantages": sub.get("fiscal_advantages", []),
        "administrative_formalities": sub.get("administrative_formalities", []),
        "confidence_score": 0.85,
        "source_url": sub.get("source_url"),
        "crawled_at": extracted_at,
    }


def _load_dza_authentic_line(hs_code: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Look up an authentic DZA tariff line.

    Lookup order:
        1. Latest published authentic dataset (`published/DZA/dza_published_*.json`)
        2. Enriched crawled fallback (`data/crawled/DZA_tariffs_enriched.json`)
    """
    cfg = get_crawler_config()
    files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)

    hs_clean = hs_code.replace(".", "").replace(" ", "")
    hs6 = hs_clean[:6]

    # 1) Published authentic dataset
    if files:
        try:
            data = json.loads(files[0].read_text(encoding="utf-8"))
            for line in data.get("tariff_lines", []):
                if line.get("hs10_code", "").startswith(hs_clean):
                    return line, "dza_authentic"
                if line.get("hs6_code") == hs6:
                    return line, "dza_authentic"
        except Exception as exc:
            logger.warning(f"Could not load DZA authentic data: {exc}")

    # 2) Enriched crawled fallback
    enriched_path = Path(__file__).resolve().parent.parent / "data" / "crawled" / "DZA_tariffs_enriched.json"
    if not enriched_path.exists():
        return None, "etl_fallback"

    try:
        enriched = json.loads(enriched_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Could not load DZA enriched data: {exc}")
        return None, "etl_fallback"

    extracted_at = enriched.get("extracted_at", "")

    # Exact HS10 match first
    for sub in enriched.get("sub_positions", []):
        sub_hs = str(sub.get("hs_code", "")).replace(".", "").replace(" ", "")
        raw_code = str(sub.get("raw_code", "")).replace(".", "").replace(" ", "")
        if sub_hs == hs_clean or raw_code == hs_clean:
            return _build_dza_enriched_line(sub, extracted_at), "dza_enriched"

    # HS6 prefix fallback (lower confidence)
    for sub in enriched.get("sub_positions", []):
        sub_hs = str(sub.get("hs_code", "")).replace(".", "").replace(" ", "")
        if sub_hs.startswith(hs6):
            line = _build_dza_enriched_line(sub, extracted_at)
            line["confidence_score"] = 0.75
            return line, "dza_enriched"

    return None, "etl_fallback"


@router.post("/dza", summary="Calculate DZA tariff with DZA-specific features")
async def calculate_dza(request: DZACalculationRequest):
    """
    Calculate NPF vs ZLECAf tariff comparison for Algeria (DZA) using
    the priority data-source system:

    1. **dza_authentic**  – published dataset from douane.gov.dz
    2. **dza_enriched**   – enriched crawl with HS10 sub-positions
    3. **tariff_service** – fallback pre-collected JSON files
    4. **etl_fallback**   – built-in rates from the ETL layer
    """
    country_iso3 = "DZA"
    hs_code = request.hs_code.replace(".", "").replace(" ", "")

    data_source = "etl_fallback"
    authentic_line: Optional[Dict[str, Any]] = None

    if request.use_authentic_data:
        authentic_line, data_source = _load_dza_authentic_line(hs_code)

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

    int_cfg = get_integration_config()
    result["data_source"] = data_source
    result["data_confidence"] = int_cfg.confidence_scores.get(data_source, 0.6)
    result["country_iso3"] = country_iso3

    return result


@router.get("/sources", summary="Show data source priority configuration")
async def get_data_sources():
    """
    Return the data source priority used by the enhanced calculator,
    along with each source's availability and confidence score.
    """
    int_cfg = get_integration_config()
    cfg = get_crawler_config()

    # DZA authentic published dataset
    dza_files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)
    dza_authentic_available = len(dza_files) > 0
    dza_authentic_info: Dict[str, Any] = {"available": dza_authentic_available}
    if dza_authentic_available:
        from datetime import datetime, timezone
        mtime = dza_files[0].stat().st_mtime
        file_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - file_dt).total_seconds() / 3600
        dza_authentic_info.update({
            "file": dza_files[0].name,
            "last_updated": file_dt.isoformat(),
            "age_hours": round(age_hours, 2),
            "is_fresh": age_hours < 24,
        })

    # DZA enriched crawl
    enriched_path = Path(__file__).resolve().parent.parent / "data" / "crawled" / "DZA_tariffs_enriched.json"
    dza_enriched_info = {"available": enriched_path.exists()}
    if enriched_path.exists():
        from datetime import datetime, timezone
        mtime = enriched_path.stat().st_mtime
        file_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - file_dt).total_seconds() / 3600
        dza_enriched_info.update({
            "file": enriched_path.name,
            "last_updated": file_dt.isoformat(),
            "age_hours": round(age_hours, 2),
            "is_fresh": age_hours < 24,
        })

    # Tariff service
    ts_stats = tariff_service.get_stats()
    tariff_available = ts_stats.get("countries", 0) > 0

    sources = []
    for priority, source in enumerate(int_cfg.source_priority, start=1):
        if source == "dza_authentic":
            extras = dza_authentic_info
            available = dza_authentic_info["available"]
        elif source == "dza_enriched":
            extras = dza_enriched_info
            available = dza_enriched_info["available"]
        elif source == "tariff_service":
            extras = {"countries_loaded": ts_stats.get("countries", 0)}
            available = tariff_available
        else:
            extras = {}
            available = True  # etl_fallback always available

        sources.append({
            "priority": priority,
            "source": source,
            "confidence_score": int_cfg.confidence_scores.get(source, 0.0),
            "available": available,
            **extras,
        })

    return {
        "priority_order": int_cfg.source_priority,
        "sources": sources,
    }
