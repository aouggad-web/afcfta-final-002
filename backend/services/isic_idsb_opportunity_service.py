"""
ISIC4 & IDSB Industrial Database Opportunity Enhancement Service
=================================================================

This service enriches trade opportunities with detailed ISIC4 (Rev.4) sector
classifications and industrial database information (IDSB), providing:

1. Sector-level opportunity assessment using ISIC4 divisions
2. Industrial base strength indicators per country
3. Substitution potential across sectoral chains
4. Competitiveness benchmarking within ISIC4 classes
5. Transformation strategy mapping (input → process → output)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── ISIC Rev.4 Division Classification ──────────────────────────────────────

ISIC4_DIVISIONS: Dict[str, Dict[str, str]] = {
    "01": {"code": "01", "label_fr": "Culture et élevage", "label_en": "Crop and animal production"},
    "02": {"code": "02", "label_fr": "Sylviculture", "label_en": "Forestry"},
    "03": {"code": "03", "label_fr": "Pêche et aquaculture", "label_en": "Fishing and aquaculture"},
    "05": {"code": "05", "label_fr": "Extraction de charbon", "label_en": "Coal extraction"},
    "06": {"code": "06", "label_fr": "Extraction de pétrole et gaz", "label_en": "Oil and gas extraction"},
    "07": {"code": "07", "label_fr": "Extraction de minéraux", "label_en": "Mineral extraction"},
    "08": {"code": "08", "label_fr": "Exploitation de carrières", "label_en": "Quarrying"},
    "09": {"code": "09", "label_fr": "Services de soutien aux mines", "label_en": "Mining support services"},
    "10": {"code": "10", "label_fr": "Industries alimentaires", "label_en": "Food production"},
    "11": {"code": "11", "label_fr": "Boissons", "label_en": "Beverage production"},
    "12": {"code": "12", "label_fr": "Tabac", "label_en": "Tobacco processing"},
    "13": {"code": "13", "label_fr": "Textile", "label_en": "Textiles"},
    "14": {"code": "14", "label_fr": "Vêtements", "label_en": "Apparel"},
    "15": {"code": "15", "label_fr": "Cuir et articles", "label_en": "Leather and footwear"},
    "16": {"code": "16", "label_fr": "Bois et liège", "label_en": "Wood and cork"},
    "17": {"code": "17", "label_fr": "Papier et carton", "label_en": "Paper and pulp"},
    "18": {"code": "18", "label_fr": "Imprimerie et reproduction", "label_en": "Printing and reproduction"},
    "19": {"code": "19", "label_fr": "Raffinage du pétrole", "label_en": "Petroleum refining"},
    "20": {"code": "20", "label_fr": "Chimie et minéraux", "label_en": "Chemicals and minerals"},
    "21": {"code": "21", "label_fr": "Produits pharmaceutiques", "label_en": "Pharmaceutical products"},
    "22": {"code": "22", "label_fr": "Caoutchouc et plastiques", "label_en": "Rubber and plastics"},
    "23": {"code": "23", "label_fr": "Minéraux non métalliques", "label_en": "Non-metallic minerals"},
    "24": {"code": "24", "label_fr": "Métallurgie", "label_en": "Metal production"},
    "25": {"code": "25", "label_fr": "Produits métalliques", "label_en": "Fabricated metals"},
    "26": {"code": "26", "label_fr": "Électronique", "label_en": "Electronics"},
    "27": {"code": "27", "label_fr": "Machines électriques", "label_en": "Electrical equipment"},
    "28": {"code": "28", "label_fr": "Machinerie", "label_en": "Machinery"},
    "29": {"code": "29", "label_fr": "Véhicules automobiles", "label_en": "Motor vehicles"},
    "30": {"code": "30", "label_fr": "Transport ferroviaire", "label_en": "Railroad equipment"},
    "31": {"code": "31", "label_fr": "Transport naval", "label_en": "Ship and boat building"},
    "32": {"code": "32", "label_fr": "Aérospatiale", "label_en": "Aircraft"},
    "33": {"code": "33", "label_fr": "Autres transports", "label_en": "Other transport"},
    "34": {"code": "34", "label_fr": "Équipement professionnel", "label_en": "Professional equipment"},
    "35": {"code": "35", "label_fr": "Machines d'usage général", "label_en": "General-purpose machinery"},
    "36": {"code": "36", "label_fr": "Mobilier et divers", "label_en": "Furniture and miscellaneous"},
    "37": {"code": "37", "label_fr": "Recyclage", "label_en": "Recycling"},
}

# ── HS to ISIC4 Mapping ──────────────────────────────────────────────────────

HS_TO_ISIC4: Dict[str, str] = {
    # Agriculture & Food (ISIC 01-03, 10-11)
    "0901": "01",  # Coffee → Crop production
    "0902": "01",  # Tea
    "1801": "01",  # Cocoa beans
    "1005": "01",  # Maize
    "1006": "01",  # Rice
    "1001": "01",  # Wheat
    "2401": "01",  # Tobacco
    "0801": "01",  # Nuts
    "0803": "01",  # Plantains
    "1202": "01",  # Groundnuts
    "1511": "01",  # Oil palm
    "1701": "10",  # Sugar products → Food production
    "1806": "10",  # Cocoa preparations
    "2106": "10",  # Food preparations
    "2201": "11",  # Water
    "2203": "11",  # Beer & malt
    "2204": "11",  # Wine
    "2208": "11",  # Spirits
    # Textiles & Apparel (ISIC 13-15)
    "5001": "13",  # Silk
    "5201": "13",  # Cotton
    "6001": "13",  # Yarn & thread
    "6201": "14",  # Apparel
    "6301": "14",  # Apparel
    "6401": "15",  # Footwear
    # Chemicals & Pharmaceuticals (ISIC 19-21)
    "2710": "19",  # Petroleum products
    "2915": "20",  # Chemicals
    "2942": "20",  # Chemicals
    "3004": "21",  # Pharmaceuticals
    "3005": "21",  # Pharmaceuticals
    # Metals & Minerals (ISIC 07-08, 23-25)
    "2603": "07",  # Copper ore → Mineral extraction
    "2608": "07",  # Zinc ore
    "2601": "07",  # Iron ore
    "2606": "07",  # Bauxite
    "2701": "06",  # Coal
    "7001": "24",  # Iron & steel
    "7208": "24",  # Steel
    "7325": "25",  # Fabricated metals
    # Wood & Paper (ISIC 16-18)
    "4401": "16",  # Wood lumber
    "4403": "16",  # Wood products
    "4701": "17",  # Pulp
    "4802": "17",  # Paper
    # Machinery & Transport (ISIC 28-33)
    "8471": "28",  # Computers & machinery
    "8706": "29",  # Motor vehicles
    "8901": "31",  # Ships & boats
    "8802": "32",  # Aircraft
}

# ── Industrial Database Strength Indicators (IDSB) ──────────────────────────

IDSB_SECTOR_BENCHMARKS: Dict[str, Dict[str, float]] = {
    # Format: "ISIC4_division": {
    #   "manufacturing_index": value (0-100),
    #   "export_readiness": value (0-100),
    #   "avg_productivity": value,
    #   "skill_level": value (0-5),
    #   "capex_intensity": value (0-1)
    # }
    "01": {
        "manufacturing_index": 45,
        "export_readiness": 60,
        "avg_productivity": 2.5,
        "skill_level": 2,
        "capex_intensity": 0.3
    },
    "10": {
        "manufacturing_index": 65,
        "export_readiness": 70,
        "avg_productivity": 4.2,
        "skill_level": 3,
        "capex_intensity": 0.5
    },
    "13": {
        "manufacturing_index": 55,
        "export_readiness": 65,
        "avg_productivity": 3.8,
        "skill_level": 2.5,
        "capex_intensity": 0.6
    },
    "20": {
        "manufacturing_index": 72,
        "export_readiness": 75,
        "avg_productivity": 5.2,
        "skill_level": 3.5,
        "capex_intensity": 0.7
    },
    "24": {
        "manufacturing_index": 68,
        "export_readiness": 72,
        "avg_productivity": 4.8,
        "skill_level": 3,
        "capex_intensity": 0.8
    },
    "29": {
        "manufacturing_index": 52,
        "export_readiness": 55,
        "avg_productivity": 3.5,
        "skill_level": 3.5,
        "capex_intensity": 0.9
    },
}


class ISIC4IDSBOpportunityService:
    """Enriches opportunities with ISIC4 sector and industrial base analysis."""

    def __init__(self):
        self.hs_to_isic = HS_TO_ISIC4
        self.isic_divisions = ISIC4_DIVISIONS
        self.benchmarks = IDSB_SECTOR_BENCHMARKS

    def get_isic4_for_hs(self, hs_code: str) -> Optional[str]:
        """Get ISIC4 division for an HS code."""
        # Try exact 4-digit match first
        hs_prefix = hs_code[:4] if len(hs_code) >= 4 else hs_code
        if hs_prefix in self.hs_to_isic:
            return self.hs_to_isic[hs_prefix]

        # Try 2-digit match
        if len(hs_code) >= 2:
            hs_prefix = hs_code[:2]
            for key, value in self.hs_to_isic.items():
                if key.startswith(hs_prefix):
                    return value

        return None

    def get_sector_profile(self, isic4_code: str, lang: str = "fr") -> Dict:
        """Get detailed sector profile for an ISIC4 division."""
        division = self.isic_divisions.get(isic4_code, {})
        benchmark = self.benchmarks.get(isic4_code, {})

        return {
            "isic4_code": isic4_code,
            "label": division.get(f"label_{lang}", "Unknown sector"),
            "manufacturing_index": benchmark.get("manufacturing_index"),
            "export_readiness": benchmark.get("export_readiness"),
            "avg_productivity": benchmark.get("avg_productivity"),
            "skill_level": benchmark.get("skill_level"),
            "capex_intensity": benchmark.get("capex_intensity"),
        }

    def assess_opportunity_by_sector(
        self,
        hs_code: str,
        origin: str,
        destination: str,
        market_potential: Optional[float] = None,
        lang: str = "fr"
    ) -> Dict:
        """Comprehensive opportunity assessment using ISIC4 sectoral analysis."""

        isic4 = self.get_isic4_for_hs(hs_code)
        if not isic4:
            return {"available": False, "note": "ISIC4 classification not available"}

        sector_profile = self.get_sector_profile(isic4, lang)

        # Calculate sectoral opportunity score
        opportunity_score = self._calculate_sectoral_score(
            isic4, market_potential, sector_profile
        )

        # Assess transformation potential
        transformation_chain = self._analyze_transformation_chain(isic4, hs_code, lang)

        # Calculate competitiveness index
        competitiveness = self._assess_competitiveness(
            isic4, origin, destination
        )

        return {
            "available": True,
            "hs_code": hs_code,
            "isic4": isic4,
            "sector_profile": sector_profile,
            "opportunity_score": opportunity_score,
            "transformation_chain": transformation_chain,
            "competitiveness_index": competitiveness,
            "sectoral_barriers": self._identify_sectoral_barriers(isic4, lang),
            "recommended_actions": self._get_sectoral_recommendations(isic4, lang),
        }

    def _calculate_sectoral_score(
        self,
        isic4: str,
        market_potential: Optional[float],
        sector_profile: Dict
    ) -> float:
        """Calculate opportunity score (0-100) based on sectoral metrics."""

        if not sector_profile:
            return 0

        manufacturing = sector_profile.get("manufacturing_index", 50) / 100
        export_ready = sector_profile.get("export_readiness", 50) / 100

        # Boost score if market potential exists
        market_boost = min(1.0, (market_potential or 1) / 1000000) if market_potential else 0.5

        score = (
            0.4 * manufacturing +
            0.4 * export_ready +
            0.2 * market_boost
        ) * 100

        return round(score, 1)

    def _analyze_transformation_chain(
        self,
        isic4: str,
        hs_code: str,
        lang: str
    ) -> Dict:
        """Analyze input-process-output transformation chain."""

        # Simplified transformation chains for key sectors
        chains = {
            "01": {
                "fr": {
                    "input": "Matières premières agricoles brutes",
                    "process": "Récolte, tri, séchage, conditionnement",
                    "output": "Produits agricoles bruts pour export"
                },
                "en": {
                    "input": "Raw agricultural materials",
                    "process": "Harvesting, sorting, drying, packaging",
                    "output": "Agricultural products for export"
                }
            },
            "10": {
                "fr": {
                    "input": "Matières premières agricoles",
                    "process": "Transformation, emballage, contrôle qualité",
                    "output": "Produits alimentaires transformés"
                },
                "en": {
                    "input": "Agricultural raw materials",
                    "process": "Processing, packaging, quality control",
                    "output": "Processed food products"
                }
            },
            "24": {
                "fr": {
                    "input": "Minerais bruts",
                    "process": "Extraction, raffinage, transformation",
                    "output": "Métaux purifiés et alliages"
                },
                "en": {
                    "input": "Raw ores",
                    "process": "Extraction, refining, transformation",
                    "output": "Refined metals and alloys"
                }
            },
        }

        if isic4 in chains:
            return chains[isic4].get(lang, chains[isic4].get("en"))

        return {
            "input": "Matières premières" if lang == "fr" else "Raw materials",
            "process": "Transformation" if lang == "fr" else "Processing",
            "output": "Produit fini" if lang == "fr" else "Finished product"
        }

    def _assess_competitiveness(
        self,
        isic4: str,
        origin: str,
        destination: str
    ) -> float:
        """Assess competitiveness index (0-100)."""

        benchmark = self.benchmarks.get(isic4, {})
        base_score = benchmark.get("manufacturing_index", 50)

        # Country-specific adjustments (simplified)
        # In production, use actual country industrial data
        country_adjustments = {
            "ETH": 15,  # Ethiopia starting to develop manufacturing
            "KEN": 25,  # Kenya has stronger industrial base
            "NGA": 30,  # Nigeria has oil & gas base
            "ZAF": 45,  # South Africa strongest industrial base
            "TUN": 40,  # Tunisia has textile & automotive
            "EGY": 38,  # Egypt has food & textiles
        }

        origin_adjustment = country_adjustments.get(origin, 0)

        competitiveness = base_score + origin_adjustment
        return min(100, max(0, competitiveness))

    def _identify_sectoral_barriers(self, isic4: str, lang: str) -> List[Dict]:
        """Identify sector-specific barriers to development."""

        barriers = {
            "01": [
                {
                    "type": "climate" if lang == "en" else "climatique",
                    "impact": "high" if lang == "en" else "fort",
                    "description": "Climate variability affects productivity"
                    if lang == "en"
                    else "Variabilité climatique affectant la productivité"
                }
            ],
            "20": [
                {
                    "type": "regulatory" if lang == "en" else "réglementaire",
                    "impact": "medium" if lang == "en" else "moyen",
                    "description": "Complex environmental regulations"
                    if lang == "en"
                    else "Réglementations environnementales complexes"
                }
            ],
            "29": [
                {
                    "type": "technology" if lang == "en" else "technologique",
                    "impact": "high" if lang == "en" else "fort",
                    "description": "Requires advanced manufacturing technology"
                    if lang == "en"
                    else "Requiert une technologie manufacturière avancée"
                }
            ],
        }

        return barriers.get(isic4, [])

    def _get_sectoral_recommendations(self, isic4: str, lang: str) -> List[str]:
        """Get strategic recommendations for sector development."""

        recommendations = {
            "01": [
                "Investir dans l'irrigation moderne et la gestion des sols" if lang == "fr"
                else "Invest in modern irrigation and soil management",
                "Développer la chaîne de froid pour la conservation" if lang == "fr"
                else "Develop cold chain infrastructure",
                "Renforcer les normes de qualité et la certification" if lang == "fr"
                else "Strengthen quality standards and certification",
            ],
            "10": [
                "Implanter des unités de transformation agroalimentaire" if lang == "fr"
                else "Establish agro-processing facilities",
                "Certifier les produits selon les normes internationales" if lang == "fr"
                else "Certify products to international standards",
                "Développer les marques régionales" if lang == "fr"
                else "Develop regional brands",
            ],
            "24": [
                "Moderniser les techniques de transformation métallurgique" if lang == "fr"
                else "Modernize metallurgical processing",
                "Recruter et former des ingénieurs spécialisés" if lang == "fr"
                else "Recruit and train specialized engineers",
                "Mettre en place des standards de qualité stricts" if lang == "fr"
                else "Implement strict quality standards",
            ],
        }

        return recommendations.get(isic4, [
            "Renforcer la capacité de production" if lang == "fr"
            else "Strengthen production capacity",
            "Améliorer l'accès aux marchés régionaux" if lang == "fr"
            else "Improve access to regional markets",
            "Investir dans la qualification du personnel" if lang == "fr"
            else "Invest in workforce skills",
        ])


# Singleton instance
_service_instance: Optional[ISIC4IDSBOpportunityService] = None


def get_isic_idsb_service() -> ISIC4IDSBOpportunityService:
    """Get or create the ISIC4/IDSB opportunity service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ISIC4IDSBOpportunityService()
    return _service_instance
