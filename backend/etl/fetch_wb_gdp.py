"""
Reproducible ETL — World Bank GDP per capita for African countries.

Produces ``data/json/wb_gdp_pc.json`` consumed by
``services/demand_estimation_service.py`` for the standard-of-living (L3)
adjustment of national-need estimates. Pulls one World Bank WDI indicator:

  - ``NY.GDP.PCAP.CD`` : GDP per capita, current US$.

For each country the most recent non-null observation is kept, with its year.
No value is ever synthesised: countries without data are simply omitted.

Output shape (flat, keyed by ISO3):

    {"NGA": {"value": 2162.6, "year": 2023}, ...}

Usage (run where the World Bank API is reachable — it is blocked by the egress
policy in some CI/dev sandboxes, exactly like the OEC API):

    python -m etl.fetch_wb_gdp

The World Bank API requires no key.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

from etl.wb_fetch import fetch_indicator

GDP_PER_CAPITA = "NY.GDP.PCAP.CD"

# 54 African Union members (ISO3), same list as fetch_wb_reserves.
AFRICA_ISO3 = [
    "DZA",
    "AGO",
    "BEN",
    "BWA",
    "BFA",
    "BDI",
    "CPV",
    "CMR",
    "CAF",
    "TCD",
    "COM",
    "COG",
    "COD",
    "CIV",
    "DJI",
    "EGY",
    "GNQ",
    "ERI",
    "SWZ",
    "ETH",
    "GAB",
    "GMB",
    "GHA",
    "GIN",
    "GNB",
    "KEN",
    "LSO",
    "LBR",
    "LBY",
    "MDG",
    "MWI",
    "MLI",
    "MRT",
    "MUS",
    "MAR",
    "MOZ",
    "NAM",
    "NER",
    "NGA",
    "RWA",
    "STP",
    "SEN",
    "SYC",
    "SLE",
    "SOM",
    "ZAF",
    "SSD",
    "SDN",
    "TZA",
    "TGO",
    "TUN",
    "UGA",
    "ZMB",
    "ZWE",
]

_OUT = Path(__file__).resolve().parent.parent.parent / "data" / "json" / "wb_gdp_pc.json"


def _fetch_indicator(indicator: str) -> Dict[str, Dict]:
    """Fetch robuste (lots + retries + timeout long) — voir etl/wb_fetch.py."""
    latest = fetch_indicator(indicator, AFRICA_ISO3)
    return {
        iso3: {"value": round(rec["value"], 2), "year": rec["year"]} for iso3, rec in latest.items()
    }


def build() -> Optional[dict]:
    gdp = _fetch_indicator(GDP_PER_CAPITA)
    return gdp or None


def main() -> int:
    try:
        data = build()
    except Exception as exc:  # network / parsing errors
        print(f"❌ World Bank fetch failed: {exc}", file=sys.stderr)
        return 1
    if not data:
        print("❌ No data returned from World Bank API.", file=sys.stderr)
        return 1
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote {len(data)} countries to {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
