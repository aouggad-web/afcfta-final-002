"""
SADC Regional Intelligence Service
====================================
Provides advanced analytics and decision-support for the Southern African
Development Community (SADC) regional trade and investment platform.

Capabilities:
  - Data freshness monitoring for all 16 SADC country datasets
  - Investment opportunity mapping (SEZs, sector strengths)
  - Mining sector value-chain analysis
  - Transport corridor optimization
  - SACU revenue-sharing intelligence
  - Cross-regional comparison (SADC vs EAC, SADC vs CEMAC)
  - Dual-membership handling (Tanzania, DRC)
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_BASE_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Country and regional metadata (imported inline to avoid circular imports)
# ---------------------------------------------------------------------------

SADC_COUNTRY_LIST = [
    "ZAF", "BWA", "NAM", "LSO", "SWZ",  # SACU
    "AGO", "ZMB", "ZWE", "COD",           # Resource Economies
    "MUS", "SYC", "COM",                  # Island Nations
    "MOZ", "MDG", "MWI", "TZA",           # Emerging Markets
]

SACU_MEMBERS = {"ZAF", "BWA", "NAM", "LSO", "SWZ"}
LDC_MEMBERS = {"AGO", "ZMB", "COD", "LSO", "MOZ", "MDG", "MWI", "TZA", "COM"}
DUAL_MEMBERSHIP = {
    "TZA": ["EAC", "SADC"],
    "COD": ["EAC", "SADC"],
}

COUNTRY_NAMES = {
    "ZAF": "South Africa", "BWA": "Botswana", "NAM": "Namibia",
    "LSO": "Lesotho", "SWZ": "Eswatini", "AGO": "Angola",
    "ZMB": "Zambia", "ZWE": "Zimbabwe", "COD": "DR Congo",
    "MUS": "Mauritius", "SYC": "Seychelles", "COM": "Comoros",
    "MOZ": "Mozambique", "MDG": "Madagascar", "MWI": "Malawi",
    "TZA": "Tanzania",
}

SECTOR_STRENGTHS = {
    "ZAF": ["automotive", "mining", "financial_services", "agro_processing"],
    "BWA": ["diamond_mining", "financial_services", "beef_exports", "tourism"],
    "NAM": ["diamond_mining", "fishing", "uranium_mining", "logistics"],
    "LSO": ["textiles", "water_exports", "diamond_mining"],
    "SWZ": ["sugar", "textiles", "forestry", "manufacturing"],
    "AGO": ["oil_gas", "diamond_mining", "agriculture", "construction"],
    "ZMB": ["copper_mining", "agriculture", "energy", "tourism"],
    "ZWE": ["platinum_mining", "tobacco", "agriculture", "tourism"],
    "COD": ["copper_mining", "cobalt_mining", "diamond_mining", "hydropower"],
    "MUS": ["financial_services", "tourism", "textile_manufacturing", "ict"],
    "SYC": ["tourism", "fisheries", "offshore_finance"],
    "COM": ["vanilla", "cloves", "ylang_ylang", "fisheries"],
    "MOZ": ["natural_gas", "coal", "agriculture", "logistics"],
    "MDG": ["vanilla", "textiles", "nickel_mining", "tourism"],
    "MWI": ["tobacco", "tea", "sugar", "manufacturing"],
    "TZA": ["gold_mining", "agriculture", "tourism", "logistics"],
}


class DataFreshnessReport:
    """Tracks data freshness for each SADC country dataset."""

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
            is_fresh = age <= timedelta(days=7)

        self.countries[country_code] = {
            "country_code": country_code,
            "country_name": COUNTRY_NAMES.get(country_code, country_code),
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


class SADCIntelligenceService:
    """
    Advanced analytics service for SADC regional trade and investment intelligence.

    Provides:
    - Data freshness monitoring across all 16 SADC countries
    - Investment opportunity mapping
    - Mining sector value-chain analysis
    - Transport corridor intelligence
    - SACU framework analytics
    - Cross-regional comparison
    """

    def __init__(self):
        self._data_cache: Dict[str, Any] = {}

    # ==================== Data Freshness ====================

    def get_data_freshness(self) -> DataFreshnessReport:
        """Check data freshness for all SADC countries."""
        report = DataFreshnessReport()
        crawled_dir = DATA_BASE_DIR / "crawled"

        for code in SADC_COUNTRY_LIST:
            path = crawled_dir / f"{code}_tariffs.json"
            if not path.exists():
                report.add_country(code, None, 0, None)
                continue
            try:
                mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                count = len(data.get("positions", []))
                report.add_country(code, mtime, count, str(path))
            except Exception as exc:
                logger.warning(f"Could not read {path}: {exc}")
                report.add_country(code, None, 0, str(path))

        return report

    # ==================== Regional Overview ====================

    def get_regional_overview(self) -> Dict[str, Any]:
        """Return a high-level SADC regional overview."""
        return {
            "organisation": {
                "name": "Southern African Development Community",
                "abbreviation": "SADC",
                "founded": 1992,
                "headquarters": "Gaborone, Botswana",
                "member_count": 16,
                "combined_gdp_usd_billion": 800,
                "combined_population_million": 345,
            },
            "sacu": {
                "name": "Southern African Customs Union",
                "members": list(SACU_MEMBERS),
                "description": "Oldest functioning customs union globally (since 1910)",
            },
            "country_groups": {
                "sacu": list(SACU_MEMBERS),
                "ldc_members": list(LDC_MEMBERS),
                "dual_membership": DUAL_MEMBERSHIP,
                "island_nations": ["MUS", "SYC", "COM", "MDG"],
            },
            "key_statistics": {
                "intra_sadc_trade_share_pct": 19,
                "total_trade_usd_billion": 350,
                "largest_economy": "ZAF",
                "world_diamond_production_share_pct": 60,
                "world_platinum_reserves_share_pct": 80,
            },
        }

    # ==================== Investment Intelligence ====================

    def get_investment_zones(self, country_code: Optional[str] = None) -> Dict[str, Any]:
        """Return investment zone data for one or all SADC countries."""
        try:
            from crawlers.countries.sadc.investment_zones import SADC_INVESTMENT_ZONES
        except ImportError:
            return {"error": "Investment zones data not available"}

        if country_code:
            data = SADC_INVESTMENT_ZONES.get(country_code)
            if not data:
                return {"error": f"No investment zone data for {country_code}"}
            return data

        return SADC_INVESTMENT_ZONES

    def recommend_investment_location(
        self, sector: str, priority: str = "infrastructure"
    ) -> List[Dict[str, Any]]:
        """
        Rank SADC countries for a given sector and priority.

        Parameters
        ----------
        sector : str
            Target sector (e.g. "mining", "textiles", "financial_services").
        priority : str
            Ranking priority: "infrastructure" | "tax_incentives" | "market_access" | "stability"
        """
        recommendations = []

        priority_scores = {
            "ZAF": {"infrastructure": 9, "tax_incentives": 7, "market_access": 9, "stability": 8},
            "BWA": {"infrastructure": 8, "tax_incentives": 9, "market_access": 7, "stability": 9},
            "MUS": {"infrastructure": 9, "tax_incentives": 10, "market_access": 8, "stability": 9},
            "NAM": {"infrastructure": 8, "tax_incentives": 8, "market_access": 7, "stability": 8},
            "ZMB": {"infrastructure": 6, "tax_incentives": 8, "market_access": 6, "stability": 7},
            "MOZ": {"infrastructure": 6, "tax_incentives": 7, "market_access": 6, "stability": 6},
            "TZA": {"infrastructure": 7, "tax_incentives": 8, "market_access": 7, "stability": 7},
            "MDG": {"infrastructure": 5, "tax_incentives": 9, "market_access": 6, "stability": 6},
            "SWZ": {"infrastructure": 7, "tax_incentives": 8, "market_access": 8, "stability": 7},
            "LSO": {"infrastructure": 6, "tax_incentives": 8, "market_access": 8, "stability": 7},
            "ZWE": {"infrastructure": 6, "tax_incentives": 7, "market_access": 6, "stability": 6},
            "AGO": {"infrastructure": 6, "tax_incentives": 7, "market_access": 5, "stability": 6},
            "MWI": {"infrastructure": 5, "tax_incentives": 7, "market_access": 5, "stability": 7},
            "COD": {"infrastructure": 4, "tax_incentives": 7, "market_access": 5, "stability": 5},
            "SYC": {"infrastructure": 8, "tax_incentives": 8, "market_access": 7, "stability": 9},
            "COM": {"infrastructure": 4, "tax_incentives": 6, "market_access": 4, "stability": 6},
        }

        sector_lower = sector.lower()
        for code in SADC_COUNTRY_LIST:
            strengths = SECTOR_STRENGTHS.get(code, [])
            sector_match = any(sector_lower in s for s in strengths)
            scores = priority_scores.get(code, {})
            priority_score = scores.get(priority, 5)
            sector_bonus = 2 if sector_match else 0
            total_score = priority_score + sector_bonus

            recommendations.append({
                "country_code": code,
                "country_name": COUNTRY_NAMES.get(code, code),
                "sector_match": sector_match,
                "sector_strengths": strengths,
                "priority_score": priority_score,
                "total_score": total_score,
                "is_sacu": code in SACU_MEMBERS,
                "is_ldc": code in LDC_MEMBERS,
                "dual_memberships": DUAL_MEMBERSHIP.get(code, []),
            })

        recommendations.sort(key=lambda x: x["total_score"], reverse=True)
        return recommendations

    # ==================== Mining Intelligence ====================

    def get_mining_intelligence(self, mineral: Optional[str] = None) -> Dict[str, Any]:
        """Return mining sector intelligence for SADC."""
        try:
            from crawlers.countries.sadc.mining_intelligence import SADC_MINING_INTELLIGENCE
        except ImportError:
            return {"error": "Mining intelligence data not available"}

        if mineral:
            mineral_lower = mineral.lower()
            result = {}
            for key, data in SADC_MINING_INTELLIGENCE.items():
                if mineral_lower in key:
                    result[key] = data
            return result if result else {"error": f"No data for mineral: {mineral}"}

        return SADC_MINING_INTELLIGENCE

    # ==================== Transport Corridors ====================

    def get_transport_corridors(self, country_code: Optional[str] = None) -> Dict[str, Any]:
        """Return transport corridor intelligence."""
        try:
            from crawlers.countries.sadc.transport_corridors import (
                SADC_TRANSPORT_CORRIDORS,
                SADC_MAJOR_PORTS,
            )
        except ImportError:
            return {"error": "Transport corridor data not available"}

        if country_code:
            relevant = {}
            for name, corridor in SADC_TRANSPORT_CORRIDORS.items():
                countries = corridor.get("countries", [])
                if country_code in countries:
                    relevant[name] = corridor
            ports = {
                port: info
                for port, info in SADC_MAJOR_PORTS.items()
                if info.get("country") == country_code
            }
            return {"corridors": relevant, "ports": ports}

        return {
            "corridors": SADC_TRANSPORT_CORRIDORS,
            "ports": SADC_MAJOR_PORTS,
        }

    # ==================== SACU Analytics ====================

    def get_sacu_framework(self) -> Dict[str, Any]:
        """Return the SACU customs union framework details."""
        try:
            from crawlers.countries.sacu_customs_union import (
                SACU_FRAMEWORK,
                SACU_REVENUE_SHARES,
                SACU_CET_BANDS,
            )
            return {
                "framework": SACU_FRAMEWORK,
                "revenue_shares": SACU_REVENUE_SHARES,
                "cet_bands": {str(k): v for k, v in SACU_CET_BANDS.items()},
            }
        except ImportError:
            return {"error": "SACU framework data not available"}

    def calculate_sacu_import_cost(
        self, cif_value: float, hs_chapter: str, destination: str, origin: str = "INTL"
    ) -> Dict[str, Any]:
        """Calculate landed cost for an import at a SACU entry port."""
        try:
            from crawlers.countries.sacu_customs_union import calculate_total_import_cost
            return calculate_total_import_cost(cif_value, hs_chapter, destination, origin)
        except ImportError:
            return {"error": "SACU calculation module not available"}

    # ==================== Trade Protocols ====================

    def get_trade_protocols(self, protocol: Optional[str] = None) -> Dict[str, Any]:
        """Return SADC trade agreements and protocols."""
        try:
            from crawlers.countries.sadc.trade_protocols import SADC_TRADE_PROTOCOLS
        except ImportError:
            return {"error": "Trade protocols data not available"}

        if protocol:
            data = SADC_TRADE_PROTOCOLS.get(protocol)
            if not data:
                return {"error": f"Protocol not found: {protocol}", "available": list(SADC_TRADE_PROTOCOLS.keys())}
            return data

        return SADC_TRADE_PROTOCOLS

    # ==================== Cross-Regional Comparison ====================

    def compare_sadc_eac(self) -> Dict[str, Any]:
        """Compare SADC and EAC regional blocs."""
        return {
            "comparison": {
                "sadc": {
                    "members": 16,
                    "gdp_usd_billion": 800,
                    "population_million": 345,
                    "key_strengths": ["mining", "manufacturing", "financial_services"],
                    "largest_economy": "South Africa (ZAF)",
                    "trade_protocol": "SADC Trade Protocol (FTA since 2008)",
                    "customs_union": "SACU (5 members)",
                    "intra_bloc_trade_share_pct": 19,
                },
                "eac": {
                    "members": 7,
                    "gdp_usd_billion": 320,
                    "population_million": 300,
                    "key_strengths": ["agriculture", "services", "logistics"],
                    "largest_economy": "Tanzania (TZA)",
                    "trade_protocol": "EAC Common Market (2010)",
                    "customs_union": "EAC CET (all 7 members)",
                    "intra_bloc_trade_share_pct": 22,
                },
            },
            "dual_members": {
                "TZA": {"in_both": True, "primary_cet": "EAC", "note": "Tanzania applies EAC CET"},
                "COD": {"in_both": True, "primary_cet": "EAC", "note": "DRC joined EAC in 2022"},
            },
            "complementarity": [
                "SADC mining + EAC logistics = value-chain opportunity",
                "SADC finance hub (MUS, ZAF) + EAC growth markets",
                "Tripartite FTA (SADC+EAC+COMESA) bridges both regions",
            ],
        }

    def compare_sadc_cemac(self) -> Dict[str, Any]:
        """Compare SADC and CEMAC regional blocs."""
        return {
            "comparison": {
                "sadc": {
                    "members": 16,
                    "gdp_usd_billion": 800,
                    "population_million": 345,
                    "currency": "Multiple (ZAR dominant in SACU)",
                    "common_external_tariff": "SACU CET (5 members); others national tariffs",
                },
                "cemac": {
                    "members": 6,
                    "gdp_usd_billion": 120,
                    "population_million": 60,
                    "currency": "XAF (CFA Franc – shared with UEMOA)",
                    "common_external_tariff": "TEC CEMAC (4 bands: 5%, 10%, 20%, 30%)",
                },
            },
            "key_differences": [
                "SADC: much larger economy and population",
                "CEMAC: monetary union with single currency",
                "SADC: deeper integration via SACU customs union",
                "CEMAC: simpler 4-band CET vs SADC's varied national schedules",
            ],
            "connectivity": {
                "countries_in_both": [],
                "geographic_link": "DRC borders CEMAC member Cameroon via Congo River basin",
            },
        }

    # ==================== Country Tariff Data ====================

    def get_country_tariff_data(self, country_code: str) -> Dict[str, Any]:
        """Load tariff data for a specific SADC country from disk."""
        if country_code not in SADC_COUNTRY_LIST:
            return {"error": f"{country_code} is not a SADC member state"}

        path = DATA_BASE_DIR / "crawled" / f"{country_code}_tariffs.json"
        if not path.exists():
            return {
                "country_code": country_code,
                "country_name": COUNTRY_NAMES.get(country_code),
                "error": "Tariff data not yet scraped. Run the SADC member scraper.",
                "scraper": "backend/crawlers/countries/sadc_member_scraper.py",
            }

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Error reading {path}: {exc}")
            return {"error": str(exc)}

    # ==================== Statistics ====================

    def get_trade_statistics(self) -> Dict[str, Any]:
        """Return SADC regional trade statistics."""
        try:
            from crawlers.countries.sadc.trade_protocols import SADC_TRADE_STATISTICS
            return SADC_TRADE_STATISTICS
        except ImportError:
            return {
                "intra_sadc_trade_share_pct": 19,
                "total_sadc_gdp_usd_billion": 800,
                "total_sadc_trade_usd_billion": 350,
                "largest_economy": "ZAF",
                "note": "Trade statistics module not fully loaded",
            }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_sadc_intelligence: Optional[SADCIntelligenceService] = None


def get_sadc_intelligence() -> SADCIntelligenceService:
    """Return (and lazily create) the singleton service instance."""
    global _sadc_intelligence
    if _sadc_intelligence is None:
        _sadc_intelligence = SADCIntelligenceService()
    return _sadc_intelligence
