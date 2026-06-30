"""
Afreximbank African Trade Report 2026 — sourced data accessor.

Exposes discrete factual indicators extracted (with attribution) from the
Afreximbank African Trade Report 2026:

- continental 2025 indicators (real GDP growth, inflation, merchandise trade,
  intra-African trade);
- intra-African trade by country, 2021-2025 (from the report's table).

Only facts/figures are stored (data/json/afreximbank_atr2026.json) — the
copyrighted report itself is NOT reproduced. Everything carries the source so
the UI can attribute it.
"""

import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "data",
    "json",
    "afreximbank_atr2026.json",
)

SOURCE = "Afreximbank, African Trade Report 2026"

_CACHE: Optional[Dict] = None


def _load() -> Dict:
    global _CACHE
    if _CACHE is None:
        try:
            with open(_DATA_PATH, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Afreximbank ATR 2026 dataset unavailable: %s", e)
            _CACHE = {}
    return _CACHE


def get_continental_indicators() -> Dict:
    """Continental 2025 indicators as stated by Afreximbank (or {} if missing)."""
    return _load().get("continental_indicators_2025", {})


def get_intra_african_total_busd() -> Optional[float]:
    """Total intra-African merchandise trade in 2025 (USD billions)."""
    return _load().get("intra_african_trade_total_busd_2025")


def get_intra_african_by_country() -> Dict[str, Dict]:
    """Intra-African trade by ISO3, 2021-2025 (USD billions) with 2025 share."""
    return _load().get("intra_african_trade_by_country", {})


def get_country_intra_african(iso3: str) -> Optional[Dict]:
    """Intra-African trade record for one country, or None."""
    return get_intra_african_by_country().get((iso3 or "").upper())


def get_top_intra_african(limit: int = 8) -> List[Dict]:
    """Top countries by 2025 intra-African trade (already value-sorted)."""
    rows = []
    for iso3, rec in get_intra_african_by_country().items():
        rows.append(
            {
                "iso3": iso3,
                "name": rec.get("name"),
                "intra_african_2025_busd": rec.get("intra_african_2025_busd"),
                "share_2025_pct": rec.get("share_2025_pct"),
            }
        )
    rows.sort(key=lambda r: r.get("intra_african_2025_busd") or 0, reverse=True)
    return rows[:limit]
