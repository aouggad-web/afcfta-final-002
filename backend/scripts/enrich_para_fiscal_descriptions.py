#!/usr/bin/env python3
"""
Enrich para-fiscal tax descriptions across all 54 African country tariff files.

Reads:  data/crawled/<CC>_tariffs.json
Writes: data/crawled/<CC>_tariffs.json (in-place)
        data/<CC>_tariffs.json          (in-place)

For each tariff line:
1. Fills empty `observation` fields in `taxes_detail` using the
   LEVY_DESCRIPTIONS registry in etl/para_fiscal_levies.py.
2. Recomputes `other_taxes_rate` as the sum of all taxes that are NOT
   D.D / T.V.A / IMPDEC — i.e. the non-customs, non-VAT para-fiscal
   burden as a percentage of CIF value.

This is a non-destructive enrichment: existing non-empty observations are
kept unchanged, and `dd_rate` / `vat_rate` / `total_taxes_pct` are not
touched.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.para_fiscal_levies import LEVY_DESCRIPTIONS, enrich_observation

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")

# Tax codes that are NOT para-fiscal levies (skip for other_taxes_rate computation)
_SKIP_CODES = {
    "D.D", "DD",           # customs duty
    "T.V.A", "TVA",        # VAT
}

# Display names that map to DD or VAT (some files use "Droit de Douane" as code)
_DUTY_OBS_KEYWORDS = {"droit de douane", "taxe sur la valeur ajoutée", "vat", "customs duty"}


def _is_duty_or_vat(tax_code: str, observation: str) -> bool:
    """Return True if this tax entry is customs duty or VAT."""
    c = tax_code.upper().strip()
    if c in {"D.D", "DD", "T.V.A", "TVA", "VAT"}:
        return True
    obs_lower = observation.lower()
    return any(k in obs_lower for k in _DUTY_OBS_KEYWORDS)


def _enrich_line(line: dict) -> bool:
    """
    Enrich a single tariff line in-place.

    Returns True if any change was made.
    """
    changed = False
    taxes = line.get("taxes_detail", [])
    para_fiscal_sum = 0.0

    for tx in taxes:
        code = tx.get("tax", "")
        obs = tx.get("observation", "")
        rate = float(tx.get("rate", 0.0))

        # Fill empty observations
        if not obs or obs == code:
            new_obs = enrich_observation(code)
            if new_obs and new_obs != code:
                tx["observation"] = new_obs
                changed = True

        # Accumulate para-fiscal rates (anything that is NOT DD / VAT)
        if not _is_duty_or_vat(code, tx.get("observation", "")):
            para_fiscal_sum += rate

    # Update other_taxes_rate if it was 0 and we found real para-fiscal taxes
    current_other = float(line.get("other_taxes_rate", 0.0))
    if abs(para_fiscal_sum - current_other) > 0.001:
        line["other_taxes_rate"] = round(para_fiscal_sum, 4)
        changed = True

    return changed


def _enrich_country(country_code: str, src_path: str) -> dict:
    print(f"[{country_code}] Loading {os.path.basename(src_path)} …", flush=True)
    with open(src_path, encoding="utf-8") as f:
        data = json.load(f)

    tariff_lines = data.get("tariff_lines", [])
    if not tariff_lines:
        print(f"[{country_code}] WARNING: no tariff_lines — skipping")
        return data

    changed_count = 0
    obs_filled: Counter = Counter()

    for line in tariff_lines:
        if _enrich_line(line):
            changed_count += 1
            for tx in line.get("taxes_detail", []):
                if tx.get("observation") and tx.get("observation") != tx.get("tax"):
                    obs_filled[tx["tax"]] += 1

    # Update metadata timestamp
    if "metadata" in data:
        data["metadata"]["last_enriched"] = datetime.now(timezone.utc).isoformat()

    print(
        f"[{country_code}] Lines updated: {changed_count}/{len(tariff_lines)}. "
        f"Observations filled for codes: {dict(obs_filled.most_common(10))}",
        flush=True,
    )
    return data


def _write(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(path) // 1024
    print(f"  → Written {os.path.basename(path)} ({size_kb} KB)", flush=True)


def main(target_countries: list = None) -> None:
    """
    Enrich all (or selected) country tariff files.

    Args:
        target_countries: list of ISO3 codes, or None to process all files
    """
    if target_countries:
        files = [
            (cc, os.path.join(CRAWLED_DIR, f"{cc}_tariffs.json"))
            for cc in target_countries
        ]
    else:
        files = sorted(
            [
                (fn.replace("_tariffs.json", ""),
                 os.path.join(CRAWLED_DIR, fn))
                for fn in os.listdir(CRAWLED_DIR)
                if fn.endswith("_tariffs.json")
            ],
            key=lambda x: x[0],
        )

    ok = 0
    fail = 0
    for cc, crawled_path in files:
        if not os.path.exists(crawled_path):
            print(f"[{cc}] MISSING {crawled_path} — skipping")
            continue
        try:
            data = _enrich_country(cc, crawled_path)

            _write(data, crawled_path)

            # Also update the main data/ copy if it exists
            main_path = os.path.join(DATA_DIR, f"{cc}_tariffs.json")
            if os.path.exists(main_path):
                _write(data, main_path)

            ok += 1
        except Exception as exc:
            print(f"[{cc}] ERROR: {exc}", flush=True)
            fail += 1

    print(f"\n{'='*60}")
    print(f"Done. {ok} countries enriched, {fail} errors.")


if __name__ == "__main__":
    # Allow specifying target countries on command line: python enrich_para_fiscal_descriptions.py NGA EGY ETH
    targets = sys.argv[1:] or None
    main(targets)
