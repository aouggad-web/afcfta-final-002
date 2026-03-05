"""
Investment Scoring Engine for AfCFTA platform.

Provides multi-dimensional scoring for African investment opportunities using
realistic market data. No external ML dependencies required.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Country dataset – realistic African market metrics (2024 estimates)
# ---------------------------------------------------------------------------

COUNTRY_DATA: dict[str, dict[str, Any]] = {
    "Nigeria": {
        "gdp_usd_bn": 477,
        "gdp_growth_pct": 3.4,
        "population_m": 218,
        "inflation_pct": 28.9,
        "ease_of_doing_business": 131,
        "fdi_inflow_usd_bn": 3.3,
        "lpi_score": 2.53,
        "electrification_pct": 56,
        "internet_penetration_pct": 45,
        "port_quality": 3.2,
        "road_quality": 2.8,
        "political_stability": -1.1,
        "rule_of_law": -0.9,
        "corruption_index": 24,
        "tax_rate_corporate_pct": 30,
        "special_economic_zones": 38,
        "currency_stability": 0.4,
        "trade_openness": 0.25,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.04, "market_size_usd_bn": 120, "competition": 0.5},
            "technology": {"growth": 0.18, "market_size_usd_bn": 5.2, "competition": 0.6},
            "energy": {"growth": 0.06, "market_size_usd_bn": 45, "competition": 0.4},
            "manufacturing": {"growth": 0.03, "market_size_usd_bn": 35, "competition": 0.5},
            "finance": {"growth": 0.09, "market_size_usd_bn": 28, "competition": 0.7},
            "retail": {"growth": 0.07, "market_size_usd_bn": 60, "competition": 0.6},
            "healthcare": {"growth": 0.08, "market_size_usd_bn": 18, "competition": 0.4},
            "logistics": {"growth": 0.10, "market_size_usd_bn": 22, "competition": 0.5},
        },
    },
    "South Africa": {
        "gdp_usd_bn": 405,
        "gdp_growth_pct": 0.6,
        "population_m": 60,
        "inflation_pct": 5.1,
        "ease_of_doing_business": 84,
        "fdi_inflow_usd_bn": 9.0,
        "lpi_score": 3.38,
        "electrification_pct": 85,
        "internet_penetration_pct": 72,
        "port_quality": 4.1,
        "road_quality": 4.0,
        "political_stability": -0.1,
        "rule_of_law": 0.1,
        "corruption_index": 41,
        "tax_rate_corporate_pct": 27,
        "special_economic_zones": 11,
        "currency_stability": 0.55,
        "trade_openness": 0.58,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.02, "market_size_usd_bn": 18, "competition": 0.6},
            "technology": {"growth": 0.12, "market_size_usd_bn": 14, "competition": 0.7},
            "energy": {"growth": 0.08, "market_size_usd_bn": 55, "competition": 0.5},
            "manufacturing": {"growth": 0.01, "market_size_usd_bn": 80, "competition": 0.7},
            "finance": {"growth": 0.04, "market_size_usd_bn": 90, "competition": 0.8},
            "retail": {"growth": 0.03, "market_size_usd_bn": 70, "competition": 0.8},
            "healthcare": {"growth": 0.06, "market_size_usd_bn": 30, "competition": 0.6},
            "logistics": {"growth": 0.05, "market_size_usd_bn": 35, "competition": 0.7},
        },
    },
    "Egypt": {
        "gdp_usd_bn": 396,
        "gdp_growth_pct": 4.2,
        "population_m": 105,
        "inflation_pct": 35.0,
        "ease_of_doing_business": 93,
        "fdi_inflow_usd_bn": 10.0,
        "lpi_score": 2.82,
        "electrification_pct": 99,
        "internet_penetration_pct": 72,
        "port_quality": 3.8,
        "road_quality": 3.5,
        "political_stability": -0.6,
        "rule_of_law": -0.3,
        "corruption_index": 35,
        "tax_rate_corporate_pct": 22.5,
        "special_economic_zones": 14,
        "currency_stability": 0.3,
        "trade_openness": 0.38,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.03, "market_size_usd_bn": 35, "competition": 0.5},
            "technology": {"growth": 0.15, "market_size_usd_bn": 8, "competition": 0.5},
            "energy": {"growth": 0.10, "market_size_usd_bn": 35, "competition": 0.4},
            "manufacturing": {"growth": 0.06, "market_size_usd_bn": 60, "competition": 0.6},
            "finance": {"growth": 0.07, "market_size_usd_bn": 40, "competition": 0.6},
            "retail": {"growth": 0.06, "market_size_usd_bn": 50, "competition": 0.5},
            "healthcare": {"growth": 0.09, "market_size_usd_bn": 12, "competition": 0.4},
            "logistics": {"growth": 0.11, "market_size_usd_bn": 18, "competition": 0.5},
        },
    },
    "Ethiopia": {
        "gdp_usd_bn": 126,
        "gdp_growth_pct": 7.2,
        "population_m": 126,
        "inflation_pct": 30.0,
        "ease_of_doing_business": 159,
        "fdi_inflow_usd_bn": 3.9,
        "lpi_score": 2.30,
        "electrification_pct": 45,
        "internet_penetration_pct": 22,
        "port_quality": 2.0,
        "road_quality": 2.5,
        "political_stability": -1.6,
        "rule_of_law": -0.6,
        "corruption_index": 38,
        "tax_rate_corporate_pct": 30,
        "special_economic_zones": 14,
        "currency_stability": 0.25,
        "trade_openness": 0.30,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.08, "market_size_usd_bn": 45, "competition": 0.3},
            "technology": {"growth": 0.20, "market_size_usd_bn": 1.2, "competition": 0.3},
            "energy": {"growth": 0.12, "market_size_usd_bn": 8, "competition": 0.3},
            "manufacturing": {"growth": 0.10, "market_size_usd_bn": 12, "competition": 0.3},
            "finance": {"growth": 0.11, "market_size_usd_bn": 6, "competition": 0.4},
            "retail": {"growth": 0.09, "market_size_usd_bn": 15, "competition": 0.3},
            "healthcare": {"growth": 0.12, "market_size_usd_bn": 3, "competition": 0.2},
            "logistics": {"growth": 0.13, "market_size_usd_bn": 5, "competition": 0.3},
        },
    },
    "Kenya": {
        "gdp_usd_bn": 118,
        "gdp_growth_pct": 5.3,
        "population_m": 55,
        "inflation_pct": 5.6,
        "ease_of_doing_business": 56,
        "fdi_inflow_usd_bn": 1.1,
        "lpi_score": 3.00,
        "electrification_pct": 75,
        "internet_penetration_pct": 85,
        "port_quality": 3.5,
        "road_quality": 3.2,
        "political_stability": -0.3,
        "rule_of_law": -0.1,
        "corruption_index": 31,
        "tax_rate_corporate_pct": 30,
        "special_economic_zones": 8,
        "currency_stability": 0.50,
        "trade_openness": 0.42,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.04, "market_size_usd_bn": 25, "competition": 0.5},
            "technology": {"growth": 0.22, "market_size_usd_bn": 3.5, "competition": 0.5},
            "energy": {"growth": 0.09, "market_size_usd_bn": 10, "competition": 0.4},
            "manufacturing": {"growth": 0.05, "market_size_usd_bn": 14, "competition": 0.5},
            "finance": {"growth": 0.10, "market_size_usd_bn": 20, "competition": 0.6},
            "retail": {"growth": 0.08, "market_size_usd_bn": 18, "competition": 0.5},
            "healthcare": {"growth": 0.10, "market_size_usd_bn": 6, "competition": 0.4},
            "logistics": {"growth": 0.12, "market_size_usd_bn": 8, "competition": 0.5},
        },
    },
    "Ghana": {
        "gdp_usd_bn": 76,
        "gdp_growth_pct": 2.9,
        "population_m": 33,
        "inflation_pct": 18.4,
        "ease_of_doing_business": 118,
        "fdi_inflow_usd_bn": 2.5,
        "lpi_score": 2.68,
        "electrification_pct": 86,
        "internet_penetration_pct": 62,
        "port_quality": 3.3,
        "road_quality": 3.0,
        "political_stability": 0.1,
        "rule_of_law": 0.0,
        "corruption_index": 41,
        "tax_rate_corporate_pct": 25,
        "special_economic_zones": 9,
        "currency_stability": 0.35,
        "trade_openness": 0.45,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.05, "market_size_usd_bn": 18, "competition": 0.4},
            "technology": {"growth": 0.18, "market_size_usd_bn": 1.8, "competition": 0.4},
            "energy": {"growth": 0.08, "market_size_usd_bn": 12, "competition": 0.4},
            "manufacturing": {"growth": 0.04, "market_size_usd_bn": 10, "competition": 0.4},
            "finance": {"growth": 0.07, "market_size_usd_bn": 12, "competition": 0.5},
            "retail": {"growth": 0.06, "market_size_usd_bn": 14, "competition": 0.5},
            "healthcare": {"growth": 0.09, "market_size_usd_bn": 4, "competition": 0.3},
            "logistics": {"growth": 0.10, "market_size_usd_bn": 5, "competition": 0.4},
        },
    },
    "Morocco": {
        "gdp_usd_bn": 141,
        "gdp_growth_pct": 3.5,
        "population_m": 37,
        "inflation_pct": 3.8,
        "ease_of_doing_business": 53,
        "fdi_inflow_usd_bn": 2.3,
        "lpi_score": 2.87,
        "electrification_pct": 99,
        "internet_penetration_pct": 88,
        "port_quality": 4.2,
        "road_quality": 4.0,
        "political_stability": 0.0,
        "rule_of_law": 0.0,
        "corruption_index": 38,
        "tax_rate_corporate_pct": 31,
        "special_economic_zones": 6,
        "currency_stability": 0.75,
        "trade_openness": 0.75,
        "afcfta_ratified": False,
        "sectors": {
            "agriculture": {"growth": 0.03, "market_size_usd_bn": 20, "competition": 0.5},
            "technology": {"growth": 0.14, "market_size_usd_bn": 3, "competition": 0.5},
            "energy": {"growth": 0.12, "market_size_usd_bn": 15, "competition": 0.4},
            "manufacturing": {"growth": 0.06, "market_size_usd_bn": 30, "competition": 0.6},
            "finance": {"growth": 0.05, "market_size_usd_bn": 22, "competition": 0.6},
            "retail": {"growth": 0.05, "market_size_usd_bn": 25, "competition": 0.6},
            "healthcare": {"growth": 0.07, "market_size_usd_bn": 7, "competition": 0.5},
            "logistics": {"growth": 0.09, "market_size_usd_bn": 10, "competition": 0.5},
        },
    },
    "Tanzania": {
        "gdp_usd_bn": 79,
        "gdp_growth_pct": 5.1,
        "population_m": 65,
        "inflation_pct": 4.3,
        "ease_of_doing_business": 141,
        "fdi_inflow_usd_bn": 0.9,
        "lpi_score": 2.44,
        "electrification_pct": 40,
        "internet_penetration_pct": 50,
        "port_quality": 3.0,
        "road_quality": 2.8,
        "political_stability": 0.2,
        "rule_of_law": -0.2,
        "corruption_index": 36,
        "tax_rate_corporate_pct": 30,
        "special_economic_zones": 5,
        "currency_stability": 0.60,
        "trade_openness": 0.35,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.06, "market_size_usd_bn": 28, "competition": 0.3},
            "technology": {"growth": 0.19, "market_size_usd_bn": 1.0, "competition": 0.3},
            "energy": {"growth": 0.10, "market_size_usd_bn": 6, "competition": 0.3},
            "manufacturing": {"growth": 0.07, "market_size_usd_bn": 10, "competition": 0.4},
            "finance": {"growth": 0.09, "market_size_usd_bn": 7, "competition": 0.4},
            "retail": {"growth": 0.08, "market_size_usd_bn": 12, "competition": 0.3},
            "healthcare": {"growth": 0.11, "market_size_usd_bn": 2.5, "competition": 0.2},
            "logistics": {"growth": 0.12, "market_size_usd_bn": 4, "competition": 0.3},
        },
    },
    "Rwanda": {
        "gdp_usd_bn": 14,
        "gdp_growth_pct": 7.5,
        "population_m": 14,
        "inflation_pct": 3.7,
        "ease_of_doing_business": 38,
        "fdi_inflow_usd_bn": 0.4,
        "lpi_score": 2.81,
        "electrification_pct": 68,
        "internet_penetration_pct": 55,
        "port_quality": 2.5,
        "road_quality": 3.8,
        "political_stability": 0.3,
        "rule_of_law": 0.5,
        "corruption_index": 53,
        "tax_rate_corporate_pct": 30,
        "special_economic_zones": 4,
        "currency_stability": 0.65,
        "trade_openness": 0.40,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.06, "market_size_usd_bn": 4, "competition": 0.3},
            "technology": {"growth": 0.25, "market_size_usd_bn": 0.5, "competition": 0.3},
            "energy": {"growth": 0.11, "market_size_usd_bn": 1, "competition": 0.2},
            "manufacturing": {"growth": 0.08, "market_size_usd_bn": 2, "competition": 0.3},
            "finance": {"growth": 0.10, "market_size_usd_bn": 2, "competition": 0.4},
            "retail": {"growth": 0.09, "market_size_usd_bn": 3, "competition": 0.3},
            "healthcare": {"growth": 0.13, "market_size_usd_bn": 0.8, "competition": 0.2},
            "logistics": {"growth": 0.14, "market_size_usd_bn": 1.2, "competition": 0.3},
        },
    },
    "Côte d'Ivoire": {
        "gdp_usd_bn": 68,
        "gdp_growth_pct": 6.5,
        "population_m": 27,
        "inflation_pct": 4.2,
        "ease_of_doing_business": 110,
        "fdi_inflow_usd_bn": 0.8,
        "lpi_score": 2.63,
        "electrification_pct": 70,
        "internet_penetration_pct": 47,
        "port_quality": 3.5,
        "road_quality": 3.0,
        "political_stability": -0.2,
        "rule_of_law": -0.1,
        "corruption_index": 37,
        "tax_rate_corporate_pct": 25,
        "special_economic_zones": 3,
        "currency_stability": 0.85,
        "trade_openness": 0.60,
        "afcfta_ratified": True,
        "sectors": {
            "agriculture": {"growth": 0.05, "market_size_usd_bn": 22, "competition": 0.4},
            "technology": {"growth": 0.20, "market_size_usd_bn": 0.8, "competition": 0.3},
            "energy": {"growth": 0.09, "market_size_usd_bn": 5, "competition": 0.3},
            "manufacturing": {"growth": 0.07, "market_size_usd_bn": 8, "competition": 0.4},
            "finance": {"growth": 0.08, "market_size_usd_bn": 7, "competition": 0.5},
            "retail": {"growth": 0.07, "market_size_usd_bn": 10, "competition": 0.4},
            "healthcare": {"growth": 0.10, "market_size_usd_bn": 1.8, "competition": 0.3},
            "logistics": {"growth": 0.11, "market_size_usd_bn": 4, "competition": 0.4},
        },
    },
}

# Sector-specific dimension weights
SECTOR_WEIGHTS: dict[str, dict[str, float]] = {
    "agriculture": {
        "market_access": 0.25,
        "business_environment": 0.15,
        "infrastructure": 0.20,
        "economic_fundamentals": 0.20,
        "investment_incentives": 0.10,
        "risk_adjusted_return": 0.10,
    },
    "technology": {
        "market_access": 0.15,
        "business_environment": 0.25,
        "infrastructure": 0.20,
        "economic_fundamentals": 0.15,
        "investment_incentives": 0.15,
        "risk_adjusted_return": 0.10,
    },
    "energy": {
        "market_access": 0.15,
        "business_environment": 0.15,
        "infrastructure": 0.25,
        "economic_fundamentals": 0.20,
        "investment_incentives": 0.15,
        "risk_adjusted_return": 0.10,
    },
    "manufacturing": {
        "market_access": 0.20,
        "business_environment": 0.20,
        "infrastructure": 0.25,
        "economic_fundamentals": 0.15,
        "investment_incentives": 0.10,
        "risk_adjusted_return": 0.10,
    },
    "finance": {
        "market_access": 0.20,
        "business_environment": 0.30,
        "infrastructure": 0.10,
        "economic_fundamentals": 0.20,
        "investment_incentives": 0.10,
        "risk_adjusted_return": 0.10,
    },
    "retail": {
        "market_access": 0.30,
        "business_environment": 0.20,
        "infrastructure": 0.15,
        "economic_fundamentals": 0.20,
        "investment_incentives": 0.05,
        "risk_adjusted_return": 0.10,
    },
    "healthcare": {
        "market_access": 0.25,
        "business_environment": 0.20,
        "infrastructure": 0.15,
        "economic_fundamentals": 0.20,
        "investment_incentives": 0.10,
        "risk_adjusted_return": 0.10,
    },
    "logistics": {
        "market_access": 0.20,
        "business_environment": 0.15,
        "infrastructure": 0.30,
        "economic_fundamentals": 0.15,
        "investment_incentives": 0.10,
        "risk_adjusted_return": 0.10,
    },
}

_DEFAULT_WEIGHTS: dict[str, float] = {
    "market_access": 0.20,
    "business_environment": 0.20,
    "infrastructure": 0.20,
    "economic_fundamentals": 0.20,
    "investment_incentives": 0.10,
    "risk_adjusted_return": 0.10,
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _normalize_ease_of_doing_business(rank: int, total: int = 190) -> float:
    """Convert World Bank rank (lower is better) to 0-100 score."""
    return _clamp((1 - (rank - 1) / (total - 1)) * 100)


def _normalize_corruption(score: int) -> float:
    """Transparency International CPI 0–100 (higher is cleaner)."""
    return float(score)


def _normalize_lpi(lpi: float) -> float:
    """World Bank LPI 1–5 → 0–100."""
    return _clamp((lpi - 1) / 4 * 100)


def _normalize_political_stability(score: float) -> float:
    """World Bank political stability -2.5 to +2.5 → 0-100."""
    return _clamp((score + 2.5) / 5 * 100)


# ---------------------------------------------------------------------------
# Score dataclass
# ---------------------------------------------------------------------------

@dataclass
class InvestmentScore:
    country: str
    sector: str
    total_score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "country": self.country,
            "sector": self.sector,
            "total_score": round(self.total_score, 2),
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class InvestmentScoringEngine:
    """Multi-dimensional investment scoring engine for African markets."""

    def __init__(self) -> None:
        self._country_data = COUNTRY_DATA
        self._sector_weights = SECTOR_WEIGHTS
        self._default_weights = _DEFAULT_WEIGHTS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_investment_score(
        self,
        country: str,
        sector: str,
        user_profile: dict[str, Any] | None = None,
    ) -> InvestmentScore:
        """
        Return a multi-dimensional investment score for *country* / *sector*.

        Parameters
        ----------
        country:
            Country name (must be in the dataset).
        sector:
            Sector name (agriculture, technology, energy, …).
        user_profile:
            Optional dict with keys ``risk_tolerance`` ('low'|'medium'|'high'),
            ``investment_size`` (USD amount), ``geographic_preferences`` (list).
        """
        if country not in self._country_data:
            raise ValueError(f"Unknown country: {country!r}. Available: {list(self._country_data)}")

        sector_key = sector.lower()
        data = self._country_data[country]
        sector_data = data.get("sectors", {}).get(sector_key, {})

        dimensions = {
            "market_access": self._score_market_access(data, sector_data),
            "business_environment": self._score_business_environment(data),
            "infrastructure": self._score_infrastructure(data, sector_key),
            "economic_fundamentals": self._score_economic_fundamentals(data),
            "investment_incentives": self._score_investment_incentives(data, sector_key),
            "risk_adjusted_return": self._score_risk_adjusted_return(data, sector_data),
        }

        weights = dict(self._sector_weights.get(sector_key, self._default_weights))

        if user_profile:
            weights = self._adjust_weights_for_profile(weights, user_profile)

        total = sum(dimensions[dim] * weights[dim] for dim in dimensions)

        metadata = {
            "gdp_usd_bn": data["gdp_usd_bn"],
            "gdp_growth_pct": data["gdp_growth_pct"],
            "sector_growth_pct": sector_data.get("growth", 0) * 100,
            "sector_market_size_usd_bn": sector_data.get("market_size_usd_bn", 0),
            "afcfta_ratified": data.get("afcfta_ratified", False),
            "fdi_inflow_usd_bn": data.get("fdi_inflow_usd_bn", 0),
            "weights_used": weights,
        }

        return InvestmentScore(
            country=country,
            sector=sector,
            total_score=_clamp(total),
            dimensions=dimensions,
            metadata=metadata,
        )

    def get_top_countries_by_sector(
        self,
        sector: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the top *limit* countries for *sector*, ranked by total score."""
        scores = []
        for country in self._country_data:
            try:
                score = self.calculate_investment_score(country, sector)
                scores.append(score.to_dict())
            except (KeyError, ValueError):
                continue

        scores.sort(key=lambda s: s["total_score"], reverse=True)
        return scores[:limit]

    def compare_countries(
        self,
        countries: list[str],
        sector: str,
    ) -> dict[str, Any]:
        """
        Side-by-side comparison of *countries* for *sector*.

        Returns a dict with individual scores and a ranked summary.
        """
        results: dict[str, Any] = {}
        errors: list[str] = []

        for country in countries:
            try:
                score = self.calculate_investment_score(country, sector)
                results[country] = score.to_dict()
            except ValueError as exc:
                errors.append(str(exc))

        ranked = sorted(results.keys(), key=lambda c: results[c]["total_score"], reverse=True)

        return {
            "sector": sector,
            "scores": results,
            "ranking": ranked,
            "best_overall": ranked[0] if ranked else None,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Dimension scorers (all return 0-100)
    # ------------------------------------------------------------------

    def _score_market_access(
        self,
        data: dict[str, Any],
        sector_data: dict[str, Any],
    ) -> float:
        population_score = _clamp(math.log10(max(data["population_m"], 1)) / math.log10(300) * 100)
        gdp_score = _clamp(math.log10(max(data["gdp_usd_bn"], 1)) / math.log10(500) * 100)
        trade_score = data.get("trade_openness", 0.3) * 100
        afcfta_bonus = 10.0 if data.get("afcfta_ratified") else 0.0
        market_size_score = _clamp(
            math.log10(max(sector_data.get("market_size_usd_bn", 1), 1)) / math.log10(100) * 100
        )
        raw = (
            population_score * 0.25
            + gdp_score * 0.25
            + trade_score * 0.20
            + market_size_score * 0.20
            + afcfta_bonus * 1.0 * 0.10
        )
        return _clamp(raw)

    def _score_business_environment(self, data: dict[str, Any]) -> float:
        edb_score = _normalize_ease_of_doing_business(data["ease_of_doing_business"])
        cpi_score = _normalize_corruption(data["corruption_index"])
        rule_score = _normalize_political_stability(data["rule_of_law"])
        tax_score = _clamp((50 - data["tax_rate_corporate_pct"]) / 30 * 100 + 50)
        internet_score = data["internet_penetration_pct"]
        raw = (
            edb_score * 0.30
            + cpi_score * 0.25
            + rule_score * 0.20
            + tax_score * 0.15
            + internet_score * 0.10
        )
        return _clamp(raw)

    def _score_infrastructure(self, data: dict[str, Any], sector: str) -> float:
        lpi_score = _normalize_lpi(data["lpi_score"])
        electrification_score = data["electrification_pct"]
        port_score = (data["port_quality"] / 5) * 100
        road_score = (data["road_quality"] / 5) * 100
        internet_score = data["internet_penetration_pct"]

        if sector in ("technology", "finance"):
            weights = (0.10, 0.25, 0.10, 0.15, 0.40)
        elif sector in ("energy", "manufacturing"):
            weights = (0.25, 0.30, 0.20, 0.20, 0.05)
        elif sector == "logistics":
            weights = (0.30, 0.15, 0.30, 0.20, 0.05)
        else:
            weights = (0.25, 0.25, 0.20, 0.20, 0.10)

        raw = (
            lpi_score * weights[0]
            + electrification_score * weights[1]
            + port_score * weights[2]
            + road_score * weights[3]
            + internet_score * weights[4]
        )
        return _clamp(raw)

    def _score_economic_fundamentals(self, data: dict[str, Any]) -> float:
        growth_score = _clamp(data["gdp_growth_pct"] / 10 * 100)
        inflation_penalty = _clamp(100 - data["inflation_pct"] * 2)
        stability_score = _normalize_political_stability(data["political_stability"])
        fdi_score = _clamp(math.log10(max(data["fdi_inflow_usd_bn"], 0.1) + 1) / math.log10(11) * 100)
        currency_score = data["currency_stability"] * 100
        raw = (
            growth_score * 0.25
            + inflation_penalty * 0.25
            + stability_score * 0.20
            + fdi_score * 0.15
            + currency_score * 0.15
        )
        return _clamp(raw)

    def _score_investment_incentives(self, data: dict[str, Any], sector: str) -> float:
        sez_score = _clamp(data.get("special_economic_zones", 0) / 40 * 100)
        afcfta_bonus = 15.0 if data.get("afcfta_ratified") else 0.0
        tax_incentive = _clamp((40 - data["tax_rate_corporate_pct"]) / 20 * 50 + 50)
        raw = sez_score * 0.40 + afcfta_bonus + tax_incentive * 0.45
        return _clamp(raw)

    def _score_risk_adjusted_return(
        self,
        data: dict[str, Any],
        sector_data: dict[str, Any],
    ) -> float:
        sector_growth = sector_data.get("growth", 0.05)
        competition = sector_data.get("competition", 0.5)
        opportunity_score = _clamp(sector_growth * 500)
        competition_opportunity = (1 - competition) * 100
        stability_score = _normalize_political_stability(data["political_stability"])
        currency_risk = data.get("currency_stability", 0.5) * 100
        raw = (
            opportunity_score * 0.30
            + competition_opportunity * 0.25
            + stability_score * 0.25
            + currency_risk * 0.20
        )
        return _clamp(raw)

    # ------------------------------------------------------------------
    # Profile-aware weight adjustment
    # ------------------------------------------------------------------

    def _adjust_weights_for_profile(
        self,
        weights: dict[str, float],
        profile: dict[str, Any],
    ) -> dict[str, float]:
        adjusted = dict(weights)
        risk = profile.get("risk_tolerance", "medium")

        if risk == "low":
            adjusted["business_environment"] = min(adjusted["business_environment"] * 1.2, 0.35)
            adjusted["risk_adjusted_return"] = min(adjusted["risk_adjusted_return"] * 1.3, 0.20)
            adjusted["market_access"] = max(adjusted["market_access"] * 0.9, 0.05)
        elif risk == "high":
            adjusted["market_access"] = min(adjusted["market_access"] * 1.2, 0.35)
            adjusted["economic_fundamentals"] = min(adjusted["economic_fundamentals"] * 1.1, 0.30)
            adjusted["business_environment"] = max(adjusted["business_environment"] * 0.85, 0.05)

        # Re-normalise so weights sum to 1
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted
