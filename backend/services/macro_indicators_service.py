"""
Macro-financial indicators for the premium Opportunités report engine.

Aggregates *real, sourced* country macro indicators used by the finance angle of
the report engine:

  - GAI  : Global Attractiveness Index 2025 (Mo Ibrahim) — local dataset.
  - Gold reserves (tonnes) — local dataset.
  - FX reserves (total reserves incl. gold, current US$) — World Bank WDI
    indicator ``FI.RES.TOTL.CD``.
  - Import cover (total reserves in months of imports) — World Bank WDI
    indicator ``FI.RES.TOTL.MO``.

No-fabrication discipline: GAI and gold reserves come from the committed
``gold_reserves_gai_2025.json`` dataset. FX reserves and import cover are served
from ``data/json/wb_reserves.json`` when that file has been produced by the
reproducible ETL (``etl/fetch_wb_reserves.py``); when the file is absent (e.g.
the World Bank API is unreachable from the current environment) the fields
return ``None`` with an explicit ``available: False`` flag rather than any
invented value.

All accessors key on ISO3 country codes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "json"

GAI_SOURCE = "Mo Ibrahim Foundation, Global Attractiveness Index 2025"
GOLD_SOURCE = "World Gold Council — Gold reserves (2025)"
WB_RESERVES_SOURCE = "World Bank, World Development Indicators (WDI)"
WB_FX_RESERVES_INDICATOR = "FI.RES.TOTL.CD"  # Total reserves (incl. gold), current US$
WB_IMPORT_COVER_INDICATOR = "FI.RES.TOTL.MO"  # Total reserves in months of imports


def _load_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logging.getLogger(__name__).warning("Could not load %s: %s", path.name, exc)
        return None


# GAI + gold reserves come from the same committed dataset used elsewhere in the
# platform. Reuse the existing loader to avoid duplicating the path logic.
try:
    from gold_reserves_data import GOLD_RESERVES_GAI_DATA as _GOLD_GAI
except Exception:  # pragma: no cover - fallback if import path differs
    _GOLD_GAI = _load_json(_DATA_DIR / "gold_reserves_gai_2025.json") or {}

_GAI = (_GOLD_GAI or {}).get("global_attractiveness_index_2025", {}) or {}
_GOLD = (_GOLD_GAI or {}).get("gold_reserves", {}) or {}

# FX reserves + import cover: produced by etl/fetch_wb_reserves.py when the World
# Bank API is reachable. Absent -> graceful None (never fabricated).
_WB_RESERVES = _load_json(_DATA_DIR / "wb_reserves.json")


def _iso3(country_code: str) -> str:
    return (country_code or "").strip().upper()


def get_gai(country_iso3: str) -> Optional[Dict]:
    """Global Attractiveness Index for a country, or None if absent."""
    rec = _GAI.get(_iso3(country_iso3))
    if not rec:
        return None
    return {
        "score": rec.get("score"),
        "rank_africa": rec.get("rank_africa"),
        "rank_global": rec.get("rank_global"),
        "rating": rec.get("rating"),
        "trend": rec.get("trend"),
        "source": GAI_SOURCE,
    }


def get_gold_reserves(country_iso3: str) -> Optional[Dict]:
    """Gold reserves (tonnes) for a country, or None if absent."""
    rec = _GOLD.get(_iso3(country_iso3))
    if not rec:
        return None
    return {
        "tonnes": rec.get("tonnes"),
        "rank_africa": rec.get("rank_africa"),
        "rank_global": rec.get("rank_global"),
        "source": GOLD_SOURCE,
    }


def _wb_reserves() -> Optional[dict]:
    """
    Return the WB reserves dataset, lazily (re)loading once if it was absent at
    import time. Lets a cron/ETL that produces wb_reserves.json AFTER the process
    started be picked up without a restart.
    """
    global _WB_RESERVES
    if not _WB_RESERVES:
        _WB_RESERVES = _load_json(_DATA_DIR / "wb_reserves.json")
    return _WB_RESERVES


def _wb_record(country_iso3: str) -> Optional[Dict]:
    data = _wb_reserves()
    if not data:
        return None
    return (data.get("countries", {}) or {}).get(_iso3(country_iso3))


def get_fx_reserves(country_iso3: str) -> Dict:
    """
    Total FX reserves (incl. gold), current US$ billions.

    Returns a dict with ``available`` False and ``value`` None when the WDI
    dataset has not been produced for the current environment — never invents.
    """
    rec = _wb_record(country_iso3)
    val = (rec or {}).get("fx_reserves_busd")
    if val is None:
        return {
            "available": False,
            "value_busd": None,
            "note": (
                "Données non disponibles dans cet environnement. Produire "
                "data/json/wb_reserves.json via etl/fetch_wb_reserves.py "
                f"(indicateur {WB_FX_RESERVES_INDICATOR})."
            ),
            "source": WB_RESERVES_SOURCE,
            "indicator": WB_FX_RESERVES_INDICATOR,
        }
    return {
        "available": True,
        "value_busd": val,
        "year": (rec or {}).get("fx_reserves_year"),
        "source": WB_RESERVES_SOURCE,
        "indicator": WB_FX_RESERVES_INDICATOR,
    }


def get_import_cover(country_iso3: str) -> Dict:
    """
    Import cover — total reserves in months of imports.

    Same graceful-degradation contract as :func:`get_fx_reserves`.
    """
    rec = _wb_record(country_iso3)
    val = (rec or {}).get("import_cover_months")
    if val is None:
        return {
            "available": False,
            "months": None,
            "note": (
                "Données non disponibles dans cet environnement. Produire "
                "data/json/wb_reserves.json via etl/fetch_wb_reserves.py "
                f"(indicateur {WB_IMPORT_COVER_INDICATOR})."
            ),
            "source": WB_RESERVES_SOURCE,
            "indicator": WB_IMPORT_COVER_INDICATOR,
        }
    return {
        "available": True,
        "months": val,
        "year": (rec or {}).get("import_cover_year"),
        "source": WB_RESERVES_SOURCE,
        "indicator": WB_IMPORT_COVER_INDICATOR,
    }


def get_macro_profile(country_iso3: str) -> Dict:
    """Bundle every macro indicator for a country in one call."""
    iso3 = _iso3(country_iso3)
    return {
        "country_iso3": iso3,
        "gai": get_gai(iso3),
        "gold_reserves": get_gold_reserves(iso3),
        "fx_reserves": get_fx_reserves(iso3),
        "import_cover": get_import_cover(iso3),
    }
