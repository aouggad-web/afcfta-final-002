"""
Dashboard data generator for AfCFTA executive and KPI dashboards.
All metrics are realistic hardcoded data based on 2024 African trade statistics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DashboardGenerator:
    """Generates structured data for executive summaries, KPIs and investment flows."""

    # ------------------------------------------------------------------
    # Regional summary data
    # ------------------------------------------------------------------

    _REGIONAL_SUMMARIES: dict[str, dict[str, Any]] = {
        "africa": {
            "continent_gdp_usd_bn": 2_970,
            "gdp_growth_pct": 3.5,
            "population_bn": 1.44,
            "afcfta_member_states": 54,
            "ratifying_states": 47,
            "intra_african_trade_pct_before_afcfta": 15.2,
            "intra_african_trade_pct_current": 17.6,
            "projected_intra_trade_pct_2035": 52.0,
            "fdi_total_usd_bn": 45.3,
            "top_performing_sectors": ["technology", "agriculture", "energy", "mining", "logistics"],
        },
        "west_africa": {
            "gdp_usd_bn": 794,
            "growth_pct": 3.9,
            "dominant_economies": ["Nigeria", "Ghana", "Côte d'Ivoire"],
            "key_sectors": ["oil & gas", "cocoa", "fintech"],
            "intra_trade_pct": 9.4,
        },
        "east_africa": {
            "gdp_usd_bn": 312,
            "growth_pct": 5.4,
            "dominant_economies": ["Kenya", "Ethiopia", "Tanzania"],
            "key_sectors": ["agriculture", "technology", "tourism"],
            "intra_trade_pct": 22.5,
        },
        "southern_africa": {
            "gdp_usd_bn": 725,
            "growth_pct": 1.8,
            "dominant_economies": ["South Africa", "Angola", "Zambia"],
            "key_sectors": ["mining", "manufacturing", "energy"],
            "intra_trade_pct": 18.2,
        },
        "north_africa": {
            "gdp_usd_bn": 810,
            "growth_pct": 3.0,
            "dominant_economies": ["Egypt", "Morocco", "Algeria"],
            "key_sectors": ["energy", "phosphate chemicals", "automotive"],
            "intra_trade_pct": 3.1,
        },
        "central_africa": {
            "gdp_usd_bn": 248,
            "growth_pct": 2.8,
            "dominant_economies": ["DRC", "Cameroon", "Gabon"],
            "key_sectors": ["oil & gas", "mining", "forestry"],
            "intra_trade_pct": 4.2,
        },
    }

    _KPI_DATA: dict[str, Any] = {
        "trade_metrics": {
            "total_african_exports_usd_bn": 595,
            "total_african_imports_usd_bn": 540,
            "trade_surplus_usd_bn": 55,
            "intra_african_trade_value_usd_bn": 192,
            "yoy_growth_pct": 3.2,
            "largest_trade_partner_external": "China",
        },
        "investment_metrics": {
            "total_fdi_inflow_usd_bn": 45.3,
            "greenfield_fdi_pct": 62,
            "m_and_a_fdi_pct": 38,
            "top_recipient": "South Africa",
            "top_investing_countries": ["China", "UAE", "France", "USA", "India"],
        },
        "integration_metrics": {
            "afcfta_operational_since": "2021-01-01",
            "guided_trade_initiative_participants": 8,
            "tariff_lines_liberalised_pct": 90,
            "nontariff_barriers_reduction_pct": 35,
            "digital_trade_protocol_status": "under_negotiation",
        },
        "infrastructure_metrics": {
            "road_network_km": 2_800_000,
            "electrification_rate_pct": 56,
            "broadband_penetration_pct": 38,
            "port_handling_capacity_mtpa": 720,
            "rail_network_km": 84_000,
        },
    }

    # ------------------------------------------------------------------
    # Investment flow timeseries (quarterly, 2023–2024)
    # ------------------------------------------------------------------

    _FLOW_DATA: dict[str, list[dict[str, Any]]] = {
        "2023": [
            {"quarter": "Q1-2023", "fdi_usd_bn": 9.8, "portfolio_usd_bn": 3.1, "remittances_usd_bn": 22.5},
            {"quarter": "Q2-2023", "fdi_usd_bn": 10.4, "portfolio_usd_bn": 2.8, "remittances_usd_bn": 23.1},
            {"quarter": "Q3-2023", "fdi_usd_bn": 11.2, "portfolio_usd_bn": 3.5, "remittances_usd_bn": 24.0},
            {"quarter": "Q4-2023", "fdi_usd_bn": 13.9, "portfolio_usd_bn": 4.1, "remittances_usd_bn": 26.4},
        ],
        "2024": [
            {"quarter": "Q1-2024", "fdi_usd_bn": 10.2, "portfolio_usd_bn": 3.4, "remittances_usd_bn": 23.8},
            {"quarter": "Q2-2024", "fdi_usd_bn": 11.5, "portfolio_usd_bn": 3.8, "remittances_usd_bn": 25.2},
            {"quarter": "Q3-2024", "fdi_usd_bn": 12.1, "portfolio_usd_bn": 3.2, "remittances_usd_bn": 25.9},
            {"quarter": "Q4-2024", "fdi_usd_bn": 11.5, "portfolio_usd_bn": 2.9, "remittances_usd_bn": 24.6},
        ],
    }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def generate_executive_summary(self, region: str = "africa") -> dict[str, Any]:
        """Return an executive summary for the requested region."""
        key = region.lower().replace(" ", "_")
        data = self._REGIONAL_SUMMARIES.get(key, self._REGIONAL_SUMMARIES["africa"])
        return {
            "region": region,
            "summary": data,
            "highlights": [
                f"Intra-African trade up {data.get('intra_trade_pct', data.get('intra_african_trade_pct_current', 'N/A'))}%",
                f"Top sectors: {', '.join(data.get('top_performing_sectors', data.get('key_sectors', []))[:3])}",
                "AfCFTA Phase II (investment & competition protocols) advancing",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_kpi_metrics(self) -> dict[str, Any]:
        """Return platform KPI metrics."""
        return {
            "kpis": self._KPI_DATA,
            "data_as_of": "2024-Q4",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_investment_flow_data(self, timeframe: str = "2024") -> dict[str, Any]:
        """Return investment flow data for the specified year."""
        flows = self._FLOW_DATA.get(timeframe, self._FLOW_DATA["2024"])
        total_fdi = sum(q["fdi_usd_bn"] for q in flows)
        return {
            "timeframe": timeframe,
            "quarterly_flows": flows,
            "annual_totals": {
                "fdi_usd_bn": round(total_fdi, 2),
                "portfolio_usd_bn": round(sum(q["portfolio_usd_bn"] for q in flows), 2),
                "remittances_usd_bn": round(sum(q["remittances_usd_bn"] for q in flows), 2),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
