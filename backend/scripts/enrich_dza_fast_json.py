#!/usr/bin/env python3
"""Enrich DZA fast crawl data with ETL-derived duties, taxes, and formalities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from etl.country_taxes_algeria import get_dza_taxes_for_hs6

INPUT_PATH = BACKEND_DIR / "data" / "crawled" / "DZA_tariffs_fast.json"
OUTPUT_PATH = BACKEND_DIR / "data" / "crawled" / "DZA_tariffs_enriched.json"

def enrich_sub_position(sub_position: dict) -> dict:
    hs_code = str(sub_position.get("hs_code", "")).replace(".", "").replace(" ", "")
    hs6_code = hs_code[:6]
    if len(hs6_code) != 6 or not hs6_code.isdigit():
        return sub_position

    etl_data = get_dza_taxes_for_hs6(hs6_code)
    enriched = dict(sub_position)
    enriched.update({
        "dd_rate": etl_data.get("dd_rate", 0.0),
        "daps_rate": etl_data.get("daps_rate", 0.0),
        "prct_rate": etl_data.get("prct_rate", 0.0),
        "tcs_rate": etl_data.get("tcs_rate", 0.0),
        "tva_rate": etl_data.get("tva_rate", 0.0),
        "taxes_detail": etl_data.get("taxes_detail", []),
        "total_taxes_pct": etl_data.get("total_taxes_pct", 0.0),
        "fiscal_advantages": etl_data.get("fiscal_advantages", []),
        "administrative_formalities": etl_data.get("administrative_formalities", []),
    })
    return enriched

def main() -> int:
    if not INPUT_PATH.exists():
        print(f"ERROR: input file not found: {INPUT_PATH}", file=sys.stderr)
        return 1

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    sub_positions = data.get("sub_positions", [])
    enriched_sub_positions = [enrich_sub_position(sp) for sp in sub_positions]

    enriched_data = dict(data)
    enriched_data["data_format"] = "dza_fast_enriched"
    enriched_data["sub_positions"] = enriched_sub_positions
    enriched_data["enriched_from"] = str(INPUT_PATH.relative_to(BACKEND_DIR))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(
        f"Enriched {len(enriched_sub_positions)} sub-positions "
        f"from {INPUT_PATH.relative_to(BACKEND_DIR)} -> {OUTPUT_PATH.relative_to(BACKEND_DIR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())