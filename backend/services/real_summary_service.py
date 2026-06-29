"""
Real Trade Summary Service (the "Vue d'ensemble" tab).

Replaces the LLM-generated continental overview with real, sourced aggregates:

- total African trade and top trading countries: the curated 2024 trade
  dataset (OEC/BACI, World Bank, IMF) in routes.statistics;
- total continental GDP: country_data.REAL_COUNTRY_DATA (IMF/World Bank);
- HS code universe size: the WCO HS6 database.

No value is fabricated. Figures with no continental-level source (e.g. total
intra-African trade, which only exists per-country for a subset) are returned as
null rather than invented, and ``top_sectors`` is left empty rather than guessed.

The response uses the exact field names the frontend (OpportunitySummary.jsx)
reads, so the real values actually render without any frontend change.
"""

import logging
from typing import Dict, Optional

from country_data import REAL_COUNTRY_DATA

logger = logging.getLogger(__name__)

# ISO2 -> ISO3 for the countries present in the curated 2024 trade dataset.
ISO2_TO_ISO3 = {
    "ZA": "ZAF",
    "NG": "NGA",
    "MA": "MAR",
    "EG": "EGY",
    "DZ": "DZA",
    "AO": "AGO",
    "LY": "LBY",
    "CD": "COD",
    "CI": "CIV",
    "TN": "TUN",
    "KE": "KEN",
    "GH": "GHA",
    "ET": "ETH",
}


def _hs_code_count() -> Optional[int]:
    """Real size of the HS6 reference database, if available."""
    try:
        from etl.hs6_database import get_database_stats

        stats = get_database_stats() or {}
        return stats.get("total_codes") or stats.get("total_hs6") or stats.get("total")
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("HS6 stats unavailable: %s", e)
        return None


async def get_trade_summary(lang: str = "fr") -> Dict:
    """Real continental trade overview (response shape matches the frontend)."""
    # Imported lazily to avoid any import-time coupling with the routes package.
    from routes.statistics import TRADE_PERFORMANCE_GLOBAL_2024 as trade_rows

    total_trade_billion = sum(
        (row.get("exports_2024", 0) or 0) + (row.get("imports_2024", 0) or 0) for row in trade_rows
    )
    total_gdp_billion = sum(d.get("gdp_usd_2024", 0) or 0 for d in REAL_COUNTRY_DATA.values())

    ranked = sorted(
        trade_rows,
        key=lambda r: (r.get("exports_2024", 0) or 0) + (r.get("imports_2024", 0) or 0),
        reverse=True,
    )
    top_trading_countries = []
    for i, row in enumerate(ranked[:8], start=1):
        volume = (row.get("exports_2024", 0) or 0) + (row.get("imports_2024", 0) or 0)
        top_trading_countries.append(
            {
                "country": row["country"],
                "name": row["country"],
                "iso3": ISO2_TO_ISO3.get(row.get("code", ""), ""),
                "trade_volume_billion": round(volume, 1),
                "exports_musd": round((row.get("exports_2024", 0) or 0) * 1000, 1),
                "imports_musd": round((row.get("imports_2024", 0) or 0) * 1000, 1),
                "rank": i,
            }
        )

    return {
        "overview": {
            "total_african_trade_billion_usd": round(total_trade_billion, 1),
            "total_gdp_trillion_usd": round(total_gdp_billion / 1000, 2),
            "total_opportunities_identified": _hs_code_count(),
            "afcfta_countries": 54,
            # No continental-level intra-African total in the sourced data; the
            # dataset only has it per-country for a subset. Not fabricated here.
            "intra_african_trade_billion_usd": None,
            "year": 2024,
        },
        "top_trading_countries": top_trading_countries,
        # No real continental sector aggregation available; left empty rather
        # than invented.
        "top_sectors": [],
        "sources": [
            "OEC/BACI 2024",
            "World Bank",
            "IMF WEO 2024",
            "country_data (IMF/BM/PNUD)",
        ],
        "data_source": "OEC/World Bank/IMF (2024) + country_data",
        "generated_by": "Données réelles (OEC/BM/FMI, country_data)",
        "is_estimation": False,
    }


class RealSummaryService:
    """Thin OO wrapper for symmetry with the other real_* services."""

    async def get_trade_summary(self, lang: str = "fr") -> Dict:
        return await get_trade_summary(lang=lang)


real_summary_service = RealSummaryService()
