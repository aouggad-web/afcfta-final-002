#!/usr/bin/env python3
"""
Enrich ALL 54 African country tariff files with administrative formalities.

Reads:  data/<CC>_tariffs.json  (source of truth)
Writes: data/<CC>_tariffs.json  (in-place update)
        data/crawled/<CC>_tariffs.json  (published)

For DZA, MAR, and TUN, the richer country-specific ETL modules are used:
  - etl/country_taxes_algeria.py  (DZA — DGD codes 910, 210, 215 …)
  - etl/country_taxes_morocco.py  (MAR — ADII codes 910, C01–C11)
  - etl/country_taxes_tunisia.py  (TUN — GUCE codes 910, 101–109)

For all other 51 countries, etl/africa_formalities.py is used, which
contains real regulatory authority data sourced from each country's
official customs authority, standards body, health ministry, and
environmental agency.

No data is fabricated; every entry is traceable to the official sources
documented in the two ETL module docstrings.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

# Allow direct script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.africa_formalities import get_formalities_for_line
from etl.country_taxes_morocco import get_mar_formalities_for_line
from etl.country_taxes_tunisia import get_tun_formalities_for_line
from etl.country_taxes_algeria import get_dza_taxes_for_hs6  # DZA stays as-is

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")

# Countries with their own richer ETL modules — DO NOT re-enrich with generic module
SKIP_GENERIC = {"DZA", "MAR", "TUN"}


def _enrich_country(
    country_code: str,
    src_path: str,
) -> dict:
    """
    Load a country tariff JSON and apply formalities to every tariff_line.

    For MAR and TUN, uses the dedicated ETL module (preserves ADII/GUCE codes).
    For all others, uses the universal africa_formalities module.

    Args:
        country_code: ISO3 code
        src_path:     Full path to source *_tariffs.json

    Returns:
        Updated data dict ready to be serialised
    """
    print(f"[{country_code}] Loading {os.path.basename(src_path)} …", flush=True)
    with open(src_path, encoding="utf-8") as f:
        data = json.load(f)

    tariff_lines = data.get("tariff_lines", [])
    if not tariff_lines:
        print(f"[{country_code}] WARNING: no tariff_lines — skipping")
        return data

    bucket_counts: Counter = Counter()

    if country_code == "MAR":
        for line in tariff_lines:
            forms = get_mar_formalities_for_line(
                line.get("category", "general"),
                str(line.get("chapter", "")).zfill(2),
            )
            line["administrative_formalities"] = forms
            bucket_counts[len(forms)] += 1
    elif country_code == "TUN":
        for line in tariff_lines:
            forms = get_tun_formalities_for_line(
                line.get("category", "general"),
                str(line.get("chapter", "")).zfill(2),
            )
            line["administrative_formalities"] = forms
            bucket_counts[len(forms)] += 1
    elif country_code == "DZA":
        # DZA already has correct formalities from country_taxes_algeria ETL;
        # verify presence and skip re-enrichment.
        have = sum(
            1 for l in tariff_lines if l.get("administrative_formalities")
        )
        print(f"[DZA] Already enriched — {have}/{len(tariff_lines)} lines have formalities.")
        return data
    else:
        for line in tariff_lines:
            forms = get_formalities_for_line(
                country_code,
                line.get("category", "general"),
                str(line.get("chapter", "")).zfill(2),
            )
            line["administrative_formalities"] = forms
            bucket_counts[len(forms)] += 1

    # Collect distinct codes for reporting
    distinct: set = set()
    for line in tariff_lines:
        for f in line.get("administrative_formalities", []):
            distinct.add(f["code"])

    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    total = len(tariff_lines)
    print(
        f"[{country_code}] Enriched {total:,} lines. "
        f"Distinct doc codes: {sorted(distinct)}. "
        f"Docs-per-line: {dict(sorted(bucket_counts.items()))}",
        flush=True,
    )
    return data


def _write(data: dict, path: str, country_code: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(path) / 1024
    print(f"[{country_code}] Written → {os.path.relpath(path, BACKEND_DIR)} ({size_kb:,.0f} KB)", flush=True)


def main() -> None:
    # Collect all country codes from data/*.json
    json_files = sorted(
        fn for fn in os.listdir(DATA_DIR)
        if fn.endswith("_tariffs.json") and os.path.isfile(os.path.join(DATA_DIR, fn))
    )

    if not json_files:
        print("ERROR: No *_tariffs.json files found in data/")
        sys.exit(1)

    print(f"Processing {len(json_files)} country tariff files …\n")
    success = 0
    errors = []

    for fn in json_files:
        cc = fn.replace("_tariffs.json", "")
        src = os.path.join(DATA_DIR, fn)
        try:
            enriched = _enrich_country(cc, src)
            # Write back to data/
            _write(enriched, src, cc)
            # Publish to data/crawled/
            _write(enriched, os.path.join(CRAWLED_DIR, fn), cc)
            success += 1
        except Exception as exc:
            print(f"[{cc}] ERROR: {exc}", flush=True)
            errors.append((cc, str(exc)))

    print(f"\n{'='*60}")
    print(f"Done. {success}/{len(json_files)} countries enriched successfully.")
    if errors:
        print("Errors:")
        for cc, msg in errors:
            print(f"  {cc}: {msg}")


if __name__ == "__main__":
    main()
