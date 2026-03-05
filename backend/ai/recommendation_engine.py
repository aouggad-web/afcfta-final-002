"""
Personalized Recommendation Engine for AfCFTA investment opportunities.

Matches investor profiles to curated African investment opportunities
without requiring any external ML libraries.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Opportunity catalogue
# ---------------------------------------------------------------------------

_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "opportunity_id": "NG-TECH-001",
        "country": "Nigeria",
        "sector": "technology",
        "title": "Lagos Fintech Hub Expansion",
        "description": "Scale a digital payments platform targeting Nigeria's 80M+ unbanked population.",
        "roi_projection_pct": 28.5,
        "min_investment_usd": 500_000,
        "max_investment_usd": 20_000_000,
        "risk_level": "high",
        "time_horizon_years": 5,
        "key_advantages": [
            "Largest fintech ecosystem in Africa",
            "Young, tech-savvy population",
            "Mobile money penetration growing 35% YoY",
            "CBN sandbox regulatory framework",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 5,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "20%",
            "regulatory_approvals": ["CBN licence", "SEC registration"],
            "local_employment_target": 50,
        },
        "base_confidence": 0.82,
        "geographic_region": "West Africa",
        "tags": ["fintech", "payments", "mobile", "digital"],
    },
    {
        "opportunity_id": "KE-TECH-001",
        "country": "Kenya",
        "sector": "technology",
        "title": "Nairobi Silicon Savannah AI Platform",
        "description": "Build AI-driven agri-tech and health-tech SaaS products for East African SMEs.",
        "roi_projection_pct": 32.0,
        "min_investment_usd": 250_000,
        "max_investment_usd": 5_000_000,
        "risk_level": "high",
        "time_horizon_years": 4,
        "key_advantages": [
            "Highest internet penetration in East Africa (85%)",
            "M-Pesa infrastructure for seamless payments",
            "Strong developer talent pool",
            "AfCFTA gateway to 500M+ East African consumers",
        ],
        "incentives_package": {
            "pioneer_status": False,
            "tax_holiday_years": 0,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["CA Kenya registration"],
            "local_employment_target": 20,
        },
        "base_confidence": 0.85,
        "geographic_region": "East Africa",
        "tags": ["AI", "SaaS", "agritech", "healthtech"],
    },
    {
        "opportunity_id": "ZA-ENERGY-001",
        "country": "South Africa",
        "sector": "energy",
        "title": "Renewable Energy Independent Power Producer",
        "description": "Develop utility-scale solar/wind capacity under South Africa's REIPPPP programme.",
        "roi_projection_pct": 14.5,
        "min_investment_usd": 5_000_000,
        "max_investment_usd": 500_000_000,
        "risk_level": "low",
        "time_horizon_years": 20,
        "key_advantages": [
            "Government-backed 20-year power purchase agreements",
            "Largest electricity market in Africa",
            "World-class solar irradiance in Northern Cape",
            "Established REIPPPP regulatory framework",
        ],
        "incentives_package": {
            "pioneer_status": False,
            "tax_holiday_years": 0,
            "import_duty_waiver": False,
            "repatriation_freedom": True,
            "accelerated_depreciation": True,
            "section_12b_allowance": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "30% BEE ownership",
            "regulatory_approvals": ["NERSA licence", "DEA EIA"],
            "local_employment_target": 200,
        },
        "base_confidence": 0.91,
        "geographic_region": "Southern Africa",
        "tags": ["solar", "wind", "renewable", "power", "REIPPPP"],
    },
    {
        "opportunity_id": "EG-MFG-001",
        "country": "Egypt",
        "sector": "manufacturing",
        "title": "Suez Canal Economic Zone Advanced Manufacturing",
        "description": "Establish light manufacturing for export to EU and Gulf markets from SCZone.",
        "roi_projection_pct": 19.0,
        "min_investment_usd": 1_000_000,
        "max_investment_usd": 100_000_000,
        "risk_level": "medium",
        "time_horizon_years": 8,
        "key_advantages": [
            "Strategic location linking Africa, Europe & Gulf",
            "10-year tax holiday in SCZone",
            "Competitive labour costs (USD 200–400/month)",
            "EU DCFTA preferential access",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 10,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
            "customs_suspension": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["GAFI registration", "SCZone permit"],
            "local_employment_target": 75,
        },
        "base_confidence": 0.79,
        "geographic_region": "North Africa",
        "tags": ["manufacturing", "export", "SEZ", "Suez"],
    },
    {
        "opportunity_id": "MA-LOGISTICS-001",
        "country": "Morocco",
        "sector": "logistics",
        "title": "Tanger Med Logistics & Distribution Hub",
        "description": "Operate a pan-African logistics and 3PL facility at the world's largest African port.",
        "roi_projection_pct": 17.5,
        "min_investment_usd": 2_000_000,
        "max_investment_usd": 150_000_000,
        "risk_level": "low",
        "time_horizon_years": 10,
        "key_advantages": [
            "Tanger Med: #1 port in Africa by capacity",
            "Direct ferry links to 30+ European ports",
            "Free zone with full profit repatriation",
            "Stable currency (pegged MAD)",
        ],
        "incentives_package": {
            "pioneer_status": False,
            "tax_holiday_years": 5,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
            "vat_exemption": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["Tanger Med Special Agency permit"],
            "local_employment_target": 100,
        },
        "base_confidence": 0.88,
        "geographic_region": "North Africa",
        "tags": ["logistics", "port", "3PL", "distribution", "free zone"],
    },
    {
        "opportunity_id": "RW-HEALTH-001",
        "country": "Rwanda",
        "sector": "healthcare",
        "title": "Kigali Medical Tourism & Diagnostics Centre",
        "description": "Develop a regional diagnostic imaging and specialist outpatient centre.",
        "roi_projection_pct": 22.0,
        "min_investment_usd": 1_500_000,
        "max_investment_usd": 30_000_000,
        "risk_level": "medium",
        "time_horizon_years": 7,
        "key_advantages": [
            "East Africa's safest and cleanest business environment",
            "#1 ease of doing business in East Africa",
            "Government health insurance covers 90% of population",
            "Growing medical tourism from DRC, Uganda, Burundi",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 7,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["Rwanda FDA licence", "RDB registration"],
            "local_employment_target": 40,
        },
        "base_confidence": 0.80,
        "geographic_region": "East Africa",
        "tags": ["healthcare", "diagnostics", "medical tourism", "hospital"],
    },
    {
        "opportunity_id": "CI-AGRI-001",
        "country": "Côte d'Ivoire",
        "sector": "agriculture",
        "title": "Cocoa Value Chain Industrialisation",
        "description": "Invest in cocoa processing and chocolate manufacturing to capture downstream value.",
        "roi_projection_pct": 21.0,
        "min_investment_usd": 3_000_000,
        "max_investment_usd": 80_000_000,
        "risk_level": "medium",
        "time_horizon_years": 8,
        "key_advantages": [
            "World's largest cocoa producer (45% global supply)",
            "CFA franc stability (pegged to EUR)",
            "Preferential EU access (EPA agreement)",
            "Government-backed cocoa transformation programme",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 8,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
            "export_incentive_pct": 15,
        },
        "investment_requirements": {
            "minimum_local_partnership": "15% recommended",
            "regulatory_approvals": ["CEPICI registration", "FGCCC approval"],
            "local_employment_target": 120,
        },
        "base_confidence": 0.77,
        "geographic_region": "West Africa",
        "tags": ["cocoa", "agro-processing", "food", "export"],
    },
    {
        "opportunity_id": "ET-MFG-001",
        "country": "Ethiopia",
        "sector": "manufacturing",
        "title": "Addis Ababa Industrial Park – Apparel & Textiles",
        "description": "Set up garment manufacturing in Ethiopia for export to US (AGOA) and EU markets.",
        "roi_projection_pct": 24.0,
        "min_investment_usd": 2_000_000,
        "max_investment_usd": 50_000_000,
        "risk_level": "high",
        "time_horizon_years": 6,
        "key_advantages": [
            "Lowest labour costs in Africa (USD 35–60/month)",
            "Duty-free access to US under AGOA",
            "Government-built industrial parks with plug-and-play utilities",
            "Large, youthful workforce (60M+ aged 15–35)",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 10,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
            "land_lease_subsidy": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["EIC registration", "Industrial park admission"],
            "local_employment_target": 300,
        },
        "base_confidence": 0.73,
        "geographic_region": "East Africa",
        "tags": ["textiles", "apparel", "AGOA", "export", "industrial park"],
    },
    {
        "opportunity_id": "GH-FIN-001",
        "country": "Ghana",
        "sector": "finance",
        "title": "Ghana Digital Banking & Microfinance Platform",
        "description": "Launch a mobile-first digital bank targeting Ghana's 15M unbanked adults.",
        "roi_projection_pct": 25.0,
        "min_investment_usd": 1_000_000,
        "max_investment_usd": 15_000_000,
        "risk_level": "medium",
        "time_horizon_years": 5,
        "key_advantages": [
            "High mobile penetration (130% SIM card rate)",
            "BoG fintech sandbox for rapid licensing",
            "English-speaking, educated workforce",
            "Stable democracy with strong institutions",
        ],
        "incentives_package": {
            "pioneer_status": False,
            "tax_holiday_years": 5,
            "import_duty_waiver": False,
            "repatriation_freedom": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "None required",
            "regulatory_approvals": ["Bank of Ghana licence", "SEC registration"],
            "local_employment_target": 35,
        },
        "base_confidence": 0.78,
        "geographic_region": "West Africa",
        "tags": ["fintech", "microfinance", "digital banking", "mobile money"],
    },
    {
        "opportunity_id": "TZ-AGRI-001",
        "country": "Tanzania",
        "sector": "agriculture",
        "title": "Tanzania Grain Belt Irrigation & Export Hub",
        "description": "Develop large-scale irrigated grain farming and post-harvest storage infrastructure.",
        "roi_projection_pct": 18.0,
        "min_investment_usd": 5_000_000,
        "max_investment_usd": 200_000_000,
        "risk_level": "medium",
        "time_horizon_years": 10,
        "key_advantages": [
            "44M hectares of arable land, <15% cultivated",
            "Political stability and secure land tenure framework",
            "Growing export corridor to Middle East and Asia",
            "Preferential SADC and EAC tariff access",
        ],
        "incentives_package": {
            "pioneer_status": True,
            "tax_holiday_years": 5,
            "import_duty_waiver": True,
            "repatriation_freedom": True,
            "agricultural_input_subsidy": True,
        },
        "investment_requirements": {
            "minimum_local_partnership": "10% recommended",
            "regulatory_approvals": ["TIC certificate", "Ministry of Agriculture permit"],
            "local_employment_target": 250,
        },
        "base_confidence": 0.74,
        "geographic_region": "East Africa",
        "tags": ["grain", "irrigation", "agribusiness", "food security"],
    },
]

# Build a lookup by opportunity_id
_OPPORTUNITY_INDEX: dict[str, dict[str, Any]] = {
    opp["opportunity_id"]: opp for opp in _OPPORTUNITIES
}

# ---------------------------------------------------------------------------
# Matching utilities
# ---------------------------------------------------------------------------

def _risk_compat(opp_risk: str, tolerance: str) -> float:
    """Return 0–1 compatibility score between opportunity risk and user tolerance."""
    _order = {"low": 0, "medium": 1, "high": 2}
    opp_v = _order.get(opp_risk, 1)
    tol_v = _order.get(tolerance, 1)
    diff = abs(opp_v - tol_v)
    return 1.0 if diff == 0 else (0.6 if diff == 1 else 0.2)


def _investment_size_compat(opp: dict[str, Any], investment_usd: float) -> float:
    lo = opp.get("min_investment_usd", 0)
    hi = opp.get("max_investment_usd", float("inf"))
    if lo <= investment_usd <= hi:
        return 1.0
    if investment_usd < lo:
        gap = (lo - investment_usd) / lo
        return max(0.0, 1 - gap)
    return 0.9  # over-capitalized is fine


def _sector_preference_score(opp_sector: str, prefs: list[str]) -> float:
    if not prefs:
        return 0.5
    prefs_lower = [p.lower() for p in prefs]
    return 1.0 if opp_sector.lower() in prefs_lower else 0.0


def _geo_preference_score(opp: dict[str, Any], geo_prefs: list[str]) -> float:
    if not geo_prefs:
        return 0.5
    prefs_lower = [g.lower() for g in geo_prefs]
    country = opp.get("country", "").lower()
    region = opp.get("geographic_region", "").lower()
    if country in prefs_lower or region in prefs_lower:
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Recommendation dataclass
# ---------------------------------------------------------------------------

@dataclass
class InvestmentOpportunity:
    opportunity_id: str
    country: str
    sector: str
    title: str
    confidence_score: float
    match_score: float
    roi_projection: float
    key_advantages: list[str]
    investment_requirements: dict[str, Any]
    incentives_package: dict[str, Any]
    risk_level: str
    time_horizon_years: int
    description: str
    geographic_region: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "country": self.country,
            "sector": self.sector,
            "title": self.title,
            "confidence_score": round(self.confidence_score, 3),
            "match_score": round(self.match_score, 3),
            "roi_projection": round(self.roi_projection, 1),
            "key_advantages": self.key_advantages,
            "investment_requirements": self.investment_requirements,
            "incentives_package": self.incentives_package,
            "risk_level": self.risk_level,
            "time_horizon_years": self.time_horizon_years,
            "description": self.description,
            "geographic_region": self.geographic_region,
        }


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class PersonalizedRecommendationEngine:
    """Match investor profiles to curated AfCFTA investment opportunities."""

    def __init__(self) -> None:
        self._opportunities = _OPPORTUNITIES
        self._index = _OPPORTUNITY_INDEX

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_recommendations(
        self,
        user_profile: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the top *limit* investment opportunities ranked by match score.

        Parameters
        ----------
        user_profile:
            ``risk_tolerance``        – 'low' | 'medium' | 'high'
            ``sector_preferences``    – list[str]  (e.g. ['technology', 'energy'])
            ``investment_size``       – float (USD amount available)
            ``geographic_preferences``– list[str]  (country names or region names)
        limit:
            Maximum number of recommendations to return.
        """
        risk = user_profile.get("risk_tolerance", "medium")
        sector_prefs: list[str] = user_profile.get("sector_preferences", [])
        inv_size: float = float(user_profile.get("investment_size", 1_000_000))
        geo_prefs: list[str] = user_profile.get("geographic_preferences", [])

        scored: list[tuple[float, float, dict[str, Any]]] = []

        for opp in self._opportunities:
            risk_s = _risk_compat(opp["risk_level"], risk)
            sector_s = _sector_preference_score(opp["sector"], sector_prefs)
            size_s = _investment_size_compat(opp, inv_size)
            geo_s = _geo_preference_score(opp, geo_prefs)

            # Weighted combination
            match_score = (
                risk_s * 0.30
                + sector_s * 0.35
                + size_s * 0.20
                + geo_s * 0.15
            )

            # Blend with base confidence
            confidence = opp["base_confidence"] * 0.6 + match_score * 0.4

            scored.append((match_score, confidence, opp))

        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)

        results = []
        for match_score, confidence, opp in scored[:limit]:
            rec = InvestmentOpportunity(
                opportunity_id=opp["opportunity_id"],
                country=opp["country"],
                sector=opp["sector"],
                title=opp["title"],
                confidence_score=confidence,
                match_score=match_score,
                roi_projection=opp["roi_projection_pct"],
                key_advantages=opp["key_advantages"],
                investment_requirements=opp["investment_requirements"],
                incentives_package=opp["incentives_package"],
                risk_level=opp["risk_level"],
                time_horizon_years=opp["time_horizon_years"],
                description=opp["description"],
                geographic_region=opp["geographic_region"],
            )
            results.append(rec.to_dict())

        return results

    def get_opportunity_details(self, opportunity_id: str) -> dict[str, Any] | None:
        """Return full details for a single opportunity by ID, or None if not found."""
        return self._index.get(opportunity_id)

    def get_opportunities_by_sector(self, sector: str) -> list[dict[str, Any]]:
        """Return all opportunities for a given sector."""
        return [o for o in self._opportunities if o["sector"].lower() == sector.lower()]

    def get_opportunities_by_country(self, country: str) -> list[dict[str, Any]]:
        """Return all opportunities for a given country."""
        return [o for o in self._opportunities if o["country"].lower() == country.lower()]

    def list_sectors(self) -> list[str]:
        """Return the unique list of sectors in the catalogue."""
        return sorted({o["sector"] for o in self._opportunities})

    def list_countries(self) -> list[str]:
        """Return the unique list of countries in the catalogue."""
        return sorted({o["country"] for o in self._opportunities})
