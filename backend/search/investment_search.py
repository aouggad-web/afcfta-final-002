"""
Investment Opportunity Search Engine.

Multi-dimensional filtering across country, region, sector and financial criteria.
"""

from __future__ import annotations

from typing import Any

_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "id": "NG-AGRI-001",
        "country": "Nigeria",
        "region": "West Africa",
        "sector": "agriculture",
        "sub_sector": "cassava processing",
        "title": "Nigeria Cassava Value Chain Hub",
        "description": "Industrial cassava starch and ethanol production serving local and export markets.",
        "investment_size_usd": 8_000_000,
        "roi_pct": 22.0,
        "risk_tolerance": "medium",
        "payback_years": 4,
        "status": "open",
    },
    {
        "id": "KE-TECH-001",
        "country": "Kenya",
        "region": "East Africa",
        "sector": "technology",
        "sub_sector": "fintech",
        "title": "Nairobi Digital Payments Platform",
        "description": "Mobile-first B2B payments infrastructure for East African SMEs.",
        "investment_size_usd": 2_500_000,
        "roi_pct": 35.0,
        "risk_tolerance": "high",
        "payback_years": 3,
        "status": "open",
    },
    {
        "id": "ZA-ENERGY-001",
        "country": "South Africa",
        "region": "Southern Africa",
        "sector": "energy",
        "sub_sector": "solar",
        "title": "Western Cape Solar Farm",
        "description": "100 MW utility-scale solar PV project with 20-year PPA.",
        "investment_size_usd": 85_000_000,
        "roi_pct": 14.5,
        "risk_tolerance": "low",
        "payback_years": 8,
        "status": "open",
    },
    {
        "id": "ET-MANUF-001",
        "country": "Ethiopia",
        "region": "East Africa",
        "sector": "manufacturing",
        "sub_sector": "textiles",
        "title": "Hawassa Industrial Park – Textile Expansion",
        "description": "Garment manufacturing for EU and US export markets leveraging AGOA/EBA preferences.",
        "investment_size_usd": 12_000_000,
        "roi_pct": 19.0,
        "risk_tolerance": "medium",
        "payback_years": 5,
        "status": "open",
    },
    {
        "id": "MA-TOURISM-001",
        "country": "Morocco",
        "region": "North Africa",
        "sector": "tourism",
        "sub_sector": "eco-tourism",
        "title": "Atlas Mountain Eco-Resort",
        "description": "Sustainable luxury eco-resort targeting European and Gulf tourists.",
        "investment_size_usd": 15_000_000,
        "roi_pct": 17.0,
        "risk_tolerance": "low",
        "payback_years": 6,
        "status": "open",
    },
    {
        "id": "GH-AGRI-001",
        "country": "Ghana",
        "region": "West Africa",
        "sector": "agriculture",
        "sub_sector": "cocoa processing",
        "title": "Kumasi Cocoa Butter Processing Plant",
        "description": "Value-added cocoa butter and powder production for global confectionery industry.",
        "investment_size_usd": 20_000_000,
        "roi_pct": 25.0,
        "risk_tolerance": "medium",
        "payback_years": 4,
        "status": "open",
    },
    {
        "id": "TZ-LOGISTICS-001",
        "country": "Tanzania",
        "region": "East Africa",
        "sector": "logistics",
        "sub_sector": "cold chain",
        "title": "Dar es Salaam Cold Chain Hub",
        "description": "Temperature-controlled warehousing and distribution for fresh produce exports.",
        "investment_size_usd": 6_500_000,
        "roi_pct": 20.0,
        "risk_tolerance": "medium",
        "payback_years": 4,
        "status": "open",
    },
    {
        "id": "CM-INFRA-001",
        "country": "Cameroon",
        "region": "Central Africa",
        "sector": "infrastructure",
        "sub_sector": "roads",
        "title": "Yaoundé-Douala Corridor Upgrade (PPP)",
        "description": "Public-private partnership for upgrading the main economic corridor.",
        "investment_size_usd": 500_000_000,
        "roi_pct": 11.0,
        "risk_tolerance": "low",
        "payback_years": 15,
        "status": "open",
    },
    {
        "id": "SN-FINANCE-001",
        "country": "Senegal",
        "region": "West Africa",
        "sector": "finance",
        "sub_sector": "microfinance",
        "title": "Dakar Microfinance Expansion",
        "description": "Digital microfinance platform targeting informal sector workers across ECOWAS.",
        "investment_size_usd": 3_000_000,
        "roi_pct": 28.0,
        "risk_tolerance": "high",
        "payback_years": 3,
        "status": "open",
    },
    {
        "id": "EG-HEALTHCARE-001",
        "country": "Egypt",
        "region": "North Africa",
        "sector": "healthcare",
        "sub_sector": "pharmaceuticals",
        "title": "Cairo Pharmaceutical Manufacturing JV",
        "description": "Generic medicine production targeting African markets under AfCFTA preferences.",
        "investment_size_usd": 40_000_000,
        "roi_pct": 21.0,
        "risk_tolerance": "medium",
        "payback_years": 5,
        "status": "open",
    },
]

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


class InvestmentOpportunitySearch:
    """Multi-dimensional investment opportunity search."""

    def __init__(self) -> None:
        self._data = _OPPORTUNITIES

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def search(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Filter opportunities by geographic, sectoral and financial criteria.

        criteria schema::

            {
                "geographic": {"country": str, "region": str},
                "sectoral":   {"primary": str, "secondary": str},
                "financial":  {
                    "investment_size_min": int,
                    "investment_size_max": int,
                    "roi_min": float,
                    "risk_tolerance": str   # "low" | "medium" | "high"
                }
            }
        """
        geo = criteria.get("geographic", {})
        sec = criteria.get("sectoral", {})
        fin = criteria.get("financial", {})

        results = []
        for opp in self._data:
            if geo.get("country") and opp["country"].lower() != geo["country"].lower():
                continue
            if geo.get("region") and geo["region"].lower() not in opp["region"].lower():
                continue
            if sec.get("primary") and opp["sector"].lower() != sec["primary"].lower():
                continue
            if sec.get("secondary") and sec["secondary"].lower() not in opp.get("sub_sector", "").lower():
                continue
            if fin.get("investment_size_min") and opp["investment_size_usd"] < fin["investment_size_min"]:
                continue
            if fin.get("investment_size_max") and opp["investment_size_usd"] > fin["investment_size_max"]:
                continue
            if fin.get("roi_min") and opp["roi_pct"] < fin["roi_min"]:
                continue
            if fin.get("risk_tolerance"):
                allowed_level = _RISK_ORDER.get(fin["risk_tolerance"], 2)
                opp_level = _RISK_ORDER.get(opp["risk_tolerance"], 2)
                if opp_level > allowed_level:
                    continue
            results.append(opp)

        return results

    def get_by_sector(self, sector: str) -> list[dict[str, Any]]:
        return [o for o in self._data if o["sector"].lower() == sector.lower()]

    def get_by_country(self, country: str) -> list[dict[str, Any]]:
        return [o for o in self._data if o["country"].lower() == country.lower()]
