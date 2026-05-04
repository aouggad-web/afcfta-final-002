"""
AfCFTA Platform - Enhanced Search Engine
==========================================
Fuzzy HS code matching, natural-language product search, and advanced
investment opportunity filtering with multi-criteria ranking.

No external NLP libraries are required — all logic is implemented with
built-in Python so the module works out of the box.
"""

from __future__ import annotations

import re
import logging
from difflib import SequenceMatcher, get_close_matches
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# HS code sample catalogue (chapter-level descriptions)
# In production this would query the PostgreSQL hs_codes table.
# =============================================================================

HS_CATALOGUE: Dict[str, Dict[str, str]] = {
    "01": {"en": "Live animals", "fr": "Animaux vivants"},
    "02": {"en": "Meat and edible meat offal", "fr": "Viandes et abats comestibles"},
    "03": {"en": "Fish and crustaceans, molluscs", "fr": "Poissons et crustacés"},
    "04": {"en": "Dairy produce, eggs, honey", "fr": "Lait, œufs, miel"},
    "06": {"en": "Live trees and other plants", "fr": "Plantes vivantes"},
    "07": {"en": "Edible vegetables and roots", "fr": "Légumes comestibles"},
    "08": {"en": "Edible fruit and nuts", "fr": "Fruits comestibles"},
    "09": {"en": "Coffee, tea, maté and spices", "fr": "Café, thé et épices"},
    "10": {"en": "Cereals", "fr": "Céréales"},
    "11": {"en": "Milling industry products", "fr": "Produits de la minoterie"},
    "12": {"en": "Oil seeds and oleaginous fruits", "fr": "Graines et fruits oléagineux"},
    "15": {"en": "Animal or vegetable fats and oils", "fr": "Graisses et huiles végétales"},
    "17": {"en": "Sugars and sugar confectionery", "fr": "Sucres et sucreries"},
    "22": {"en": "Beverages, spirits and vinegar", "fr": "Boissons, alcools et vinaigres"},
    "25": {"en": "Salt, sulphur, earths, stone", "fr": "Sel, soufre, terres et pierres"},
    "26": {"en": "Ores, slag and ash", "fr": "Minerais, scories et cendres"},
    "27": {"en": "Mineral fuels, mineral oils", "fr": "Combustibles minéraux"},
    "28": {"en": "Inorganic chemicals", "fr": "Produits chimiques inorganiques"},
    "29": {"en": "Organic chemicals", "fr": "Produits chimiques organiques"},
    "30": {"en": "Pharmaceutical products", "fr": "Produits pharmaceutiques"},
    "31": {"en": "Fertilisers", "fr": "Engrais"},
    "39": {"en": "Plastics and articles thereof", "fr": "Matières plastiques"},
    "40": {"en": "Rubber and articles thereof", "fr": "Caoutchouc et ouvrages"},
    "44": {"en": "Wood and articles of wood", "fr": "Bois et ouvrages en bois"},
    "47": {"en": "Pulp of wood", "fr": "Pâtes de bois"},
    "48": {"en": "Paper and paperboard", "fr": "Papiers et cartons"},
    "50": {"en": "Silk", "fr": "Soie"},
    "52": {"en": "Cotton", "fr": "Coton"},
    "54": {"en": "Man-made filaments", "fr": "Filaments synthétiques"},
    "61": {"en": "Knitted or crocheted apparel", "fr": "Vêtements en maille"},
    "62": {"en": "Not knitted or crocheted apparel", "fr": "Vêtements non en maille"},
    "63": {"en": "Other made-up textile articles", "fr": "Autres articles textiles"},
    "64": {"en": "Footwear", "fr": "Chaussures"},
    "70": {"en": "Glass and glassware", "fr": "Verre et ouvrages en verre"},
    "71": {"en": "Natural or cultured pearls, precious stones, precious metals",
           "fr": "Perles, pierres gemmes, métaux précieux"},
    "72": {"en": "Iron and steel", "fr": "Fonte, fer et acier"},
    "73": {"en": "Articles of iron or steel", "fr": "Ouvrages en fonte, fer ou acier"},
    "74": {"en": "Copper and articles thereof", "fr": "Cuivre et ouvrages en cuivre"},
    "76": {"en": "Aluminium and articles thereof", "fr": "Aluminium et ouvrages en aluminium"},
    "84": {"en": "Nuclear reactors, boilers, machinery", "fr": "Réacteurs nucléaires, chaudières"},
    "85": {"en": "Electrical machinery and equipment", "fr": "Machines électriques"},
    "86": {"en": "Railway locomotives and rolling stock", "fr": "Locomotives et matériel ferroviaire"},
    "87": {"en": "Vehicles other than railway", "fr": "Voitures automobiles"},
    "88": {"en": "Aircraft, spacecraft", "fr": "Aéronefs, engins spatiaux"},
    "89": {"en": "Ships, boats and floating structures", "fr": "Bateaux et engins flottants"},
    "90": {"en": "Optical, photographic instruments", "fr": "Instruments optiques"},
    "94": {"en": "Furniture, bedding, lamps", "fr": "Meubles, literie, lampes"},
    "95": {"en": "Toys, games and sports requisites", "fr": "Jouets, jeux"},
    "0901": {"en": "Coffee, whether or not roasted", "fr": "Café, même torréfié"},
    "1001": {"en": "Wheat and meslin", "fr": "Froment (blé) et méteil"},
    "1511": {"en": "Palm oil and its fractions", "fr": "Huile de palme et ses fractions"},
    "2601": {"en": "Iron ores and concentrates", "fr": "Minerais de fer et concentrés"},
    "2709": {"en": "Petroleum oils, crude", "fr": "Huiles brutes de pétrole"},
    "7108": {"en": "Gold (incl. gold plated with platinum)", "fr": "Or"},
    "8471": {"en": "Automatic data-processing machines (computers)",
             "fr": "Machines automatiques de traitement de l'information"},
    "8517": {"en": "Telephone sets, smartphones",
             "fr": "Appareils téléphoniques, smartphones"},
    "6109": {"en": "T-shirts, singlets and other vests, knitted",
             "fr": "T-shirts et maillots de corps en maille"},
    "4011": {"en": "New pneumatic tyres, of rubber", "fr": "Pneumatiques neufs, en caoutchouc"},
}


class FuzzyMatcher:
    """HS code fuzzy matcher using sequence similarity."""

    def __init__(self, threshold: float = 0.6) -> None:
        self.threshold = threshold

    def search(self, query: str, lang: str = "en", top_n: int = 10) -> List[Dict[str, Any]]:
        """Find HS codes whose description is similar to the query."""
        query_lower = query.lower()
        results = []

        for code, descriptions in HS_CATALOGUE.items():
            description = descriptions.get(lang, descriptions["en"])
            ratio = SequenceMatcher(
                None, query_lower, description.lower()
            ).ratio()
            if ratio >= self.threshold:
                results.append(
                    {
                        "hs_code": code,
                        "description": description,
                        "similarity": round(ratio, 4),
                        "match_type": "fuzzy",
                    }
                )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_n]


class SemanticSearchEngine:
    """
    Lightweight semantic search using keyword overlap.

    In production this would use a vector embedding model (e.g. sentence-transformers).
    """

    # Keyword → HS chapter mapping
    KEYWORD_MAP: Dict[str, List[str]] = {
        "coffee": ["09", "0901"],
        "wheat": ["10", "1001"],
        "oil": ["15", "27", "1511", "2709"],
        "gold": ["71", "7108"],
        "phone": ["85", "8517"],
        "smartphone": ["85", "8517"],
        "computer": ["84", "8471"],
        "car": ["87"],
        "vehicle": ["87"],
        "cotton": ["52"],
        "textile": ["50", "52", "54", "61", "62", "63"],
        "shirt": ["61", "62", "6109"],
        "tyre": ["40", "4011"],
        "rubber": ["40"],
        "steel": ["72", "73"],
        "iron": ["72", "26", "2601"],
        "copper": ["74"],
        "aluminium": ["76"],
        "fish": ["03"],
        "meat": ["02"],
        "sugar": ["17"],
        "fertiliser": ["31"],
        "fertilizer": ["31"],
        "pharmaceutical": ["30"],
        "medicine": ["30"],
        "wood": ["44"],
        "furniture": ["94"],
    }

    def find_similar(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return HS codes semantically related to the query."""
        query_words = set(re.sub(r"[^a-z0-9 ]", "", query.lower()).split())
        scored: Dict[str, float] = {}

        for keyword, codes in self.KEYWORD_MAP.items():
            if keyword in query_words:
                for code in codes:
                    scored[code] = scored.get(code, 0) + 1.0

        results = []
        for code, score in sorted(scored.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            desc = HS_CATALOGUE.get(code, {})
            results.append(
                {
                    "hs_code": code,
                    "description": desc.get("en", ""),
                    "relevance_score": score,
                    "match_type": "semantic",
                }
            )
        return results


class EnhancedSearchEngine:
    """
    Unified search engine with exact, fuzzy, and semantic matching.

    Also provides advanced investment opportunity filtering.
    """

    def __init__(self) -> None:
        self._fuzzy = FuzzyMatcher(threshold=0.55)
        self._semantic = SemanticSearchEngine()

    # ------------------------------------------------------------------
    # HS Code Search
    # ------------------------------------------------------------------

    @staticmethod
    def _is_hs_code_pattern(query: str) -> bool:
        """Return True if the query looks like an HS code."""
        return bool(re.match(r"^\d{2,10}$", query.strip()))

    @staticmethod
    def _exact_hs_lookup(query: str) -> List[Dict[str, Any]]:
        """Exact HS code lookup."""
        results = []
        q = query.strip()
        for code, descriptions in HS_CATALOGUE.items():
            if code.startswith(q) or q.startswith(code):
                results.append(
                    {
                        "hs_code": code,
                        "description_en": descriptions.get("en", ""),
                        "description_fr": descriptions.get("fr", ""),
                        "match_type": "exact",
                    }
                )
        return results

    def intelligent_hs_search(
        self,
        query: str,
        lang: str = "en",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Multi-modal HS code search:
        1. Exact match for numeric codes
        2. Fuzzy match for partial / typo queries
        3. Semantic match for natural-language descriptions
        """
        results: Dict[str, Any] = {
            "query": query,
            "exact_matches": [],
            "fuzzy_matches": [],
            "semantic_matches": [],
            "category_suggestions": [],
            "related_products": [],
        }

        if self._is_hs_code_pattern(query):
            results["exact_matches"] = self._exact_hs_lookup(query)

        results["fuzzy_matches"] = self._fuzzy.search(query, lang=lang)
        results["semantic_matches"] = self._semantic.find_similar(query)

        # Category suggestions based on top result
        top_codes = [r["hs_code"] for r in results["exact_matches"][:1]] + \
                    [r["hs_code"] for r in results["semantic_matches"][:2]]
        chapters = {c[:2] for c in top_codes if len(c) >= 4}
        for chapter in chapters:
            desc = HS_CATALOGUE.get(chapter, {})
            if desc:
                results["category_suggestions"].append(
                    {"chapter": chapter, "description": desc.get(lang, desc.get("en", ""))}
                )

        results["total_matches"] = (
            len(results["exact_matches"])
            + len(results["fuzzy_matches"])
            + len(results["semantic_matches"])
        )
        return results

    # ------------------------------------------------------------------
    # Investment Opportunity Search
    # ------------------------------------------------------------------

    def investment_opportunity_search(
        self,
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Advanced investment opportunity search with multi-criteria filtering.

        Accepted criteria keys:
        - countries / regions: list of country/bloc codes
        - sectors: list of sector names
        - investment_size: "sme" | "medium" | "large"
        - risk_tolerance: "low" | "medium" | "high"
        - required_incentives: list of incentive types (tax, sez, grants, …)
        - min_score: float 0..1
        """
        try:
            from intelligence.ai_engine.investment_scoring import (
                get_intelligence_engine,
                COUNTRY_INDICATORS,
            )
        except ImportError:
            return {"error": "Intelligence engine not available", "opportunities": []}

        engine = get_intelligence_engine()
        countries = list(COUNTRY_INDICATORS.keys())

        # Geographic filter
        filter_countries = criteria.get("countries", [])
        if filter_countries:
            countries = [c for c in countries if c in [fc.upper() for fc in filter_countries]]

        sectors = criteria.get("sectors", ["general"])
        investment_size = criteria.get("investment_size", "medium")
        risk_tolerance = criteria.get("risk_tolerance", "medium")
        min_score = float(criteria.get("min_score", 0.0))

        opportunities = []
        for country in countries:
            for sector in sectors:
                score = engine.calculate_investment_score(
                    country, sector, investment_size,
                    {"risk_tolerance": risk_tolerance}
                )

                if score.overall_score < min_score:
                    continue

                # Filter by risk tolerance
                if risk_tolerance == "low" and len(score.risk_factors) >= 3:
                    continue

                opportunities.append(
                    {
                        "country": country,
                        "sector": sector,
                        "investment_score": score.overall_score,
                        "grade": score.grade,
                        "recommendation": score.recommendation_strength,
                        "risk_count": len(score.risk_factors),
                        "top_risks": [r["name"] for r in score.risk_factors[:2]],
                        "confidence": score.confidence_interval,
                    }
                )

        # Sort by score descending
        opportunities.sort(key=lambda x: x["investment_score"], reverse=True)

        return {
            "criteria": criteria,
            "total_count": len(opportunities),
            "opportunities": opportunities[:50],
            "facets": self._generate_facets(opportunities),
            "related_searches": self._suggest_related(criteria),
        }

    @staticmethod
    def _generate_facets(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate search facets for the UI filter panel."""
        sectors = {}
        countries = {}
        grades = {}
        for opp in opportunities:
            sectors[opp["sector"]] = sectors.get(opp["sector"], 0) + 1
            countries[opp["country"]] = countries.get(opp["country"], 0) + 1
            grades[opp["grade"]] = grades.get(opp["grade"], 0) + 1
        return {
            "by_sector": dict(sorted(sectors.items(), key=lambda x: x[1], reverse=True)),
            "by_country": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)),
            "by_grade": dict(sorted(grades.items(), key=lambda x: x[1], reverse=True)),
        }

    @staticmethod
    def _suggest_related(criteria: Dict[str, Any]) -> List[str]:
        """Suggest related search variations."""
        suggestions = []
        if "sectors" in criteria and criteria["sectors"]:
            sector = criteria["sectors"][0]
            suggestions.append(f"{sector} investment North Africa")
            suggestions.append(f"{sector} SEZ incentives")
        if "countries" in criteria and criteria["countries"]:
            country = criteria["countries"][0]
            suggestions.append(f"Investment climate {country}")
            suggestions.append(f"Trade agreements {country}")
        return suggestions[:4]


# Singleton
_engine: Optional[EnhancedSearchEngine] = None


def get_search_engine() -> EnhancedSearchEngine:
    global _engine
    if _engine is None:
        _engine = EnhancedSearchEngine()
    return _engine
