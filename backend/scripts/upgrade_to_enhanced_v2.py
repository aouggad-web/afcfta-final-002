#!/usr/bin/env python3
"""
Upgrade old-format tariff data files to enhanced_v2 format.

Handles four old-format sub-types found in data/crawled/:

  cemac8     CMR, CAF, COG, GAB, TCD
             8-digit HS codes, taxes as dict, hs6 field present
             → pad code_clean to 10 digits, group by hs6

  ecowas10   BEN, BFA, CIV, GIN, MLI, NER, SEN, TGO
             10-digit HS codes, taxes as dict, hs6 field is 6-digit clean
             → use code_clean directly, group by hs6

  nga10      NGA
             10-digit HS codes, taxes as list (ID/VAT/IAT/EXC)
             → use code_clean directly, group by first-6-char

  sadc_mixed BWA, LSO, NAM, SWZ, ZAF
             6-digit (hs6 level) and 8-digit (sub-pos) codes, taxes as list
             → 6-digit entries are tariff_lines, 8-digit are sub-positions

Usage:
    # Upgrade all 22 old-format countries
    python scripts/upgrade_to_enhanced_v2.py

    # Upgrade specific countries
    python scripts/upgrade_to_enhanced_v2.py CMR BEN ZAF
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"

# Countries that need upgrading (old-format, non-empty data)
OLD_COUNTRIES = [
    "BEN", "BFA", "BWA", "CAF", "CIV", "CMR", "COG",
    "GAB", "GIN", "LSO", "MLI", "NAM", "NER", "NGA",
    "SEN", "SWZ", "TCD", "TGO", "ZAF",
]

# Empty countries — upgrade format but keep tariff_lines empty
EMPTY_COUNTRIES = ["DZA", "MAR", "TUN"]

ALL_OLD = OLD_COUNTRIES + EMPTY_COUNTRIES


# ================================================================
# Tax extraction helpers
# ================================================================

def _to_float(val: Any) -> float:
    """Convert a tax rate value to float, returning 0.0 for non-numeric values."""
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0  # "variable", "free", etc.


def _tax_rate(taxes: Any, *codes: str, default: float = 0.0) -> float:
    """Extract a duty rate from either dict or list tax format."""
    if isinstance(taxes, dict):
        for code in codes:
            if code in taxes:
                return _to_float(taxes[code])
    elif isinstance(taxes, list):
        for code in codes:
            for t in taxes:
                if t.get("code") == code or t.get("tax_code") == code:
                    v = t.get("rate_pct", t.get("rate", default))
                    return _to_float(v)
    return default


def _total_rate(taxes: Any) -> float:
    """Sum all tax rates in a taxes dict or list."""
    if isinstance(taxes, dict):
        return round(sum(_to_float(v) for v in taxes.values()), 2)
    if isinstance(taxes, list):
        return round(sum(_to_float(t.get("rate_pct", t.get("rate", 0.0))) for t in taxes), 2)
    return 0.0


# ================================================================
# Format detection
# ================================================================

def _detect_format(data: Dict) -> str:
    """
    Detect old-format sub-type from data structure.

    Returns one of: "cemac8" | "ecowas10" | "nga10" | "sadc_mixed" | "empty"
    """
    positions = data.get("positions", [])
    if not positions:
        return "empty"

    p0 = positions[0]
    taxes = p0.get("taxes", {})
    cc = p0.get("code_clean", "")
    cc_len = len(cc)

    if isinstance(taxes, list):
        # SADC (6 or 8 digit) or NGA (10 digit)
        if cc_len == 10:
            return "nga10"
        else:
            return "sadc_mixed"   # 6 or mix of 6/8
    else:
        # CEMAC (8 digit) or ECOWAS (10 digit) — taxes are a dict
        if cc_len <= 8:
            return "cemac8"
        return "ecowas10"


# ================================================================
# HS6 extraction
# ================================================================

def _hs6_of(pos: Dict) -> str:
    """Return the clean 6-digit hs6 code for a position."""
    # Explicit hs6 field (clean or dotted)
    if "hs6" in pos:
        h = pos["hs6"].replace(".", "").replace(" ", "")
        if len(h) >= 6:
            return h[:6]
    # Fall back to first 6 chars of code_clean
    cc = pos.get("code_clean", "")
    return cc[:6] if len(cc) >= 6 else cc


# ================================================================
# taxes_detail builder
# ================================================================

_TAX_LABELS: Dict[str, Tuple[str, str]] = {
    "DD":  ("D.D",   "Droit de Douane"),
    "TVA": ("T.V.A", "Taxe sur la Valeur Ajoutée"),
    "TCI": ("TCI",   "Taxe Communautaire d'Intégration"),
    "RI":  ("RI",    "Redevance Informatique"),
    "RS":  ("RS",    "Redevance Statistique"),
    "TS":  ("TS",    "Taxe Statistique"),
    "PCS": ("PCS",   "Prélèvement Communautaire de Solidarité"),
    "PCC": ("PCC",   "Prélèvement Communautaire CEDEAO"),
    "PUA": ("PUA",   "Prélèvement Union Africaine"),
    "SUR": ("SUR",   "Taxe Complémentaire (Surtaxe)"),
}


def _build_taxes_detail_from_dict(taxes: Dict) -> List[Dict]:
    """Convert old-format taxes dict to enhanced_v2 taxes_detail list."""
    result = []
    for code, rate in taxes.items():
        short, obs = _TAX_LABELS.get(code, (code, code))
        result.append({"tax": short, "rate": _to_float(rate), "observation": obs})
    return result


def _build_taxes_detail_from_list(taxes: List[Dict]) -> List[Dict]:
    """Convert old-format taxes list to enhanced_v2 taxes_detail list."""
    result = []
    for t in taxes:
        code = t.get("code", "")
        rate = _to_float(t.get("rate_pct", t.get("rate", 0.0)))
        obs = t.get("name", t.get("tax_name", code))
        result.append({"tax": code, "rate": rate, "observation": obs})
    return result


def _build_taxes_detail(taxes: Any) -> List[Dict]:
    if isinstance(taxes, dict):
        return _build_taxes_detail_from_dict(taxes)
    if isinstance(taxes, list):
        return _build_taxes_detail_from_list(taxes)
    return []


# ================================================================
# Sub-position builder
# ================================================================

def _build_sub_position(pos: Dict, format_type: str, dd_rate: float, country_code: str) -> Dict:
    """Build one sub_position entry from an old-format position."""
    code_clean = pos.get("code_clean", "")

    if format_type == "cemac8":
        # 8-digit → pad to 10 digits
        code10 = code_clean + "00"
    elif format_type in ("ecowas10", "nga10"):
        # already 10-digit
        code10 = code_clean
    elif format_type == "sadc_mixed":
        # 8-digit sub-positions → pad to 10
        code10 = code_clean + "00"
    else:
        code10 = code_clean

    desc_fr = pos.get("designation") or pos.get("hs6_desc") or ""
    desc_en = desc_fr  # Bilingual designation not available in old format

    return {
        "code": code10,
        "digits": len(code10),
        "dd": dd_rate,
        "description_fr": desc_fr,
        "description_en": desc_en,
        "source": f"Nomenclature nationale {country_code} ({format_type})",
    }


# ================================================================
# Default fiscal structures
# ================================================================

def _default_fiscal_advantage(dd_rate: float) -> List[Dict]:
    return [
        {
            "tax": "D.D",
            "rate": 0.0,
            "condition_fr": "Certificat d'Origine dans le cadre ZLECAf - Exonération DD",
            "condition_en": "Certificate of Origin under AfCFTA - DD Exemption",
        }
    ]


_DEFAULT_ADMIN = [
    {
        "code": "910",
        "document_fr": "Déclaration d'Importation du Produit",
        "document_en": "Product Import Declaration",
    }
]


# ================================================================
# Core migration per position group
# ================================================================

def _group_positions(positions: List[Dict]) -> Dict[str, List[Dict]]:
    """Group positions by their 6-digit hs6 code."""
    by_hs6: Dict[str, List[Dict]] = defaultdict(list)
    for pos in positions:
        hs6 = _hs6_of(pos)
        if hs6:
            by_hs6[hs6].append(pos)
    return by_hs6


def _build_tariff_line(
    hs6: str,
    group: List[Dict],
    format_type: str,
    country_code: str,
) -> Dict:
    """Convert one hs6 group of old-format positions into an enhanced_v2 tariff_line."""

    # Separate hs6-level entries (6-digit) from sub-position entries (>6 digits)
    hs6_entries = [p for p in group if len(p.get("code_clean", "")) == 6]
    sub_entries = [p for p in group if len(p.get("code_clean", "")) > 6]

    # For formats where all codes are longer than 6 digits (cemac8, ecowas10, nga10)
    # every entry in the group is a sub-position.
    # The tariff_line descriptor is synthesised from the first entry.
    if format_type in ("cemac8", "ecowas10", "nga10"):
        primary = group[0]
        sub_positions_raw = group  # all entries become sub-positions
    else:
        # sadc_mixed: 6-digit entry is the descriptor, 8-digit entries are sub-positions
        primary = hs6_entries[0] if hs6_entries else group[0]
        sub_positions_raw = sub_entries

    taxes = primary.get("taxes", {})
    dd_code = "DD" if isinstance(taxes, dict) else ("ID" if "ID" in str(taxes) else "GENERAL")
    dd_rate = _tax_rate(taxes, "DD", "ID", "GENERAL", default=0.0)
    vat_rate = _tax_rate(taxes, "TVA", "VAT", default=0.0)
    other_taxes = _tax_rate(taxes, "TCI", "RS", "PCS", default=0.0)
    total_rate = _total_rate(taxes)

    # Description — prefer hs6_desc (ECOWAS has it), fallback to designation
    desc_fr = primary.get("hs6_desc") or primary.get("designation") or ""
    desc_en = desc_fr

    chapter = str(primary.get("chapter", hs6[:2]) or hs6[:2]).zfill(2)
    unit = primary.get("unit") or primary.get("statistical_unit") or "KG"
    source = primary.get("source") or f"Tarif national {country_code}"

    # Preserve existing fiscal structures if present in old format
    fiscal = primary.get("fiscal_advantages", _default_fiscal_advantage(dd_rate))
    admin = primary.get("administrative_formalities", _DEFAULT_ADMIN)

    # Build sub-positions
    sub_list = []
    for sp in sub_positions_raw:
        sp_taxes = sp.get("taxes", taxes)
        sp_dd = _tax_rate(sp_taxes, "DD", "ID", "GENERAL", default=dd_rate)
        sub_list.append(_build_sub_position(sp, format_type, sp_dd, country_code))

    has_sub = len(sub_list) > 0

    return {
        "hs6": hs6,
        "chapter": chapter,
        "description_fr": desc_fr,
        "description_en": desc_en,
        "category": primary.get("category", "general"),
        "unit": unit,
        "sensitivity": "normal",
        "dd_rate": dd_rate,
        "dd_source": source,
        "zlecaf_rate": 0.0,
        "zlecaf_source": "ZLECAf (tarif préférentiel AfCFTA)",
        "vat_rate": vat_rate,
        "other_taxes_rate": other_taxes,
        "taxes_detail": _build_taxes_detail(taxes),
        "total_taxes_pct": total_rate,
        "fiscal_advantages": fiscal,
        "administrative_formalities": admin,
        "total_import_taxes": total_rate,
        "zlecaf_total_taxes": round(total_rate - dd_rate, 2),
        "sub_positions": sub_list,
        "has_sub_positions": has_sub,
        "sub_position_count": len(sub_list),
    }


# ================================================================
# Top-level migration
# ================================================================

def _migrate_country(data: Dict, country_code: str) -> Dict:
    """Convert an old-format dict to enhanced_v2."""
    positions = data.get("positions", [])
    country_name = data.get("country_name", country_code)

    if not positions:
        return {
            "country_code": country_code,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_format": "enhanced_v2",
            "summary": {
                "total_tariff_lines": 0,
                "total_sub_positions": 0,
                "total_positions": 0,
                "lines_with_sub_positions": 0,
                "vat_rate_pct": 0.0,
                "vat_source": country_name,
                "other_taxes_pct": 0.0,
                "other_taxes_detail": {},
                "dd_rate_range": {"min": 0.0, "max": 0.0, "avg": 0.0},
                "chapters_covered": 0,
                "has_detailed_taxes": False,
            },
            "tariff_lines": [],
        }

    format_type = _detect_format(data)
    logger.info(f"  format_type={format_type}, positions={len(positions)}")

    by_hs6 = _group_positions(positions)

    tariff_lines = []
    total_sub = 0
    lines_with_sub = 0
    all_dd_rates: List[float] = []
    chapters: set = set()

    for hs6 in sorted(by_hs6):
        group = by_hs6[hs6]
        line = _build_tariff_line(hs6, group, format_type, country_code)
        tariff_lines.append(line)

        n_sub = line["sub_position_count"]
        total_sub += n_sub
        if line["has_sub_positions"]:
            lines_with_sub += 1

        all_dd_rates.append(line["dd_rate"])
        ch = str(line.get("chapter", hs6[:2])).zfill(2)
        if ch:
            chapters.add(ch)

    # Summary stats
    vat_sample = _tax_rate(positions[0].get("taxes", {}), "TVA", "VAT", default=0.0)
    other_sample = _tax_rate(positions[0].get("taxes", {}), "TCI", "RS", "PCS", default=0.0)

    summary = {
        "total_tariff_lines": len(tariff_lines),
        "total_sub_positions": total_sub,
        "total_positions": len(tariff_lines) + total_sub,
        "lines_with_sub_positions": lines_with_sub,
        "vat_rate_pct": vat_sample,
        "vat_source": country_name,
        "other_taxes_pct": other_sample,
        "other_taxes_detail": {},
        "dd_rate_range": {
            "min": min(all_dd_rates) if all_dd_rates else 0.0,
            "max": max(all_dd_rates) if all_dd_rates else 0.0,
            "avg": round(sum(all_dd_rates) / len(all_dd_rates), 2) if all_dd_rates else 0.0,
        },
        "chapters_covered": len(chapters),
        "has_detailed_taxes": True,
    }

    return {
        "country_code": country_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_format": "enhanced_v2",
        "summary": summary,
        "tariff_lines": tariff_lines,
    }


# ================================================================
# File I/O
# ================================================================

def upgrade_country(country_code: str) -> bool:
    """Read, migrate, and overwrite one country's tariff data file."""
    path = CRAWLED_DIR / f"{country_code}_tariffs.json"
    if not path.exists():
        logger.warning(f"{country_code}: file not found at {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("data_format") == "enhanced_v2":
        logger.info(f"{country_code}: already enhanced_v2, skipping")
        return True

    logger.info(f"{country_code}: upgrading from old format ...")
    v2 = _migrate_country(data, country_code)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(v2, f, ensure_ascii=False, indent=2)

    n_lines = v2["summary"]["total_tariff_lines"]
    n_sub = v2["summary"]["total_sub_positions"]
    logger.info(f"{country_code}: ✓ {n_lines} tariff_lines, {n_sub} sub-positions")
    return True


def main() -> None:
    targets = sys.argv[1:] if len(sys.argv) > 1 else ALL_OLD
    targets = [t.upper() for t in targets]

    success = 0
    for cc in targets:
        if upgrade_country(cc):
            success += 1

    logger.info(f"Done: {success}/{len(targets)} countries upgraded to enhanced_v2")


if __name__ == "__main__":
    main()
