"""
AfCFTA Platform - Regional Analytics Engine
============================================
Comparative analysis and aggregated regional metrics for all African blocs.
Results are cached in L2 (regional intelligence) layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regional bloc definitions
REGIONAL_BLOCS: Dict[str, Dict[str, Any]] = {
    "ECOWAS": {
        "full_name": "Economic Community of West African States",
        "countries": ["BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI",
                      "MRT", "NER", "NGA", "SEN", "SLE", "TGO"],
        "headquarters": "Abuja, Nigeria",
        "established": 1975,
        "gdp_bn_usd": 700,
        "population_mn": 420,
        "intra_trade_pct": 9.5,
    },
    "CEMAC": {
        "full_name": "Economic and Monetary Community of Central Africa",
        "countries": ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"],
        "headquarters": "Bangui, CAR",
        "established": 1994,
        "gdp_bn_usd": 120,
        "population_mn": 60,
        "intra_trade_pct": 3.2,
    },
    "EAC": {
        "full_name": "East African Community",
        "countries": ["BDI", "COD", "KEN", "RWA", "SSD", "TZA", "UGA"],
        "headquarters": "Arusha, Tanzania",
        "established": 1967,
        "gdp_bn_usd": 270,
        "population_mn": 310,
        "intra_trade_pct": 11.2,
    },
    "SADC": {
        "full_name": "Southern African Development Community",
        "countries": ["AGO", "BWA", "COM", "COD", "LSO", "MDG", "MWI", "MUS", "MOZ", "NAM",
                      "SYC", "ZAF", "SWZ", "TZA", "ZMB", "ZWE"],
        "headquarters": "Gaborone, Botswana",
        "established": 1980,
        "gdp_bn_usd": 640,
        "population_mn": 370,
        "intra_trade_pct": 17.8,
    },
    "UMA": {
        "full_name": "Arab Maghreb Union",
        "countries": ["DZA", "LBA", "MAR", "MRT", "TUN"],
        "headquarters": "Rabat, Morocco",
        "established": 1989,
        "gdp_bn_usd": 320,
        "population_mn": 105,
        "intra_trade_pct": 3.0,
    },
    "COMESA": {
        "full_name": "Common Market for Eastern and Southern Africa",
        "countries": ["BDI", "COM", "COD", "DJI", "EGY", "ERI", "ETH", "KEN", "LBA", "MDG",
                      "MWI", "MUS", "RWA", "SOM", "SDN", "SWZ", "TUN", "UGA", "ZMB", "ZWE"],
        "headquarters": "Lusaka, Zambia",
        "established": 1994,
        "gdp_bn_usd": 820,
        "population_mn": 640,
        "intra_trade_pct": 8.5,
    },
    "IGAD": {
        "full_name": "Intergovernmental Authority on Development",
        "countries": ["DJI", "ERI", "ETH", "KEN", "SOM", "SSD", "SDN", "UGA"],
        "headquarters": "Djibouti",
        "established": 1996,
        "gdp_bn_usd": 280,
        "population_mn": 285,
        "intra_trade_pct": 7.2,
    },
}

# Metric benchmarks for comparative analysis
REGIONAL_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "SADC":   {"tariff_avg": 8.2,  "investment_score": 0.65, "infrastructure": 0.68, "trade_integration": 17.8},
    "EAC":    {"tariff_avg": 12.5, "investment_score": 0.61, "infrastructure": 0.60, "trade_integration": 11.2},
    "ECOWAS": {"tariff_avg": 15.3, "investment_score": 0.56, "infrastructure": 0.52, "trade_integration": 9.5},
    "COMESA": {"tariff_avg": 11.8, "investment_score": 0.59, "infrastructure": 0.58, "trade_integration": 8.5},
    "IGAD":   {"tariff_avg": 18.2, "investment_score": 0.50, "infrastructure": 0.48, "trade_integration": 7.2},
    "UMA":    {"tariff_avg": 14.5, "investment_score": 0.62, "infrastructure": 0.65, "trade_integration": 3.0},
    "CEMAC":  {"tariff_avg": 19.5, "investment_score": 0.48, "infrastructure": 0.46, "trade_integration": 3.2},
}


class RegionalAnalyticsEngine:
    """
    Computes comparative analytics for African regional blocs.
    Results are cached in the L2 layer.
    """

    def __init__(self) -> None:
        try:
            from performance.caching.cache_layers import get_cache
            self._cache = get_cache()
        except Exception:
            self._cache = None

    def get_bloc_summary(self, bloc: str) -> Dict[str, Any]:
        """Return a summary for a single regional bloc."""
        bloc = bloc.upper()
        cache_key = f"bloc_summary:{bloc}"
        if self._cache:
            cached = self._cache.l2.get(cache_key)
            if cached:
                return cached

        if bloc not in REGIONAL_BLOCS:
            return {"error": f"Unknown regional bloc: {bloc}"}

        info = REGIONAL_BLOCS[bloc]
        benchmarks = REGIONAL_BENCHMARKS.get(bloc, {})

        result = {
            "bloc": bloc,
            "full_name": info["full_name"],
            "headquarters": info["headquarters"],
            "established": info["established"],
            "member_count": len(info["countries"]),
            "countries": info["countries"],
            "gdp_bn_usd": info["gdp_bn_usd"],
            "population_mn": info["population_mn"],
            "intra_trade_pct": info["intra_trade_pct"],
            "metrics": benchmarks,
        }

        if self._cache:
            self._cache.l2.set(cache_key, result)

        return result

    def compare_regions(
        self,
        blocs: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compare multiple regional blocs across selected metrics."""
        if blocs is None:
            blocs = list(REGIONAL_BLOCS.keys())
        if metrics is None:
            metrics = ["tariff_avg", "investment_score", "infrastructure", "trade_integration"]

        blocs = [b.upper() for b in blocs]
        comparison: Dict[str, Any] = {
            "blocs": {},
            "rankings": {},
            "best_performer": {},
        }

        for bloc in blocs:
            benchmarks = REGIONAL_BENCHMARKS.get(bloc, {})
            comparison["blocs"][bloc] = {
                m: benchmarks.get(m, "N/A") for m in metrics
            }

        # Rankings per metric
        for metric in metrics:
            sorted_blocs = sorted(
                [(b, REGIONAL_BENCHMARKS.get(b, {}).get(metric, 0)) for b in blocs],
                key=lambda x: x[1],
                reverse=(metric not in ["tariff_avg"]),  # lower tariff = better
            )
            comparison["rankings"][metric] = [
                {"rank": i + 1, "bloc": b, "value": v}
                for i, (b, v) in enumerate(sorted_blocs)
            ]
            if sorted_blocs:
                comparison["best_performer"][metric] = sorted_blocs[0][0]

        return comparison

    def get_investment_heatmap(self) -> List[Dict[str, Any]]:
        """Generate investment opportunity heatmap data for all blocs."""
        heatmap = []
        for bloc, info in REGIONAL_BLOCS.items():
            benchmarks = REGIONAL_BENCHMARKS.get(bloc, {})
            heatmap.append(
                {
                    "bloc": bloc,
                    "full_name": info["full_name"],
                    "investment_score": benchmarks.get("investment_score", 0.50),
                    "trade_integration": benchmarks.get("trade_integration", 5.0),
                    "infrastructure": benchmarks.get("infrastructure", 0.50),
                    "country_count": len(info["countries"]),
                    "gdp_bn_usd": info["gdp_bn_usd"],
                    "opportunity_tier": (
                        "tier1" if benchmarks.get("investment_score", 0) >= 0.63
                        else "tier2" if benchmarks.get("investment_score", 0) >= 0.55
                        else "tier3"
                    ),
                }
            )
        return sorted(heatmap, key=lambda x: x["investment_score"], reverse=True)

    def get_trade_corridor_analysis(
        self,
        origin_bloc: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyse intra-African trade corridors.
        If origin_bloc is provided, returns corridors starting from that bloc.
        """
        corridors = [
            {
                "origin": "EAC", "destination": "SADC",
                "trade_value_bn": 18.2, "growth_pct": 12.5,
                "key_products": ["Coffee", "Tea", "Minerals"],
                "main_route": "Dar es Salaam - Beit Bridge",
            },
            {
                "origin": "ECOWAS", "destination": "UMA",
                "trade_value_bn": 8.6, "growth_pct": 8.2,
                "key_products": ["Cotton", "Cocoa", "Oil"],
                "main_route": "Trans-Saharan Highway",
            },
            {
                "origin": "SADC", "destination": "COMESA",
                "trade_value_bn": 22.4, "growth_pct": 15.3,
                "key_products": ["Gold", "Copper", "Manufactures"],
                "main_route": "North-South Corridor",
            },
            {
                "origin": "UMA", "destination": "ECOWAS",
                "trade_value_bn": 5.8, "growth_pct": 6.8,
                "key_products": ["Phosphates", "Fish", "Electronics"],
                "main_route": "Trans-African Highway",
            },
            {
                "origin": "CEMAC", "destination": "EAC",
                "trade_value_bn": 3.2, "growth_pct": 9.5,
                "key_products": ["Timber", "Oil", "Cocoa"],
                "main_route": "Central Corridor",
            },
        ]

        if origin_bloc:
            corridors = [c for c in corridors if c["origin"] == origin_bloc.upper()]

        return corridors

    def get_all_blocs(self) -> List[str]:
        return list(REGIONAL_BLOCS.keys())


# Singleton
_analytics: Optional[RegionalAnalyticsEngine] = None


def get_regional_analytics() -> RegionalAnalyticsEngine:
    global _analytics
    if _analytics is None:
        _analytics = RegionalAnalyticsEngine()
    return _analytics
