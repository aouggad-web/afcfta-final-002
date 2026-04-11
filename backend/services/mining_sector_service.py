"""
Mining Sector Service
======================
Specialist service for SADC mining sector intelligence, covering the full
value chains for diamonds, platinum group metals, copper, coal, and critical
minerals (cobalt, lithium, manganese, chromium, etc.).

Provides:
  - Mining value-chain analysis by mineral
  - Country-level production statistics
  - Transport route optimization for mineral exports
  - Beneficiation opportunity mapping
  - Regulatory overview per country
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Import mining data (with graceful fallback)
# ---------------------------------------------------------------------------

def _load_mining_data() -> Dict[str, Any]:
    try:
        from crawlers.countries.sadc.mining_intelligence import (
            SADC_MINING_INTELLIGENCE,
            MINING_REGULATORY_OVERVIEW,
        )
        return {
            "intelligence": SADC_MINING_INTELLIGENCE,
            "regulatory": MINING_REGULATORY_OVERVIEW,
        }
    except ImportError:
        logger.warning("Mining intelligence module not available")
        return {"intelligence": {}, "regulatory": {}}


# ---------------------------------------------------------------------------
# Mineral metadata
# ---------------------------------------------------------------------------

MINERAL_PROFILES = {
    "diamond": {
        "hs_code_prefix": "7102",
        "description": "Diamonds – natural, unworked or simply sawn",
        "sadc_global_share_pct": 60,
        "key_producers": ["BWA", "ZAF", "NAM", "AGO", "ZWE"],
        "processing_stages": ["mining", "sorting", "cutting_polishing", "jewellery"],
        "primary_markets": ["Antwerp", "Dubai", "Mumbai", "Hong Kong"],
        "price_driver": "Kimberley Process certification + De Beers sightholder system",
    },
    "platinum": {
        "hs_code_prefix": "7110",
        "description": "Platinum – unwrought or in semi-manufactured forms",
        "sadc_global_share_pct": 80,
        "key_producers": ["ZAF", "ZWE"],
        "processing_stages": ["mining", "smelting", "refining", "catalyst_fabrication"],
        "primary_markets": ["USA", "Europe", "Japan"],
        "price_driver": "Automotive catalyst demand + hydrogen fuel cell growth",
    },
    "copper": {
        "hs_code_prefix": "7403",
        "description": "Copper – refined; cathodes and sections",
        "sadc_global_share_pct": 15,
        "key_producers": ["ZMB", "COD", "ZWE"],
        "processing_stages": ["mining", "concentrating", "smelting", "refining", "fabrication"],
        "primary_markets": ["China", "Europe", "USA"],
        "price_driver": "EV and renewable energy demand + infrastructure investment",
    },
    "cobalt": {
        "hs_code_prefix": "8105",
        "description": "Cobalt mattes; cobalt and articles thereof",
        "sadc_global_share_pct": 70,
        "key_producers": ["COD", "ZMB"],
        "processing_stages": ["mining", "hydroxide_precipitation", "refining", "battery_precursor"],
        "primary_markets": ["China", "Japan", "South Korea"],
        "price_driver": "EV battery (NMC/NCA cathode) demand",
    },
    "coal": {
        "hs_code_prefix": "2701",
        "description": "Coal; briquettes, ovoids from coal",
        "sadc_global_share_pct": 4,
        "key_producers": ["ZAF", "MOZ", "ZWE", "BWA"],
        "processing_stages": ["mining", "washing_beneficiation", "export"],
        "primary_markets": ["India", "China", "Japan", "EU"],
        "price_driver": "Asian power generation demand + European energy security",
    },
    "gold": {
        "hs_code_prefix": "7108",
        "description": "Gold – unwrought or in semi-manufactured forms",
        "sadc_global_share_pct": 15,
        "key_producers": ["ZAF", "ZMB", "TZA", "ZWE", "MOZ"],
        "processing_stages": ["mining", "milling", "smelting", "refining"],
        "primary_markets": ["Zürich", "London", "Dubai", "Shanghai"],
        "price_driver": "Safe-haven demand + central bank reserves",
    },
}


class MiningSectorService:
    """
    Comprehensive mining sector intelligence service for SADC.

    Singleton pattern – use get_mining_service() factory function.
    """

    def __init__(self):
        self._data = _load_mining_data()

    @property
    def intelligence(self) -> Dict[str, Any]:
        return self._data.get("intelligence", {})

    @property
    def regulatory(self) -> Dict[str, Any]:
        return self._data.get("regulatory", {})

    # ==================== Mineral queries ====================

    def get_mineral_profile(self, mineral: str) -> Dict[str, Any]:
        """Return profile for a named mineral."""
        mineral_lower = mineral.lower()
        profile = MINERAL_PROFILES.get(mineral_lower)
        if not profile:
            available = list(MINERAL_PROFILES.keys())
            return {"error": f"Mineral '{mineral}' not found", "available": available}

        # Enrich with production data from intelligence module
        intel_key = None
        if mineral_lower == "diamond":
            intel_key = "diamond_pipeline"
        elif mineral_lower == "platinum":
            intel_key = "platinum_group_metals"
        elif mineral_lower == "copper":
            intel_key = "copper_belt"
        elif mineral_lower == "cobalt":
            intel_key = "copper_belt"
        elif mineral_lower == "coal":
            intel_key = "coal"

        result = dict(profile)
        if intel_key and intel_key in self.intelligence:
            result["production_data"] = self.intelligence[intel_key]

        return result

    def list_minerals(self) -> List[str]:
        """List all supported minerals."""
        return list(MINERAL_PROFILES.keys())

    # ==================== Country mining profile ====================

    def get_country_mining_profile(self, country_code: str) -> Dict[str, Any]:
        """Return all mining sector data for a specific SADC country."""
        involvement: Dict[str, List[str]] = {}

        for mineral, profile in MINERAL_PROFILES.items():
            if country_code in profile.get("key_producers", []):
                involvement.setdefault("producer", []).append(mineral)

        # Regulatory overview
        regulatory = self.regulatory.get(country_code, {})

        if not involvement and not regulatory:
            return {
                "country_code": country_code,
                "mining_role": "minor_or_emerging",
                "note": "Limited mining sector data available for this country",
            }

        return {
            "country_code": country_code,
            "minerals_produced": involvement.get("producer", []),
            "regulatory_framework": regulatory,
        }

    # ==================== Value-chain analysis ====================

    def get_value_chain(self, mineral: str) -> Dict[str, Any]:
        """Return value-chain analysis for a given mineral."""
        mineral_lower = mineral.lower()
        profile = MINERAL_PROFILES.get(mineral_lower)
        if not profile:
            return {"error": f"Mineral '{mineral}' not found"}

        stages = profile.get("processing_stages", [])
        producers = profile.get("key_producers", [])

        stage_countries: Dict[str, List[str]] = {}
        for i, stage in enumerate(stages):
            # First stage = all producers; further stages = countries with processing
            if i == 0:
                stage_countries[stage] = producers
            else:
                # Simplified: more advanced stages in more developed economies
                advanced = [c for c in producers if c in {"ZAF", "MUS", "BWA"}]
                stage_countries[stage] = advanced if advanced else producers[:2]

        return {
            "mineral": mineral_lower,
            "hs_code_prefix": profile.get("hs_code_prefix"),
            "value_chain_stages": stages,
            "countries_per_stage": stage_countries,
            "primary_export_markets": profile.get("primary_markets", []),
            "sadc_beneficiation_opportunity": {
                "description": "Shift from raw mineral exports to processed/refined goods",
                "value_addition_potential": "3–10x for most minerals",
                "bottlenecks": ["Energy cost", "Skills availability", "Logistics infrastructure"],
            },
        }

    # ==================== Transport for minerals ====================

    def get_mineral_export_routes(self, country_code: str) -> Dict[str, Any]:
        """
        Return recommended export routes for a mineral-producing country.
        """
        EXPORT_ROUTES: Dict[str, List[Dict]] = {
            "ZMB": [
                {"route": "North-South Corridor", "port": "Durban (ZAF)", "mode": "road/rail", "priority": 1},
                {"route": "Dar-es-Salaam Corridor", "port": "Dar-es-Salaam (TZA)", "mode": "road/TAZARA", "priority": 2},
                {"route": "Walvis Bay Corridor", "port": "Walvis Bay (NAM)", "mode": "road", "priority": 3},
                {"route": "Lobito Corridor", "port": "Lobito (AGO)", "mode": "rail (rehabilitating)", "priority": 4},
            ],
            "COD": [
                {"route": "Dar-es-Salaam Corridor", "port": "Dar-es-Salaam (TZA)", "mode": "road/rail", "priority": 1},
                {"route": "Lobito Corridor", "port": "Lobito (AGO)", "mode": "rail (Benguela)", "priority": 2},
                {"route": "North-South Corridor", "port": "Durban (ZAF)", "mode": "road/rail (indirect)", "priority": 3},
            ],
            "ZWE": [
                {"route": "North-South Corridor", "port": "Durban (ZAF)", "mode": "road/rail", "priority": 1},
                {"route": "Beira Corridor", "port": "Beira (MOZ)", "mode": "road/rail", "priority": 2},
            ],
            "MOZ": [
                {"route": "Nacala Corridor", "port": "Nacala (MOZ)", "mode": "rail/road", "priority": 1},
                {"route": "Beira Corridor", "port": "Beira (MOZ)", "mode": "road/rail", "priority": 2},
            ],
            "ZAF": [
                {"route": "Direct", "port": "Durban / Richards Bay / Cape Town (ZAF)", "mode": "road/rail", "priority": 1},
            ],
            "BWA": [
                {"route": "North-South Corridor", "port": "Durban (ZAF)", "mode": "road/rail", "priority": 1},
                {"route": "Trans-Kalahari Corridor", "port": "Walvis Bay (NAM)", "mode": "road", "priority": 2},
            ],
            "TZA": [
                {"route": "Direct", "port": "Dar-es-Salaam (TZA)", "mode": "road/rail", "priority": 1},
            ],
        }

        routes = EXPORT_ROUTES.get(country_code)
        if not routes:
            return {
                "country_code": country_code,
                "note": "No specific route data; use nearest SADC port",
            }

        return {
            "country_code": country_code,
            "export_routes": routes,
            "recommendation": routes[0] if routes else None,
        }

    # ==================== Beneficiation opportunities ====================

    def get_beneficiation_opportunities(self) -> List[Dict[str, Any]]:
        """Return top beneficiation opportunities across SADC."""
        return [
            {
                "mineral": "diamond",
                "current_state": "Rough diamonds exported to Belgium/India",
                "opportunity": "Cutting & polishing, jewellery manufacturing",
                "leading_country": "BWA",
                "value_multiplier": "3–5x",
                "example": "Botswana (De Beers sightholder system)",
            },
            {
                "mineral": "platinum",
                "current_state": "PGM concentrate/matte exported",
                "opportunity": "Catalytic converter manufacturing, fuel cell components",
                "leading_country": "ZAF",
                "value_multiplier": "4–8x",
                "example": "South Africa – BASF catalyst plant",
            },
            {
                "mineral": "copper",
                "current_state": "Cathodes exported to China",
                "opportunity": "Wire rod, electrical cables, copper tubing",
                "leading_country": "ZMB",
                "value_multiplier": "2–3x",
                "example": "Zambia – KCM cable manufacturing",
            },
            {
                "mineral": "cobalt",
                "current_state": "Cobalt hydroxide exported to Asia",
                "opportunity": "Precursor cathode material, battery-grade cobalt",
                "leading_country": "COD",
                "value_multiplier": "5–10x",
                "example": "DRC – Glencore Murrin Murrin analogy",
            },
            {
                "mineral": "lithium",
                "current_state": "Lithium ore/spodumene exported",
                "opportunity": "Lithium carbonate, battery-grade lithium hydroxide",
                "leading_country": "ZWE",
                "value_multiplier": "6–10x",
                "example": "Zimbabwe – Prospect Lithium Zimbabwe",
            },
        ]


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_mining_service: Optional[MiningSectorService] = None


def get_mining_service() -> MiningSectorService:
    """Return (and lazily create) the singleton mining service."""
    global _mining_service
    if _mining_service is None:
        _mining_service = MiningSectorService()
    return _mining_service
