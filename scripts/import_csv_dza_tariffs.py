#!/usr/bin/env python3
"""
Import TARIF-DZA_CRAWLED_VALIDATION_AUTHENTIQUE CSV into backend/data/crawled/DZA_tariffs.json
Preserves the existing JSON structure (sub_positions list) and enriches with CSV data.
"""

import csv
import json
import os
import sys
from datetime import datetime

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "attached_assets",
    "TARIF-DZA_CRAWLED_VALIDATION_AUTHENTIQUE__1778803280738.csv",
)
OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "backend", "data", "crawled", "DZA_tariffs.json"
)

AVANTAGE_COLS = [
    "Avantage_ZLECAf",
    "Avantage_GZALE_GAFTA",
    "Avantage_UE_Association",
    "Avantage_Conv_Algerie_Tunisie",
    "Avantage_Conv_Algerie_Jordanie",
    "Avantage_Hydrocarbures",
    "Avantage_Sonatrach",
    "Avantage_Ministere_Sante",
    "Avantage_Medicament_Veterinaire",
    "Avantage_Emploi",
    "Avantage_Admin_Penitentiaire",
    "Avantage_COVID19",
    "Avantage_Loi_Miniere",
    "Avantage_Transport_Aerien",
]


def parse_rate(val: str) -> float | None:
    v = val.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def make_raw_code(hs10: str) -> str:
    """Convert 10-digit hs_code to dotted format: 0101211100 → 01.01.211100"""
    if len(hs10) < 6:
        return hs10
    return f"{hs10[:2]}.{hs10[2:4]}.{hs10[4:]}"


def build_sub_position(row: dict) -> dict | None:
    raw_hs = row.get("Code_HS10", "").strip()
    if not raw_hs:
        return None

    hs10 = raw_hs.zfill(10)
    chapter_raw = row.get("Chapitre", "").strip()
    section_raw = row.get("Section", "").strip()
    hs4_raw = row.get("HS4", "").strip()

    chapter = chapter_raw.zfill(2)
    section = section_raw.zfill(2)
    heading = f"{hs10[:2]}.{hs10[2:4]}"

    designation_exacte = row.get("Designation_Exacte_PT", "").strip()
    designation_hier = row.get("Designation_Hierarchique_Complete", "").strip()

    # Tax rates — prefer CORRIGE columns when available
    dd_corr = parse_rate(row.get("DD_CORRIGE", ""))
    dd_base = parse_rate(row.get("DD_pct", ""))
    dd_rate = dd_corr if dd_corr is not None else (dd_base if dd_base is not None else 0.0)

    daps_corr = parse_rate(row.get("DAPS_CORRIGE", ""))
    daps_base = parse_rate(row.get("DAPS_pct", ""))
    daps_rate = (
        daps_corr if daps_corr is not None else (daps_base if daps_base is not None else 0.0)
    )

    tva_corr = parse_rate(row.get("TVA_CORRIGE", ""))
    tva_base = parse_rate(row.get("TVA_pct", ""))
    tva_rate = tva_corr if tva_corr is not None else (tva_base if tva_base is not None else 0.0)

    prct_rate = parse_rate(row.get("PRCT_pct", "")) or 0.0
    tcs_rate = parse_rate(row.get("TCS_pct", "")) or 0.0

    # Was any rate corrected?
    corrected = bool(dd_corr is not None or daps_corr is not None or tva_corr is not None)
    src_quality = "crawled_authentic"

    # Build taxes dict (omit zero-rate DAPS unless explicitly set)
    taxes = {
        "DD": {
            "name": "Droit de douane",
            "rate": dd_rate,
            "raw": f"{int(dd_rate) if dd_rate == int(dd_rate) else dd_rate}%",
            "source": "douane.gov.dz/conformepro.dz",
            "corrected": corrected,
        },
        "TVA": {
            "name": "TVA",
            "rate": tva_rate,
            "raw": f"{int(tva_rate) if tva_rate == int(tva_rate) else tva_rate}%",
            "source": "douane.gov.dz/conformepro.dz",
        },
    }
    if tcs_rate > 0:
        taxes["TCS"] = {
            "name": "TCS",
            "rate": tcs_rate,
            "raw": f"{int(tcs_rate)}%",
            "source": "douane.gov.dz/conformepro.dz",
        }
    if prct_rate > 0:
        taxes["PRCT"] = {
            "name": "PRCT",
            "rate": prct_rate,
            "raw": f"{int(prct_rate)}%",
            "source": "douane.gov.dz/conformepro.dz",
        }
    if daps_rate > 0:
        taxes["DAPS"] = {
            "name": "DAPS",
            "rate": daps_rate,
            "raw": f"{int(daps_rate) if daps_rate == int(daps_rate) else daps_rate}%",
            "source": "douane.gov.dz/conformepro.dz",
            "corrected": corrected,
        }

    # Fiscal advantages — collect non-empty columns
    advantages = [row[col].strip() for col in AVANTAGE_COLS if row.get(col, "").strip()]

    # Administrative formalities
    formalities_raw = row.get("Formalites_Administratives", "").strip()
    formalities = (
        [f.strip() for f in formalities_raw.split("|") if f.strip()] if formalities_raw else []
    )

    # Extra metadata
    groupe = row.get("Groupe_Utilisation", "").strip()
    validation_ok = row.get("VALIDATION_OK", "").strip()
    commentaire = row.get("COMMENTAIRE", "").strip()

    entry = {
        "raw_code": make_raw_code(hs10),
        "hs_code": hs10,
        "heading": heading,
        "chapter": chapter,
        "section": section,
        "name": designation_exacte,
        "description": designation_exacte,
        "designation": designation_hier or designation_exacte,
        "groupe_utilisation": groupe,
        "taxes": taxes,
        "advantages": advantages,
        "formalities": formalities,
        "source": "douane.gov.dz / conformepro.dz",
        "source_quality": src_quality,
        "validated": validation_ok == "1" or validation_ok.lower() == "true",
        "commentaire": commentaire,
    }
    return entry


def main():
    print(f"Reading CSV: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    sub_positions = []
    errors = 0
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader, 1):
            try:
                entry = build_sub_position(row)
                if entry:
                    sub_positions.append(entry)
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  Row {i} error: {e}")

    print(f"Parsed {len(sub_positions)} sub-positions ({errors} errors)")

    # Compute stats
    dd_rates = set(e["taxes"]["DD"]["rate"] for e in sub_positions)
    validated_count = sum(1 for e in sub_positions if e.get("validated"))
    has_daps = sum(1 for e in sub_positions if "DAPS" in e["taxes"])
    has_advantages = sum(1 for e in sub_positions if e["advantages"])

    output = {
        "country": "DZA",
        "country_name": "Algérie",
        "source": "douane.gov.dz / conformepro.dz — Validation CSV authentique",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "csv_source": "TARIF-DZA_CRAWLED_VALIDATION_AUTHENTIQUE",
        "stats": {
            "total_positions": len(sub_positions),
            "validated_positions": validated_count,
            "positions_with_daps": has_daps,
            "positions_with_advantages": has_advantages,
            "distinct_dd_rates": sorted(dd_rates),
        },
        "sub_positions": sub_positions,
    }

    print(f"Writing JSON to: {OUT_PATH}")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(OUT_PATH) / 1024 / 1024
    print(f"Done — {len(sub_positions):,} positions written ({size_mb:.1f} MB)")
    print(f"Distinct DD rates: {sorted(dd_rates)}")
    print(
        f"Validated: {validated_count} | With DAPS: {has_daps} | With advantages: {has_advantages}"
    )


if __name__ == "__main__":
    main()
