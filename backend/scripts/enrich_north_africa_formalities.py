#!/usr/bin/env python3
"""
Enrich MAR and TUN enhanced_v2 tariff data with proper administrative formalities.

Reads:  data/MAR_tariffs.json, data/TUN_tariffs.json
Writes: data/MAR_tariffs.json, data/TUN_tariffs.json (in-place update)
        data/crawled/MAR_tariffs.json, data/crawled/TUN_tariffs.json

Each tariff_line receives a country-specific set of required administrative
documents drawn from the ETL modules:
  - etl/country_taxes_morocco.py  → get_mar_formalities_for_line()
  - etl/country_taxes_tunisia.py  → get_tun_formalities_for_line()

No data is fabricated; every document code is sourced from the official
customs authority portals referenced in the ETL module docstrings.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

# Allow direct script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.country_taxes_morocco import get_mar_formalities_for_line
from etl.country_taxes_tunisia import get_tun_formalities_for_line

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")


def _enrich_country(
    src_path: str,
    get_formalities_fn,
    country_code: str,
) -> dict:
    """
    Load a country's tariff JSON, apply formalities to every tariff_line,
    and return the updated data dict.

    Args:
        src_path: Path to the source *_tariffs.json file
        get_formalities_fn: Callable(category, chapter) → list[dict]
        country_code: ISO3 code for logging

    Returns:
        Updated data dictionary ready to be serialised
    """
    print(f"\n[{country_code}] Loading {src_path} ...")
    with open(src_path, encoding="utf-8") as f:
        data = json.load(f)

    tariff_lines = data.get("tariff_lines", [])
    total = len(tariff_lines)
    bucket_counts: Counter = Counter()

    for line in tariff_lines:
        category = line.get("category", "general")
        chapter = str(line.get("chapter", "")).zfill(2)
        formalities = get_formalities_fn(category, chapter)
        line["administrative_formalities"] = formalities
        # Count for reporting
        bucket_counts[len(formalities)] += 1

    # Refresh summary metadata
    distinct_docs: set = set()
    for line in tariff_lines:
        for f in line.get("administrative_formalities", []):
            distinct_docs.add(f["code"])

    data["summary"]["has_detailed_taxes"] = True
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    print(
        f"[{country_code}] Enriched {total:,} tariff lines. "
        f"Document codes used: {sorted(distinct_docs)}. "
        f"Docs-per-line distribution: {dict(sorted(bucket_counts.items()))}"
    )
    return data


def _write(data: dict, path: str, country_code: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(path) / 1024
    print(f"[{country_code}] Written → {path} ({size_kb:,.0f} KB)")


def main() -> None:
    configs = [
        {
            "country": "MAR",
            "src": os.path.join(DATA_DIR, "MAR_tariffs.json"),
            "fn": get_mar_formalities_for_line,
        },
        {
            "country": "TUN",
            "src": os.path.join(DATA_DIR, "TUN_tariffs.json"),
            "fn": get_tun_formalities_for_line,
        },
    ]

    for cfg in configs:
        cc = cfg["country"]
        src = cfg["src"]

        if not os.path.exists(src):
            print(f"[{cc}] ERROR: source file not found: {src}")
            sys.exit(1)

        enriched = _enrich_country(src, cfg["fn"], cc)

        # Overwrite data/ source
        _write(enriched, src, cc)

        # Publish to data/crawled/
        crawled_dst = os.path.join(CRAWLED_DIR, f"{cc}_tariffs.json")
        _write(enriched, crawled_dst, cc)

    print("\nDone. MAR and TUN formalities enrichment complete.")


if __name__ == "__main__":
    main()
