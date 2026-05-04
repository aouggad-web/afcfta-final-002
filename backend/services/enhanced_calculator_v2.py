"""
Enhanced Calculator v2 – DZA-integrated tariff calculator service.

This module re-exports the existing EnhancedTariffCalculator and
calculate_detailed_tariff function from enhanced_calculator_service.py,
and extends them with DZA-specific authentic-data integration.

Priority system:
    1. DZA authentic data (crawled from douane.gov.dz)
    2. Collected crawled data
    3. Tariff data service (pre-built JSON)
    4. ETL fallback (built-in rates)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Re-export from the original service so existing callers are unaffected
from services.enhanced_calculator_service import (  # noqa: F401
    EnhancedTariffCalculator,
    calculate_detailed_tariff,
    ComparisonResult,
    CalculationBreakdown,
    TaxLine,
    COUNTRY_TAX_CONFIG,
)

from config.crawler_config import get_crawler_config, get_integration_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DZA-specific helpers
# ---------------------------------------------------------------------------

def _get_latest_published_file() -> Optional[Path]:
    cfg = get_crawler_config()
    files = sorted(cfg.published_dir.glob("dza_published_*.json"), reverse=True)
    return files[0] if files else None


def get_dza_authentic_line(hs_code: str) -> Optional[Dict[str, Any]]:
    """
    Look up an authentic DZA tariff line from the latest published dataset.

    Returns None if no published data exists or if the HS code is not found.
    """
    f = _get_latest_published_file()
    if not f:
        return None

    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Could not read DZA published data: {exc}")
        return None

    hs6 = hs_code[:6]
    hs_clean = hs_code.replace(".", "").replace(" ", "")

    for line in data.get("tariff_lines", []):
        if line.get("hs10_code", "").startswith(hs_clean):
            return line
        if line.get("hs6_code") == hs6:
            return line

    return None


def is_dza_data_fresh(max_age_hours: float = 24.0) -> bool:
    """Return True if the latest published DZA dataset is younger than max_age_hours."""
    f = _get_latest_published_file()
    if not f:
        return False
    age = (datetime.now(timezone.utc).timestamp() - f.stat().st_mtime) / 3600
    return age < max_age_hours


def get_dza_data_source_info() -> Dict[str, Any]:
    """Return metadata about the DZA authentic data availability."""
    f = _get_latest_published_file()
    if not f:
        return {"available": False}

    stat = f.stat()
    file_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - file_dt).total_seconds() / 3600

    try:
        meta = json.loads(f.read_text(encoding="utf-8"))
        total_lines = meta.get("total_lines", 0)
    except Exception:
        total_lines = 0

    return {
        "available": True,
        "file": f.name,
        "last_updated": file_dt.isoformat(),
        "age_hours": round(age_hours, 2),
        "is_fresh": age_hours < 24,
        "total_lines": total_lines,
    }


# ---------------------------------------------------------------------------
# v2 Extended Calculator
# ---------------------------------------------------------------------------

class EnhancedTariffCalculatorV2(EnhancedTariffCalculator):
    """
    Extended version of EnhancedTariffCalculator with DZA authentic-data
    integration and the full priority-based data-source system.
    """

    def calculate_dza(
        self,
        hs_code: str,
        fob_value: float,
        freight: float = 0.0,
        insurance: float = 0.0,
        language: str = "fr",
        use_authentic_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate DZA tariff comparison with priority-based data source selection.

        Returns a dict mirroring calculate_detailed_tariff() output, enriched
        with authentic-source details and confidence scoring.
        """
        int_cfg = get_integration_config()

        # --- Resolve data source ---
        authentic_line: Optional[Dict[str, Any]] = None
        data_source = "etl_fallback"

        if use_authentic_data:
            authentic_line = get_dza_authentic_line(hs_code)
            if authentic_line:
                data_source = "dza_authentic"

        # --- Base calculation ---
        result = calculate_detailed_tariff(
            country_iso3="DZA",
            hs_code=hs_code,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            language=language,
        )

        # --- Enrich with authentic metadata ---
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

        result["data_source"] = data_source
        result["data_confidence"] = int_cfg.confidence_scores.get(data_source, 0.6)
        result["country_iso3"] = "DZA"
        return result


# Singleton v2 calculator
enhanced_calculator_v2 = EnhancedTariffCalculatorV2()
