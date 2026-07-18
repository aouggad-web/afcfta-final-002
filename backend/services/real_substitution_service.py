"""
Real Trade Substitution Analysis Service

Primary path: real bilateral/product trade flows from the OEC (Observatory of
Economic Complexity, BACI/UN Comtrade) API, so both the products listed and
their volumes are real and reproducible across the 54 AfCFTA countries.

Fallback path: the curated static profiles below are used ONLY when the OEC API
is unreachable, and the response is then explicitly flagged as an estimation
(``is_estimation: True``). No value is ever randomised.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.real_trade_data_service import (
    AFRICAN_COUNTRIES,
    get_country_name,
    get_product_name,
    has_trade_data,
    real_trade_service,
)
from services.substitution_feasibility_service import realistic_substitution_potential

logger = logging.getLogger(__name__)

# Pre-computed substitution data by country (based on real trade patterns)
# This is used as fallback when OEC API is slow
COUNTRY_SUBSTITUTION_PROFILES = {
    "DZA": {  # Algeria
        "major_imports": [
            {
                "hs_code": "8703",
                "name_fr": "Voitures de tourisme",
                "name_en": "Motor vehicles",
                "value_musd": 3200,
                "potential_suppliers": ["MAR", "ZAF", "EGY"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé et méteil",
                "name_en": "Wheat and meslin",
                "value_musd": 2800,
                "potential_suppliers": ["EGY", "ETH", "ZAF"],
            },
            {
                "hs_code": "8517",
                "name_fr": "Téléphones et équipements de télécommunication",
                "name_en": "Telephones and telecom equipment",
                "value_musd": 1500,
                "potential_suppliers": ["EGY", "MAR", "TUN"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 1200,
                "potential_suppliers": ["EGY", "ZAF", "MAR", "TUN"],
            },
            {
                "hs_code": "8471",
                "name_fr": "Ordinateurs et machines de traitement de données",
                "name_en": "Computers",
                "value_musd": 980,
                "potential_suppliers": ["EGY", "MAR", "ZAF"],
            },
            {
                "hs_code": "1701",
                "name_fr": "Sucres de canne ou de betterave",
                "name_en": "Cane or beet sugar",
                "value_musd": 850,
                "potential_suppliers": ["EGY", "ZAF", "SWZ", "MUS"],
            },
            {
                "hs_code": "8708",
                "name_fr": "Parties et accessoires de véhicules automobiles",
                "name_en": "Motor vehicle parts",
                "value_musd": 720,
                "potential_suppliers": ["MAR", "ZAF", "EGY"],
            },
            {
                "hs_code": "7308",
                "name_fr": "Constructions et parties de constructions en fer ou acier",
                "name_en": "Steel structures",
                "value_musd": 680,
                "potential_suppliers": ["ZAF", "EGY"],
            },
            {
                "hs_code": "0402",
                "name_fr": "Lait et crème de lait concentrés",
                "name_en": "Concentrated milk and cream",
                "value_musd": 620,
                "potential_suppliers": ["EGY", "ZAF", "TUN"],
            },
            {
                "hs_code": "8481",
                "name_fr": "Articles de robinetterie",
                "name_en": "Taps, valves and similar appliances",
                "value_musd": 540,
                "potential_suppliers": ["EGY", "ZAF", "TUN"],
            },
        ],
        "export_strengths": ["2709", "2710", "2711", "3102", "2814"],  # Petroleum, fertilizers
        "total_imports_from_outside_musd": 35000,
        "substitution_potential_percent": 18,
    },
    "MAR": {  # Morocco
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 8500,
                "potential_suppliers": ["NGA", "AGO", "DZA", "LBY"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé et méteil",
                "name_en": "Wheat",
                "value_musd": 1800,
                "potential_suppliers": ["EGY", "ETH", "ZAF"],
            },
            {
                "hs_code": "2711",
                "name_fr": "Gaz de pétrole",
                "name_en": "Petroleum gases",
                "value_musd": 1500,
                "potential_suppliers": ["DZA", "NGA", "EGY"],
            },
            {
                "hs_code": "8703",
                "name_fr": "Voitures de tourisme",
                "name_en": "Motor vehicles",
                "value_musd": 1200,
                "potential_suppliers": ["ZAF", "EGY"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 850,
                "potential_suppliers": ["EGY", "ZAF", "TUN"],
            },
            {
                "hs_code": "1201",
                "name_fr": "Fèves de soja",
                "name_en": "Soya beans",
                "value_musd": 720,
                "potential_suppliers": ["ZAF", "ZMB", "MWI"],
            },
            {
                "hs_code": "8517",
                "name_fr": "Téléphones",
                "name_en": "Telephones",
                "value_musd": 680,
                "potential_suppliers": ["EGY", "TUN"],
            },
            {
                "hs_code": "1005",
                "name_fr": "Maïs",
                "name_en": "Maize",
                "value_musd": 580,
                "potential_suppliers": ["ZAF", "ZMB", "TZA"],
            },
        ],
        "export_strengths": ["8703", "3102", "0805", "6109"],  # Cars, fertilizers, citrus, textiles
        "total_imports_from_outside_musd": 42000,
        "substitution_potential_percent": 22,
    },
    "EGY": {  # Egypt
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 12000,
                "potential_suppliers": ["NGA", "AGO", "DZA", "LBY"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé et méteil",
                "name_en": "Wheat",
                "value_musd": 4500,
                "potential_suppliers": ["ETH", "ZAF", "SDN"],
            },
            {
                "hs_code": "1005",
                "name_fr": "Maïs",
                "name_en": "Maize",
                "value_musd": 2800,
                "potential_suppliers": ["ZAF", "ZMB", "TZA"],
            },
            {
                "hs_code": "1201",
                "name_fr": "Fèves de soja",
                "name_en": "Soya beans",
                "value_musd": 2200,
                "potential_suppliers": ["ZAF", "ZMB"],
            },
            {
                "hs_code": "7207",
                "name_fr": "Produits semi-finis en fer ou acier",
                "name_en": "Semi-finished steel",
                "value_musd": 1800,
                "potential_suppliers": ["ZAF", "DZA"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 1500,
                "potential_suppliers": ["ZAF", "MAR", "TUN"],
            },
        ],
        "export_strengths": [
            "2711",
            "2710",
            "3102",
            "0805",
            "5201",
        ],  # Gas, petroleum products, fertilizers
        "total_imports_from_outside_musd": 68000,
        "substitution_potential_percent": 15,
    },
    "NGA": {  # Nigeria
        "major_imports": [
            {
                "hs_code": "1001",
                "name_fr": "Blé et méteil",
                "name_en": "Wheat",
                "value_musd": 3500,
                "potential_suppliers": ["EGY", "ETH", "ZAF"],
            },
            {
                "hs_code": "8703",
                "name_fr": "Voitures de tourisme",
                "name_en": "Motor vehicles",
                "value_musd": 2800,
                "potential_suppliers": ["ZAF", "MAR", "EGY"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 2200,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
            {
                "hs_code": "1006",
                "name_fr": "Riz",
                "name_en": "Rice",
                "value_musd": 1800,
                "potential_suppliers": ["EGY", "TZA", "MDG"],
            },
            {
                "hs_code": "2710",
                "name_fr": "Produits raffinés du pétrole",
                "name_en": "Refined petroleum",
                "value_musd": 12000,
                "potential_suppliers": ["DZA", "EGY", "ZAF"],
            },
            {
                "hs_code": "1701",
                "name_fr": "Sucre",
                "name_en": "Sugar",
                "value_musd": 1200,
                "potential_suppliers": ["EGY", "ZAF", "SWZ", "MUS"],
            },
        ],
        "export_strengths": ["2709", "2711", "1801", "4001"],  # Crude oil, gas, cocoa, rubber
        "total_imports_from_outside_musd": 45000,
        "substitution_potential_percent": 20,
    },
    "ZAF": {  # South Africa
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 18000,
                "potential_suppliers": ["NGA", "AGO", "DZA", "LBY", "GNQ"],
            },
            {
                "hs_code": "8703",
                "name_fr": "Voitures de tourisme",
                "name_en": "Motor vehicles",
                "value_musd": 4500,
                "potential_suppliers": ["MAR", "EGY"],
            },
            {
                "hs_code": "8517",
                "name_fr": "Téléphones",
                "name_en": "Telephones",
                "value_musd": 3200,
                "potential_suppliers": ["EGY", "MAR", "TUN"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 2800,
                "potential_suppliers": ["EGY", "MAR", "TUN"],
            },
            {
                "hs_code": "8471",
                "name_fr": "Ordinateurs",
                "name_en": "Computers",
                "value_musd": 2200,
                "potential_suppliers": ["EGY", "MAR"],
            },
        ],
        "export_strengths": [
            "7102",
            "8703",
            "7108",
            "2601",
            "0805",
        ],  # Diamonds, cars, gold, iron ore
        "total_imports_from_outside_musd": 85000,
        "substitution_potential_percent": 12,
    },
    "KEN": {  # Kenya
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 4500,
                "potential_suppliers": ["NGA", "AGO", "SDN", "SSD"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé",
                "name_en": "Wheat",
                "value_musd": 850,
                "potential_suppliers": ["EGY", "ETH", "ZAF"],
            },
            {
                "hs_code": "1511",
                "name_fr": "Huile de palme",
                "name_en": "Palm oil",
                "value_musd": 780,
                "potential_suppliers": ["CIV", "GHA", "CMR"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 650,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
            {
                "hs_code": "1701",
                "name_fr": "Sucre",
                "name_en": "Sugar",
                "value_musd": 580,
                "potential_suppliers": ["EGY", "ZAF", "SWZ", "MUS"],
            },
        ],
        "export_strengths": ["0902", "0603", "0901", "1801"],  # Tea, flowers, coffee
        "total_imports_from_outside_musd": 18000,
        "substitution_potential_percent": 25,
    },
    "CIV": {  # Côte d'Ivoire
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 3800,
                "potential_suppliers": ["NGA", "AGO", "GNQ"],
            },
            {
                "hs_code": "1006",
                "name_fr": "Riz",
                "name_en": "Rice",
                "value_musd": 1200,
                "potential_suppliers": ["EGY", "TZA", "SEN"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 580,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé",
                "name_en": "Wheat",
                "value_musd": 450,
                "potential_suppliers": ["EGY", "ETH", "ZAF"],
            },
        ],
        "export_strengths": ["1801", "0901", "1511", "4001"],  # Cocoa, coffee, palm oil, rubber
        "total_imports_from_outside_musd": 12000,
        "substitution_potential_percent": 28,
    },
    "TUN": {  # Tunisia
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 3200,
                "potential_suppliers": ["DZA", "LBY", "NGA"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé",
                "name_en": "Wheat",
                "value_musd": 980,
                "potential_suppliers": ["EGY", "ETH"],
            },
            {
                "hs_code": "8517",
                "name_fr": "Téléphones",
                "name_en": "Telephones",
                "value_musd": 580,
                "potential_suppliers": ["EGY", "MAR"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 450,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
        ],
        "export_strengths": [
            "1509",
            "8544",
            "6109",
            "0805",
        ],  # Olive oil, electrical cables, textiles
        "total_imports_from_outside_musd": 18000,
        "substitution_potential_percent": 22,
    },
    "ETH": {  # Ethiopia
        "major_imports": [
            {
                "hs_code": "2710",
                "name_fr": "Produits pétroliers raffinés",
                "name_en": "Refined petroleum",
                "value_musd": 4200,
                "potential_suppliers": ["DZA", "EGY", "ZAF"],
            },
            {
                "hs_code": "1001",
                "name_fr": "Blé",
                "name_en": "Wheat",
                "value_musd": 1500,
                "potential_suppliers": ["EGY", "ZAF"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 650,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
            {
                "hs_code": "8703",
                "name_fr": "Voitures",
                "name_en": "Motor vehicles",
                "value_musd": 480,
                "potential_suppliers": ["ZAF", "MAR", "EGY"],
            },
        ],
        "export_strengths": ["0901", "1207", "0713", "0603"],  # Coffee, sesame, legumes, flowers
        "total_imports_from_outside_musd": 15000,
        "substitution_potential_percent": 30,
    },
    "GHA": {  # Ghana
        "major_imports": [
            {
                "hs_code": "2709",
                "name_fr": "Huiles brutes de pétrole",
                "name_en": "Crude petroleum",
                "value_musd": 2800,
                "potential_suppliers": ["NGA", "AGO", "GNQ"],
            },
            {
                "hs_code": "8703",
                "name_fr": "Voitures",
                "name_en": "Motor vehicles",
                "value_musd": 1200,
                "potential_suppliers": ["ZAF", "MAR", "EGY"],
            },
            {
                "hs_code": "1006",
                "name_fr": "Riz",
                "name_en": "Rice",
                "value_musd": 850,
                "potential_suppliers": ["EGY", "TZA", "SEN"],
            },
            {
                "hs_code": "3004",
                "name_fr": "Médicaments",
                "name_en": "Medicaments",
                "value_musd": 520,
                "potential_suppliers": ["EGY", "ZAF", "MAR"],
            },
        ],
        "export_strengths": ["1801", "2709", "7108", "0803"],  # Cocoa, petroleum, gold, bananas
        "total_imports_from_outside_musd": 14000,
        "substitution_potential_percent": 26,
    },
}

# Default profile for countries not explicitly defined
DEFAULT_SUBSTITUTION_PROFILE = {
    "major_imports": [
        {
            "hs_code": "2709",
            "name_fr": "Pétrole brut",
            "name_en": "Crude petroleum",
            "value_musd": 500,
            "potential_suppliers": ["NGA", "AGO", "DZA"],
        },
        {
            "hs_code": "3004",
            "name_fr": "Médicaments",
            "name_en": "Medicaments",
            "value_musd": 200,
            "potential_suppliers": ["EGY", "ZAF", "MAR"],
        },
        {
            "hs_code": "1001",
            "name_fr": "Blé",
            "name_en": "Wheat",
            "value_musd": 150,
            "potential_suppliers": ["EGY", "ZAF"],
        },
        {
            "hs_code": "8703",
            "name_fr": "Véhicules",
            "name_en": "Motor vehicles",
            "value_musd": 100,
            "potential_suppliers": ["ZAF", "MAR"],
        },
    ],
    "export_strengths": [],
    "total_imports_from_outside_musd": 2000,
    "substitution_potential_percent": 20,
}


# African countries with enough trade volume to act as realistic intra-African
# suppliers/markets. Used to build the product->supplier and product->market
# indices from real OEC data with a bounded number of API calls.
MAJOR_AFRICAN_TRADERS = [
    "ZAF",
    "EGY",
    "NGA",
    "MAR",
    "DZA",
    "KEN",
    "ETH",
    "GHA",
    "CIV",
    "TUN",
    "TZA",
    "SEN",
    "CMR",
    "COD",
    "AGO",
    "ZMB",
]


class RealSubstitutionService:
    """
    Service for analyzing trade substitution opportunities.

    Primary path uses real OEC trade flows; the static profiles are only a
    fallback when the API is unreachable (then flagged ``is_estimation: True``).
    """

    def __init__(self):
        self.african_countries = list(AFRICAN_COUNTRIES.keys())
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache

    def _cache_get(self, key: str):
        """Return a cached value if present and not expired, else None."""
        entry = self._cache.get(key)
        if not entry:
            return None
        ts, value = entry
        if (datetime.utcnow() - ts).total_seconds() > self._cache_ttl:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = (datetime.utcnow(), value)

    async def _build_african_export_index(self, year: int) -> Dict[str, List[Dict]]:
        """Index real African exports by HS2 chapter: {chapter: [{iso3, value, ...}]}.

        Fetches each major African exporter's top exports once (in parallel) and
        groups them by HS2 chapter, so per-product supplier lookups need no extra
        API calls. Cached for ``_cache_ttl`` seconds."""
        return await self._build_trader_index(year, kind="export")

    async def _build_african_import_index(self, year: int) -> Dict[str, List[Dict]]:
        """Index real African imports by HS2 chapter: {chapter: [{iso3, value, ...}]}."""
        return await self._build_trader_index(year, kind="import")

    async def _build_trader_index(self, year: int, kind: str) -> Dict[str, List[Dict]]:
        cache_key = f"{kind}_index_{year}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        fetch = (
            real_trade_service.get_oec_exports
            if kind == "export"
            else real_trade_service.get_oec_imports
        )
        tasks = [fetch(iso3, year=year, limit=100) for iso3 in MAJOR_AFRICAN_TRADERS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        index: Dict[str, List[Dict]] = defaultdict(list)
        for iso3, res in zip(MAJOR_AFRICAN_TRADERS, results):
            if isinstance(res, Exception) or not res:
                continue
            for product in res:
                hs_code = product.get("hs_code", "")
                chapter = hs_code[:2]
                if not chapter:
                    continue
                index[chapter].append(
                    {
                        "iso3": iso3,
                        "value": product.get("trade_value", 0),
                        "hs_code": hs_code,
                        "product_name": product.get("product_name", ""),
                    }
                )

        # Only cache a non-empty index (an empty one usually means the API was down)
        if index:
            self._cache_set(cache_key, dict(index))
        return index

    async def find_import_substitution_opportunities(
        self, importer_iso3: str, year: int = 2022, min_value: int = 5000000, lang: str = "fr"
    ) -> Dict:
        """
        Find import substitution opportunities using pre-computed profiles + live OEC data
        OPTIMIZED: Uses cached trade profiles to avoid API timeouts
        """
        importer = importer_iso3.upper()
        if importer not in self.african_countries:
            return {"error": f"Country {importer} not found in AfCFTA"}

        # Check if country has trade data
        if not has_trade_data(importer):
            country_info = AFRICAN_COUNTRIES.get(importer, {})
            return {
                "error": None,
                "no_data": True,
                "message": f"Aucune donnée commerciale disponible pour {country_info.get('name_fr', importer)}",
                "reason": country_info.get(
                    "note", "Données non disponibles dans les bases internationales"
                ),
                "importer": {"iso3": importer, "name": get_country_name(importer, lang)},
                "opportunities": [],
                "summary": {
                    "total_opportunities": 0,
                    "total_substitutable_value": 0,
                    "status": "NO_DATA",
                },
            }

        cache_key = f"import_sub_{importer}_{year}_{min_value}_{lang}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # --- Primary path: real OEC bilateral trade flows ---
        bilateral = await real_trade_service.get_oec_bilateral_from_world(importer, year=year)
        products_outside = (bilateral or {}).get("products_from_outside", [])

        if products_outside:
            export_index = await self._build_african_export_index(year)
            opportunities = []
            total_substitutable = 0

            for product in products_outside:
                import_value = product.get("import_value", 0)
                if import_value < min_value:
                    continue

                hs_code = product.get("hs_code", "")
                chapter = hs_code[:2]

                # Aggregate real African export capacity in the same HS2 chapter
                by_country: Dict[str, float] = defaultdict(float)
                for supplier in export_index.get(chapter, []):
                    if supplier["iso3"] == importer:
                        continue
                    by_country[supplier["iso3"]] += supplier["value"]

                african_suppliers = []
                for iso3, value in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:5]:
                    african_suppliers.append(
                        {
                            "country_iso3": iso3,
                            "country_name": get_country_name(iso3, lang),
                            "export_value": int(value),
                            "share_potential": (
                                round(min(value / import_value * 100, 100.0), 1)
                                if import_value
                                else 0.0
                            ),
                        }
                    )

                total_supply = sum(s["export_value"] for s in african_suppliers)
                # Substitutable value bounded by BOTH real African export capacity
                # AND the product's substitutability coefficient (brand effect,
                # technology gap, after-sales, certification) — a car or phone
                # dollar is not as substitutable as a wheat dollar.
                realistic = realistic_substitution_potential(import_value, total_supply, hs_code)
                substitution_potential = realistic["potential_usd"]

                opportunities.append(
                    {
                        "imported_product": {
                            "hs_code": hs_code,
                            "name": product.get("product_name") or get_product_name(hs_code, lang),
                            "import_value": int(import_value),
                            "current_source": ", ".join(product.get("source_regions", []))
                            or "Hors Afrique",
                        },
                        "african_suppliers": african_suppliers,
                        "substitution_potential": substitution_potential,
                        "substitution_feasibility": realistic["feasibility"],
                        "addressable_value": realistic["addressable_value_usd"],
                        "binding_constraint": realistic["binding_constraint"],
                        "difficulty": self._assess_difficulty(import_value, total_supply),
                    }
                )
                total_substitutable += substitution_potential

            opportunities.sort(key=lambda x: x["substitution_potential"], reverse=True)

            result = {
                "importer": {"iso3": importer, "name": get_country_name(importer, lang)},
                "year": year,
                "analysis_date": datetime.utcnow().isoformat(),
                "data_source": "OEC (Observatory of Economic Complexity) - BACI",
                "summary": {
                    "total_opportunities": len(opportunities),
                    "total_substitutable_value": total_substitutable,
                    "total_imports_from_outside": int((bilateral or {}).get("from_outside", 0)),
                    "africa_share_percent": round((bilateral or {}).get("africa_share", 0), 1),
                    "top_sectors": self._identify_top_sectors(opportunities, lang),
                },
                "opportunities": opportunities,
                "sources": ["OEC BACI", "UN Comtrade"],
                "is_estimation": False,
            }
            self._cache_set(cache_key, result)
            return result

        # --- Fallback path: curated static profile (OEC unreachable) ---
        logger.warning(
            "OEC unavailable for import substitution of %s; using static fallback profile",
            importer,
        )
        return self._static_import_fallback(importer, year, min_value, lang)

    def _static_import_fallback(self, importer: str, year: int, min_value: int, lang: str) -> Dict:
        """Deterministic fallback from curated profiles when OEC is unreachable.

        Values are NOT randomised: per-supplier capacity is an even split of a
        conservative 30% substitution rate, and the response is flagged as an
        estimation so the UI can label it accordingly."""
        profile = COUNTRY_SUBSTITUTION_PROFILES.get(importer, DEFAULT_SUBSTITUTION_PROFILE)
        name_key = f"name_{lang}"
        substitution_rate = 0.30

        opportunities = []
        total_substitutable = 0
        for product in profile["major_imports"]:
            import_value = product["value_musd"] * 1_000_000
            if import_value < min_value:
                continue

            suppliers = product["potential_suppliers"]
            n = max(len(suppliers), 1)
            per_supplier = int(import_value * substitution_rate / n)
            african_suppliers = [
                {
                    "country_iso3": supplier_iso,
                    "country_name": get_country_name(supplier_iso, lang),
                    "export_value": per_supplier,
                    "share_potential": round(substitution_rate * 100 / n, 1),
                }
                for supplier_iso in suppliers
            ]

            # Même discipline que le chemin OEC réel : le taux forfaitaire de 30 %
            # est en plus borné par la substituabilité du produit (effet marque...).
            realistic = realistic_substitution_potential(
                import_value, import_value * substitution_rate, product["hs_code"]
            )
            substitution_potential = realistic["potential_usd"]
            opportunities.append(
                {
                    "imported_product": {
                        "hs_code": product["hs_code"],
                        "name": product.get(name_key, product.get("name_en", ""))
                        or get_product_name(product["hs_code"], lang),
                        "import_value": import_value,
                        "current_source": "Hors Afrique",
                    },
                    "african_suppliers": african_suppliers,
                    "substitution_potential": substitution_potential,
                    "substitution_feasibility": realistic["feasibility"],
                    "addressable_value": realistic["addressable_value_usd"],
                    "binding_constraint": realistic["binding_constraint"],
                    "difficulty": self._assess_difficulty(
                        import_value, sum(s["export_value"] for s in african_suppliers)
                    ),
                }
            )
            total_substitutable += substitution_potential

        opportunities.sort(key=lambda x: x["substitution_potential"], reverse=True)

        return {
            "importer": {"iso3": importer, "name": get_country_name(importer, lang)},
            "year": year,
            "analysis_date": datetime.utcnow().isoformat(),
            "data_source": "Profil statique (OEC indisponible)",
            "summary": {
                "total_opportunities": len(opportunities),
                "total_substitutable_value": total_substitutable,
                "total_imports_from_outside": profile["total_imports_from_outside_musd"]
                * 1_000_000,
                "potential_savings_percent": profile["substitution_potential_percent"],
                "top_sectors": self._identify_top_sectors(opportunities, lang),
            },
            "opportunities": opportunities,
            "sources": ["Profils ZLECAf curés (repli)"],
            "is_estimation": True,
        }

    async def find_export_opportunities(
        self, exporter_iso3: str, year: int = 2022, min_market_size: int = 5000000, lang: str = "fr"
    ) -> Dict:
        """
        Find export opportunities for a country
        OPTIMIZED: Uses pre-computed profiles
        """
        exporter = exporter_iso3.upper()
        if exporter not in self.african_countries:
            return {"error": f"Country {exporter} not found in AfCFTA"}

        # Check if country has trade data
        if not has_trade_data(exporter):
            country_info = AFRICAN_COUNTRIES.get(exporter, {})
            return {
                "error": None,
                "no_data": True,
                "message": f"Aucune donnée commerciale disponible pour {country_info.get('name_fr', exporter)}",
                "reason": country_info.get(
                    "note", "Données non disponibles dans les bases internationales"
                ),
                "exporter": {"iso3": exporter, "name": get_country_name(exporter, lang)},
                "opportunities": [],
                "summary": {
                    "total_opportunities": 0,
                    "total_market_potential": 0,
                    "status": "NO_DATA",
                },
            }

        cache_key = f"export_opp_{exporter}_{year}_{min_market_size}_{lang}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # --- Primary path: real OEC export flows + real African import markets ---
        exporter_exports = await real_trade_service.get_oec_exports(exporter, year=year, limit=100)

        if exporter_exports:
            import_index = await self._build_african_import_index(year)

            # Real export value of the exporter aggregated by HS2 chapter
            export_value_by_chapter: Dict[str, float] = defaultdict(float)
            product_name_by_chapter: Dict[str, str] = {}
            for product in exporter_exports:
                hs_code = product.get("hs_code", "")
                chapter = hs_code[:2]
                if not chapter:
                    continue
                export_value_by_chapter[chapter] += product.get("trade_value", 0)
                product_name_by_chapter.setdefault(
                    chapter, product.get("product_name", "") or get_product_name(hs_code, lang)
                )

            opportunities = []
            total_market_potential = 0

            # Keep the exporter's strongest chapters
            top_chapters = sorted(
                export_value_by_chapter.items(), key=lambda x: x[1], reverse=True
            )[:10]

            for chapter, exporter_export_value in top_chapters:
                potential_markets = []
                for market in import_index.get(chapter, []):
                    if market["iso3"] == exporter:
                        continue
                    market_size = market["value"]
                    if market_size < min_market_size:
                        continue
                    # Capture potential is bounded by the exporter's real capacity
                    capture = round(min(exporter_export_value, market_size) / market_size, 2)
                    potential_markets.append(
                        {
                            "country_iso3": market["iso3"],
                            "country_name": get_country_name(market["iso3"], lang),
                            "market_size": int(market_size),
                            "capture_potential": capture,
                        }
                    )

                if not potential_markets:
                    continue

                potential_markets.sort(key=lambda m: m["market_size"], reverse=True)
                potential_markets = potential_markets[:5]
                total_potential = sum(
                    m["market_size"] * m["capture_potential"] for m in potential_markets
                )

                opportunities.append(
                    {
                        "export_product": {
                            "hs_code": chapter,
                            "name": product_name_by_chapter.get(chapter, f"Chapitre {chapter}"),
                        },
                        "potential_markets": potential_markets,
                        "total_market_potential": int(total_potential),
                        "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
                    }
                )
                total_market_potential += total_potential

            opportunities.sort(key=lambda x: x["total_market_potential"], reverse=True)

            result = {
                "exporter": {"iso3": exporter, "name": get_country_name(exporter, lang)},
                "year": year,
                "analysis_date": datetime.utcnow().isoformat(),
                "data_source": "OEC (Observatory of Economic Complexity) - BACI",
                "summary": {
                    "total_opportunities": len(opportunities),
                    "total_market_potential": int(total_market_potential),
                    "export_strengths": len(top_chapters),
                },
                "opportunities": opportunities,
                "sources": ["OEC BACI", "UN Comtrade"],
                "is_estimation": False,
            }
            self._cache_set(cache_key, result)
            return result

        # --- Fallback path: curated static profile (OEC unreachable) ---
        logger.warning(
            "OEC unavailable for export opportunities of %s; using static fallback profile",
            exporter,
        )
        return self._static_export_fallback(exporter, year, min_market_size, lang)

    def _static_export_fallback(
        self, exporter: str, year: int, min_market_size: int, lang: str
    ) -> Dict:
        """Deterministic fallback from curated profiles when OEC is unreachable."""
        profile = COUNTRY_SUBSTITUTION_PROFILES.get(exporter, DEFAULT_SUBSTITUTION_PROFILE)
        # Conservative, fixed capture rate (no randomisation)
        capture_rate = 0.20

        opportunities = []
        total_market_potential = 0
        for hs_code in profile.get("export_strengths", []):
            product_name = get_product_name(hs_code, lang)
            potential_markets = []
            for country_iso, country_profile in COUNTRY_SUBSTITUTION_PROFILES.items():
                if country_iso == exporter:
                    continue
                for imp in country_profile.get("major_imports", []):
                    if imp["hs_code"][:2] == hs_code[:2]:
                        market_size = imp["value_musd"] * 1_000_000
                        if market_size >= min_market_size:
                            potential_markets.append(
                                {
                                    "country_iso3": country_iso,
                                    "country_name": get_country_name(country_iso, lang),
                                    "market_size": market_size,
                                    "capture_potential": capture_rate,
                                }
                            )

            if not potential_markets:
                continue

            potential_markets = potential_markets[:5]
            total_potential = sum(
                m["market_size"] * m["capture_potential"] for m in potential_markets
            )
            opportunities.append(
                {
                    "export_product": {"hs_code": hs_code, "name": product_name},
                    "potential_markets": potential_markets,
                    "total_market_potential": int(total_potential),
                    "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
                }
            )
            total_market_potential += total_potential

        opportunities.sort(key=lambda x: x["total_market_potential"], reverse=True)

        return {
            "exporter": {"iso3": exporter, "name": get_country_name(exporter, lang)},
            "year": year,
            "analysis_date": datetime.utcnow().isoformat(),
            "data_source": "Profil statique (OEC indisponible)",
            "summary": {
                "total_opportunities": len(opportunities),
                "total_market_potential": int(total_market_potential),
                "export_strengths": len(profile.get("export_strengths", [])),
            },
            "opportunities": opportunities,
            "sources": ["Profils ZLECAf curés (repli)"],
            "is_estimation": True,
        }

    def _assess_difficulty(self, import_value: float, african_capacity: float) -> str:
        """Assess substitution difficulty based on value and capacity"""
        if african_capacity >= import_value * 0.5:
            return "Facile"
        elif african_capacity >= import_value * 0.25:
            return "Modéré"
        elif african_capacity >= import_value * 0.1:
            return "Difficile"
        else:
            return "Très difficile"

    def _identify_top_sectors(self, opportunities: List[Dict], lang: str) -> List[Dict]:
        """Identify top sectors from opportunities"""
        sector_values = defaultdict(float)
        sector_counts = defaultdict(int)

        sector_names = {
            "27": {"fr": "Combustibles minéraux, huiles", "en": "Mineral fuels, oils"},
            "87": {"fr": "Véhicules automobiles", "en": "Motor vehicles"},
            "10": {"fr": "Céréales", "en": "Cereals"},
            "30": {"fr": "Produits pharmaceutiques", "en": "Pharmaceuticals"},
            "85": {"fr": "Machines et appareils électriques", "en": "Electrical machinery"},
            "84": {"fr": "Machines et appareils mécaniques", "en": "Mechanical machinery"},
            "17": {"fr": "Sucres et sucreries", "en": "Sugars and confectionery"},
            "15": {"fr": "Graisses et huiles", "en": "Animal or vegetable fats"},
            "73": {"fr": "Ouvrages en fer ou acier", "en": "Articles of iron or steel"},
            "04": {"fr": "Produits laitiers, œufs, miel", "en": "Dairy products, eggs, honey"},
        }

        for opp in opportunities:
            hs_code = opp["imported_product"]["hs_code"]
            chapter = hs_code[:2]
            value = opp["substitution_potential"]

            sector_values[chapter] += value
            sector_counts[chapter] += 1

        top_sectors = []
        for chapter, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)[:5]:
            names = sector_names.get(
                chapter, {"fr": f"Chapitre {chapter}", "en": f"Chapter {chapter}"}
            )
            top_sectors.append(
                {
                    "chapter": chapter,
                    "name": names.get(lang, names["en"]),
                    "total_value": int(value),
                    "opportunity_count": sector_counts[chapter],
                }
            )

        return top_sectors


# Singleton instance
real_substitution_service = RealSubstitutionService()
