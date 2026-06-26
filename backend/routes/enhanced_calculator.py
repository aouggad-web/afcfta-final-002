from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from config.crawler_config import get_crawler_config, get_integration_config
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.enhanced_calculator_service import calculate_detailed_tariff

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
    enriched_path = (
        Path(__file__).resolve().parent.parent / "data" / "crawled" / "DZA_tariffs_enriched.json"
    )
    if not enriched_path.exists():
        return None, "etl_fallback"

    try:
        enriched = json.loads(enriched_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Could not load DZA enriched data: {exc}")
        return None, "etl_fallback"

    extracted_at = enriched.get("extracted_at", "")

    for sub in enriched.get("sub_positions", []):
        sub_hs = str(sub.get("hs_code", "")).replace(".", "").replace(" ", "")
        raw_code = str(sub.get("raw_code", "")).replace(".", "").replace(" ", "")
        if sub_hs == hs_clean or raw_code == hs_clean:
            return _build_dza_enriched_line(sub, extracted_at), "dza_enriched"

    for sub in enriched.get("sub_positions", []):
        sub_hs = str(sub.get("hs_code", "")).replace(".", "").replace(" ", "")
        if sub_hs.startswith(hs6):
            line = _build_dza_enriched_line(sub, extracted_at)
            line["confidence_score"] = 0.75
            return line, "dza_enriched"

    return None, "etl_fallback"


@router.post("/dza", summary="Calculate DZA tariff with DZA-specific features")
async def calculate_dza(request: DZACalculationRequest):
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
