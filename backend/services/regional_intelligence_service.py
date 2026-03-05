"""
Regional Intelligence Service for North Africa.

Provides advanced analytics and decision support for North African trade:
- Investment opportunity mapping across DZA/MAR/EGY/TUN
- Data freshness monitoring for all country datasets
- Regional trade intelligence reporting
- Best market entry strategy recommendations
- Optimal trade route finder with multi-preference ranking
- Investment location analysis with sector scoring
- Preferential agreement matrix by HS code
- Regional trade flow analytics
- Sectoral opportunity mapping
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

    # ==================== Optimal Trade Route ====================

    def optimal_trade_route(
        self,
        hs_code: str,
        origin_region: str = "sub_saharan_africa",
        target_market: str = "europe",
        annual_volume: float = 1_000_000,
        preferences: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find the optimal North African transit/processing country for a trade lane.

        For goods flowing from an origin region to a target market, ranks the
        four North African countries based on:
        - Customs duty (cost preference)
        - Port throughput / clearance speed (fastest_clearance preference)
        - Trade agreement coverage (most_reliable preference)
        - Special economic zone availability

        Args:
            hs_code: HS tariff code
            origin_region: Origin macro-region (sub_saharan_africa, asia, americas, etc.)
            target_market: Destination market (europe, us, mena, africa, etc.)
            annual_volume: Annual shipment value in USD
            preferences: Ordered list of preferences to weight ranking
                         (lowest_cost, fastest_clearance, most_reliable)

        Returns:
            Ranked list of optimal routes with justification
        """
        if preferences is None:
            preferences = ["lowest_cost", "fastest_clearance", "most_reliable"]

        target_upper = target_market.upper()

        # Country-level suitability data for routing
        country_routing: Dict[str, Dict[str, Any]] = {
            "DZA": {
                "country_name": "Algeria",
                "port_capacity_score": 5,   # Algiers, Oran, Annaba
                "clearance_days_avg": 5,
                "eu_agreement": False,
                "us_agreement": False,
                "comesa": False,
                "afcfta": True,
                "free_zones": [],
                "dd_rate_typical": 15.0,
                "infrastructure_score": 5,
                "reliability_score": 6,
            },
            "MAR": {
                "country_name": "Morocco",
                "port_capacity_score": 9,   # Tanger-Med largest in Africa
                "clearance_days_avg": 2,
                "eu_agreement": True,
                "us_agreement": True,
                "comesa": False,
                "afcfta": True,
                "free_zones": ["Tanger-Med Free Zone", "Casablanca Finance City"],
                "dd_rate_typical": 10.0,
                "infrastructure_score": 8,
                "reliability_score": 8,
            },
            "EGY": {
                "country_name": "Egypt",
                "port_capacity_score": 8,   # Suez Canal gateway
                "clearance_days_avg": 3,
                "eu_agreement": True,
                "us_agreement": True,  # via QIZ
                "comesa": True,
                "afcfta": True,
                "free_zones": ["SCZONE", "Port Said SEZ", "QIZ Zones"],
                "dd_rate_typical": 12.0,
                "infrastructure_score": 7,
                "reliability_score": 7,
            },
            "TUN": {
                "country_name": "Tunisia",
                "port_capacity_score": 6,   # Tunis-La Goulette, Sfax
                "clearance_days_avg": 2,
                "eu_agreement": True,
                "us_agreement": False,
                "comesa": False,
                "afcfta": True,
                "free_zones": ["Offshore enterprise zones", "Economic development zones"],
                "dd_rate_typical": 8.0,
                "infrastructure_score": 7,
                "reliability_score": 8,
            },
        }

        routes = []
        for country_code, profile in country_routing.items():
            # Score based on preferences
            cost_score = max(0, 10 - profile["dd_rate_typical"] / 4)
            clearance_score = max(0, 10 - profile["clearance_days_avg"])
            reliability_score = profile["reliability_score"]

            # Bonus for target market agreements
            agreement_bonus = 0
            if target_upper in ("EUROPE", "EU") and profile["eu_agreement"]:
                agreement_bonus += 2
            if target_upper in ("US", "UNITED_STATES") and profile["us_agreement"]:
                agreement_bonus += 2
            if target_upper in ("COMESA", "EAST_AFRICA") and profile["comesa"]:
                agreement_bonus += 2
            if target_upper in ("AFRICA", "MENA"):
                agreement_bonus += 1  # All have AfCFTA

            # Weighted combined score per preference order
            pref_weights = {"lowest_cost": 0, "fastest_clearance": 0, "most_reliable": 0}
            n = len(preferences)
            for i, pref in enumerate(preferences[:3]):
                pref = pref.lower()
                if pref in pref_weights:
                    pref_weights[pref] = (n - i) / n

            combined = (
                cost_score * pref_weights["lowest_cost"]
                + clearance_score * pref_weights["fastest_clearance"]
                + reliability_score * pref_weights["most_reliable"]
                + agreement_bonus
            )

            annual_duty_estimate = annual_volume * profile["dd_rate_typical"] / 100
            routes.append({
                "country_code": country_code,
                "country_name": profile["country_name"],
                "combined_score": round(combined, 2),
                "cost_score": round(cost_score, 1),
                "clearance_speed_score": round(clearance_score, 1),
                "reliability_score": round(reliability_score, 1),
                "clearance_days_avg": profile["clearance_days_avg"],
                "dd_rate_typical_pct": profile["dd_rate_typical"],
                "annual_duty_estimate_usd": round(annual_duty_estimate, 0),
                "eu_agreement": profile["eu_agreement"],
                "us_agreement": profile["us_agreement"],
                "free_zones": profile["free_zones"],
                "infrastructure_score": profile["infrastructure_score"],
                "port_capacity_score": profile["port_capacity_score"],
            })

        routes.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "hs_code": hs_code,
            "origin_region": origin_region,
            "target_market": target_market,
            "annual_volume_usd": annual_volume,
            "preferences": preferences,
            "routes": routes,
            "optimal_route": routes[0] if routes else None,
            "generated_at": datetime.utcnow().isoformat(),
        }

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
                "labour_cost_index": 4,      # 1=cheapest, 10=most expensive
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
                    "automotive", "aerospace", "textiles", "agriculture",
                    "renewable_energy", "phosphates", "tourism",
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
                    "textiles", "food_processing", "ict", "petrochemicals",
                    "tourism", "construction", "renewable_energy",
                ],
                "labour_cost_index": 3,      # lower cost
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
                    "textiles", "automotive_components", "ict", "olive_oil",
                    "phosphates", "tourism",
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
            # Sector match score
            sector_score = 5  # default
            for strength in profile["sector_strengths"]:
                if strength.replace("_", " ") in industry_lower or industry_lower in strength:
                    sector_score = 9
                    break
                # partial match
                if any(w in industry_lower for w in strength.replace("_", " ").split()):
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

            # Operational cost score (lower cost = higher score)
            cost_score = 10 - (profile["est_op_cost_factor"] * 10 - 5)

            # Investment environment
            env_score = (profile["ease_of_investment"] + profile["infrastructure_quality"]) / 2

            # Weighted combined
            combined = (
                sector_score * 0.30
                + market_score * 0.30
                + env_score * 0.25
                + cost_score * 0.15
            )

            results.append({
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
            })

        results.sort(key=lambda x: x["combined_score"], reverse=True)
        for rank, rec in enumerate(results, 1):
            rec["rank"] = rank

        # Size-adjusted recommendation note
        size_note = ""
        if investment_size >= 50_000_000:
            size_note = "Large-scale investment: Morocco and Egypt offer strongest incentive packages."
        elif investment_size >= 10_000_000:
            size_note = "Mid-scale investment: All four countries offer viable incentive frameworks."
        else:
            size_note = "Smaller investment: Tunisia offshore regime or Morocco CFC may offer best ROI."

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

    # ==================== Preferential Matrix by HS ====================

    def get_preferential_matrix_by_hs(
        self,
        hs_code: str,
    ) -> Dict[str, Any]:
        """
        Return the full preferential trade agreement matrix applicable to a given HS code.

        Cross-references the HS code chapter/section against known
        sector-specific preferences (agricultural, textile, automotive, etc.)
        and returns per-country applicable agreements with indicative rates.

        Args:
            hs_code: HS tariff code (6-10 digits)

        Returns:
            Matrix of {country: [applicable_agreements]} for the HS code
        """
        # Extract the 2-digit chapter from the HS code
        if len(hs_code) < 2:
            raise ValueError(f"Invalid HS code '{hs_code}': must be at least 2 digits")
        try:
            ch_int = int(hs_code[:2])
        except ValueError:
            raise ValueError(f"Invalid HS code '{hs_code}': first two characters must be numeric")
        if ch_int < 1 or ch_int > 99:
            raise ValueError(f"Invalid HS chapter {ch_int}: must be between 01 and 99")

        # Determine product category from chapter
        if 1 <= ch_int <= 24:
            product_category = "agricultural"
        elif 25 <= ch_int <= 27:
            product_category = "minerals_energy"
        elif 28 <= ch_int <= 40:
            product_category = "chemicals_plastics"
        elif 41 <= ch_int <= 63:
            product_category = "textiles_leather"
        elif 64 <= ch_int <= 83:
            product_category = "manufactured_goods"
        elif 84 <= ch_int <= 85:
            product_category = "machinery_electronics"
        elif 86 <= ch_int <= 89:
            product_category = "vehicles_transport"
        elif 90 <= ch_int <= 97:
            product_category = "precision_instruments"
        else:
            product_category = "other"

        # Base agreement matrix
        base_matrix = self.get_preferential_agreements_matrix()["matrix"]

        matrix: Dict[str, Any] = {}
        for country_code, agreements in base_matrix.items():
            applicable = []

            # GAFTA is universal
            if agreements.get("GAFTA"):
                applicable.append({
                    "agreement": "Arab Free Trade Area (GAFTA)",
                    "markets": "Arab countries",
                    "indicative_dd_reduction": "0-100%",
                    "notes": "Applies to most goods",
                })

            # AfCFTA - universal
            applicable.append({
                "agreement": "African Continental FTA (AfCFTA)",
                "markets": "Africa (54 countries)",
                "indicative_dd_reduction": "Phased to 0% over schedule",
                "notes": "Tariff phase-down per national schedule",
            })

            # EU Association
            if agreements.get("EU"):
                dd_reduction = "0%" if product_category not in ("agricultural",) else "reduced"
                applicable.append({
                    "agreement": "EU Association Agreement",
                    "markets": "European Union (27 members)",
                    "indicative_dd_reduction": dd_reduction,
                    "notes": (
                        "Most preferential rates; agricultural products may have quotas"
                        if product_category == "agricultural"
                        else "Duty-free for industrial products"
                    ),
                })

            # EFTA
            if agreements.get("EFTA"):
                applicable.append({
                    "agreement": "EFTA Agreement",
                    "markets": "Switzerland, Norway, Iceland, Liechtenstein",
                    "indicative_dd_reduction": "0-100%",
                    "notes": "Similar to EU; mainly industrial goods",
                })

            # Agadir (MAR, EGY, TUN + Jordan)
            if agreements.get("Agadir"):
                applicable.append({
                    "agreement": "Agadir Agreement",
                    "markets": "Morocco, Egypt, Tunisia, Jordan",
                    "indicative_dd_reduction": "0%",
                    "notes": "Full liberalisation within member states",
                })

            # US via Morocco FTA
            if agreements.get("US") and country_code == "MAR":
                applicable.append({
                    "agreement": "US-Morocco FTA",
                    "markets": "United States",
                    "indicative_dd_reduction": "0-100% (phased)",
                    "notes": "Comprehensive bilateral FTA since 2006",
                })

            # QIZ (Egypt specific)
            if agreements.get("QIZ") and country_code == "EGY":
                applicable.append({
                    "agreement": "QIZ (Qualified Industrial Zones)",
                    "markets": "United States",
                    "indicative_dd_reduction": "0%",
                    "notes": (
                        "Duty-free US access for qualifying manufactured goods "
                        "with Israeli content requirement"
                    ),
                })

            # COMESA (Egypt)
            if agreements.get("COMESA") and country_code == "EGY":
                applicable.append({
                    "agreement": "COMESA Preferential Rates",
                    "markets": "COMESA member states (21 countries)",
                    "indicative_dd_reduction": "0-80%",
                    "notes": "Common Market for Eastern and Southern Africa",
                })

            # Turkey FTA
            if agreements.get("Turkey"):
                applicable.append({
                    "agreement": "Turkey FTA",
                    "markets": "Turkey",
                    "indicative_dd_reduction": "0-100% (sector dependent)",
                    "notes": "Bilateral FTA covering industrial and agricultural goods",
                })

            matrix[country_code] = {
                "applicable_agreements": applicable,
                "agreement_count": len(applicable),
                "has_eu_access": bool(agreements.get("EU")),
                "has_us_access": bool(agreements.get("US") or agreements.get("QIZ")),
                "has_africa_access": True,  # all have AfCFTA
            }

        return {
            "hs_code": hs_code,
            "hs_chapter": f"{ch_int:02d}",
            "product_category": product_category,
            "matrix": matrix,
            "best_for_eu_access": [c for c, d in matrix.items() if d["has_eu_access"]],
            "best_for_us_access": [c for c, d in matrix.items() if d["has_us_access"]],
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
                    "dd_reduction": "0% on industrial goods",
                    "notes": "Most integrated EU supply chain partner in North Africa",
                },
                "tun_deep_integration": {
                    "country": "TUN",
                    "agreement": "EU Association Agreement (most advanced in region)",
                    "key_sectors": ["Textiles", "Automotive components", "ICT", "Olive oil"],
                    "port": "Tunis-La Goulette",
                    "dd_reduction": "0% on industrial goods",
                    "notes": "Preparing DCFTA (Deep Comprehensive FTA) for deeper integration",
                },
                "egy_eu_partnership": {
                    "country": "EGY",
                    "agreement": "EU Partnership Agreement",
                    "key_sectors": ["Textiles", "Chemicals", "Food"],
                    "port": "Port Said, Alexandria",
                    "dd_reduction": "Progressive reduction",
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
                    "cost_structure": 6, "market_access": 4, "regulatory": 5, "infrastructure": 5,
                    "notes": "Growing domestic market; limited export FTAs",
                },
                "MAR": {
                    "cost_structure": 7, "market_access": 9, "regulatory": 8, "infrastructure": 8,
                    "notes": "Renault, Stellantis plants; Tanger-Med hub for EU export",
                },
                "EGY": {
                    "cost_structure": 8, "market_access": 7, "regulatory": 7, "infrastructure": 7,
                    "notes": "Large domestic market; growing regional hub",
                },
                "TUN": {
                    "cost_structure": 7, "market_access": 8, "regulatory": 7, "infrastructure": 7,
                    "notes": "Established components cluster; EU proximity",
                },
            },
            "textile": {
                "DZA": {
                    "cost_structure": 6, "market_access": 4, "regulatory": 5, "infrastructure": 5,
                    "notes": "Large workforce; limited EU/US access",
                },
                "MAR": {
                    "cost_structure": 7, "market_access": 9, "regulatory": 8, "infrastructure": 8,
                    "notes": "Fast-fashion cluster; EU Association near-shoring",
                },
                "EGY": {
                    "cost_structure": 9, "market_access": 8, "regulatory": 7, "infrastructure": 7,
                    "notes": "QIZ for US duty-free; very competitive labour cost",
                },
                "TUN": {
                    "cost_structure": 8, "market_access": 9, "regulatory": 8, "infrastructure": 7,
                    "notes": "Offshore regime; most advanced EU integration for textile",
                },
            },
            "agriculture": {
                "DZA": {
                    "cost_structure": 7, "market_access": 4, "regulatory": 5, "infrastructure": 5,
                    "notes": "Fertile Mitidja plain; subsidized inputs; limited exports",
                },
                "MAR": {
                    "cost_structure": 8, "market_access": 9, "regulatory": 8, "infrastructure": 8,
                    "notes": "Plan Maroc Vert; EU seasonal workers; citrus/olive exports",
                },
                "EGY": {
                    "cost_structure": 8, "market_access": 7, "regulatory": 7, "infrastructure": 7,
                    "notes": "Nile delta fertility; COMESA/GAFTA market access",
                },
                "TUN": {
                    "cost_structure": 7, "market_access": 8, "regulatory": 7, "infrastructure": 6,
                    "notes": "World's largest olive oil exporter; EU origin quotas",
                },
            },
            "renewable_energy": {
                "DZA": {
                    "cost_structure": 9, "market_access": 5, "regulatory": 6, "infrastructure": 6,
                    "notes": "World's largest solar potential; Desertec concept",
                },
                "MAR": {
                    "cost_structure": 8, "market_access": 9, "regulatory": 9, "infrastructure": 8,
                    "notes": "Noor solar complex; 52% renewable target 2030; EU grid connection",
                },
                "EGY": {
                    "cost_structure": 8, "market_access": 7, "regulatory": 7, "infrastructure": 7,
                    "notes": "Benban solar park; wind corridor Zafarana/Gulf of Suez",
                },
                "TUN": {
                    "cost_structure": 7, "market_access": 8, "regulatory": 7, "infrastructure": 6,
                    "notes": "TuNur solar export project; EU green hydrogen potential",
                },
            },
            "ict": {
                "DZA": {
                    "cost_structure": 7, "market_access": 4, "regulatory": 5, "infrastructure": 5,
                    "notes": "Growing tech ecosystem; large educated workforce",
                },
                "MAR": {
                    "cost_structure": 7, "market_access": 8, "regulatory": 8, "infrastructure": 8,
                    "notes": "Casablanca Finance City; nearshore EU IT services",
                },
                "EGY": {
                    "cost_structure": 8, "market_access": 7, "regulatory": 7, "infrastructure": 7,
                    "notes": "Smart Village tech park; large developer pool; lower costs",
                },
                "TUN": {
                    "cost_structure": 7, "market_access": 8, "regulatory": 7, "infrastructure": 7,
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
                    c: {"cost_structure": 6, "market_access": 6, "regulatory": 6, "infrastructure": 6, "notes": ""}
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
                sector_results.append({
                    "country_code": country_code,
                    "combined_score": round(combined, 2),
                    "cost_structure": scores.get("cost_structure", 5),
                    "market_access": scores.get("market_access", 5),
                    "regulatory_environment": scores.get("regulatory", 5),
                    "infrastructure_quality": scores.get("infrastructure", 5),
                    "notes": scores.get("notes", ""),
                })

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
                {"country_code": c, "total_score": round(s, 2)}
                for c, s in overall_ranking
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
