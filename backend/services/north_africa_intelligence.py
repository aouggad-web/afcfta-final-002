"""
North Africa / UMA Regional Intelligence Service
=================================================
Provides advanced analytics and decision support for all 7 North African
UMA-member countries:

  DZA – Algeria
  EGY – Egypt
  LBY – Libya
  MAR – Morocco (reference)
  TUN – Tunisia
  SDN – Sudan
  MRT – Mauritania

This service extends (and complements) the existing
`regional_intelligence_service.py` (which covers DZA, MAR, EGY, TUN)
by adding LBY, SDN and MRT and providing UMA-wide analytics.

Key features:
  - Complete 7-country investment map
  - UMA preferential agreement matrix
  - Country-specific SEZ / free zone intelligence
  - Regional trade corridor analysis
  - COMESA / GAFTA integration scoring
  - AfCFTA readiness assessment
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# UMA country profiles (static intelligence data)
# ---------------------------------------------------------------------------

_UMA_PROFILES: Dict[str, Dict[str, Any]] = {
    "DZA": {
        "country_name": "Algeria",
        "country_name_fr": "Algérie",
        "gdp_bn_usd": 190,
        "population_m": 45,
        "strategic_position": "Sahel gateway, Mediterranean coast",
        "key_sectors": ["Hydrocarbons", "Agriculture", "Manufacturing"],
        "trade_agreements": ["GAFTA", "EU (assoc.)", "AfCFTA"],
        "eu_access": False,
        "us_access": False,
        "comesa_member": False,
        "ports": ["Algiers", "Oran", "Annaba"],
        "special_zones": [],
        "vat_rate": 19.0,
        "dd_avg_pct": 9.0,
        "investment_score": 6.0,
        "afcfta_readiness": 6.5,
        "notes": "Large domestic market; import substitution policy constrains imports",
    },
    "EGY": {
        "country_name": "Egypt",
        "country_name_fr": "Égypte",
        "gdp_bn_usd": 400,
        "population_m": 105,
        "strategic_position": "Suez Canal, MENA hub, Africa bridge",
        "key_sectors": ["Textiles", "Food Processing", "ICT", "Petrochemicals"],
        "trade_agreements": ["GAFTA", "EU (assoc.)", "US QIZ", "COMESA", "Agadir", "AfCFTA"],
        "eu_access": True,
        "us_access": True,
        "comesa_member": True,
        "ports": ["Port Said", "Alexandria", "Suez"],
        "special_zones": [
            {"name": "SCZONE (Suez Canal Zone)", "benefit": "5% flat customs, VAT-free inputs"},
            {"name": "QIZ Zones", "benefit": "0% US tariff for textile/apparel"},
            {"name": "New Capital SEZ", "benefit": "10% flat income tax"},
        ],
        "vat_rate": 14.0,
        "dd_avg_pct": 18.0,
        "investment_score": 7.5,
        "afcfta_readiness": 7.0,
        "notes": "Largest market (105M pop.); QIZ gives US duty-free textile access; COMESA hub",
    },
    "LBY": {
        "country_name": "Libya",
        "country_name_fr": "Libye",
        "gdp_bn_usd": 45,
        "population_m": 7,
        "strategic_position": "Mediterranean coast, oil wealth, Sahara gateway",
        "key_sectors": ["Hydrocarbons", "Construction", "Infrastructure"],
        "trade_agreements": ["GAFTA", "COMESA", "AfCFTA"],
        "eu_access": False,
        "us_access": False,
        "comesa_member": True,
        "ports": ["Tripoli", "Misurata", "Benghazi"],
        "special_zones": [
            {"name": "Misurata Free Zone", "benefit": "Customs exemption for reconstruction goods"},
        ],
        "vat_rate": 0.0,
        "dd_avg_pct": 10.0,
        "investment_score": 4.5,
        "afcfta_readiness": 4.0,
        "notes": "Post-conflict reconstruction focus; no VAT; political instability",
    },
    "MAR": {
        "country_name": "Morocco",
        "country_name_fr": "Maroc",
        "gdp_bn_usd": 134,
        "population_m": 37,
        "strategic_position": "EU gateway, Atlantic + Mediterranean",
        "key_sectors": ["Automotive", "Aerospace", "Agriculture", "Tourism", "Phosphates"],
        "trade_agreements": ["EU", "US FTA", "GAFTA", "Agadir", "AfCFTA", "EFTA", "Turkey"],
        "eu_access": True,
        "us_access": True,
        "comesa_member": False,
        "ports": ["Tanger-Med (Africa #1)", "Casablanca", "Agadir"],
        "special_zones": [
            {"name": "Tanger-Med Free Zone", "benefit": "Full customs + tax exemption"},
            {"name": "Casablanca Finance City", "benefit": "Financial hub, 0% withholding"},
            {"name": "Ait Melloul Industrial Zone", "benefit": "Industrial free zone – Agadir"},
        ],
        "vat_rate": 20.0,
        "dd_avg_pct": 12.3,
        "investment_score": 8.5,
        "afcfta_readiness": 8.0,
        "notes": "Most FTAs in region; EU automotive supply chain integration; Tanger-Med #1 Africa",
    },
    "TUN": {
        "country_name": "Tunisia",
        "country_name_fr": "Tunisie",
        "gdp_bn_usd": 46,
        "population_m": 12,
        "strategic_position": "Mediterranean bridge, EU proximity",
        "key_sectors": ["Textiles", "Automotive Components", "ICT", "Olive Oil"],
        "trade_agreements": ["EU (assoc.)", "GAFTA", "Agadir", "AfCFTA", "EFTA"],
        "eu_access": True,
        "us_access": False,
        "comesa_member": False,
        "ports": ["Rades", "Sfax", "Bizerte"],
        "special_zones": [
            {"name": "Zone Franche de Bizerte", "benefit": "Full exemption 10 years"},
            {"name": "Technology Parks (Sousse, Sfax)", "benefit": "ICT incentives"},
        ],
        "vat_rate": 19.0,
        "dd_avg_pct": 19.4,
        "investment_score": 7.0,
        "afcfta_readiness": 7.5,
        "notes": "EU association 0% industrial; FODEC 1%; DCFTA negotiations ongoing",
    },
    "SDN": {
        "country_name": "Sudan",
        "country_name_fr": "Soudan",
        "gdp_bn_usd": 35,
        "population_m": 46,
        "strategic_position": "Red Sea gateway, Nile corridor, COMESA",
        "key_sectors": ["Agriculture", "Livestock", "Gold", "Gum Arabic"],
        "trade_agreements": ["COMESA", "GAFTA", "AfCFTA"],
        "eu_access": False,
        "us_access": False,
        "comesa_member": True,
        "ports": ["Port Sudan"],
        "special_zones": [
            {"name": "Port Sudan Free Zone", "benefit": "Customs-free on trade inputs"},
        ],
        "vat_rate": 17.0,
        "dd_avg_pct": 13.0,
        "investment_score": 4.0,
        "afcfta_readiness": 5.0,
        "notes": "COMESA member; Port Sudan strategic Red Sea position; political transition",
    },
    "MRT": {
        "country_name": "Mauritania",
        "country_name_fr": "Mauritanie",
        "gdp_bn_usd": 10,
        "population_m": 4.5,
        "strategic_position": "Atlantic coast, Sahara bridge, West Africa interface",
        "key_sectors": ["Iron Ore", "Fishing", "Hydrocarbons", "Livestock"],
        "trade_agreements": ["GAFTA", "AfCFTA", "UMA/AMU"],
        "eu_access": False,
        "us_access": False,
        "comesa_member": False,
        "ports": ["Nouakchott", "Nouadhibou"],
        "special_zones": [],
        "vat_rate": 16.0,
        "dd_avg_pct": 9.0,
        "investment_score": 5.0,
        "afcfta_readiness": 5.5,
        "notes": "SNIM iron ore; Atlantic fishing; ECOWAS observer; small domestic market",
    },
}

# ---------------------------------------------------------------------------
# Preferential agreement matrix
# ---------------------------------------------------------------------------

_UMA_AGREEMENTS: Dict[str, Dict[str, Any]] = {
    "GAFTA": {
        "name": "Greater Arab Free Trade Area",
        "applicable_countries": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"],
        "indicative_rate": "0% on Arab-origin goods",
        "conditions": "Certificate of Origin required",
    },
    "AfCFTA": {
        "name": "African Continental Free Trade Area",
        "applicable_countries": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"],
        "indicative_rate": "Progressive reduction to 0% (90% of lines)",
        "conditions": "AfCFTA CoO + phase-in schedule",
    },
    "EU_Association": {
        "name": "EU Association Agreements (EuroMed)",
        "applicable_countries": ["MAR", "TUN", "EGY"],
        "indicative_rate": "0% on industrial goods",
        "conditions": "EU rules of origin satisfied",
    },
    "Agadir": {
        "name": "Agadir Agreement",
        "applicable_countries": ["MAR", "TUN", "EGY"],
        "indicative_rate": "0% between members",
        "conditions": "EU Pan-Euro-Med rules of origin",
    },
    "US_FTA": {
        "name": "US Free Trade Agreement",
        "applicable_countries": ["MAR"],
        "indicative_rate": "0% (phased from 2006)",
        "conditions": "US rules of origin",
    },
    "US_QIZ": {
        "name": "US Qualifying Industrial Zones",
        "applicable_countries": ["EGY"],
        "indicative_rate": "0% for qualifying textile/apparel",
        "conditions": "≥10.5% Israeli content + approved zone",
    },
    "COMESA": {
        "name": "Common Market for Eastern & Southern Africa",
        "applicable_countries": ["EGY", "LBY", "SDN"],
        "indicative_rate": "0% for COMESA goods",
        "conditions": "COMESA Certificate of Origin",
    },
    "EFTA": {
        "name": "EFTA (Switzerland, Norway, Iceland, Liechtenstein)",
        "applicable_countries": ["MAR", "TUN"],
        "indicative_rate": "0% on most goods",
        "conditions": "Pan-Euro-Med rules of origin",
    },
    "Turkey_FTA": {
        "name": "Turkey Free Trade Agreement",
        "applicable_countries": ["MAR", "TUN"],
        "indicative_rate": "0% on most goods",
        "conditions": "Diagonal cumulation with EU",
    },
}

UMA_COUNTRIES: List[str] = ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"]


class NorthAfricaIntelligenceService:
    """
    Regional intelligence service covering all 7 UMA North African countries.

    Provides:
      - 7-country investment map
      - SEZ / free zone directory
      - Preferential agreement matrix by country and HS chapter
      - Regional trade route scoring
      - Sector opportunity analysis
      - AfCFTA readiness scores
    """

    COUNTRIES = UMA_COUNTRIES

    def __init__(self):
        self._profiles = _UMA_PROFILES
        self._agreements = _UMA_AGREEMENTS

    # ------------------------------------------------------------------
    # 1. Investment map
    # ------------------------------------------------------------------

    def build_investment_map(self) -> Dict[str, Any]:
        """
        Return a ranked investment opportunity map across all 7 UMA countries.

        Returns:
            dict with 'countries' (list, sorted by investment_score desc)
            and 'top_country' with the highest score.
        """
        ranked = sorted(
            self._profiles.items(),
            key=lambda kv: kv[1]["investment_score"],
            reverse=True,
        )
        countries_list = []
        for rank, (code, prof) in enumerate(ranked, start=1):
            countries_list.append({
                "rank": rank,
                "iso3": code,
                "country_name": prof["country_name"],
                "gdp_bn_usd": prof["gdp_bn_usd"],
                "population_m": prof["population_m"],
                "investment_score": prof["investment_score"],
                "afcfta_readiness": prof["afcfta_readiness"],
                "eu_access": prof["eu_access"],
                "us_access": prof["us_access"],
                "comesa_member": prof["comesa_member"],
                "key_sectors": prof["key_sectors"],
                "special_zones_count": len(prof["special_zones"]),
                "vat_rate": prof["vat_rate"],
                "dd_avg_pct": prof["dd_avg_pct"],
                "notes": prof["notes"],
            })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "North Africa (UMA/AMU)",
            "total_countries": len(countries_list),
            "countries": countries_list,
            "top_country": countries_list[0]["iso3"] if countries_list else None,
        }

    # ------------------------------------------------------------------
    # 2. Special economic zones
    # ------------------------------------------------------------------

    def get_special_zones(self, country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Return SEZ / free zone information for one or all UMA countries.

        Args:
            country_code: Optional ISO3 filter (e.g. 'MAR').
                          If None, returns all countries.
        """
        results: Dict[str, Any] = {}
        codes = [country_code.upper()] if country_code else self.COUNTRIES

        for code in codes:
            profile = self._profiles.get(code)
            if not profile:
                continue
            results[code] = {
                "country_name": profile["country_name"],
                "special_zones": profile["special_zones"],
                "total_zones": len(profile["special_zones"]),
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "North Africa (UMA/AMU)",
            "data": results,
        }

    # ------------------------------------------------------------------
    # 3. Preferential agreement matrix
    # ------------------------------------------------------------------

    def get_agreement_matrix(
        self,
        country_code: Optional[str] = None,
        hs_chapter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return the preferential agreement matrix for UMA countries.

        Args:
            country_code: Optional ISO3 filter.
            hs_chapter:   Optional 2-digit HS chapter (used for chapter-level
                          notes; does not restrict agreements).

        Returns:
            dict with per-country agreement lists.
        """
        codes = [country_code.upper()] if country_code else self.COUNTRIES
        matrix: Dict[str, Any] = {}

        for code in codes:
            applicable = [
                {
                    "agreement": key,
                    "name": agr["name"],
                    "indicative_rate": agr["indicative_rate"],
                    "conditions": agr["conditions"],
                }
                for key, agr in self._agreements.items()
                if code in agr["applicable_countries"]
            ]
            matrix[code] = {
                "country_name": self._profiles.get(code, {}).get("country_name", code),
                "agreements": applicable,
                "agreements_count": len(applicable),
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "North Africa (UMA/AMU)",
            "hs_chapter_filter": hs_chapter,
            "country_filter": country_code,
            "matrix": matrix,
        }

    # ------------------------------------------------------------------
    # 4. Sector opportunity map
    # ------------------------------------------------------------------

    _SECTOR_SCORES: Dict[str, Dict[str, float]] = {
        "automotive": {
            "MAR": 9.0, "TUN": 7.5, "EGY": 6.5, "DZA": 5.0,
            "MRT": 2.0, "LBY": 2.0, "SDN": 2.0,
        },
        "textile": {
            "EGY": 9.0, "MAR": 8.0, "TUN": 8.0, "DZA": 5.0,
            "MRT": 3.0, "LBY": 2.0, "SDN": 3.0,
        },
        "agriculture": {
            "MAR": 8.5, "TUN": 7.0, "EGY": 7.5, "SDN": 7.0,
            "DZA": 6.0, "MRT": 5.5, "LBY": 3.0,
        },
        "renewable_energy": {
            "MAR": 9.5, "EGY": 8.0, "TUN": 7.5, "DZA": 7.0,
            "MRT": 6.0, "LBY": 5.0, "SDN": 4.0,
        },
        "ict": {
            "MAR": 8.0, "TUN": 8.5, "EGY": 7.5, "DZA": 5.5,
            "MRT": 3.0, "LBY": 2.5, "SDN": 3.5,
        },
        "hydrocarbons": {
            "DZA": 9.5, "LBY": 9.0, "EGY": 8.0, "SDN": 6.0,
            "MAR": 3.0, "TUN": 4.0, "MRT": 6.5,
        },
        "mining": {
            "MRT": 9.0, "MAR": 7.0, "DZA": 7.5, "SDN": 6.5,
            "EGY": 5.0, "TUN": 4.0, "LBY": 5.5,
        },
    }

    def get_sector_opportunity_map(
        self, sectors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Return sector-level opportunity scores for UMA countries.

        Args:
            sectors: List of sector keys.  Defaults to all defined sectors.

        Returns:
            dict with per-sector country rankings.
        """
        available = list(self._SECTOR_SCORES.keys())
        if sectors is None:
            sectors = available
        else:
            sectors = [s for s in sectors if s in self._SECTOR_SCORES]

        result: Dict[str, Any] = {}
        for sector in sectors:
            scores = self._SECTOR_SCORES[sector]
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            result[sector] = {
                "rankings": [
                    {
                        "rank": i + 1,
                        "iso3": code,
                        "country_name": self._profiles.get(code, {}).get("country_name", code),
                        "score": score,
                    }
                    for i, (code, score) in enumerate(ranked)
                ],
                "top_country": ranked[0][0] if ranked else None,
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "North Africa (UMA/AMU)",
            "sectors_analyzed": sectors,
            "sector_map": result,
        }

    # ------------------------------------------------------------------
    # 5. Trade route analysis
    # ------------------------------------------------------------------

    def get_trade_routes(
        self,
        origin: Optional[str] = None,
        destination_market: str = "EU",
    ) -> Dict[str, Any]:
        """
        Analyse optimal trade routes through UMA countries.

        Args:
            origin:             Optional origin country ISO3.
            destination_market: Target market ('EU', 'US', 'AFRICA', 'MENA', 'COMESA').

        Returns:
            dict with route options ranked by access + cost score.
        """
        market_scores: Dict[str, Dict[str, float]] = {
            "EU":     {"MAR": 9.0, "TUN": 8.5, "EGY": 7.5, "DZA": 4.0,
                       "LBY": 3.0, "SDN": 2.0, "MRT": 3.5},
            "US":     {"MAR": 9.0, "EGY": 8.0, "TUN": 5.0, "DZA": 3.0,
                       "LBY": 2.0, "SDN": 2.0, "MRT": 2.5},
            "AFRICA": {"MAR": 8.0, "EGY": 8.5, "SDN": 7.0, "TUN": 6.0,
                       "DZA": 6.5, "MRT": 6.0, "LBY": 4.5},
            "MENA":   {"EGY": 9.0, "MAR": 7.0, "TUN": 7.5, "LBY": 6.0,
                       "DZA": 6.5, "SDN": 5.5, "MRT": 4.0},
            "COMESA": {"EGY": 9.0, "SDN": 8.0, "LBY": 7.0, "TUN": 4.0,
                       "MAR": 3.0, "DZA": 3.5, "MRT": 3.0},
        }

        dest = destination_market.upper()
        scores_for_dest = market_scores.get(dest, market_scores["EU"])

        ranked = sorted(scores_for_dest.items(), key=lambda kv: kv[1], reverse=True)
        routes = []
        for rank, (code, score) in enumerate(ranked, start=1):
            prof = self._profiles.get(code, {})
            routes.append({
                "rank": rank,
                "iso3": code,
                "country_name": prof.get("country_name", code),
                "access_score": score,
                "ports": prof.get("ports", []),
                "eu_access": prof.get("eu_access", False),
                "us_access": prof.get("us_access", False),
                "comesa_member": prof.get("comesa_member", False),
                "special_zones": prof.get("special_zones", []),
            })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "destination_market": dest,
            "origin_filter": origin,
            "region": "North Africa (UMA/AMU)",
            "routes": routes,
            "recommended": routes[0]["iso3"] if routes else None,
        }

    # ------------------------------------------------------------------
    # 6. AfCFTA readiness assessment
    # ------------------------------------------------------------------

    def get_afcfta_readiness(self) -> Dict[str, Any]:
        """
        Return AfCFTA readiness scores for all 7 UMA countries.

        Scores are composite assessments based on:
          - Tariff liberalisation progress
          - Rules of origin compliance capacity
          - Trade facilitation infrastructure
          - NTB reduction measures
        """
        countries_list = sorted(
            [
                {
                    "iso3": code,
                    "country_name": prof["country_name"],
                    "afcfta_readiness": prof["afcfta_readiness"],
                    "investment_score": prof["investment_score"],
                    "comesa_member": prof["comesa_member"],
                    "eu_access": prof["eu_access"],
                }
                for code, prof in self._profiles.items()
            ],
            key=lambda x: x["afcfta_readiness"],
            reverse=True,
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "North Africa (UMA/AMU)",
            "countries": countries_list,
            "regional_average": round(
                sum(c["afcfta_readiness"] for c in countries_list) / len(countries_list), 2
            ),
        }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_service_instance: Optional[NorthAfricaIntelligenceService] = None


def get_north_africa_intelligence() -> NorthAfricaIntelligenceService:
    """Return the singleton NorthAfricaIntelligenceService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = NorthAfricaIntelligenceService()
    return _service_instance
