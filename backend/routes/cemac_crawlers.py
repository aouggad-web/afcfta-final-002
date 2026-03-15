"""
CEMAC (Central Africa) Crawlers API Routes.

Answers the question "what data we get now" for the 6 CEMAC member states:
  CMR (Cameroon), CAF (Central African Republic), COG (Congo-Brazzaville),
  GAB (Gabon), GNQ (Equatorial Guinea), TCD (Chad)

All share the CEMAC Common External Tariff (TEC CEMAC) with 4 DD bands
(5%, 10%, 20%, 30%) plus country-specific national taxes.

Endpoints:
  GET /api/crawlers/cemac/countries        # CEMAC member configs
  GET /api/crawlers/cemac/data-summary     # What data we have now (per country)
  GET /api/crawlers/cemac/data/{country}   # Full tariff data for one country
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawlers/cemac", tags=["CEMAC Crawlers"])

# ==================== CEMAC country metadata ====================

CEMAC_COUNTRIES: Dict[str, Dict[str, Any]] = {
    "CMR": {
        "iso3": "CMR",
        "country_name": "Cameroun",
        "country_name_en": "Cameroon",
        "primary_source": "cameroontradeportal.cm / douanes.gouv.cm",
        "currency": "XAF (FCFA)",
        "tva_rate": 19.25,
        "tva_note": "17.5% base + 10% CAC (Centimes Additionnels Communaux)",
        "national_taxes": {"TCI": 1.0, "RI": 0.45, "CAC": 10.0},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
    "CAF": {
        "iso3": "CAF",
        "country_name": "République Centrafricaine",
        "country_name_en": "Central African Republic",
        "primary_source": "finances.gouv.cf / edouanes.cf",
        "currency": "XAF (FCFA)",
        "tva_rate": 19.0,
        "tva_note": "Standard rate",
        "national_taxes": {"TCI": 1.0, "RS": 1.0},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
    "COG": {
        "iso3": "COG",
        "country_name": "Congo (Brazzaville)",
        "country_name_en": "Republic of the Congo",
        "primary_source": "douanes.gouv.cg / finances.gouv.cg",
        "currency": "XAF (FCFA)",
        "tva_rate": 18.0,
        "tva_note": "Standard rate (surtaxe 5% possible on some goods)",
        "national_taxes": {"TCI": 1.0, "TS": 0.2, "OHADA": 0.05},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
    "GAB": {
        "iso3": "GAB",
        "country_name": "Gabon",
        "country_name_en": "Gabon",
        "primary_source": "douanes.ga / dgi.ga",
        "currency": "XAF (FCFA)",
        "tva_rate": 18.0,
        "tva_note": "Standard rate (reduced 10%/5% for some sectors)",
        "national_taxes": {"TCI": 1.0, "CIA": 0.2},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
    "GNQ": {
        "iso3": "GNQ",
        "country_name": "Guinée Équatoriale",
        "country_name_en": "Equatorial Guinea",
        "primary_source": "douanes.gq / finances.gq",
        "currency": "XAF (FCFA)",
        "tva_rate": 15.0,
        "tva_note": "Standard rate",
        "national_taxes": {"TCI": 1.0},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
    "TCD": {
        "iso3": "TCD",
        "country_name": "Tchad",
        "country_name_en": "Chad",
        "primary_source": "finances.gouv.td",
        "currency": "XAF (FCFA)",
        "tva_rate": 19.25,
        "tva_note": "17.5% base + 10% Centimes Additionnels (reduced 9.9% for local goods)",
        "national_taxes": {"TCI": 1.0, "TS": 2.0, "PUA": 0.2},
        "preferential_agreements": ["AfCFTA/ZLECAf", "TEC CEMAC", "ECCAS"],
        "dd_bands": [0, 5, 10, 20, 30],
    },
}

DATA_DIR = Path(__file__).parent.parent / "data" / "crawled"


# ==================== Helpers ====================

def _load_country_file(country_code: str) -> Optional[Dict]:
    """Load a CEMAC country tariff JSON file. Returns None if not found."""
    path = DATA_DIR / f"{country_code}_tariffs.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"Failed to read {path}: {exc}")
        return None


def _count_sub_positions(lines: List[Dict], data_format: str) -> int:
    """
    Count total sub-positions across all tariff lines.

    For enhanced_v2 files each line carries a ``sub_position_count`` integer
    (or a ``sub_positions`` list when the count field is absent).
    Old-format files store the leaf-level HS8 codes directly as positions —
    they contain no nested sub-positions, so the count is 0.
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


def _country_data_summary(country_code: str) -> Dict[str, Any]:
    """Build a per-country data summary entry."""
    data = _load_country_file(country_code)
    cfg = CEMAC_COUNTRIES.get(country_code, {})

    if data is None:
        return {
            "iso3": country_code,
            "status": "no_data",
            "tariff_lines": 0,
            "sub_positions": 0,
            "lines_with_sub_positions": 0,
            "chapters_covered": 0,
            "data_format": None,
            "generated_at": None,
        }

    # Support both old and enhanced_v2 formats
    data_format = data.get("data_format", "old")
    if data_format == "enhanced_v2":
        lines = data.get("tariff_lines", [])
        summary = data.get("summary", {})
        total_lines = summary.get("total_tariff_lines", len(lines))
        # Prefer the precise per-line count over the summary field
        sub_positions = _count_sub_positions(lines, data_format)
        lines_with_sub = summary.get(
            "lines_with_sub_positions",
            sum(1 for ln in lines if ln.get("has_sub_positions", False)),
        )
        chapters = summary.get("chapters_covered", 0)
        dd_range = summary.get("dd_rate_range", {})
        generated_at = data.get("generated_at")
    else:
        lines = data.get("positions", [])
        total_lines = len(lines)
        chapters_set = {p.get("chapter", "") for p in lines if p.get("chapter")}
        chapters = len(chapters_set)
        sub_positions = 0   # old-format positions are already leaf-level HS8 codes
        lines_with_sub = 0
        dd_rates = [p.get("taxes", {}).get("DD", 0) for p in lines if "DD" in p.get("taxes", {})]
        dd_range = {
            "min": min(dd_rates) if dd_rates else 0,
            "max": max(dd_rates) if dd_rates else 0,
            "avg": round(sum(dd_rates) / len(dd_rates), 2) if dd_rates else 0,
        }
        generated_at = data.get("extracted_at")

    return {
        "iso3": country_code,
        "country_name": cfg.get("country_name_en", country_code),
        "status": "available",
        "data_format": data_format,
        "generated_at": generated_at,
        "tariff_lines": total_lines,
        "sub_positions": sub_positions,
        "lines_with_sub_positions": lines_with_sub,
        "chapters_covered": chapters,
        "dd_rate_range": dd_range,
        "vat_rate": cfg.get("tva_rate"),
        "national_taxes": list(cfg.get("national_taxes", {}).keys()),
        "preferential_agreements": cfg.get("preferential_agreements", []),
        "fields_available": [
            "hs6", "chapter", "description_fr", "description_en",
            "dd_rate", "vat_rate", "other_taxes_rate", "total_taxes_pct",
            "zlecaf_rate", "zlecaf_total_taxes", "taxes_detail",
            "fiscal_advantages", "administrative_formalities", "sub_positions",
        ] if data_format == "enhanced_v2" else [
            "code", "code_clean", "designation", "chapter", "hs6",
            "taxes", "taxes_detail", "source", "data_type",
        ],
    }


# ==================== Endpoints ====================

@router.get("/countries")
def get_cemac_countries():
    """
    Return the configuration of all 6 CEMAC member states.

    All members share the CEMAC Common External Tariff (TEC CEMAC) with
    four duty bands: 5%, 10%, 20%, 30%. Country-specific national taxes
    (TVA rate, TCI, statistical levies) differ per member.
    """
    countries = list(CEMAC_COUNTRIES.values())
    return {
        "region": "CEMAC (Communauté Économique et Monétaire de l'Afrique Centrale)",
        "trade_bloc": "CEMAC",
        "total_countries": len(countries),
        "common_tariff": "TEC CEMAC (Tarif Extérieur Commun)",
        "dd_bands_pct": [0, 5, 10, 20, 30],
        "common_taxes": {
            "TCI": "Taxe Communautaire d'Intégration — 1% on CIF (all members)",
        },
        "preferential_agreements": ["AfCFTA/ZLECAf", "ECCAS", "TEC CEMAC"],
        "countries": countries,
    }


@router.get("/data-summary")
def get_cemac_data_summary():
    """
    Answer "what data we get now" for all CEMAC member states.

    Reads the crawled tariff data files and returns per-country statistics:
    - Number of tariff lines and sub-positions
    - HS chapters covered
    - DD rate range
    - Tax fields available
    - Data format and freshness
    """
    summaries = []
    total_lines = 0
    total_sub = 0

    for cc in CEMAC_COUNTRIES:
        entry = _country_data_summary(cc)
        summaries.append(entry)
        total_lines += entry.get("tariff_lines", 0)
        total_sub += entry.get("sub_positions", 0)

    available = [s for s in summaries if s["status"] == "available"]

    return {
        "region": "CEMAC",
        "total_countries": len(CEMAC_COUNTRIES),
        "countries_with_data": len(available),
        "total_tariff_lines": total_lines,
        "total_sub_positions": total_sub,
        "cemac_tec_note": (
            "All CEMAC members share the same HS nomenclature and DD bands "
            "(5/10/20/30%). TVA and national levies differ per country."
        ),
        "countries": summaries,
    }


@router.get("/data/{country_code}")
def get_cemac_country_data(
    country_code: str,
    chapter: Optional[str] = Query(None, description="Filter by 2-digit HS chapter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    Get tariff data for a single CEMAC member state.

    Path parameter:
    - country_code: ISO3 code — CMR, CAF, COG, GAB, GNQ, or TCD

    Optional query parameters:
    - chapter: Filter by 2-digit HS chapter (e.g. "01", "87")
    - page / page_size: Pagination (default: page 1, 100 records)
    """
    cc = country_code.upper()
    if cc not in CEMAC_COUNTRIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported country '{cc}'. Valid codes: {list(CEMAC_COUNTRIES)}",
        )

    data = _load_country_file(cc)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No tariff data found for {cc}. Run the CEMAC scraper first.",
        )

    data_format = data.get("data_format", "old")
    if data_format == "enhanced_v2":
        lines = data.get("tariff_lines", [])
    else:
        lines = data.get("positions", [])

    if chapter:
        chapter = chapter.zfill(2)
        lines = [ln for ln in lines if str(ln.get("chapter", "")).zfill(2) == chapter]

    total = len(lines)
    start = (page - 1) * page_size
    paginated = lines[start : start + page_size]

    cfg = CEMAC_COUNTRIES[cc]
    return {
        "country": {
            "iso3": cc,
            "country_name": cfg["country_name_en"],
            "currency": cfg["currency"],
            "tva_rate": cfg["tva_rate"],
        },
        "data_format": data_format,
        "generated_at": data.get("generated_at") or data.get("extracted_at"),
        "filter": {"chapter": chapter},
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
        "tariff_lines": paginated,
    }


@router.get("/sub-positions")
def get_cemac_sub_positions():
    """
    How many sub-positions (10-digit HS codes) we get per CEMAC member state.

    Sub-positions are the most granular tariff level: each 6-digit HS tariff
    line (hs6) may expand into multiple 10-digit national sub-positions that
    carry the actual applicable rate.

    Returns per-country counts sorted from highest to lowest, plus CEMAC
    regional totals.

    Notes:
    - Countries with *enhanced_v2* data (e.g. GNQ) have full sub-position data.
    - Countries with *old-format* data (CMR, CAF, COG, GAB, TCD) store HS8
      codes as flat positions; their 10-digit sub-positions are not yet
      available in the current crawl output.
    """
    rows = []
    regional_sub = 0
    regional_lines = 0
    regional_lines_with_sub = 0

    for cc, cfg in CEMAC_COUNTRIES.items():
        data = _load_country_file(cc)
        if data is None:
            rows.append({
                "iso3": cc,
                "country_name": cfg["country_name_en"],
                "data_format": None,
                "tariff_lines": 0,
                "sub_positions": 0,
                "lines_with_sub_positions": 0,
                "avg_sub_per_line": 0.0,
                "status": "no_data",
            })
            continue

        data_format = data.get("data_format", "old")
        if data_format == "enhanced_v2":
            lines = data.get("tariff_lines", [])
            sub_total = _count_sub_positions(lines, data_format)
            lines_with_sub = sum(1 for ln in lines if ln.get("has_sub_positions", False))
        else:
            lines = data.get("positions", [])
            sub_total = 0
            lines_with_sub = 0

        n_lines = len(lines)
        avg = round(sub_total / n_lines, 2) if n_lines else 0.0

        regional_sub += sub_total
        regional_lines += n_lines
        regional_lines_with_sub += lines_with_sub

        rows.append({
            "iso3": cc,
            "country_name": cfg["country_name_en"],
            "data_format": data_format,
            "tariff_lines": n_lines,
            "sub_positions": sub_total,
            "lines_with_sub_positions": lines_with_sub,
            "avg_sub_per_line": avg,
            "status": "available",
        })

    rows.sort(key=lambda r: r["sub_positions"], reverse=True)

    regional_avg = (
        round(regional_sub / regional_lines, 2) if regional_lines else 0.0
    )

    return {
        "region": "CEMAC",
        "note": (
            "Sub-positions are 10-digit national HS codes nested under each "
            "6-digit tariff line. Only enhanced_v2 data files include them."
        ),
        "regional_totals": {
            "total_tariff_lines": regional_lines,
            "total_sub_positions": regional_sub,
            "total_lines_with_sub_positions": regional_lines_with_sub,
            "avg_sub_positions_per_line": regional_avg,
        },
        "countries": rows,
    }
