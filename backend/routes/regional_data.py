"""
Regional Data API Routes.

Cross-country data inventory endpoints covering all African countries in the
crawled data directory.

Endpoints:
  GET /api/regional/sub-positions     # Sub-position counts for every country
  GET /api/regional/data-inventory    # Full data inventory for every country
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regional", tags=["Regional Data Inventory"])

CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"

# ==================== Helpers ====================

def _iter_country_files():
    """Yield (country_code, raw_dict) for every *_tariffs.json in crawled dir."""
    if not CRAWLED_DIR.exists():
        return
    for fn in sorted(CRAWLED_DIR.iterdir()):
        if not fn.name.endswith("_tariffs.json"):
            continue
        cc = fn.stem.replace("_tariffs", "").upper()
        try:
            with open(fn, "r", encoding="utf-8") as f:
                yield cc, json.load(f)
        except Exception as exc:
            logger.warning(f"Could not read {fn}: {exc}")


def _get_lines(data: Dict) -> List[Dict]:
    """Return the list of tariff records regardless of file format."""
    if "tariff_lines" in data:
        return data["tariff_lines"]
    if "positions" in data:
        return data["positions"]
    if "sub_positions" in data:
        return data["sub_positions"]
    return []


def _count_sub_positions(lines: List[Dict], data_format: str) -> int:
    """
    Count total 10-digit sub-positions in a list of tariff lines.

    Only enhanced_v2 files embed sub-positions inside each tariff line.
    Old-format files store leaf HS8 codes as flat positions (no nesting).
    """
    if data_format != "enhanced_v2":
        return 0
    total = 0
    for ln in lines:
        cnt = ln.get("sub_position_count")
        if cnt is not None:
            total += int(cnt)
        else:
            total += len(ln.get("sub_positions", []))
    return total


def _build_country_entry(cc: str, data: Dict) -> Dict[str, Any]:
    """Build a standardised inventory entry for one country."""
    data_format = data.get("data_format", "old")
    lines = _get_lines(data)
    summary = data.get("summary", {})

    n_lines = len(lines)
    if n_lines == 0:
        return {
            "iso3": cc,
            "data_format": data_format,
            "status": "empty",
            "tariff_lines": 0,
            "sub_positions": 0,
            "lines_with_sub_positions": 0,
            "avg_sub_per_line": 0.0,
            "chapters_covered": 0,
            "generated_at": data.get("generated_at") or data.get("extracted_at"),
        }

    if data_format == "enhanced_v2":
        total_lines = summary.get("total_tariff_lines", n_lines)
        sub_total = _count_sub_positions(lines, data_format)
        lines_with_sub = summary.get(
            "lines_with_sub_positions",
            sum(1 for ln in lines if ln.get("has_sub_positions", False)),
        )
        chapters = summary.get("chapters_covered", 0)
        generated_at = data.get("generated_at")
    else:
        total_lines = n_lines
        sub_total = 0
        lines_with_sub = 0
        chapters_set = {
            str(p.get("chapter", "") or p.get("hs6", "")[:2]).zfill(2)
            for p in lines
            if p.get("chapter") or p.get("hs6")
        }
        chapters = len(chapters_set) if chapters_set - {""} else 0
        generated_at = data.get("extracted_at") or data.get("generated_at")

    avg_sub = round(sub_total / total_lines, 2) if total_lines else 0.0

    return {
        "iso3": cc,
        "data_format": data_format,
        "status": "available",
        "tariff_lines": total_lines,
        "sub_positions": sub_total,
        "lines_with_sub_positions": lines_with_sub,
        "avg_sub_per_line": avg_sub,
        "chapters_covered": chapters,
        "generated_at": generated_at,
    }


# ==================== Business logic (testable without FastAPI) ====================

def _compute_sub_positions(
    sort: str = "sub_positions",
    min_sub: int = 0,
) -> Dict[str, Any]:
    """
    Core logic for the sub-positions report — callable without FastAPI context.
    """
    rows: List[Dict[str, Any]] = []
    total_lines = 0
    total_sub = 0

    for cc, data in _iter_country_files():
        entry = _build_country_entry(cc, data)
        rows.append(entry)
        total_lines += entry["tariff_lines"]
        total_sub += entry["sub_positions"]

    if min_sub > 0:
        rows = [r for r in rows if r["sub_positions"] >= min_sub]

    reverse = sort != "iso3"
    key = sort if sort in ("sub_positions", "tariff_lines") else "iso3"
    rows.sort(key=lambda r: r.get(key, 0), reverse=reverse)

    countries_with_sub = sum(1 for r in rows if r["sub_positions"] > 0)
    avg_sub = round(total_sub / total_lines, 2) if total_lines else 0.0

    return {
        "note": (
            "Sub-positions are 10-digit national HS codes nested under each "
            "6-digit tariff line. Only countries with enhanced_v2 data include them."
        ),
        "totals": {
            "total_countries": len(rows),
            "countries_with_sub_positions": countries_with_sub,
            "total_tariff_lines": total_lines,
            "total_sub_positions": total_sub,
            "avg_sub_positions_per_line": avg_sub,
        },
        "countries": rows,
    }


def _compute_data_inventory(format_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Core logic for the data inventory report — callable without FastAPI context.
    """
    rows: List[Dict[str, Any]] = []
    total_lines = 0
    total_sub = 0

    for cc, data in _iter_country_files():
        entry = _build_country_entry(cc, data)
        if format_filter and entry.get("data_format") != format_filter:
            continue
        rows.append(entry)
        total_lines += entry["tariff_lines"]
        total_sub += entry["sub_positions"]

    rows.sort(key=lambda r: r["iso3"])

    enhanced = sum(1 for r in rows if r.get("data_format") == "enhanced_v2")
    old_fmt = sum(1 for r in rows if r.get("data_format") != "enhanced_v2")

    return {
        "summary": {
            "total_countries": len(rows),
            "enhanced_v2_countries": enhanced,
            "old_format_countries": old_fmt,
            "total_tariff_lines": total_lines,
            "total_sub_positions": total_sub,
        },
        "countries": rows,
    }


# ==================== Endpoints ====================

@router.get("/sub-positions")
def get_regional_sub_positions(
    sort: str = Query(
        "sub_positions",
        description="Sort field: sub_positions | tariff_lines | iso3",
    ),
    min_sub: int = Query(0, ge=0, description="Filter: minimum sub-position count"),
):
    """
    How many sub-positions (10-digit HS codes) we get per country — all countries.

    Sub-positions are the most granular tariff level: each 6-digit HS tariff
    line (hs6) may expand into multiple 10-digit national sub-positions that
    carry the applicable duty rate, product description, and fiscal regime.

    Query parameters:
    - sort: sub_positions (default) | tariff_lines | iso3
    - min_sub: include only countries with at least this many sub-positions
    """
    return _compute_sub_positions(sort=sort, min_sub=min_sub)


@router.get("/data-inventory")
def get_regional_data_inventory(
    format_filter: Optional[str] = Query(
        None,
        description="Filter by data format: enhanced_v2 | old",
    ),
):
    """
    Full data inventory for all crawled African countries.

    Returns per-country statistics: tariff line counts, sub-position counts,
    HS chapters covered, data format, and data freshness timestamp.

    Query parameters:
    - format_filter: restrict to enhanced_v2 or old format files
    """
    return _compute_data_inventory(format_filter=format_filter)
