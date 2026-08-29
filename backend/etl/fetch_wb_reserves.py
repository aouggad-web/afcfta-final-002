"""
Reproducible ETL — World Bank FX reserves & import cover for African countries.

Produces ``data/json/wb_reserves.json`` consumed by
``services/macro_indicators_service.py``. Pulls two World Bank WDI indicators:

  - ``FI.RES.TOTL.CD`` : Total reserves (includes gold), current US$.
  - ``FI.RES.TOTL.MO`` : Total reserves in months of imports.

For each country the most recent non-null observation is kept, with its year.
No value is ever synthesised: countries/indicators without data are simply
omitted from the output.

Usage (run where the World Bank API is reachable — it is blocked by the egress
policy in some CI/dev sandboxes, exactly like the OEC API):

    python -m etl.fetch_wb_reserves

The World Bank API requires no key.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

from etl.wb_fetch import fetch_indicator

FX_RESERVES = "FI.RES.TOTL.CD"
IMPORT_COVER = "FI.RES.TOTL.MO"

# 54 African Union members (ISO3). World Bank uses these alpha-3 codes.
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

_OUT = Path(__file__).resolve().parent.parent.parent / "data" / "json" / "wb_reserves.json"


def _fetch_indicator(indicator: str) -> Dict[str, Dict]:
    """Fetch robuste (lots + retries + timeout long) — voir etl/wb_fetch.py."""
    return fetch_indicator(indicator, AFRICA_ISO3)


def build() -> Optional[dict]:
    fx = _fetch_indicator(FX_RESERVES)
    cover = _fetch_indicator(IMPORT_COVER)
    if not fx and not cover:
        return None

    countries: Dict[str, Dict] = {}
    for iso3 in AFRICA_ISO3:
        rec: Dict = {}
        if iso3 in fx:
            rec["fx_reserves_busd"] = round(fx[iso3]["value"] / 1e9, 3)
            rec["fx_reserves_year"] = fx[iso3]["year"]
        if iso3 in cover:
            rec["import_cover_months"] = round(cover[iso3]["value"], 2)
            rec["import_cover_year"] = cover[iso3]["year"]
        if rec:
            countries[iso3] = rec

    return {
        "source": "World Bank, World Development Indicators (WDI)",
        "indicators": {
            "fx_reserves_busd": FX_RESERVES,
            "import_cover_months": IMPORT_COVER,
        },
        "note": "Total reserves include gold. Latest available observation per country.",
        "countries": countries,
    }


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
    print(f"✅ Wrote {_OUT} ({len(data['countries'])} countries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
