#!/usr/bin/env python3
"""Read-only documentary audit for an existing country tariff file.

No network access, rate update, or source transformation is performed.
The country argument makes the control reusable for the priority countries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

QUALITY_VALUES = {"DOCUMENTED", "PARTIAL", "UNVERIFIED", "NOT_AVAILABLE", "NOT_APPLICABLE"}
COUNTRY_NAMES = {"DZA": "Algérie", "MAR": "Maroc", "TUN": "Tunisie", "EGY": "Égypte", "ZAF": "Afrique du Sud", "KEN": "Kenya"}
TAX_ALIASES = {
    "dd": "DD", "d.d": "DD", "droit_de_douane": "DD", "droit de douane": "DD",
    "duty": "DD", "customs_duty": "DD", "general": "DD", "dddroit": "DD",
    "vat": "TVA", "tva": "TVA", "value added tax": "TVA",
    "prct": "PRCT", "tcs": "TCS", "daps": "DAPS", "tic": "TIC",
}
NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def clean_code(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def first(row: Dict[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def tax_name(value: Any) -> str:
    raw = str(value or "").strip()
    low = raw.lower()
    if any(token in low for token in ("droit de douane", "droit d'importation", "customs duty", "cet import", "dddroit", "rntadroit")) or low.startswith("dd"):
        return "DD"
    if "value added tax" in low or low == "vat" or "tva" in low:
        return "TVA"
    return TAX_ALIASES.get(low, raw.upper() or "UNKNOWN")


def parse_rate(raw: Any, unit: Optional[str] = None) -> Dict[str, Any]:
    """Expose raw and parsed values; never overwrite the input rate."""
    if raw in (None, ""):
        return {"normalized_rate_raw": None, "normalized_rate_numeric": None, "rate_type": "UNPARSED", "rate_unit": unit, "rate_parse_status": "MISSING"}
    text = str(raw).strip()
    match = NUMBER_RE.search(text.replace(" ", ""))
    numeric = None
    if match:
        try:
            numeric = float(match.group(0).replace(",", "."))
        except ValueError:
            pass
    low = text.lower()
    if "free" in low or "gratuit" in low or "zero" in low or "صفر" in low:
        rate_type = "FREE"
    elif "exempt" in low or "exon" in low:
        rate_type = "EXEMPT"
    elif "%" in text:
        rate_type = "MIXED" if any(token in low for token in ("+", " or ", "min", "max", "/")) else "AD_VALOREM"
    elif unit or any(token in low for token in ("/kg", "/t", "par kg", "per kg", "usd", "dzd")):
        rate_type = "SPECIFIC"
    elif any(token in low for token in ("+", " or ", "min", "max")):
        rate_type = "COMPOUND"
    else:
        rate_type = "AD_VALOREM" if numeric is not None else "UNPARSED"
    return {
        "normalized_rate_raw": text,
        "normalized_rate_numeric": numeric,
        "rate_type": rate_type,
        "rate_unit": unit,
        "rate_parse_status": "PARSED" if numeric is not None or rate_type in {"FREE", "EXEMPT"} else "UNPARSED",
    }


def flatten(data: Any) -> List[Dict[str, Any]]:
    """Flatten the repository's parent/sub-position variants."""
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("sub_positions"), list):
        return [row for row in data["sub_positions"] if isinstance(row, dict)]
    result: List[Dict[str, Any]] = []
    for parent in data.get("tariff_lines", data.get("positions", data.get("data", []))) or []:
        if not isinstance(parent, dict):
            continue
        children = parent.get("sub_positions")
        if isinstance(children, list) and children:
            for child in children:
                if isinstance(child, dict):
                    merged = dict(parent)
                    merged.update(child)
                    result.append(merged)
        else:
            result.append(parent)
    return result


def load_rows(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            delimiter = ";" if sample.count(";") >= sample.count(",") else ","
            return {}, [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]
    data = json.loads(path.read_text(encoding="utf-8"))
    return (data if isinstance(data, dict) else {}), flatten(data)


def taxes(row: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(row.get("taxes"), dict):
        return {tax_name(key): value for key, value in row["taxes"].items()}
    detail = row.get("taxes_detail", row.get("taxes_import", row.get("tax_structure")))
    if isinstance(row.get("taxes"), list):
        return {tax_name(item.get("name") or item.get("code")): item for item in row["taxes"] if isinstance(item, dict)}
    if isinstance(detail, list):
        return {tax_name(item.get("tax") or item.get("code") or item.get("tax_name")): item for item in detail if isinstance(item, dict)}
    if isinstance(detail, dict):
        return {tax_name(key): value for key, value in detail.items()}
    return {tax_name(key.replace("_rate", "")): row[key] for key in (
        "dd_rate", "duty_rate", "customs_duty", "vat_rate", "tva_rate", "prct_rate", "tcs_rate", "daps_rate"
    ) if key in row}


def tax_value(value: Any) -> Tuple[Any, Optional[str]]:
    if isinstance(value, dict):
        return first(value, ("raw", "raw_value", "rate", "rate_pct", "value", "amount", "specific_value")), first(value, ("unit", "rate_unit"), None)
    return value, None


def normalize(row: Dict[str, Any]) -> Dict[str, Any]:
    code = clean_code(first(row, ("hs_code", "code", "code_clean", "national_code", "tariff_code", "Code_SH_10_chiffres", "Code_HS10")))
    hs6 = clean_code(first(row, ("hs6", "HS6", "HS6_code"))) or code[:6]
    description = str(first(row, ("description", "description_fr", "Designation_complete", "Designation_Exacte", "designation", "name", "description_en"), "") or "").strip()
    chapter = clean_code(first(row, ("chapter", "Chapitre", "chapter_code")))
    unit = first(row, ("unit", "statistical_unit", "rate_unit", "unite"), None)
    parsed = {}
    for key, value in taxes(row).items():
        raw, rate_unit = tax_value(value)
        parsed[key] = {"tax": key, **parse_rate(raw, rate_unit)}
    return {"national_code": code, "hs6": hs6, "chapter": chapter, "description": description, "taxes": parsed, "raw_row": row}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_artifacts(root: Path, country: str) -> Dict[str, Optional[Path]]:
    base_candidates = [
        root / "backend" / "data" / f"{country}_tariffs.json",
        root / "backend" / "data" / "tariffs" / f"{country}_tariffs.json",
        root / "backend" / "data" / "crawled" / f"{country}_tariffs.json",
        root / "frontend" / "public" / f"{country}_tarif_douanier_echantillon.csv",
    ]
    crawled = root / "backend" / "data" / "crawled" / f"{country}_tariffs.json"
    enriched = root / "backend" / "data" / "crawled" / f"{country}_tariffs_enriched.json"
    primary = next((path for path in base_candidates if path.exists()), None)
    return {
        "primary": primary,
        "effective": crawled if crawled.exists() else primary,
        "detail": crawled if crawled.exists() else None,
        "enriched": enriched if enriched.exists() else None,
    }


SAMPLE_RULES = [
    ("agriculture", {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15"}, r"animal|semence|cereal|agric|viande|poisson|legume|fruit"),
    ("alimentation", {"16", "17", "18", "19", "20", "21", "22", "23", "24"}, r"aliment|sucre|cacao|chocolat|boisson|tabac|preparation"),
    ("médicament", {"30"}, r"medicament|pharm|serum|vaccin|therapeut"),
    ("textile", {"50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"}, r"textile|coton|fibre|fil|tissu|vetement"),
    ("machine", {"84"}, r"machine|moteur|pompe|mecanique|chaudiere"),
    ("électronique", {"85"}, r"electron|electri|circuit|telephone|ordinateur"),
    ("véhicule", {"87"}, r"vehicule|voiture|tracteur|automobile|motocycle"),
    ("produit chimique", {"28", "29", "31", "32", "33", "34", "35", "36", "37", "38"}, r"chim|acide|engrais|peinture|cosmet|savon"),
    ("matière première", {"25", "26", "27", "44", "45", "47"}, r"minerai|petrole|bois|matiere|caoutchouc|pierre"),
    ("produit exonéré ou à taux nul", {"98"}, r"exoner|exempt|gratuit|free|0\s*%"),
]


def samples(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected, used = [], set()
    for category, chapters, pattern in SAMPLE_RULES:
        choice = None
        # Prefer the chapter for the category. Keyword matching is only a
        # fallback because descriptions can mention another use.
        for index, row in enumerate(rows):
            if index not in used and row["chapter"] in chapters:
                choice = (index, row)
                break
        if choice is None:
            for index, row in enumerate(rows):
                if index not in used and re.search(pattern, row["description"], re.I):
                    choice = (index, row)
                    break
        if choice is None:
            choice = next(((index, row) for index, row in enumerate(rows) if index not in used), None)
        if choice is None:
            continue
        index, row = choice
        used.add(index)
        selected.append({
            "category": category,
            "national_code": row["national_code"],
            "hs6": row["hs6"],
            "description": row["description"],
            "taxes": row["taxes"],
            "source_comparison": "NOT_AVAILABLE",
            "comparison_note": "Aucune archive officielle locale retrouvée.",
        })
    return selected



def rate_signature(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not row:
        return {}
    result = {}
    for key, value in row.get("taxes", {}).items():
        result[key] = (
            value.get("normalized_rate_numeric"),
            value.get("rate_type"),
            value.get("rate_unit"),
        )
    return result


def dd_record(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    dd = row.get("taxes", {}).get("DD")
    if not dd:
        return None
    return dd


def dd_is_numeric(row: Optional[Dict[str, Any]]) -> bool:
    dd = dd_record(row)
    return bool(dd and dd.get("rate_parse_status") == "PARSED")


def compact_side(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "national_code": row.get("national_code"),
        "hs6": row.get("hs6"),
        "description": row.get("description", "")[:300],
        "rates": row.get("taxes", {}),
    }


def reconcile_rows(canonical_rows: List[Dict[str, Any]], crawled_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare two flattened datasets without selecting a preferred side."""
    canonical = {row["national_code"]: row for row in canonical_rows if row.get("national_code")}
    crawled = {row["national_code"]: row for row in crawled_rows if row.get("national_code")}
    flags: Dict[str, set] = {}
    pairs: Dict[str, Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]] = {}
    for code in sorted(set(canonical) | set(crawled)):
        c, r = canonical.get(code), crawled.get(code)
        if c is None:
            flags.setdefault(code, set()).add("ONLY_CRAWLED")
            pairs[code] = (None, r)
            continue
        if r is None:
            flags.setdefault(code, set()).add("ONLY_CANONICAL")
            pairs[code] = (c, None)
            continue
        pairs[code] = (c, r)
        if not dd_is_numeric(c):
            flags.setdefault(code, set()).add("MISSING_RATE_CANONICAL")
        if not dd_is_numeric(r):
            flags.setdefault(code, set()).add("MISSING_RATE_CRAWLED")
        if rate_signature(c) != rate_signature(r):
            flags.setdefault(code, set()).add("RATE_DIFFERENCE")
        if re.sub(r"\s+", " ", c.get("description", "").strip().lower()) != re.sub(r"\s+", " ", r.get("description", "").strip().lower()):
            flags.setdefault(code, set()).add("DESCRIPTION_DIFFERENCE")
        if not flags.get(code):
            flags[code] = {"IDENTICAL"}

    # Detect a national-code change where the same HS6 and normalized
    # description occur on opposite sides under different national codes.
    canonical_only = [code for code, values in flags.items() if "ONLY_CANONICAL" in values]
    crawled_only = [code for code, values in flags.items() if "ONLY_CRAWLED" in values]
    used_c, used_r = set(), set()
    for ccode in canonical_only:
        c = canonical[ccode]
        for rcode in crawled_only:
            if rcode in used_r or ccode in used_c:
                continue
            r = crawled[rcode]
            same_desc = re.sub(r"\s+", " ", c.get("description", "").strip().lower()) == re.sub(r"\s+", " ", r.get("description", "").strip().lower())
            if c.get("hs6") and c.get("hs6") == r.get("hs6") and same_desc:
                flags[ccode].discard("ONLY_CANONICAL")
                flags[rcode].discard("ONLY_CRAWLED")
                flags[ccode].add("NATIONAL_CODE_DIFFERENCE")
                flags[rcode].add("NATIONAL_CODE_DIFFERENCE")
                pairs[ccode] = (c, r)
                pairs[rcode] = (c, r)
                used_c.add(ccode)
                used_r.add(rcode)
                break

    categories = [
        "IDENTICAL", "ONLY_CANONICAL", "ONLY_CRAWLED", "RATE_DIFFERENCE",
        "DESCRIPTION_DIFFERENCE", "NATIONAL_CODE_DIFFERENCE",
        "MISSING_RATE_CANONICAL", "MISSING_RATE_CRAWLED",
    ]
    output: Dict[str, Any] = {
        "canonical_line_count": len(canonical_rows),
        "crawled_line_count": len(crawled_rows),
        "canonical_unique_codes": len(canonical),
        "crawled_unique_codes": len(crawled),
        "categories": {},
        "classification_note": "Flags may overlap: one code can have a rate and description difference at the same time. IDENTICAL is emitted only when no flag is present.",
    }
    for category in categories:
        codes: List[str] = []
        examples: List[Dict[str, Any]] = []
        for code, code_flags in sorted(flags.items()):
            if category not in code_flags:
                continue
            c, r = pairs.get(code, (canonical.get(code), crawled.get(code)))
            display_code = code
            if category == "NATIONAL_CODE_DIFFERENCE" and c and r:
                display_code = f"{c.get('national_code')} => {r.get('national_code')}"
            codes.append(display_code)
            if len(examples) < 20:
                examples.append({
                    "code": display_code,
                    "canonical": compact_side(c),
                    "crawled": compact_side(r),
                })
        output["categories"][category] = {"count": len(codes), "codes": codes, "examples": examples}
    return output


def analyze_missing_dd(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    for row in rows:
        if dd_is_numeric(row):
            continue
        raw = row.get("raw_row", {})
        text = json.dumps(raw, ensure_ascii=False).lower()
        nested = raw.get("taxes_detail") or raw.get("taxes_import") or raw.get("sub_positions") or raw.get("dd_rate")
        nested_text = json.dumps(nested, ensure_ascii=False).lower()
        if re.search(r"droit.?de.?douane|customs.?duty|\bdd\b|dddroit", nested_text) and re.search(r"\d", nested_text):
            cause = "RATE_STORED_ELSEWHERE"
        elif re.search(r"\bfree\b|gratuit|zero|صفر|\b0\s*%", text):
            cause = "EXPLICIT_FREE"
        elif re.search(r"exon|exempt", text):
            cause = "EXPLICIT_EXEMPT"
        elif re.search(r"suspend", text):
            cause = "REVIEW_REQUIRED"
        elif not raw.get("taxes") and not raw.get("taxes_detail") and not raw.get("taxes_import"):
            cause = "DESCRIPTIVE_LINE"
        else:
            cause = "TRUE_MISSING"
        records.append({
            "national_code": row.get("national_code"),
            "hs6": row.get("hs6"),
            "description": row.get("description", "")[:300],
            "cause": cause,
            "evidence": {
                "free_or_zero_found": bool(re.search(r"\bfree\b|gratuit|zero|صفر|\b0\s*%", text)),
                "exempt_found": bool(re.search(r"exon|exempt", text)),
                "suspended_found": bool(re.search(r"suspend", text)),
                "other_dd_field_found": bool(re.search(r"droit.?de.?douane|customs.?duty|\bdd\b|dddroit", nested_text)),
            },
        })
    counts = Counter(item["cause"] for item in records)
    return {
        "total_missing_dd": len(records),
        "counts_by_cause": dict(sorted(counts.items())),
        "records": records,
        "examples": {cause: [item for item in records if item["cause"] == cause][:20] for cause in sorted(counts)},
        "note": "Les causes sont documentaires; aucune cause n'est convertie en taux numérique.",
    }


def availability(effective_rows: List[Dict[str, Any]], canonical_rows: List[Dict[str, Any]], reconciliation: Optional[Dict[str, Any]]) -> Dict[str, int]:
    canonical = {row["national_code"]: row for row in canonical_rows if row.get("national_code")}
    effective = [row for row in effective_rows if row.get("national_code")]
    flagged = {}
    if reconciliation:
        for category, content in reconciliation.get("categories", {}).items():
            for code in content.get("codes", []):
                flagged[code] = flagged.get(code, set()) | {category}
    simulatable = unavailable = review = 0
    for row in effective:
        code = row["national_code"]
        canonical_row = canonical.get(code)
        categories = flagged.get(code, set())
        if canonical_row and categories & {"RATE_DIFFERENCE", "DESCRIPTION_DIFFERENCE", "NATIONAL_CODE_DIFFERENCE", "MISSING_RATE_CANONICAL", "MISSING_RATE_CRAWLED"}:
            review += 1
        elif dd_is_numeric(row):
            simulatable += 1
        else:
            unavailable += 1
    return {
        "total_positions": len(effective_rows),
        "positions_simulatable": simulatable,
        "positions_calculation_unavailable": unavailable,
        "positions_review_required": review,
    }

def audit(root: Path, country: str) -> Dict[str, Any]:
    country = country.upper()
    artifacts = resolve_artifacts(root, country)
    effective, primary = artifacts["effective"], artifacts["primary"]
    if effective is None:
        raise FileNotFoundError(f"Aucun fichier tarifaire local trouvé pour {country}")
    effective_meta, raw_rows = load_rows(effective)
    rows = [normalize(row) for row in raw_rows]
    primary_meta, primary_raw_rows = load_rows(primary) if primary and primary != effective else (effective_meta, raw_rows)
    primary_parent_rows = primary_meta.get("tariff_lines", []) if isinstance(primary_meta.get("tariff_lines"), list) else []
    canonical_rows = [normalize(row) for row in primary_raw_rows]
    reconciliation_result = reconcile_rows(canonical_rows, rows) if primary and primary != effective else None
    missing_dd_result = analyze_missing_dd(rows)
    availability_result = availability(rows, canonical_rows, reconciliation_result)

    codes = [row["national_code"] for row in rows]
    counter = Counter(code for code in codes if code)
    lengths = Counter(len(code) for code in codes if code)
    duplicates = sorted(code for code, count in counter.items() if count > 1)
    invalid = [code for code in codes if not re.fullmatch(r"\d{6,12}", code or "")]
    hs6_missing = sum(not re.fullmatch(r"\d{6}", row["hs6"] or "") for row in rows)
    descriptions_missing = sum(not row["description"] for row in rows)
    rates_missing = sum("DD" not in row["taxes"] or row["taxes"]["DD"]["rate_parse_status"] == "MISSING" for row in rows)
    rates_unparsed = sum(any(rate["rate_parse_status"] == "UNPARSED" for rate in row["taxes"].values()) for row in rows)
    chapter_mismatch = [row["national_code"] for row in rows if row["chapter"] and row["hs6"] and row["chapter"].zfill(2) != row["hs6"][:2]]
    tax_types = Counter()
    specific, no_unit = [], []
    for row in rows:
        tax_types.update(row["taxes"].keys())
        for rate in row["taxes"].values():
            if rate["rate_type"] in {"SPECIFIC", "COMPOUND", "MIXED"}:
                specific.append({"code": row["national_code"], "tax": rate["tax"], "rate_type": rate["rate_type"]})
                raw_rate = str(rate.get("normalized_rate_raw") or "").lower()
                has_embedded_unit = bool(re.search(r"/\s*(kg|t|l|unit|piece|\S+)|\b(kg|tonne|dinars?|dzd|zar|usd)\b|\d+u\b", raw_rate))
                if not rate.get("rate_unit") and not has_embedded_unit:
                    no_unit.append({"code": row["national_code"], "tax": rate["tax"]})

    extracted_at = effective_meta.get("extracted_at") or effective_meta.get("generated_at")
    row_sources = Counter(str(row["raw_row"].get("source") or "") for row in rows if row["raw_row"].get("source"))
    row_urls = Counter(str(row["raw_row"].get("source_url") or "") for row in rows if row["raw_row"].get("source_url"))
    source_name = effective_meta.get("source") or primary_meta.get("summary", {}).get("source_name")
    row_source_url = next(iter(row_urls), None)
    source_url = effective_meta.get("source_url") or row_source_url or primary_meta.get("summary", {}).get("source_url")
    archive_candidates = [
        path for base in (root / "data" / "archive", root / "backend" / "data" / "raw")
        if base.exists() for path in base.rglob("*")
        if path.is_file() and country.lower() in path.name.lower() and "official" in path.name.lower()
    ]
    archive_available = any(path.exists() for path in archive_candidates)
    source_status = "DOCUMENTED" if archive_available else "UNVERIFIED"
    temporal_status = "PARTIAL" if extracted_at else "NOT_AVAILABLE"
    classification_status = "DOCUMENTED" if rows and not invalid and not hs6_missing else "PARTIAL"
    taxes_status = "PARTIAL" if tax_types else "NOT_AVAILABLE"
    dimensions = {
        "source": source_status,
        "temporal_validity": temporal_status,
        "classification": classification_status,
        "taxes_and_levies": taxes_status,
        "preference_and_origin": "PARTIAL" if any(row["raw_row"].get("advantages") or row["raw_row"].get("fiscal_advantages") or row["raw_row"].get("preferences") for row in rows) else "NOT_AVAILABLE",
        "formalities": "PARTIAL" if any(row["raw_row"].get("formalities") or row["raw_row"].get("administrative_formalities") or row["raw_row"].get("reglementation_import") for row in rows) else "NOT_AVAILABLE",
    }
    overall = "INFORMATIVE_COMPLETE" if all(value in {"DOCUMENTED", "NOT_APPLICABLE"} for value in dimensions.values()) else "INFORMATIVE_PARTIAL"
    version = next((str(meta[key]) for meta in (effective_meta, primary_meta) for key in ("hs_version", "nomenclature", "hs_level") if meta.get(key)), None)
    rel = lambda path: str(path.relative_to(root)) if path else None
    code_version_declaration = "HS2022" if country == "DZA" else None
    related_candidates = [
        root / "backend" / "data" / f"{country}_tariffs.json",
        root / "backend" / "data" / "tariffs" / f"{country}_tariffs.json",
        root / "backend" / "data" / "crawled" / f"{country}_tariffs_enriched.json",
        root / "data" / "archive" / "csv" / "TARIF-DZA_CRAWLED_VALIDATION  AUTHENTIQUE .csv",
        root / "docs" / "archive" / "attached_assets" / "TARIF-DZA_CRAWLED_VALIDATION_AUTHENTIQUE__1778803280738.csv",
    ]
    related_files = []
    for related in related_candidates:
        if related.exists():
            role = "secondary_local_artifact"
            if related == primary:
                role = "primary_runtime_artifact"
            elif related == effective:
                role = "effective_national_artifact"
            elif related.name.endswith("DZA_tariffs_enriched.json"):
                role = "calculator_fallback_artifact"
            related_files.append({"path": rel(related), "role": role, "sha256": file_hash(related)})
    pipeline_scripts = [
        "backend/scripts/build_dza_tariffs_complete.py",
        "backend/scripts/enrich_dza_fast_json.py",
        "backend/etl/dza_tariff_connector.py",
        "engine/converters/dza_converter.py",
        "engine/adapters/dza_conformepro_adapter.py",
    ] if country == "DZA" else []
    result = {
        "country_iso3": country,
        "country_name": COUNTRY_NAMES.get(country, country),
        "audit_tool": "scripts/audit_tariff_documentation.py",
        "consultation_date": date.today().isoformat(),
        "read_only_audit": True,
        "local_related_files": related_files,
        "runtime_artifacts": {
            "primary_tariff_file": rel(primary),
            "effective_national_file": rel(effective),
            "detail_override_file": rel(artifacts["detail"]),
            "enriched_fallback_file": rel(artifacts["enriched"]),
            "consumers": [
                "backend/services/tariff_provider_service.py::get_tariff_line",
                "backend/services/authentic_tariff_service.py::load_country_tariffs",
                "backend/services/authentic_tariff_service.py::load_crawled_position_index",
                "backend/routes/authentic_tariffs.py::get_tariff_line_endpoint",
                "backend/routes/authentic_tariffs.py::get_sub_positions_endpoint",
                "backend/routes/enhanced_calculator.py::_load_dza_authentic_line",
            ],
            "import_and_normalization_scripts": pipeline_scripts,
        },
        "source": {
            "source_authority": source_name,
            "source_title": "Tarif national intégré — données de crawl conformepro.dz" if country == "DZA" else source_name,
            "source_url": source_url or ("https://conformepro.dz/" if country == "DZA" else None),
            "source_root_url": "https://conformepro.dz/resources/tarif-douanier" if country == "DZA" else None,
            "official_authority_url": "https://www.douane.gov.dz" if country == "DZA" else None,
            "publication_date": None,
            "effective_from": None,
            "effective_to": None,
            "hs_version": version,
            "hs_version_declared_in_code": code_version_declaration,
            "hs_version_status": "UNVERIFIED" if code_version_declaration and not version else ("DOCUMENTED" if version else "NOT_AVAILABLE"),
            "date_consulted": date.today().isoformat(),
            "extracted_at": extracted_at,
            "source_hash_sha256": file_hash(effective),
            "archive_official_available": archive_available,
            "official_archive_candidates": [rel(path) for path in archive_candidates],
            "status": source_status,
            "status_basis": "Les champs data_status/reliability/source_quality du fichier ne sont pas utilisés.",
        },
        "position_availability": availability_result,
        "missing_dd_analysis": missing_dd_result,
        "reconciliation_summary": ({"category_counts": {key: value["count"] for key, value in reconciliation_result["categories"].items()}, "runtime_preference_confirmed": True} if reconciliation_result else None),
        "declared_metadata_not_used_for_status": {
            "effective_source_quality_present": bool(effective_meta.get("source_quality")),
            "primary_data_status_present": bool(primary_meta.get("summary", {}).get("data_status")),
            "primary_reliability_present": bool(primary_meta.get("summary", {}).get("reliability")),
            "ignored_for_quality_status": True,
        },
        "coverage": {
            "effective_lines": len(rows),
            "unique_national_codes": len({code for code in codes if code}),
            "unique_hs6": len({row["hs6"] for row in rows if row["hs6"]}),
            "parent_lines_in_primary_file": len(primary_parent_rows) or len(primary_raw_rows),
            "national_sub_positions_in_primary_file": sum(len(raw.get("sub_positions", [])) for raw in primary_parent_rows if isinstance(raw, dict)),
            "chapters_present": len({row["chapter"] for row in rows if row["chapter"]}),
            "code_lengths": {str(length): count for length, count in sorted(lengths.items())},
        },
        "controls": {
            "total_rows_audited": len(rows),
            "duplicate_codes": duplicates,
            "duplicate_code_count": len(duplicates),
            "invalid_codes": invalid[:100],
            "invalid_code_count": len(invalid),
            "hs6_missing_count": hs6_missing,
            "missing_descriptions": descriptions_missing,
            "missing_rates": rates_missing,
            "unparseable_rates": rates_unparsed,
            "specific_or_composite_rights_count": len(specific),
            "specific_or_composite_examples": specific[:20],
            "taxes_without_unit_count": len(no_unit),
            "taxes_without_unit_examples": no_unit[:20],
            "chapter_hs6_inconsistency_count": len(chapter_mismatch),
            "chapter_hs6_inconsistency_examples": chapter_mismatch[:20],
            "dates_missing": len(rows) if not any(row["raw_row"].get(key) for row in rows for key in ("effective_from", "effective_to", "publication_date", "date")) else None,
            "tax_types": dict(sorted(tax_types.items())),
            "row_sources": dict(row_sources.most_common(10)),
            "row_source_urls_count": len(row_urls),
        },
        "sample_rows": samples(rows),
        "source_comparison": {"status": "NOT_AVAILABLE", "official_lines_compared": 0, "note": "Aucune copie officielle tarifaire archivée dans le dépôt; les dix lignes restent non comparées."},
        "quality_dimensions": dimensions,
        "overall_informative_status": overall,
        "known_data_gaps": [
            "Archive officielle tarifaire non retrouvée localement.",
            "Date de publication et date d'effet documentées absentes.",
            "Version SH explicite absente des métadonnées JSON consommées." if not version else "Date d'effet juridiquement documentée absente.",
        ] + (["Écart entre les lignes canoniques et crawled; les divergences restent en revue."] if reconciliation_result else []),
        "actions_required": [
            "Archiver le document tarifaire de l'autorité déclarée sans remplacer le fichier actuel.",
            "Comparer un échantillon de lignes et conserver les empreintes des documents.",
            "Documenter la version SH et les dates de publication/effet.",
            "Résoudre les divergences entre artefacts avant une utilisation documentaire plus forte.",
        ],
    }
    return result


def report(result: Dict[str, Any]) -> str:
    source, coverage, controls = result["source"], result["coverage"], result["controls"]
    runtime = result["runtime_artifacts"]
    lines = [
        f"# Documentation tarifaire {result['country_iso3']} — {result['consultation_date']}",
        "",
        "> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.",
        "",
        "## Résultat informatif",
        "",
        f"- Statut global : **{result['overall_informative_status']}**",
        *[f"- {key} : **{value}**" for key, value in result["quality_dimensions"].items()],
        "",
        "## Inventaire et consommation",
        "",
        f"- Fichier canonique parent : {runtime['primary_tariff_file']} ({coverage['parent_lines_in_primary_file']} lignes SH6).",
        f"- Fichier national effectif : {runtime['effective_national_file']} ({coverage['effective_lines']} lignes, {coverage['unique_national_codes']} codes nationaux, {coverage['unique_hs6']} SH6).",
        f"- Fichier enrichi de repli : {runtime['enriched_fallback_file'] or 'absent'}.",
        f"- Artefacts locaux apparentés hachés : {len(result['local_related_files'])} (les CSV de validation restent secondaires).",
        "- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.",
        f"- Import/normalisation : {', '.join(runtime['import_and_normalization_scripts']) or 'non identifié'}.",
        "",
        "## Provenance locale",
        "",
        f"- Autorité déclarée : {source['source_authority'] or 'non indiquée'}.",
        f"- Titre : {source['source_title']}.",
        f"- URL de ligne : {source['source_url'] or 'non indiquée'}; URL d'acquisition déclarée : {source['source_root_url'] or 'non indiquée'}; autorité douanière : {source['official_authority_url'] or 'non indiquée'}.",
        f"- Archive officielle locale : **{'disponible' if source['archive_official_available'] else 'non retrouvée'}**.",
        f"- SHA-256 du fichier effectif : {source['source_hash_sha256']}.",
        f"- Extraction : {source['extracted_at'] or 'non indiquée'} (ce n'est pas une date d'effet).",
        f"- Publication/effet : {source['publication_date'] or 'non documentée'} / {source['effective_from'] or 'non documentée'}.",
        f"- Version SH dans les métadonnées : {source['hs_version'] or 'non déclarée'}; déclaration trouvée dans l'adaptateur : {source['hs_version_declared_in_code'] or 'aucune'} (statut : {source['hs_version_status']}).",
        "",
        "Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.",
        "",
        "## Contrôles automatiques",
        "",
        f"- Lignes aplaties : **{controls['total_rows_audited']}**; codes uniques : **{coverage['unique_national_codes']}**.",
        f"- Doublons : **{controls['duplicate_code_count']}**; codes invalides : **{controls['invalid_code_count']}**.",
        f"- SH6 manquants : **{controls['hs6_missing_count']}**; descriptions manquantes : **{controls['missing_descriptions']}**.",
        f"- Taux DD manquants : **{controls['missing_rates']}**; taux non analysables : **{controls['unparseable_rates']}**.",
        f"- Droits spécifiques/composites : **{controls['specific_or_composite_rights_count']}**; taxes sans unité : **{controls['taxes_without_unit_count']}**.",
        f"- Incohérences chapitre/SH6 : **{controls['chapter_hs6_inconsistency_count']}**; dates manquantes : **{controls['dates_missing']}**.",
        f"- Taxes : {', '.join(f'{key} ({value})' for key, value in controls['tax_types'].items())}.",
        "",
        "## Échantillon rapide (10 lignes)",
        "",
        "| Catégorie | Code national | SH6 | Description | Comparaison |",
        "|---|---:|---:|---|---|",
    ]
    for item in result["sample_rows"]:
        lines.append(f"| {item['category']} | {item['national_code']} | {item['hs6']} | {item['description'].replace('|', '/')} | {item['source_comparison']} |")
    lines += [
        "",
        "Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.",
        "",
        "## Disponibilité par position",
        "",
        f"- Total positions : **{result['position_availability']['total_positions']}**.",
        f"- Simulables : **{result['position_availability']['positions_simulatable']}**.",
        f"- Calcul indisponible : **{result['position_availability']['positions_calculation_unavailable']}**.",
        f"- Revue requise : **{result['position_availability']['positions_review_required']}**.",
        "",
        "## Analyse des DD manquants",
        "",
        f"- Lignes DD absentes/non analysables : **{result['missing_dd_analysis']['total_missing_dd']}**.",
        f"- Causes : {', '.join(f'{key} ({value})' for key, value in result['missing_dd_analysis']['counts_by_cause'].items()) or 'aucune'}.",
        "Aucune cause n'est transformée en taux numérique.",
        "",
        "## Lacunes et actions",
        "",
        *[f"- {item}" for item in result["known_data_gaps"]],
        *[f"- Action : {item}" for item in result["actions_required"]],
        "",
        "Le même contrôle peut être relancé pour les autres pays en paramètre; aucun script séparé n'est créé.",
        "",
    ]
    return "\n".join(lines)



def write_reconciliation(root: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    artifacts = resolve_artifacts(root, "DZA")
    if not artifacts["primary"] or not artifacts["effective"]:
        raise FileNotFoundError("Fichiers DZA canonique/crawled introuvables")
    _, canonical_raw = load_rows(artifacts["primary"])
    _, crawled_raw = load_rows(artifacts["effective"])
    result = reconcile_rows([normalize(row) for row in canonical_raw], [normalize(row) for row in crawled_raw])
    result.update({
        "country_iso3": "DZA",
        "canonical_file": str(artifacts["primary"].relative_to(root)),
        "crawled_file": str(artifacts["effective"].relative_to(root)),
        "canonical_sha256": file_hash(artifacts["primary"]),
        "crawled_sha256": file_hash(artifacts["effective"]),
        "runtime_prefers_crawled": True,
        "runtime_evidence": [
            "backend/services/authentic_tariff_service.py::load_crawled_position_index",
            "backend/services/authentic_tariff_service.py::calculate_import_taxes",
            "backend/services/tariff_provider_service.py::get_tariff_line",
        ],
        "consultation_date": date.today().isoformat(),
    })
    output = output_path or root / "data" / "coverage" / "DZA_tariff_reconciliation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def write_wave_a(root: Path) -> Dict[str, Any]:
    countries = ["DZA", "MAR", "TUN", "EGY", "ZAF", "KEN"]
    rows = []
    for country in countries:
        result = audit(root, country)
        output = root / "data" / "coverage" / f"{country}_documentation_status.json"
        report_path = root / "reports" / f"{country}_TARIFF_DOCUMENTATION.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(report(result), encoding="utf-8")
        rows.append({
            "country_iso3": country,
            "file_used": result["runtime_artifacts"]["effective_national_file"],
            "total_lines": result["position_availability"]["total_positions"],
            "hs6_covered": result["coverage"]["unique_hs6"],
            "rates_present": result["controls"]["total_rows_audited"] - result["controls"]["missing_rates"],
            "rates_missing": result["controls"]["missing_rates"],
            "hs_version": result["source"]["hs_version"] or result["source"]["hs_version_declared_in_code"],
            "effective_date": result["source"]["effective_from"],
            "official_archive_available": result["source"]["archive_official_available"],
            "declared_source": result["source"]["source_authority"],
            "informative_status": result["overall_informative_status"],
            "positions_simulatable": result["position_availability"]["positions_simulatable"],
            "positions_calculation_unavailable": result["position_availability"]["positions_calculation_unavailable"],
            "positions_review_required": result["position_availability"]["positions_review_required"],
            "conflicts": result["position_availability"]["positions_review_required"],
        })
    reconciliation = write_reconciliation(root)
    summary = {
        "wave": "A",
        "countries": rows,
        "consultation_date": date.today().isoformat(),
        "no_network_access": True,
        "no_rate_modification": True,
        "dza_reconciliation_categories": {key: value["count"] for key, value in reconciliation["categories"].items()},
    }
    out = root / "data" / "coverage" / "WAVE_A_documentation_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_lines = [
        f"# Documentation tarifaire — Vague A ({summary['consultation_date']})", "",
        "> Synthèse locale en lecture seule. Aucune nouvelle source ni aucun taux n'a été collecté ou modifié.", "",
        "| Pays | Fichier utilisé | Lignes | SH6 | Taux renseignés | Taux manquants | Version SH | Date effet | Archive officielle | Source | Statut | Simulables | Indisponibles | Conflits |",
        "|---|---|---:|---:|---:|---:|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append("| {country_iso3} | {file_used} | {total_lines} | {hs6_covered} | {rates_present} | {rates_missing} | {hs_version} | {effective_date} | {official_archive_available} | {declared_source} | {informative_status} | {positions_simulatable} | {positions_calculation_unavailable} | {conflicts} |".format(**row))
    report_lines += ["", "## DZA — réconciliation", "", "Les catégories peuvent se chevaucher; le runtime privilégie crawled pour les positions nationales, sans arbitrer les divergences.", ""]
    report_lines += [f"- {key} : **{value['count']}**" for key, value in reconciliation["categories"].items()]
    report_lines += ["", "## Règles", "", "Une position sans DD analysable est CALCULATION_UNAVAILABLE. Une divergence entre fichiers est REVIEW_REQUIRED. Aucune cause de DD manquant n'est convertie en taux.", ""]
    (root / "reports" / "WAVE_A_TARIFF_DOCUMENTATION.md").write_text("\n".join(report_lines), encoding="utf-8")
    return summary

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit documentaire tarifaire local, sans modification des sources")
    parser.add_argument("country", nargs="?", help="Code ISO3, par exemple DZA")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--reconcile-dza", action="store_true", help="Produire la réconciliation DZA canonique/crawled")
    parser.add_argument("--batch-wave-a", action="store_true", help="Auditer DZA, MAR, TUN, EGY, ZAF et KEN")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.batch_wave_a:
        summary = write_wave_a(root)
        print(json.dumps({"wave": "A", "countries": len(summary["countries"]), "summary": str(root / "data/coverage/WAVE_A_documentation_summary.json")}, ensure_ascii=False))
        return 0
    if args.reconcile_dza:
        result = write_reconciliation(root, args.output)
        print(json.dumps({"country": "DZA", "output": str(args.output or root / "data/coverage/DZA_tariff_reconciliation.json"), "categories": {key: value["count"] for key, value in result["categories"].items()}}, ensure_ascii=False))
        return 0
    if not args.country:
        parser.error("country, --reconcile-dza ou --batch-wave-a requis")
    country = args.country.upper()
    result = audit(root, country)
    output = args.output or root / "data" / "coverage" / f"{country}_documentation_status.json"
    report_path = args.report or root / "reports" / f"{country}_TARIFF_DOCUMENTATION.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"country": country, "output": str(output), "report": str(report_path), "status": result["overall_informative_status"], "rows": result["controls"]["total_rows_audited"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
