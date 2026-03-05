"""
Regional Analytics Engine for AfCFTA blocs.

Provides trade performance, investment attractiveness and integration progress
metrics for ECOWAS, SADC, EAC, UMA and ECCAS regional blocs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_REGIONAL_DATA: dict[str, dict[str, Any]] = {
    "ECOWAS": {
        "full_name": "Economic Community of West African States",
        "members": [
            "Benin", "Burkina Faso", "Cabo Verde", "Côte d'Ivoire", "Gambia",
            "Ghana", "Guinea", "Guinea-Bissau", "Liberia", "Mali",
            "Niger", "Nigeria", "Senegal", "Sierra Leone", "Togo",
        ],
        "population_m": 424,
        "gdp_usd_bn": 794,
        "trade_performance": {
            "intra_regional_trade_pct": 9.4,
            "total_exports_usd_bn": 112,
            "total_imports_usd_bn": 98,
            "trade_balance_usd_bn": 14,
            "top_exports": ["crude oil", "cocoa", "gold", "natural gas", "timber"],
            "top_partners": ["EU", "China", "USA", "India"],
            "trade_growth_yoy_pct": 3.8,
        },
        "investment_attractiveness": {
            "fdi_inflow_usd_bn": 8.2,
            "ease_of_doing_business_avg": 148,
            "infrastructure_index": 3.1,
            "top_sectors": ["oil & gas", "agriculture", "fintech", "mining"],
            "sez_count": 65,
            "score": 5.8,
        },
        "integration_progress": {
            "afcfta_ratified_members": 13,
            "common_tariff": "ECOWAS CET (operational)",
            "free_movement": "Protocol in force",
            "single_currency_progress": "Eco currency – 2027 target",
            "integration_score_pct": 58,
        },
    },
    "SADC": {
        "full_name": "Southern African Development Community",
        "members": [
            "Angola", "Botswana", "Comoros", "DRC", "Eswatini", "Lesotho",
            "Madagascar", "Malawi", "Mauritius", "Mozambique", "Namibia",
            "Seychelles", "South Africa", "Tanzania", "Zambia", "Zimbabwe",
        ],
        "population_m": 368,
        "gdp_usd_bn": 725,
        "trade_performance": {
            "intra_regional_trade_pct": 18.2,
            "total_exports_usd_bn": 198,
            "total_imports_usd_bn": 175,
            "trade_balance_usd_bn": 23,
            "top_exports": ["platinum", "diamonds", "gold", "coal", "copper"],
            "top_partners": ["China", "EU", "USA", "India"],
            "trade_growth_yoy_pct": 2.1,
        },
        "investment_attractiveness": {
            "fdi_inflow_usd_bn": 12.5,
            "ease_of_doing_business_avg": 118,
            "infrastructure_index": 3.6,
            "top_sectors": ["mining", "tourism", "manufacturing", "energy"],
            "sez_count": 42,
            "score": 6.4,
        },
        "integration_progress": {
            "afcfta_ratified_members": 14,
            "common_tariff": "SADC FTA (85% tariff elimination)",
            "free_movement": "Limited bilateral protocols",
            "single_currency_progress": "No formal timeline",
            "integration_score_pct": 62,
        },
    },
    "EAC": {
        "full_name": "East African Community",
        "members": [
            "Burundi", "DRC", "Kenya", "Rwanda", "Somalia",
            "South Sudan", "Tanzania", "Uganda",
        ],
        "population_m": 305,
        "gdp_usd_bn": 312,
        "trade_performance": {
            "intra_regional_trade_pct": 22.5,
            "total_exports_usd_bn": 45,
            "total_imports_usd_bn": 68,
            "trade_balance_usd_bn": -23,
            "top_exports": ["coffee", "tea", "flowers", "sesame", "gold"],
            "top_partners": ["EU", "China", "India", "USA"],
            "trade_growth_yoy_pct": 5.2,
        },
        "investment_attractiveness": {
            "fdi_inflow_usd_bn": 6.1,
            "ease_of_doing_business_avg": 123,
            "infrastructure_index": 2.9,
            "top_sectors": ["agriculture", "technology", "logistics", "healthcare"],
            "sez_count": 28,
            "score": 6.8,
        },
        "integration_progress": {
            "afcfta_ratified_members": 6,
            "common_tariff": "EAC CET (operational)",
            "free_movement": "EAC Protocol – citizens free movement",
            "single_currency_progress": "East African Shilling – 2030 target",
            "integration_score_pct": 71,
        },
    },
    "UMA": {
        "full_name": "Arab Maghreb Union",
        "members": ["Algeria", "Libya", "Mauritania", "Morocco", "Tunisia"],
        "population_m": 105,
        "gdp_usd_bn": 410,
        "trade_performance": {
            "intra_regional_trade_pct": 3.1,
            "total_exports_usd_bn": 88,
            "total_imports_usd_bn": 72,
            "trade_balance_usd_bn": 16,
            "top_exports": ["crude oil", "phosphates", "natural gas", "automobiles", "fertilisers"],
            "top_partners": ["EU", "China", "USA", "Turkey"],
            "trade_growth_yoy_pct": 1.4,
        },
        "investment_attractiveness": {
            "fdi_inflow_usd_bn": 4.8,
            "ease_of_doing_business_avg": 101,
            "infrastructure_index": 4.1,
            "top_sectors": ["energy", "phosphate chemicals", "automotive", "tourism"],
            "sez_count": 18,
            "score": 5.2,
        },
        "integration_progress": {
            "afcfta_ratified_members": 3,
            "common_tariff": "Largely suspended – political tensions",
            "free_movement": "Restricted",
            "single_currency_progress": "No active discussions",
            "integration_score_pct": 22,
        },
    },
    "ECCAS": {
        "full_name": "Economic Community of Central African States",
        "members": [
            "Angola", "Burundi", "Cameroon", "CAR", "Chad",
            "DRC", "Equatorial Guinea", "Gabon", "Republic of Congo", "Rwanda", "São Tomé and Príncipe",
        ],
        "population_m": 210,
        "gdp_usd_bn": 248,
        "trade_performance": {
            "intra_regional_trade_pct": 4.2,
            "total_exports_usd_bn": 52,
            "total_imports_usd_bn": 44,
            "trade_balance_usd_bn": 8,
            "top_exports": ["crude oil", "timber", "cobalt", "copper", "cotton"],
            "top_partners": ["China", "EU", "USA", "India"],
            "trade_growth_yoy_pct": 2.6,
        },
        "investment_attractiveness": {
            "fdi_inflow_usd_bn": 3.4,
            "ease_of_doing_business_avg": 162,
            "infrastructure_index": 2.4,
            "top_sectors": ["oil & gas", "mining", "agriculture", "forestry"],
            "sez_count": 12,
            "score": 4.1,
        },
        "integration_progress": {
            "afcfta_ratified_members": 7,
            "common_tariff": "CEMAC CET for 6 members",
            "free_movement": "Limited – CEMAC zone only",
            "single_currency_progress": "CFA Franc (CEMAC zone)",
            "integration_score_pct": 35,
        },
    },
}


class RegionalAnalyticsEngine:
    """Provides regional trade & investment intelligence for AfCFTA blocs."""

    def __init__(self) -> None:
        self._data = _REGIONAL_DATA

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_regional_dashboard(
        self,
        regions: list[str] | None = None,
        timeframe: str = "2024",
    ) -> dict[str, Any]:
        """Return a dashboard dict for the requested regions (all if None)."""
        target_regions = regions or list(self._data.keys())
        result: dict[str, Any] = {}
        for region in target_regions:
            data = self._data.get(region.upper())
            if not data:
                continue
            result[region.upper()] = {
                "full_name": data["full_name"],
                "members_count": len(data["members"]),
                "population_m": data["population_m"],
                "gdp_usd_bn": data["gdp_usd_bn"],
                "trade_performance": data["trade_performance"],
                "investment_attractiveness": data["investment_attractiveness"],
                "integration_progress": data["integration_progress"],
                "timeframe": timeframe,
            }
        return {
            "regions": result,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "timeframe": timeframe,
        }

    def compare_regions(self, region1: str, region2: str) -> dict[str, Any]:
        """Side-by-side comparison of two blocs."""
        r1 = self._data.get(region1.upper())
        r2 = self._data.get(region2.upper())

        def _summary(bloc: dict[str, Any] | None, name: str) -> dict[str, Any]:
            if not bloc:
                return {"error": f"Region '{name}' not found"}
            return {
                "full_name": bloc["full_name"],
                "members_count": len(bloc["members"]),
                "gdp_usd_bn": bloc["gdp_usd_bn"],
                "population_m": bloc["population_m"],
                "intra_regional_trade_pct": bloc["trade_performance"]["intra_regional_trade_pct"],
                "fdi_inflow_usd_bn": bloc["investment_attractiveness"]["fdi_inflow_usd_bn"],
                "investment_score": bloc["investment_attractiveness"]["score"],
                "integration_score_pct": bloc["integration_progress"]["integration_score_pct"],
                "afcfta_ratified_members": bloc["integration_progress"]["afcfta_ratified_members"],
            }

        return {
            region1.upper(): _summary(r1, region1),
            region2.upper(): _summary(r2, region2),
            "winner": {
                "trade": region1.upper()
                if (r1 or {}).get("trade_performance", {}).get("intra_regional_trade_pct", 0) >=
                   (r2 or {}).get("trade_performance", {}).get("intra_regional_trade_pct", 0)
                else region2.upper(),
                "investment": region1.upper()
                if (r1 or {}).get("investment_attractiveness", {}).get("score", 0) >=
                   (r2 or {}).get("investment_attractiveness", {}).get("score", 0)
                else region2.upper(),
                "integration": region1.upper()
                if (r1 or {}).get("integration_progress", {}).get("integration_score_pct", 0) >=
                   (r2 or {}).get("integration_progress", {}).get("integration_score_pct", 0)
                else region2.upper(),
            },
            "compared_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_trade_corridors(self) -> dict[str, Any]:
        """Return major intra-African trade corridors with volume estimates."""
        corridors = [
            {
                "id": "ECOWAS-SADC",
                "from_bloc": "ECOWAS",
                "to_bloc": "SADC",
                "estimated_volume_usd_bn": 4.2,
                "primary_commodities": ["cocoa", "crude oil", "refined petroleum"],
                "key_nodes": ["Lagos", "Johannesburg", "Durban"],
                "growth_potential": "high",
            },
            {
                "id": "EAC-SADC",
                "from_bloc": "EAC",
                "to_bloc": "SADC",
                "estimated_volume_usd_bn": 6.8,
                "primary_commodities": ["coffee", "tea", "manufactured goods"],
                "key_nodes": ["Mombasa", "Dar es Salaam", "Beira", "Nacala"],
                "growth_potential": "very_high",
            },
            {
                "id": "UMA-ECOWAS",
                "from_bloc": "UMA",
                "to_bloc": "ECOWAS",
                "estimated_volume_usd_bn": 2.1,
                "primary_commodities": ["fertilisers", "phosphates", "machinery"],
                "key_nodes": ["Casablanca", "Dakar", "Abidjan"],
                "growth_potential": "medium",
            },
            {
                "id": "ECCAS-EAC",
                "from_bloc": "ECCAS",
                "to_bloc": "EAC",
                "estimated_volume_usd_bn": 1.5,
                "primary_commodities": ["timber", "palm oil", "minerals"],
                "key_nodes": ["Douala", "Kinshasa", "Kampala"],
                "growth_potential": "medium",
            },
        ]
        return {
            "corridors": corridors,
            "total_corridors": len(corridors),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
