"""
Regional Intelligence Service for North Africa.

Provides advanced analytics and decision support for North African trade:
- Data freshness monitoring for all country datasets
- Regional trade intelligence reporting
- Best market entry strategy recommendations
- Investment location analysis with sector scoring
- Regional trade flow analytics
- Sectoral opportunity mapping
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.regional_config import (
    CEMAC_CONFIG,
    CEMAC_COUNTRIES,
    NORTH_AFRICA_COUNTRIES,
    REGIONAL_CONFIG,
)

logger = logging.getLogger(__name__)

DATA_BASE_DIR = Path(__file__).parent.parent / "data"


class DataFreshnessReport:
    """Tracks data freshness for each North African country."""

    def __init__(self):
        self.checked_at = datetime.utcnow()
        self.countries: Dict[str, Dict[str, Any]] = {}

    def add_country(
        self,
        country_code: str,
        last_updated: Optional[datetime],
        record_count: int,
        source_file: Optional[str] = None,
    ):
        age_hours = None
        is_fresh = False
        if last_updated:
            age = datetime.utcnow() - last_updated
            age_hours = round(age.total_seconds() / 3600, 1)
            target_days = REGIONAL_CONFIG["performance_targets"]["data_freshness_days"]
            is_fresh = age <= timedelta(days=target_days)

        self.countries[country_code] = {
            "country_code": country_code,
            "last_updated": last_updated.isoformat() if last_updated else None,
            "age_hours": age_hours,
            "is_fresh": is_fresh,
            "record_count": record_count,
            "source_file": source_file,
        }

    def to_dict(self) -> Dict[str, Any]:
        fresh_count = sum(1 for v in self.countries.values() if v["is_fresh"])
        total_records = sum(v["record_count"] for v in self.countries.values())
        return {
            "checked_at": self.checked_at.isoformat(),
            "countries": self.countries,
            "fresh_count": fresh_count,
            "total_countries": len(self.countries),
            "total_records": total_records,
            "all_fresh": fresh_count == len(self.countries),
        }


class RegionalIntelligenceService:
    """
    Advanced analytics service for North African regional trade intelligence.

    Provides:
    - Data freshness monitoring across all 4 countries
    - Investment opportunity mapping
    - Market entry strategy analysis
    - Regulatory environment comparison
    - Regional value chain opportunities
    """

    COUNTRIES = NORTH_AFRICA_COUNTRIES

    def __init__(self):
        self._data_cache: Dict[str, Any] = {}

    # ==================== Data Freshness ====================

    def get_data_freshness(self) -> DataFreshnessReport:
        """
        Check data freshness for all North African countries.

        Scans the published data directories for each country
        and reports the age and size of the latest datasets.
        """
        report = DataFreshnessReport()

        for country_code in self.COUNTRIES:
            pub_dir = DATA_BASE_DIR / "published" / country_code
            if not pub_dir.exists():
                report.add_country(country_code, None, 0)
                continue

            json_files = sorted(pub_dir.glob("*.json"), reverse=True)
            if not json_files:
                report.add_country(country_code, None, 0)
                continue

            latest = json_files[0]
            mtime = datetime.fromtimestamp(latest.stat().st_mtime)

            try:
                with open(latest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("records", data if isinstance(data, list) else [])
                count = len(records)
            except Exception as exc:
                logger.warning(f"Could not read {latest}: {exc}")
                count = 0

            report.add_country(country_code, mtime, count, str(latest))

        return report

    # ==================== Investment Intelligence ====================

    def recommend_market_entry(
        self,
        sector: str,
        origin_country: str = "INTL",
        target_market_size: str = "large",
        priority: str = "eu_access",
    ) -> Dict[str, Any]:
        """
        Recommend the best African market entry country for a given sector.

        Args:
            sector: Industry sector (automotive, textiles, agriculture, oil_gas, timber, mining, etc.)
            origin_country: Investor's home country ISO2/3
            target_market_size: 'large' | 'medium' | 'small'
            priority: 'eu_access' | 'us_access' | 'regional_hub' | 'cost'

        Returns:
            Market entry recommendations ranked by suitability
        """
        recommendations = []

        sector_lower = sector.lower()
        priority_lower = priority.lower()

        # Country suitability rules
        rules: Dict[str, Dict[str, int]] = {
            "DZA": {
                "hydrocarbons": 10,
                "agriculture": 7,
                "manufacturing": 5,
                "eu_access": 2,
                "us_access": 1,
                "regional_hub": 5,
                "cost": 6,
            },
            "MAR": {
                "automotive": 10,
                "aerospace": 9,
                "agriculture": 8,
                "textiles": 7,
                "eu_access": 10,
                "us_access": 8,
                "regional_hub": 7,
                "cost": 7,
            },
            "EGY": {
                "textiles": 9,
                "food_processing": 9,
                "ict": 8,
                "petrochemicals": 8,
                "eu_access": 7,
                "us_access": 8,
                "regional_hub": 10,
                "cost": 6,
            },
            "TUN": {
                "textiles": 10,
                "automotive": 8,
                "ict": 8,
                "olive_oil": 10,
                "eu_access": 9,
                "us_access": 3,
                "regional_hub": 5,
                "cost": 7,
            },
            # CEMAC countries
            "CMR": {
                "oil_gas": 9,
                "timber": 8,
                "agriculture": 7,
                "mining": 6,
                "eu_access": 6,
                "us_access": 2,
                "regional_hub": 9,
                "cost": 6,
            },
            "CAF": {
                "mining": 7,
                "agriculture": 5,
                "timber": 6,
                "eu_access": 2,
                "us_access": 1,
                "regional_hub": 2,
                "cost": 5,
            },
            "TCD": {
                "oil": 8,
                "agriculture": 6,
                "livestock": 7,
                "eu_access": 2,
                "us_access": 1,
                "regional_hub": 3,
                "cost": 5,
            },
            "COG": {
                "oil_gas": 9,
                "timber": 7,
                "mining": 6,
                "eu_access": 3,
                "us_access": 1,
                "regional_hub": 5,
                "cost": 5,
            },
            "GNQ": {
                "oil_gas": 10,
                "fishing": 6,
                "eu_access": 2,
                "us_access": 1,
                "regional_hub": 3,
                "cost": 4,
            },
            "GAB": {
                "oil_gas": 8,
                "timber": 9,
                "mining": 8,
                "agriculture": 5,
                "eu_access": 5,
                "us_access": 1,
                "regional_hub": 5,
                "cost": 6,
            },
        }

        for country_code, scores in rules.items():
            # Find sector score
            sector_score = 5  # default
            for key, val in scores.items():
                if key in sector_lower:
                    sector_score = val
                    break

            priority_score = scores.get(priority_lower, 5)

            combined = sector_score * 0.6 + priority_score * 0.4
            recommendations.append(
                {
                    "country_code": country_code,
                    "sector_score": sector_score,
                    "priority_score": priority_score,
                    "combined_score": round(combined, 1),
                }
            )

        recommendations.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "sector": sector,
            "priority": priority,
            "target_market_size": target_market_size,
            "recommendations": recommendations,
            "top_recommendation": recommendations[0]["country_code"] if recommendations else None,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_preferential_agreements_matrix(self) -> Dict[str, Any]:
        """
        Return a cross-country preferential agreement matrix.

        Shows which North African countries have agreements
        with which external markets, enabling stacking analysis.
        """
        matrix = {
            "DZA": {
                "EU": False,
                "US": False,
                "EFTA": False,
                "Agadir": False,
                "COMESA": False,
                "GAFTA": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "MAR": {
                "EU": True,
                "US": True,
                "EFTA": True,
                "Agadir": True,
                "COMESA": False,
                "GAFTA": True,
                "AFCFTA": True,
                "QIZ": False,
                "Turkey": True,
            },
            "EGY": {
                "EU": True,
                "US": False,
                "EFTA": True,
                "Agadir": True,
                "COMESA": True,
                "GAFTA": True,
                "AFCFTA": True,
                "QIZ": True,  # US market access via QIZ
                "Turkey": True,
            },
            "TUN": {
                "EU": True,
                "US": False,
                "EFTA": True,
                "Agadir": True,
                "COMESA": False,
                "GAFTA": True,
                "AFCFTA": True,
                "QIZ": False,
                "Turkey": True,
            },
            # CEMAC countries
            "CMR": {
                "EU": True,  # Economic Partnership Agreement (EPA)
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "CAF": {
                "EU": False,
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "TCD": {
                "EU": False,
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "COG": {
                "EU": False,
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "GNQ": {
                "EU": False,
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
            "GAB": {
                "EU": True,  # Economic Partnership Agreement (EPA)
                "US": False,
                "EFTA": False,
                "CEMAC": True,
                "ECCAS": True,
                "AFCFTA": True,
                "QIZ": False,
            },
        }

        # Identify best country per external market
        external_markets = ["EU", "US", "EFTA", "COMESA", "QIZ", "CEMAC"]
        best_by_market = {}
        for market in external_markets:
            countries_with_access = [
                c for c, agreements in matrix.items() if agreements.get(market)
            ]
            best_by_market[market] = countries_with_access

        return {
            "matrix": matrix,
            "best_country_by_market": best_by_market,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_regional_dataset(
        self,
        include_countries: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate and export the regional dataset for all countries.

        Args:
            include_countries: Optional subset of countries to include

        Returns:
            Dict with combined dataset metadata and per-country summaries
        """
        countries = include_countries or self.COUNTRIES
        result = {
            "exported_at": datetime.utcnow().isoformat(),
            "countries": {},
            "total_records": 0,
        }

        for country_code in countries:
            pub_dir = DATA_BASE_DIR / "published" / country_code
            if not pub_dir.exists():
                result["countries"][country_code] = {
                    "status": "no_data",
                    "record_count": 0,
                }
                continue

            json_files = sorted(pub_dir.glob("*.json"), reverse=True)
            if not json_files:
                result["countries"][country_code] = {
                    "status": "no_data",
                    "record_count": 0,
                }
                continue

            try:
                with open(json_files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("records", [])
                result["countries"][country_code] = {
                    "status": "available",
                    "record_count": len(records),
                    "source_file": json_files[0].name,
                    "last_updated": datetime.fromtimestamp(
                        json_files[0].stat().st_mtime
                    ).isoformat(),
                }
                result["total_records"] += len(records)
            except Exception as exc:
                result["countries"][country_code] = {
                    "status": "error",
                    "error": str(exc),
                    "record_count": 0,
                }

        return result

    # ==================== Investment Analysis ====================

    def investment_analysis(
        self,
        industry: str,
        target_markets: Optional[List[str]] = None,
        investment_size: float = 10_000_000,
        employment_target: int = 100,
    ) -> Dict[str, Any]:
        """
        Analyze investment opportunities across North African countries for a given industry.

        Scores each country on:
        - Sector-specific capabilities
        - Target market access (EU, US, Africa, MENA)
        - Investment environment (incentives, SEZs, legal framework)
        - Cost of employment / operational costs
        - Infrastructure quality

        Args:
            industry: Industry/sector name (automotive, textile, agriculture, ict, etc.)
            target_markets: List of target export markets (eu, us, africa, mena, arab)
            investment_size: Capital investment in USD
            employment_target: Target number of employees

        Returns:
            Investment analysis with country rankings and recommendations
        """
        if target_markets is None:
            target_markets = ["eu", "africa"]

        target_markets_lower = [m.lower() for m in target_markets]

        industry_lower = industry.lower()

        # Country investment profiles
        country_investment: Dict[str, Dict[str, Any]] = {
            "DZA": {
                "country_name": "Algeria",
                "sector_strengths": ["hydrocarbons", "agriculture", "mining", "construction"],
                "labour_cost_index": 4,  # 1=cheapest, 10=most expensive
                "ease_of_investment": 5,
                "infrastructure_quality": 5,
                "incentives": ["Tax holidays", "Customs exemptions (ANDI)"],
                "investment_law": "Ordinance 22-18 (2022)",
                "eu_access": False,
                "us_access": False,
                "special_zones": [],
                "est_op_cost_factor": 0.8,  # relative to regional average
            },
            "MAR": {
                "country_name": "Morocco",
                "sector_strengths": [
                    "automotive",
                    "aerospace",
                    "textiles",
                    "agriculture",
                    "renewable_energy",
                    "phosphates",
                    "tourism",
                ],
                "labour_cost_index": 4,
                "ease_of_investment": 8,
                "infrastructure_quality": 8,
                "incentives": [
                    "Industrial Acceleration Plan",
                    "Tanger-Med SEZ",
                    "Investment Charter 2022",
                    "CIMR pension exemptions",
                ],
                "investment_law": "Investment Charter Law 03-22 (2022)",
                "eu_access": True,
                "us_access": True,
                "special_zones": ["Tanger-Med", "Casablanca Finance City", "Dakhla Offshore"],
                "est_op_cost_factor": 0.85,
            },
            "EGY": {
                "country_name": "Egypt",
                "sector_strengths": [
                    "textiles",
                    "food_processing",
                    "ict",
                    "petrochemicals",
                    "tourism",
                    "construction",
                    "renewable_energy",
                ],
                "labour_cost_index": 3,  # lower cost
                "ease_of_investment": 7,
                "infrastructure_quality": 7,
                "incentives": [
                    "Investment Law 72/2017",
                    "QIZ US market access",
                    "SCZONE Suez Canal zone",
                    "New Administrative Capital SEZ",
                    "COMESA preferential access",
                ],
                "investment_law": "Investment Law 72/2017",
                "eu_access": True,
                "us_access": True,  # via QIZ
                "special_zones": ["SCZONE", "QIZ Zones", "Port Said SEZ"],
                "est_op_cost_factor": 0.70,
            },
            "TUN": {
                "country_name": "Tunisia",
                "sector_strengths": [
                    "textiles",
                    "automotive_components",
                    "ict",
                    "olive_oil",
                    "phosphates",
                    "tourism",
                ],
                "labour_cost_index": 4,
                "ease_of_investment": 7,
                "infrastructure_quality": 7,
                "incentives": [
                    "Offshore regime (full tax exemption for export-oriented firms)",
                    "Investment Code 2016",
                    "DCFTA preparation benefits",
                    "EU deep association advantages",
                ],
                "investment_law": "Investment Code Law 71/2016",
                "eu_access": True,
                "us_access": False,
                "special_zones": ["Offshore enterprise zones", "Economic development zones"],
                "est_op_cost_factor": 0.80,
            },
        }

        results = []
        for country_code, profile in country_investment.items():
            # Sector match score: pre-process strengths to avoid redundant operations in loop
            sector_score = 5  # default
            for strength in profile["sector_strengths"]:
                strength_normalized = strength.replace("_", " ")
                if strength_normalized in industry_lower or industry_lower in strength:
                    sector_score = 9
                    break
                # partial word match
                if any(w in industry_lower for w in strength_normalized.split()):
                    sector_score = max(sector_score, 7)

            # Market access score
            market_score = 0
            markets_matched = []
            for mkt in target_markets_lower:
                if mkt in ("eu", "europe") and profile["eu_access"]:
                    market_score += 3
                    markets_matched.append("EU")
                elif mkt in ("us", "usa", "united_states") and profile["us_access"]:
                    market_score += 3
                    markets_matched.append("US")
                elif mkt in ("africa", "afcfta"):
                    market_score += 1  # all have AfCFTA
                    markets_matched.append("Africa (AfCFTA)")
                elif mkt in ("mena", "arab", "gafta"):
                    market_score += 1
                    markets_matched.append("MENA/GAFTA")
            market_score = min(10, market_score * 2)

            # Operational cost score: maps est_op_cost_factor [0.7, 1.0] to score [8, 5]
            # Lower cost factor → higher score (more cost-efficient for the investor)
            cost_score = 10 - (profile["est_op_cost_factor"] * 10 - 5)

            # Investment environment
            env_score = (profile["ease_of_investment"] + profile["infrastructure_quality"]) / 2

            # Weighted combined
            combined = (
                sector_score * 0.30 + market_score * 0.30 + env_score * 0.25 + cost_score * 0.15
            )

            results.append(
                {
                    "country_code": country_code,
                    "country_name": profile["country_name"],
                    "combined_score": round(combined, 2),
                    "sector_score": sector_score,
                    "market_access_score": round(market_score, 1),
                    "environment_score": round(env_score, 1),
                    "cost_efficiency_score": round(cost_score, 1),
                    "markets_accessible": markets_matched,
                    "key_incentives": profile["incentives"],
                    "investment_law": profile["investment_law"],
                    "special_zones": profile["special_zones"],
                    "estimated_op_cost_factor": profile["est_op_cost_factor"],
                    "eu_access": profile["eu_access"],
                    "us_access": profile["us_access"],
                }
            )

        results.sort(key=lambda x: x["combined_score"], reverse=True)
        for rank, rec in enumerate(results, 1):
            rec["rank"] = rank

        # Size-adjusted recommendation note
        size_note = ""
        if investment_size >= 50_000_000:
            size_note = (
                "Large-scale investment: Morocco and Egypt offer strongest incentive packages."
            )
        elif investment_size >= 10_000_000:
            size_note = (
                "Mid-scale investment: All four countries offer viable incentive frameworks."
            )
        else:
            size_note = (
                "Smaller investment: Tunisia offshore regime or Morocco CFC may offer best ROI."
            )

        return {
            "industry": industry,
            "target_markets": target_markets,
            "investment_size_usd": investment_size,
            "employment_target": employment_target,
            "recommendations": results,
            "top_recommendation": results[0]["country_code"] if results else None,
            "size_note": size_note,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ==================== Trade Flows ====================

    def get_trade_flows(self) -> Dict[str, Any]:
        """
        Return regional trade flow intelligence across North African countries.

        Provides:
        - Intra-regional trade metrics
        - EU-bound trade advantages by country
        - MENA hub positioning
        - Africa gateway opportunities
        - Key commodity flows

        Returns:
            Dict with intra-regional, EU, MENA, and Africa trade flow data
        """
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "intra_regional": {
                "dza_mar": {
                    "status": "active",
                    "main_flows": ["Natural gas", "Agricultural products", "Manufactured goods"],
                    "agreements": ["GAFTA", "AfCFTA"],
                    "border_crossings": ["Tlemcen-Oujda"],
                    "notes": "Land and sea. Border reopened 2021 partially.",
                },
                "dza_tun": {
                    "status": "active",
                    "main_flows": ["Petroleum products", "Food", "Textiles"],
                    "agreements": ["GAFTA", "AfCFTA"],
                    "border_crossings": ["Ghardimaou-Souk Ahras"],
                    "notes": "Strong historical trade relationship",
                },
                "egy_tun": {
                    "status": "active",
                    "main_flows": ["Machinery", "Chemicals", "Textiles"],
                    "agreements": ["Agadir", "GAFTA", "AfCFTA"],
                    "border_crossings": ["Sea routes: Alexandria-Tunis"],
                    "notes": "Both Agadir members - enhanced preferences",
                },
                "mar_tun": {
                    "status": "active",
                    "main_flows": ["Olive oil", "Phosphates", "Automotive parts"],
                    "agreements": ["Agadir", "GAFTA", "AfCFTA"],
                    "border_crossings": ["Sea routes: Tunis-Casablanca"],
                    "notes": "Strong Agadir Agreement integration",
                },
                "mar_egy": {
                    "status": "active",
                    "main_flows": ["Chemicals", "Agricultural products", "Manufactured goods"],
                    "agreements": ["Agadir", "GAFTA", "AfCFTA"],
                    "border_crossings": ["Sea routes via Mediterranean"],
                    "notes": "Both have EU agreements enabling triangular EU trade",
                },
            },
            "eu_access": {
                "mar_advantage": {
                    "country": "MAR",
                    "agreement": "EU Association Agreement + US FTA",
                    "key_sectors": ["Automotive", "Aerospace", "Agriculture", "Textiles"],
                    "port": "Tanger-Med (largest in Africa - 9M TEU capacity)",
                    "notes": "Most integrated EU supply chain partner in North Africa",
                },
                "tun_deep_integration": {
                    "country": "TUN",
                    "agreement": "EU Association Agreement (most advanced in region)",
                    "key_sectors": ["Textiles", "Automotive components", "ICT", "Olive oil"],
                    "port": "Tunis-La Goulette",
                    "notes": "Preparing DCFTA (Deep Comprehensive FTA) for deeper integration",
                },
                "egy_eu_partnership": {
                    "country": "EGY",
                    "agreement": "EU Partnership Agreement",
                    "key_sectors": ["Textiles", "Chemicals", "Food"],
                    "port": "Port Said, Alexandria",
                    "notes": "Also benefits from QIZ for US market access",
                },
            },
            "mena_hub": {
                "egy_position": {
                    "country": "EGY",
                    "strategic_assets": ["Suez Canal", "SCZONE", "Largest Arab market (105M)"],
                    "agreements": ["COMESA", "GAFTA", "Agadir", "QIZ", "AfCFTA"],
                    "annual_suez_transits": "~21,000 vessels",
                    "notes": "Largest MENA economy, COMESA anchor, QIZ US gateway",
                },
                "mar_atlantic_position": {
                    "country": "MAR",
                    "strategic_assets": ["Tanger-Med", "Atlantic + Mediterranean access", "EU FTA"],
                    "agreements": ["EU", "US", "EFTA", "Agadir", "GAFTA", "AfCFTA"],
                    "notes": "Atlantic gateway for sub-Saharan Africa to EU/US",
                },
            },
            "africa_gateway": {
                "dza_sahel_corridor": {
                    "country": "DZA",
                    "corridor": "Trans-Saharan Highway",
                    "connects": ["Mali", "Niger", "Nigeria"],
                    "notes": "Key land corridor to sub-Saharan Africa via Sahel",
                },
                "egy_east_africa": {
                    "country": "EGY",
                    "corridor": "Suez Canal + COMESA membership",
                    "connects": ["East Africa", "Horn of Africa", "Southern Africa"],
                    "notes": "COMESA membership enables preferential access to 21 countries",
                },
                "mar_west_africa": {
                    "country": "MAR",
                    "corridor": "Atlantic coast + AfCFTA",
                    "connects": ["West Africa", "Senegal", "Côte d'Ivoire"],
                    "notes": "Morocco-Nigeria gas pipeline project will enhance connectivity",
                },
            },
        }

    # ==================== Opportunity Map ====================

    def get_opportunity_map(
        self,
        sectors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a sectoral investment opportunity map across North Africa.

        For each requested sector, scores all four countries across multiple
        dimensions (cost structure, market access, regulatory environment,
        infrastructure quality) and identifies the best location.

        Args:
            sectors: List of sectors to analyze
                     (automotive, textile, agriculture, renewable_energy, ict, etc.)

        Returns:
            Sector-by-sector opportunity map with country scores
        """
        if sectors is None:
            sectors = ["automotive", "textile", "agriculture", "renewable_energy"]

        # Sector opportunity matrix: {sector: {country: {dimension: score}}}
        sector_profiles: Dict[str, Dict[str, Dict[str, Any]]] = {
            "automotive": {
                "DZA": {
                    "cost_structure": 6,
                    "market_access": 4,
                    "regulatory": 5,
                    "infrastructure": 5,
                    "notes": "Growing domestic market; limited export FTAs",
                },
                "MAR": {
                    "cost_structure": 7,
                    "market_access": 9,
                    "regulatory": 8,
                    "infrastructure": 8,
                    "notes": "Renault, Stellantis plants; Tanger-Med hub for EU export",
                },
                "EGY": {
                    "cost_structure": 8,
                    "market_access": 7,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Large domestic market; growing regional hub",
                },
                "TUN": {
                    "cost_structure": 7,
                    "market_access": 8,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Established components cluster; EU proximity",
                },
            },
            "textile": {
                "DZA": {
                    "cost_structure": 6,
                    "market_access": 4,
                    "regulatory": 5,
                    "infrastructure": 5,
                    "notes": "Large workforce; limited EU/US access",
                },
                "MAR": {
                    "cost_structure": 7,
                    "market_access": 9,
                    "regulatory": 8,
                    "infrastructure": 8,
                    "notes": "Fast-fashion cluster; EU Association near-shoring",
                },
                "EGY": {
                    "cost_structure": 9,
                    "market_access": 8,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "QIZ for US duty-free; very competitive labour cost",
                },
                "TUN": {
                    "cost_structure": 8,
                    "market_access": 9,
                    "regulatory": 8,
                    "infrastructure": 7,
                    "notes": "Offshore regime; most advanced EU integration for textile",
                },
            },
            "agriculture": {
                "DZA": {
                    "cost_structure": 7,
                    "market_access": 4,
                    "regulatory": 5,
                    "infrastructure": 5,
                    "notes": "Fertile Mitidja plain; subsidized inputs; limited exports",
                },
                "MAR": {
                    "cost_structure": 8,
                    "market_access": 9,
                    "regulatory": 8,
                    "infrastructure": 8,
                    "notes": "Plan Maroc Vert; EU seasonal workers; citrus/olive exports",
                },
                "EGY": {
                    "cost_structure": 8,
                    "market_access": 7,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Nile delta fertility; COMESA/GAFTA market access",
                },
                "TUN": {
                    "cost_structure": 7,
                    "market_access": 8,
                    "regulatory": 7,
                    "infrastructure": 6,
                    "notes": "World's largest olive oil exporter; EU origin quotas",
                },
            },
            "renewable_energy": {
                "DZA": {
                    "cost_structure": 9,
                    "market_access": 5,
                    "regulatory": 6,
                    "infrastructure": 6,
                    "notes": "World's largest solar potential; Desertec concept",
                },
                "MAR": {
                    "cost_structure": 8,
                    "market_access": 9,
                    "regulatory": 9,
                    "infrastructure": 8,
                    "notes": "Noor solar complex; 52% renewable target 2030; EU grid connection",
                },
                "EGY": {
                    "cost_structure": 8,
                    "market_access": 7,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Benban solar park; wind corridor Zafarana/Gulf of Suez",
                },
                "TUN": {
                    "cost_structure": 7,
                    "market_access": 8,
                    "regulatory": 7,
                    "infrastructure": 6,
                    "notes": "TuNur solar export project; EU green hydrogen potential",
                },
            },
            "ict": {
                "DZA": {
                    "cost_structure": 7,
                    "market_access": 4,
                    "regulatory": 5,
                    "infrastructure": 5,
                    "notes": "Growing tech ecosystem; large educated workforce",
                },
                "MAR": {
                    "cost_structure": 7,
                    "market_access": 8,
                    "regulatory": 8,
                    "infrastructure": 8,
                    "notes": "Casablanca Finance City; nearshore EU IT services",
                },
                "EGY": {
                    "cost_structure": 8,
                    "market_access": 7,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Smart Village tech park; large developer pool; lower costs",
                },
                "TUN": {
                    "cost_structure": 7,
                    "market_access": 8,
                    "regulatory": 7,
                    "infrastructure": 7,
                    "notes": "Strong EU IT service export; offshore regime for IT firms",
                },
            },
        }

        opportunity_map: Dict[str, Any] = {}
        for sector in sectors:
            sector_lower = sector.lower().replace(" ", "_").replace("-", "_")

            # Try exact match first, then partial match
            profile = sector_profiles.get(sector_lower)
            if profile is None:
                for key in sector_profiles:
                    if key in sector_lower or sector_lower in key:
                        profile = sector_profiles[key]
                        break
            if profile is None:
                # Generic fallback
                profile = {
                    c: {
                        "cost_structure": 6,
                        "market_access": 6,
                        "regulatory": 6,
                        "infrastructure": 6,
                        "notes": "",
                    }
                    for c in NORTH_AFRICA_COUNTRIES
                }

            sector_results = []
            for country_code in NORTH_AFRICA_COUNTRIES:
                scores = profile.get(country_code, {})
                combined = (
                    scores.get("cost_structure", 5) * 0.25
                    + scores.get("market_access", 5) * 0.30
                    + scores.get("regulatory", 5) * 0.25
                    + scores.get("infrastructure", 5) * 0.20
                )
                sector_results.append(
                    {
                        "country_code": country_code,
                        "combined_score": round(combined, 2),
                        "cost_structure": scores.get("cost_structure", 5),
                        "market_access": scores.get("market_access", 5),
                        "regulatory_environment": scores.get("regulatory", 5),
                        "infrastructure_quality": scores.get("infrastructure", 5),
                        "notes": scores.get("notes", ""),
                    }
                )

            sector_results.sort(key=lambda x: x["combined_score"], reverse=True)
            opportunity_map[sector] = {
                "rankings": sector_results,
                "top_country": sector_results[0]["country_code"] if sector_results else None,
            }

        # Summary: best overall country across sectors
        country_totals: Dict[str, float] = {c: 0.0 for c in NORTH_AFRICA_COUNTRIES}
        for sector_data in opportunity_map.values():
            for rec in sector_data["rankings"]:
                country_totals[rec["country_code"]] += rec["combined_score"]

        overall_ranking = sorted(country_totals.items(), key=lambda x: x[1], reverse=True)

        return {
            "sectors_analyzed": sectors,
            "opportunity_map": opportunity_map,
            "overall_ranking": [
                {"country_code": c, "total_score": round(s, 2)} for c, s in overall_ranking
            ],
            "best_overall": overall_ranking[0][0] if overall_ranking else None,
            "generated_at": datetime.utcnow().isoformat(),
        }


# Module-level singleton
_service: Optional[RegionalIntelligenceService] = None


def get_regional_intelligence() -> RegionalIntelligenceService:
    """Get or create the singleton RegionalIntelligenceService."""
    global _service
    if _service is None:
        _service = RegionalIntelligenceService()
    return _service
