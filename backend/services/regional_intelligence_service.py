"""
Regional Intelligence Service for North Africa.

Provides advanced analytics and decision support for North African trade:
- Investment opportunity mapping across DZA/MAR/EGY/TUN
- Data freshness monitoring for all country datasets
- Regional trade intelligence reporting
- Best market entry strategy recommendations
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.regional_config import (
    NORTH_AFRICA_COUNTRIES,
    REGIONAL_CONFIG,
    NORTH_AFRICA_VAT_RATES,
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

    def build_investment_map(self) -> Dict[str, Any]:
        """
        Build an investment opportunity map across North African countries.

        Compares:
        - Regulatory environment (tariff complexity, trade agreements)
        - Market access (EU, US, Arab, African markets)
        - Special economic zones and incentives
        - Tax burden profiles
        - Strategic geographic position
        """
        investment_map = {}

        country_profiles = {
            "DZA": {
                "country_name": "Algeria",
                "market_size_gdp_bn_usd": 190,
                "population_m": 45,
                "strategic_position": "Sahel gateway, Mediterranean coast",
                "key_sectors": ["Hydrocarbons", "Agriculture", "Manufacturing"],
                "trade_agreements_count": 4,
                "eu_access": False,
                "us_access": False,
                "port_access": ["Algiers", "Oran", "Annaba"],
                "special_zones": [],
                "vat_rate": NORTH_AFRICA_VAT_RATES["DZA"],
                "investment_score": 6.0,
                "notes": "Large domestic market, hydrocarbons dominance, import controls",
            },
            "MAR": {
                "country_name": "Morocco",
                "market_size_gdp_bn_usd": 134,
                "population_m": 37,
                "strategic_position": "EU gateway, Atlantic + Mediterranean",
                "key_sectors": ["Automotive", "Aerospace", "Agriculture", "Tourism"],
                "trade_agreements_count": 7,
                "eu_access": True,
                "us_access": True,
                "port_access": ["Tanger-Med (largest in Africa)", "Casablanca", "Agadir"],
                "special_zones": ["Tanger-Med Free Zone", "Casablanca Finance City"],
                "vat_rate": NORTH_AFRICA_VAT_RATES["MAR"],
                "investment_score": 8.5,
                "notes": "Most FTAs in region, EU automotive supply chain integration",
            },
            "EGY": {
                "country_name": "Egypt",
                "market_size_gdp_bn_usd": 400,
                "population_m": 105,
                "strategic_position": "Suez Canal, MENA hub, Africa bridge",
                "key_sectors": ["Textiles", "Food Processing", "ICT", "Petrochemicals"],
                "trade_agreements_count": 6,
                "eu_access": True,
                "us_access": True,  # via QIZ
                "port_access": ["Port Said", "Alexandria", "Suez"],
                "special_zones": ["SCZONE (Suez Canal)", "QIZ Zones", "New Capital SEZ"],
                "vat_rate": NORTH_AFRICA_VAT_RATES["EGY"],
                "investment_score": 7.5,
                "notes": "Largest market (105M), QIZ US access, COMESA regional hub",
            },
            "TUN": {
                "country_name": "Tunisia",
                "market_size_gdp_bn_usd": 46,
                "population_m": 12,
                "strategic_position": "Mediterranean bridge, EU proximity",
                "key_sectors": ["Textiles", "Automotive", "ICT", "Olive Oil"],
                "trade_agreements_count": 6,
                "eu_access": True,
                "us_access": False,
                "port_access": ["Tunis-La Goulette", "Sfax", "Bizerte"],
                "special_zones": ["Offshore enterprise regime", "Economic development zones"],
                "vat_rate": NORTH_AFRICA_VAT_RATES["TUN"],
                "investment_score": 7.0,
                "notes": "Most advanced EU association, textile/automotive expertise",
            },
        }

        for country_code, profile in country_profiles.items():
            investment_map[country_code] = profile

        # Add ranking
        ranked = sorted(
            investment_map.items(),
            key=lambda x: x[1]["investment_score"],
            reverse=True,
        )
        for rank, (code, _) in enumerate(ranked, 1):
            investment_map[code]["rank"] = rank

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "countries": investment_map,
            "top_ranked": ranked[0][0] if ranked else None,
            "notes": (
                "Investment scores are indicative only. "
                "Consult official sources for binding rates and incentives."
            ),
        }

    def recommend_market_entry(
        self,
        sector: str,
        origin_country: str = "INTL",
        target_market_size: str = "large",
        priority: str = "eu_access",
    ) -> Dict[str, Any]:
        """
        Recommend the best North African market entry country for a given sector.

        Args:
            sector: Industry sector (automotive, textiles, agriculture, etc.)
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
                "hydrocarbons": 10, "agriculture": 7, "manufacturing": 5,
                "eu_access": 2, "us_access": 1, "regional_hub": 5, "cost": 6,
            },
            "MAR": {
                "automotive": 10, "aerospace": 9, "agriculture": 8, "textiles": 7,
                "eu_access": 10, "us_access": 8, "regional_hub": 7, "cost": 7,
            },
            "EGY": {
                "textiles": 9, "food_processing": 9, "ict": 8, "petrochemicals": 8,
                "eu_access": 7, "us_access": 8, "regional_hub": 10, "cost": 6,
            },
            "TUN": {
                "textiles": 10, "automotive": 8, "ict": 8, "olive_oil": 10,
                "eu_access": 9, "us_access": 3, "regional_hub": 5, "cost": 7,
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

            combined = (sector_score * 0.6 + priority_score * 0.4)
            recommendations.append({
                "country_code": country_code,
                "sector_score": sector_score,
                "priority_score": priority_score,
                "combined_score": round(combined, 1),
            })

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
        }

        # Identify best country per external market
        external_markets = ["EU", "US", "EFTA", "COMESA", "QIZ"]
        best_by_market = {}
        for market in external_markets:
            countries_with_access = [
                c for c, agreements in matrix.items()
                if agreements.get(market)
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


# Module-level singleton
_service: Optional[RegionalIntelligenceService] = None


def get_regional_intelligence() -> RegionalIntelligenceService:
    """Get or create the singleton RegionalIntelligenceService."""
    global _service
    if _service is None:
        _service = RegionalIntelligenceService()
    return _service
