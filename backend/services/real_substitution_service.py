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

from services import cache_service, production_capacity_service
from services.real_trade_data_service import (
    AFRICAN_COUNTRIES,
    get_country_name,
    get_product_name,
    has_trade_data,
    real_trade_service,
)
from services.substitution_feasibility_service import (
    realistic_substitution_potential,
    substitutability_for_hs,
)

try:
    # Référentiel complet des 97 chapitres SH (FR/EN) — le même que la base HS6.
    from etl.hs_codes_data import HS_CHAPTERS
except ImportError:  # pragma: no cover - le référentiel fait partie du dépôt
    HS_CHAPTERS = {}

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

    # Version de SCHÉMA des réponses mises en cache. À incrémenter à CHAQUE
    # évolution de la forme du payload (nouveau champ, granularité...) : le
    # cache est persistant (Redis/disque, TTL 24h) et SURVIT AUX DÉPLOIEMENTS —
    # sans ce versionnage, une release qui enrichit la réponse (ex. ajout de
    # substitution_feasibility, prix moyens, niveau produit) continue de servir
    # les anciens payloads pendant des heures, et les nouveautés semblent
    # « non implémentées » à l'écran alors que le code est bien déployé
    # (constaté en production après les PR #281/#282).
    # v4 : production vérifiée (FAOSTAT/UNIDO/USGS) sur chaque opportunité +
    # bloc summary.analysis + top_sectors sur les exports.
    # v5 : correction du tri OEC (Trade Value.desc). Les index import/export
    # d'avant le correctif étaient tronqués dans l'ordre du code SH — ils
    # excluaient les hydrocarbures/machines/véhicules et rendaient l'analyse
    # d'export vide pour les pays diversifiés (ex : Algérie). Bump indispensable
    # pour purger ces index tronqués mis en cache sur les instances déployées.
    _CACHE_SCHEMA_VERSION = 5

    @staticmethod
    def _verified_production(hs_code: str, memo: Dict[str, Optional[Dict]]) -> Optional[Dict]:
        """
        Croisement avec le référentiel de production RÉELLE (FAOSTAT / USGS /
        UNIDO — données locales, aucun appel réseau) : qui produit effectivement
        ce produit en Afrique, en volume physique, dernière année disponible.

        C'est la preuve matérielle qui manque à la seule lecture des flux
        commerciaux : un « fournisseur africain potentiel » identifié via ses
        exports est bien plus crédible quand le référentiel confirme une
        production continentale mesurée. ``memo`` déduplique les appels — de
        nombreux SH6 d'un même rapport retombent sur la même commodité.
        """
        if hs_code in memo:
            return memo[hs_code]
        compact: Optional[Dict] = None
        try:
            prod = production_capacity_service.get_continental_producers(hs_code)
            if prod.get("available"):
                compact = {
                    "commodity": prod.get("commodity"),
                    "measure": prod.get("measure"),
                    "unit": prod.get("unit"),
                    "year": prod.get("year"),
                    "institution": (prod.get("source") or {}).get("institution"),
                    "continental_total": prod.get("continental_total"),
                    "top_producers": (prod.get("top_producers") or [])[:3],
                    "coverage_caveat": prod.get("coverage_caveat"),
                    "commodity_caveat": prod.get("commodity_caveat"),
                }
        except Exception:  # noqa: BLE001 - enrichissement, jamais bloquant
            logger.warning("verified_production lookup failed for %s", hs_code, exc_info=True)
        memo[hs_code] = compact
        return compact

    @staticmethod
    def _build_product_hierarchy(
        opportunities: List[Dict], product_key: str, value_key: str, lang: str, top_n: int = 5
    ) -> List[Dict]:
        """
        Drill-down chapitre (SH2) -> position (SH4) -> produit (SH6), pour
        affiner l'analyse par étapes plutôt que de tout aplatir au chapitre :
        un utilisateur repère d'abord le CHAPITRE porteur (ex. 87 véhicules),
        puis affine sur la POSITION SH4 (8703 tourisme vs 8708 pièces), puis
        sur le CODE SH6 exact — la granularité où se prend la décision
        d'achat ou de sourcing.

        Aucun nom n'est inventé au niveau SH4 : le libellé retenu est celui du
        produit SH6 réel de plus forte valeur dans ce groupe (donnée réelle,
        jamais une description fabriquée pour le niveau intermédiaire).
        """
        chapters: Dict[str, Dict] = {}
        for opp in opportunities:
            product = opp.get(product_key) or {}
            hs_code = "".join(ch for ch in str(product.get("hs_code") or "") if ch.isdigit())
            if len(hs_code) < 2:
                continue
            value = int(opp.get(value_key) or 0)
            chapter_code = hs_code[:2]
            hs4_code = hs_code[:4] if len(hs_code) >= 4 else hs_code

            chapter_names = HS_CHAPTERS.get(chapter_code, {})
            chapter = chapters.setdefault(
                chapter_code,
                {
                    "chapter": chapter_code,
                    "name": chapter_names.get(lang, chapter_names.get("en", f"SH {chapter_code}")),
                    "total_value": 0,
                    "opportunity_count": 0,
                    "_hs4": {},
                },
            )
            chapter["total_value"] += value
            chapter["opportunity_count"] += 1

            hs4 = chapter["_hs4"].setdefault(
                hs4_code, {"hs4_code": hs4_code, "total_value": 0, "_hs6": []}
            )
            hs4["total_value"] += value
            hs4["_hs6"].append(
                {
                    "hs_code": product.get("hs_code"),
                    "name": product.get("name"),
                    "value": value,
                    "feasibility_coefficient": (opp.get("substitution_feasibility") or {}).get(
                        "coefficient"
                    ),
                    "binding_constraint": opp.get("binding_constraint"),
                }
            )

        result = []
        for chapter in sorted(chapters.values(), key=lambda c: c["total_value"], reverse=True)[
            :top_n
        ]:
            hs4_list = sorted(
                chapter["_hs4"].values(), key=lambda h: h["total_value"], reverse=True
            )[:top_n]
            hs4_out = []
            for hs4 in hs4_list:
                hs6_sorted = sorted(hs4["_hs6"], key=lambda p: p["value"], reverse=True)
                # Libellé de la position SH4 = nom du produit SH6 réel dominant
                # de ce groupe (pas de nom inventé pour le niveau intermédiaire).
                representative_name = hs6_sorted[0]["name"] if hs6_sorted else None
                hs4_out.append(
                    {
                        "hs4_code": hs4["hs4_code"],
                        "representative_name": representative_name,
                        "total_value": hs4["total_value"],
                        "products": hs6_sorted[:top_n],
                    }
                )
            result.append(
                {
                    "chapter": chapter["chapter"],
                    "name": chapter["name"],
                    "total_value": chapter["total_value"],
                    "opportunity_count": chapter["opportunity_count"],
                    "hs4": hs4_out,
                }
            )
        return result

    @staticmethod
    def _build_analysis_block(opportunities: List[Dict]) -> Dict:
        """
        Lecture transversale du portefeuille d'opportunités : coefficient de
        substituabilité moyen (pondéré par la valeur en jeu), répartition des
        difficultés et des facteurs limitants, couverture du référentiel
        production. C'est l'étage d'ANALYSE au-dessus de la liste brute.
        """
        if not opportunities:
            return {}
        difficulty_dist: Dict[str, int] = defaultdict(int)
        constraint_dist: Dict[str, int] = defaultdict(int)
        weighted_coef = 0.0
        weight = 0.0
        verified = 0
        for opp in opportunities:
            if opp.get("difficulty"):
                difficulty_dist[opp["difficulty"]] += 1
            if opp.get("binding_constraint"):
                constraint_dist[opp["binding_constraint"]] += 1
            if opp.get("verified_production"):
                verified += 1
            coef = (opp.get("substitution_feasibility") or {}).get("coefficient")
            value = (opp.get("imported_product") or {}).get("import_value") or opp.get(
                "total_market_potential"
            )
            if coef is not None and value:
                weighted_coef += coef * value
                weight += value
        return {
            "avg_feasibility_coefficient": (round(weighted_coef / weight, 2) if weight else None),
            "difficulty_distribution": dict(difficulty_dist),
            "binding_constraint_distribution": dict(constraint_dist),
            "verified_production_count": verified,
        }

    @classmethod
    def _full_key(cls, key: str) -> str:
        return cache_service.generate_cache_key(
            "substitution", f"v{cls._CACHE_SCHEMA_VERSION}", key
        )

    def _cache_get(self, key: str):
        """
        Return a cached value if present and not expired, else None.

        Uses the SHARED cache_service (Redis, or in-memory + disk fallback)
        instead of a private per-instance dict: a private cache is wiped on
        every process restart AND duplicated across every uvicorn worker, so
        the expensive multi-country trader index (16 parallel OEC calls) had
        to be rebuilt from scratch far more often than necessary — needlessly
        multiplying OEC traffic and exposure to its rate limits/outages.
        """
        return cache_service.cache_get(self._full_key(key))

    def _cache_get_stale(self, key: str):
        """Stale-on-error read: serve the last known value even if expired."""
        return cache_service.cache_get_stale(self._full_key(key))

    def _cache_set(self, key: str, value: Any, ttl_type: str = "oec_data") -> None:
        cache_service.cache_set(self._full_key(key), value, ttl_type)

    async def _build_african_export_index(
        self, year: int, hs_level: str = "HS4"
    ) -> Dict[str, List[Dict]]:
        """Index real African exports by HS code level: {hs_code: [{iso3, value, ...}]}.

        Fetches each major African exporter's top exports once (in parallel) and
        groups them by the specified HS level (HS2, HS4, HS6).
        Cached for ``_cache_ttl`` seconds."""
        return await self._build_trader_index(year, kind="export", hs_level=hs_level)

    async def _build_african_import_index(
        self, year: int, hs_level: str = "HS4", limit: int = 100
    ) -> Dict[str, List[Dict]]:
        """Index real African imports by HS code level: {hs_code: [{iso3, value, ...}]}.

        ``limit`` = profondeur du top-N par pays (par valeur). Le défaut 100 sert
        la substitution d'imports (gros postes) ; le moteur de flux stratégiques
        demande une profondeur supérieure pour capter la demande de produits
        transformés de milieu de gamme (peintures, cosmétiques, détergents…) qui
        se classent au-delà du top-100 mais restent des débouchés réels.
        """
        return await self._build_trader_index(year, kind="import", hs_level=hs_level, limit=limit)

    async def _build_trader_index(
        self, year: int, kind: str, hs_level: str = "HS4", limit: int = 100
    ) -> Dict[str, List[Dict]]:
        cache_key = f"{kind}_index_{year}_{hs_level}_{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        fetch = (
            real_trade_service.get_oec_exports
            if kind == "export"
            else real_trade_service.get_oec_imports
        )
        tasks = [
            fetch(iso3, year=year, limit=limit, hs_level=hs_level) for iso3 in MAJOR_AFRICAN_TRADERS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        index: Dict[str, List[Dict]] = defaultdict(list)
        for iso3, res in zip(MAJOR_AFRICAN_TRADERS, results):
            if isinstance(res, Exception) or not res:
                continue
            for product in res:
                hs_code = product.get("hs_code", "")
                if not hs_code:
                    continue
                # Use the full HS code as the index key
                index[hs_code].append(
                    {
                        "iso3": iso3,
                        "value": product.get("trade_value", 0),
                        # Volume BACI (poids net, tonnes) : permet les valeurs
                        # unitaires ($/t) pour le positionnement prix.
                        "quantity": product.get("quantity", 0) or 0,
                        "hs_code": hs_code,
                        "product_name": product.get("product_name", ""),
                    }
                )

        # Only cache a non-empty index (an empty one usually means the API was down).
        # 24h TTL ("oec_index"): this index is expensive to rebuild (up to 16
        # parallel OEC calls) and the underlying annual trade data barely moves
        # day to day — no reason to refetch hourly.
        if index:
            self._cache_set(cache_key, dict(index), ttl_type="oec_index")
            return index

        # Empty result (OEC down/rate-limited for this batch): serve the last
        # known-good index rather than silently degrading every per-product
        # supplier lookup to "no African suppliers found" for this call.
        stale = self._cache_get_stale(cache_key)
        if stale is not None:
            logger.warning(
                "OEC trader index (%s, %s, %s) unavailable — serving stale index",
                kind,
                year,
                hs_level,
            )
            return stale
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
        bilateral = await real_trade_service.get_oec_bilateral_from_world(
            importer, year=year, hs_level="HS6"
        )
        products_outside = (bilateral or {}).get("products_from_outside", [])

        if products_outside:
            export_index = await self._build_african_export_index(year, hs_level="HS6")
            opportunities = []
            total_substitutable = 0
            production_memo: Dict[str, Optional[Dict]] = {}

            for product in products_outside:
                import_value = product.get("import_value", 0)
                if import_value < min_value:
                    continue

                hs_code = product.get("hs_code", "")

                # For HS6, try exact match first, then fallback to HS4 prefix match
                by_country: Dict[str, float] = defaultdict(float)
                hs4_code = hs_code[:4] if len(hs_code) >= 4 else hs_code

                # Look for exact HS6 matches in export index
                exact_matches = export_index.get(hs_code, [])
                if exact_matches:
                    for supplier in exact_matches:
                        if supplier["iso3"] == importer:
                            continue
                        by_country[supplier["iso3"]] += supplier["value"]
                else:
                    # Fallback to HS4 prefix matches if no exact HS6 data available
                    # Group all exports by HS4 prefix
                    for export_hs_key, suppliers_list in export_index.items():
                        if len(export_hs_key) >= 4 and export_hs_key[:4] == hs4_code:
                            for supplier in suppliers_list:
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
                        # Production africaine RÉELLE (FAOSTAT/UNIDO/USGS) du produit :
                        # la preuve matérielle derrière les fournisseurs potentiels.
                        "verified_production": self._verified_production(hs_code, production_memo),
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
                    # Drill-down chapitre (SH2) -> position (SH4) -> produit (SH6).
                    "product_hierarchy": self._build_product_hierarchy(
                        opportunities, "imported_product", "substitution_potential", lang
                    ),
                    "analysis": self._build_analysis_block(opportunities),
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
        production_memo: Dict[str, Optional[Dict]] = {}
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
                    "verified_production": self._verified_production(
                        product["hs_code"], production_memo
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
                "product_hierarchy": self._build_product_hierarchy(
                    opportunities, "imported_product", "substitution_potential", lang
                ),
                "analysis": self._build_analysis_block(opportunities),
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
        exporter_exports = await real_trade_service.get_oec_exports(
            exporter, year=year, limit=100, hs_level="HS6"
        )

        if exporter_exports:
            import_index = await self._build_african_import_index(year, hs_level="HS6")

            # Forces d'export au niveau PRODUIT (SH6), spécifique au code SH exact :
            # un producteur étudie ses opportunités produit par produit — vendre des
            # plantains (SH6 080310) n'est pas vendre des bananes fraîches autres que
            # plantains (SH6 080390), et la granularité SH6 permet au producteur
            # d'identifier exactement où exporter son produit précis.
            exporter_products: Dict[str, Dict] = {}
            for product in exporter_exports:
                hs_code = product.get("hs_code", "")
                if not hs_code:
                    continue
                rec = exporter_products.setdefault(
                    hs_code,
                    {
                        "value": 0.0,
                        "quantity": 0.0,
                        "name": product.get("product_name", "") or get_product_name(hs_code, lang),
                    },
                )
                rec["value"] += product.get("trade_value", 0) or 0
                rec["quantity"] += product.get("quantity", 0) or 0

            opportunities = []
            total_market_potential = 0
            production_memo: Dict[str, Optional[Dict]] = {}

            # Keep the exporter's strongest products
            top_products = sorted(
                exporter_products.items(), key=lambda x: x[1]["value"], reverse=True
            )[:10]

            for hs6, export_rec in top_products:
                exporter_export_value = export_rec["value"]
                # Prix moyen à l'export ($/t, valeur unitaire BACI) : la donnée
                # dont l'exportateur a besoin pour se positionner face au prix
                # moyen que le marché cible paie déjà à ses fournisseurs actuels.
                exporter_price = (
                    exporter_export_value / export_rec["quantity"]
                    if export_rec["quantity"] > 0
                    else None
                )
                # Même discipline que la substitution d'imports : la part
                # adressable d'un marché est bornée par le coefficient de
                # substituabilité du produit (résolu au SH4 prefix du SH6, ex :
                # 0803 → 0,9 pour les bananes), pas seulement par la capacité d'export.
                hs4_prefix = hs6[:4] if len(hs6) >= 4 else hs6
                feasibility = substitutability_for_hs(hs4_prefix)
                coef = feasibility["coefficient"]

                # Marchés = pays africains important CE produit (correspondance
                # SH6 exacte). Repli HS4 uniquement si aucun marché exact
                # (le produit n'apparaît dans le top-imports d'aucun pays), et
                # alors dit explicitement — un marché "HS4" n'est pas un marché
                # pour le SH6 spécifique.
                exact = [m for m in import_index.get(hs6, []) if m["iso3"] != exporter]
                market_match_level = "hs6"
                pool = exact
                if not pool:
                    market_match_level = "hs4"
                    # Group all imports by HS4 prefix for this product
                    by_country: Dict[str, Dict] = {}
                    for hs_key, imports_list in import_index.items():
                        # Check if this HS key matches the HS4 prefix
                        if len(hs_key) >= 4 and hs_key[:4] == hs4_prefix:
                            for m in imports_list:
                                if m["iso3"] == exporter:
                                    continue
                                agg = by_country.setdefault(
                                    m["iso3"], {"value": 0.0, "quantity": 0.0}
                                )
                                agg["value"] += m["value"]
                                agg["quantity"] += m.get("quantity", 0) or 0
                    pool = [
                        {"iso3": iso, "value": a["value"], "quantity": a["quantity"]}
                        for iso, a in by_country.items()
                    ]

                potential_markets = []
                for market in pool:
                    market_size = market["value"]
                    if market_size < min_market_size:
                        continue
                    addressable = market_size * coef
                    # Capture bounded by BOTH the exporter's real capacity and the
                    # realistically addressable share of the market.
                    capture = round(min(exporter_export_value, addressable) / market_size, 2)

                    # Positionnement prix : valeur unitaire du marché ($/t) vs
                    # prix moyen d'export du pays — calculable seulement quand
                    # les deux volumes BACI sont présents ET que le marché
                    # correspond EXACTEMENT au produit (hs6). En repli HS4,
                    # market_price est une moyenne mélangeant plusieurs
                    # produits différents du même HS4 — le comparer au
                    # prix d'export d'UN produit précis serait trompeur (et
                    # afficherait un chip prix à côté de l'avertissement
                    # "marché estimé au niveau HS4", contradictoire).
                    market_qty = market.get("quantity", 0) or 0
                    market_price = market_size / market_qty if market_qty > 0 else None
                    price_positioning = None
                    if market_match_level == "hs6" and exporter_price and market_price:
                        ratio = exporter_price / market_price
                        price_positioning = {
                            "exporter_avg_price_usd_per_tonne": round(exporter_price, 1),
                            "market_avg_price_usd_per_tonne": round(market_price, 1),
                            "price_ratio": round(ratio, 2),
                            "price_delta_pct": round((ratio - 1) * 100, 1),
                            "positioning": (
                                "compétitif"
                                if ratio <= 0.95
                                else "aligné" if ratio <= 1.15 else "premium"
                            ),
                        }

                    potential_markets.append(
                        {
                            "country_iso3": market["iso3"],
                            "country_name": get_country_name(market["iso3"], lang),
                            "market_size": int(market_size),
                            "addressable_market_size": int(addressable),
                            "capture_potential": capture,
                            "price_positioning": price_positioning,
                        }
                    )

                if not potential_markets:
                    continue

                potential_markets.sort(key=lambda m: m["market_size"], reverse=True)
                potential_markets = potential_markets[:5]
                total_potential = sum(
                    m["market_size"] * m["capture_potential"] for m in potential_markets
                )
                total_addressable = sum(m["addressable_market_size"] for m in potential_markets)

                opportunities.append(
                    {
                        "export_product": {
                            "hs_code": hs6,
                            "name": export_rec["name"] or f"SH {hs6}",
                        },
                        "exporter_avg_price_usd_per_tonne": (
                            round(exporter_price, 1) if exporter_price else None
                        ),
                        "market_match_level": market_match_level,
                        "potential_markets": potential_markets,
                        "total_market_potential": int(total_potential),
                        "substitution_feasibility": feasibility,
                        "binding_constraint": (
                            "capacité exportateur"
                            if exporter_export_value < total_addressable
                            else "substituabilité"
                        ),
                        "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
                        # Production africaine RÉELLE (FAOSTAT/UNIDO/USGS) : preuve
                        # matérielle de la capacité d'export au-delà des seuls flux OEC.
                        "verified_production": self._verified_production(hs6, production_memo),
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
                    "export_strengths": len(top_products),
                    "top_sectors": self._identify_top_sectors(
                        opportunities, lang, "export_product", "total_market_potential"
                    ),
                    # Drill-down chapitre (SH2) -> position (SH4) -> produit (SH6).
                    "product_hierarchy": self._build_product_hierarchy(
                        opportunities, "export_product", "total_market_potential", lang
                    ),
                    "analysis": self._build_analysis_block(opportunities),
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
        production_memo: Dict[str, Optional[Dict]] = {}
        for hs_code in profile.get("export_strengths", []):
            product_name = get_product_name(hs_code, lang)
            # Même discipline que le chemin OEC réel : le taux de capture
            # forfaitaire est en plus plafonné par la substituabilité du produit
            # (un taux de capture ne peut pas dépasser la part adressable).
            feasibility = substitutability_for_hs(hs_code)
            effective_capture = min(capture_rate, feasibility["coefficient"])
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
                                    "addressable_market_size": int(
                                        market_size * feasibility["coefficient"]
                                    ),
                                    "capture_potential": effective_capture,
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
                    "substitution_feasibility": feasibility,
                    "binding_constraint": (
                        "substituabilité"
                        if feasibility["coefficient"] < capture_rate
                        else "capacité exportateur"
                    ),
                    "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
                    "verified_production": self._verified_production(hs_code, production_memo),
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
                "top_sectors": self._identify_top_sectors(
                    opportunities, lang, "export_product", "total_market_potential"
                ),
                "product_hierarchy": self._build_product_hierarchy(
                    opportunities, "export_product", "total_market_potential", lang
                ),
                "analysis": self._build_analysis_block(opportunities),
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

    def _identify_top_sectors(
        self,
        opportunities: List[Dict],
        lang: str,
        product_key: str = "imported_product",
        value_key: str = "substitution_potential",
    ) -> List[Dict]:
        """
        Regroupe les opportunités par CHAPITRE SH (2 premiers chiffres) avec le
        référentiel COMPLET des 97 chapitres (etl.hs_codes_data.HS_CHAPTERS) —
        et non plus une table de 10 chapitres codée en dur qui affichait
        « Chapitre XX » générique dès qu'un produit sortait de cette liste.
        """
        sector_values = defaultdict(float)
        sector_counts = defaultdict(int)

        for opp in opportunities:
            hs_code = (opp.get(product_key) or {}).get("hs_code") or ""
            if len(hs_code) < 2:
                continue
            chapter = hs_code[:2]
            value = opp.get(value_key) or 0

            sector_values[chapter] += value
            sector_counts[chapter] += 1

        top_sectors = []
        for chapter, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)[:5]:
            names = HS_CHAPTERS.get(chapter, {})
            top_sectors.append(
                {
                    "chapter": chapter,
                    "name": names.get(lang, names.get("en", f"SH {chapter}")),
                    "total_value": int(value),
                    "opportunity_count": sector_counts[chapter],
                }
            )

        return top_sectors


# Singleton instance
real_substitution_service = RealSubstitutionService()
