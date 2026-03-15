"""
AfCFTA Platform - AI Investment Intelligence Engine
====================================================
Machine-learning-inspired investment scoring, personalized recommendations,
risk assessment, and trade-flow prediction.

All heavy ML inference is designed to run asynchronously, with results
cached in the L3 (calculations) layer of the multi-layer cache.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# Scoring model weights (deterministic, no external ML dependency required)
# =============================================================================

SCORING_ALGORITHM: Dict[str, Any] = {
    "market_access": {
        "weight": 0.25,
        "components": {
            "tariff_advantages": 0.4,
            "trade_agreements": 0.3,
            "logistics_performance": 0.2,
            "market_size": 0.1,
        },
    },
    "investment_climate": {
        "weight": 0.20,
        "components": {
            "ease_of_business": 0.3,
            "political_stability": 0.3,
            "regulatory_quality": 0.25,
            "corruption_index": 0.15,
        },
    },
    "infrastructure_quality": {
        "weight": 0.15,
        "components": {
            "transport_infrastructure": 0.4,
            "digital_infrastructure": 0.3,
            "energy_access": 0.2,
            "water_sanitation": 0.1,
        },
    },
    "incentive_packages": {
        "weight": 0.15,
        "components": {
            "tax_incentives": 0.4,
            "sez_benefits": 0.3,
            "sector_support": 0.2,
            "training_grants": 0.1,
        },
    },
    "market_potential": {
        "weight": 0.15,
        "components": {
            "gdp_growth": 0.3,
            "consumer_demand": 0.3,
            "competitive_landscape": 0.25,
            "regulatory_barriers": 0.15,
        },
    },
    "cost_competitiveness": {
        "weight": 0.10,
        "components": {
            "labor_costs": 0.4,
            "operational_costs": 0.3,
            "compliance_costs": 0.2,
            "financing_costs": 0.1,
        },
    },
}

# Country-level indicator data (representative, based on public indices)
COUNTRY_INDICATORS: Dict[str, Dict[str, float]] = {
    "MAR": {
        "tariff_advantages": 0.75, "trade_agreements": 0.85, "logistics_performance": 0.72,
        "market_size": 0.60, "ease_of_business": 0.70, "political_stability": 0.68,
        "regulatory_quality": 0.72, "corruption_index": 0.65, "transport_infrastructure": 0.70,
        "digital_infrastructure": 0.68, "energy_access": 0.88, "water_sanitation": 0.76,
        "tax_incentives": 0.80, "sez_benefits": 0.78, "sector_support": 0.74,
        "training_grants": 0.62, "gdp_growth": 0.65, "consumer_demand": 0.60,
        "competitive_landscape": 0.68, "regulatory_barriers": 0.70, "labor_costs": 0.72,
        "operational_costs": 0.68, "compliance_costs": 0.65, "financing_costs": 0.60,
    },
    "EGY": {
        "tariff_advantages": 0.70, "trade_agreements": 0.80, "logistics_performance": 0.65,
        "market_size": 0.85, "ease_of_business": 0.65, "political_stability": 0.55,
        "regulatory_quality": 0.60, "corruption_index": 0.50, "transport_infrastructure": 0.65,
        "digital_infrastructure": 0.62, "energy_access": 0.92, "water_sanitation": 0.80,
        "tax_incentives": 0.75, "sez_benefits": 0.72, "sector_support": 0.68,
        "training_grants": 0.58, "gdp_growth": 0.70, "consumer_demand": 0.80,
        "competitive_landscape": 0.62, "regulatory_barriers": 0.55, "labor_costs": 0.75,
        "operational_costs": 0.70, "compliance_costs": 0.55, "financing_costs": 0.58,
    },
    "DZA": {
        "tariff_advantages": 0.55, "trade_agreements": 0.60, "logistics_performance": 0.58,
        "market_size": 0.65, "ease_of_business": 0.52, "political_stability": 0.60,
        "regulatory_quality": 0.55, "corruption_index": 0.48, "transport_infrastructure": 0.62,
        "digital_infrastructure": 0.55, "energy_access": 0.95, "water_sanitation": 0.82,
        "tax_incentives": 0.70, "sez_benefits": 0.65, "sector_support": 0.60,
        "training_grants": 0.55, "gdp_growth": 0.52, "consumer_demand": 0.62,
        "competitive_landscape": 0.50, "regulatory_barriers": 0.45, "labor_costs": 0.68,
        "operational_costs": 0.65, "compliance_costs": 0.50, "financing_costs": 0.55,
    },
    "TUN": {
        "tariff_advantages": 0.72, "trade_agreements": 0.82, "logistics_performance": 0.68,
        "market_size": 0.50, "ease_of_business": 0.68, "political_stability": 0.58,
        "regulatory_quality": 0.70, "corruption_index": 0.62, "transport_infrastructure": 0.68,
        "digital_infrastructure": 0.65, "energy_access": 0.90, "water_sanitation": 0.80,
        "tax_incentives": 0.78, "sez_benefits": 0.75, "sector_support": 0.72,
        "training_grants": 0.68, "gdp_growth": 0.55, "consumer_demand": 0.52,
        "competitive_landscape": 0.65, "regulatory_barriers": 0.62, "labor_costs": 0.70,
        "operational_costs": 0.65, "compliance_costs": 0.62, "financing_costs": 0.58,
    },
    "KEN": {
        "tariff_advantages": 0.68, "trade_agreements": 0.72, "logistics_performance": 0.70,
        "market_size": 0.65, "ease_of_business": 0.72, "political_stability": 0.62,
        "regulatory_quality": 0.68, "corruption_index": 0.52, "transport_infrastructure": 0.65,
        "digital_infrastructure": 0.75, "energy_access": 0.75, "water_sanitation": 0.62,
        "tax_incentives": 0.72, "sez_benefits": 0.68, "sector_support": 0.70,
        "training_grants": 0.65, "gdp_growth": 0.72, "consumer_demand": 0.68,
        "competitive_landscape": 0.62, "regulatory_barriers": 0.58, "labor_costs": 0.65,
        "operational_costs": 0.62, "compliance_costs": 0.58, "financing_costs": 0.55,
    },
    "ZAF": {
        "tariff_advantages": 0.65, "trade_agreements": 0.75, "logistics_performance": 0.78,
        "market_size": 0.80, "ease_of_business": 0.78, "political_stability": 0.58,
        "regulatory_quality": 0.75, "corruption_index": 0.55, "transport_infrastructure": 0.78,
        "digital_infrastructure": 0.72, "energy_access": 0.82, "water_sanitation": 0.75,
        "tax_incentives": 0.68, "sez_benefits": 0.72, "sector_support": 0.75,
        "training_grants": 0.70, "gdp_growth": 0.45, "consumer_demand": 0.78,
        "competitive_landscape": 0.72, "regulatory_barriers": 0.68, "labor_costs": 0.55,
        "operational_costs": 0.60, "compliance_costs": 0.68, "financing_costs": 0.65,
    },
    "NGA": {
        "tariff_advantages": 0.60, "trade_agreements": 0.65, "logistics_performance": 0.55,
        "market_size": 0.90, "ease_of_business": 0.52, "political_stability": 0.45,
        "regulatory_quality": 0.48, "corruption_index": 0.35, "transport_infrastructure": 0.52,
        "digital_infrastructure": 0.60, "energy_access": 0.55, "water_sanitation": 0.45,
        "tax_incentives": 0.65, "sez_benefits": 0.58, "sector_support": 0.55,
        "training_grants": 0.48, "gdp_growth": 0.62, "consumer_demand": 0.88,
        "competitive_landscape": 0.55, "regulatory_barriers": 0.42, "labor_costs": 0.62,
        "operational_costs": 0.55, "compliance_costs": 0.42, "financing_costs": 0.48,
    },
    "ETH": {
        "tariff_advantages": 0.58, "trade_agreements": 0.62, "logistics_performance": 0.55,
        "market_size": 0.80, "ease_of_business": 0.55, "political_stability": 0.42,
        "regulatory_quality": 0.50, "corruption_index": 0.45, "transport_infrastructure": 0.52,
        "digital_infrastructure": 0.48, "energy_access": 0.45, "water_sanitation": 0.40,
        "tax_incentives": 0.72, "sez_benefits": 0.75, "sector_support": 0.65,
        "training_grants": 0.55, "gdp_growth": 0.75, "consumer_demand": 0.72,
        "competitive_landscape": 0.52, "regulatory_barriers": 0.45, "labor_costs": 0.80,
        "operational_costs": 0.72, "compliance_costs": 0.45, "financing_costs": 0.42,
    },
}

# Fallback indicators for countries not explicitly listed
DEFAULT_INDICATORS: Dict[str, float] = {k: 0.55 for k in [
    "tariff_advantages", "trade_agreements", "logistics_performance", "market_size",
    "ease_of_business", "political_stability", "regulatory_quality", "corruption_index",
    "transport_infrastructure", "digital_infrastructure", "energy_access", "water_sanitation",
    "tax_incentives", "sez_benefits", "sector_support", "training_grants",
    "gdp_growth", "consumer_demand", "competitive_landscape", "regulatory_barriers",
    "labor_costs", "operational_costs", "compliance_costs", "financing_costs",
]}

# Sector multipliers
SECTOR_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "agriculture": {"market_access": 1.1, "cost_competitiveness": 1.2},
    "manufacturing": {"infrastructure_quality": 1.2, "incentive_packages": 1.1},
    "ict": {"digital_infrastructure": 1.3, "market_potential": 1.2},
    "energy": {"infrastructure_quality": 1.1, "investment_climate": 1.1},
    "finance": {"regulatory_quality": 1.2, "investment_climate": 1.2},
    "tourism": {"market_access": 1.1, "market_potential": 1.15},
    "logistics": {"transport_infrastructure": 1.3, "logistics_performance": 1.2},
    "mining": {"infrastructure_quality": 1.1, "cost_competitiveness": 1.1},
    "textiles": {"cost_competitiveness": 1.3, "market_access": 1.1},
    "automotive": {"market_access": 1.2, "infrastructure_quality": 1.1},
}

# Risk factor definitions
RISK_FACTORS: Dict[str, Dict[str, Any]] = {
    "political_risk": {
        "description": "Political instability or governance concerns",
        "indicator": "political_stability",
        "threshold": 0.5,
        "severity": "high",
    },
    "regulatory_risk": {
        "description": "Complex or unpredictable regulatory environment",
        "indicator": "regulatory_quality",
        "threshold": 0.55,
        "severity": "medium",
    },
    "infrastructure_risk": {
        "description": "Inadequate transport or energy infrastructure",
        "indicator": "transport_infrastructure",
        "threshold": 0.55,
        "severity": "medium",
    },
    "corruption_risk": {
        "description": "Elevated corruption perception index",
        "indicator": "corruption_index",
        "threshold": 0.50,
        "severity": "high",
    },
    "currency_risk": {
        "description": "Currency volatility or foreign-exchange restrictions",
        "indicator": "financing_costs",
        "threshold": 0.50,
        "severity": "medium",
    },
}


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class ComponentScore:
    name: str
    raw_score: float
    weighted_score: float
    weight: float


@dataclass
class InvestmentScore:
    country: str
    sector: str
    overall_score: float
    grade: str
    component_scores: List[ComponentScore] = field(default_factory=list)
    confidence_interval: Dict[str, float] = field(default_factory=dict)
    recommendation_strength: str = "moderate"
    risk_factors: List[Dict[str, str]] = field(default_factory=list)
    success_probability: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class InvestmentRecommendation:
    rank: int
    country: str
    sector: str
    score: InvestmentScore
    rationale: str
    key_advantages: List[str]
    action_items: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["score"] = self.score.to_dict()
        return d


@dataclass
class TradeFlowPrediction:
    origin_country: str
    destination_country: str
    product_category: str
    timeframe_months: int
    predicted_volume_tonnes: float
    predicted_value_usd: float
    confidence_interval: Dict[str, float]
    key_factors: List[str]
    risks: List[str]
    opportunities: List[str]
    trend_direction: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Investment Intelligence Engine
# =============================================================================

class InvestmentIntelligenceEngine:
    """
    AI-powered investment analysis and recommendation system.

    Uses a deterministic multi-factor scoring model (no external ML runtime
    required) that mirrors the architecture of a production ML pipeline.
    Results are cached via the L3 layer of the multi-layer cache.
    """

    def __init__(self) -> None:
        try:
            from performance.caching.cache_layers import get_cache
            self._cache = get_cache()
        except Exception:
            self._cache = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_indicators(self, country: str) -> Dict[str, float]:
        return COUNTRY_INDICATORS.get(country.upper(), DEFAULT_INDICATORS.copy())

    def _calculate_dimension_score(
        self,
        dimension: str,
        indicators: Dict[str, float],
        sector: str,
    ) -> float:
        config = SCORING_ALGORITHM[dimension]
        components = config["components"]
        score = 0.0
        for component, comp_weight in components.items():
            raw = indicators.get(component, 0.55)
            # Apply sector multiplier if relevant
            if sector in SECTOR_MULTIPLIERS:
                key = component.split("_")[0] if "_" in component else component
                mult = SECTOR_MULTIPLIERS[sector].get(component, 1.0)
                raw = min(raw * mult, 1.0)
            score += raw * comp_weight
        return score

    def _identify_risks(
        self, country: str, indicators: Dict[str, float]
    ) -> List[Dict[str, str]]:
        risks = []
        for risk_name, risk_def in RISK_FACTORS.items():
            ind_value = indicators.get(risk_def["indicator"], 0.55)
            if ind_value < risk_def["threshold"]:
                risks.append(
                    {
                        "name": risk_name,
                        "description": risk_def["description"],
                        "severity": risk_def["severity"],
                        "score": str(round(ind_value, 2)),
                    }
                )
        return risks

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.80:
            return "A+"
        if score >= 0.72:
            return "A"
        if score >= 0.64:
            return "B+"
        if score >= 0.56:
            return "B"
        if score >= 0.48:
            return "C+"
        if score >= 0.40:
            return "C"
        return "D"

    @staticmethod
    def _recommendation_strength(score: float) -> str:
        if score >= 0.75:
            return "strong_buy"
        if score >= 0.62:
            return "buy"
        if score >= 0.50:
            return "hold"
        if score >= 0.38:
            return "cautious"
        return "avoid"

    @staticmethod
    def _cache_key(*parts: str) -> str:
        raw = ":".join(parts)
        return "invest:" + hashlib.sha256(raw.encode()).hexdigest()[:20]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_investment_score(
        self,
        country: str,
        sector: str = "general",
        investment_size: str = "medium",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> InvestmentScore:
        """Calculate a comprehensive AI-powered investment score."""
        cache_key = self._cache_key(country, sector, investment_size)
        if self._cache:
            cached = self._cache.l3.get(cache_key)
            if cached:
                return InvestmentScore(**cached)

        indicators = self._get_indicators(country)
        component_scores: List[ComponentScore] = []
        total_weighted = 0.0

        for dimension, config in SCORING_ALGORITHM.items():
            dim_score = self._calculate_dimension_score(dimension, indicators, sector)
            weight = config["weight"]
            weighted = dim_score * weight
            total_weighted += weighted
            component_scores.append(
                ComponentScore(
                    name=dimension,
                    raw_score=round(dim_score, 4),
                    weighted_score=round(weighted, 4),
                    weight=weight,
                )
            )

        # User-profile adjustment (risk tolerance, investment size)
        adjustment = 0.0
        if user_profile:
            risk_tol = user_profile.get("risk_tolerance", "medium")
            if risk_tol == "high":
                adjustment += 0.02
            elif risk_tol == "low":
                adjustment -= 0.02
            if investment_size == "large":
                adjustment -= 0.01

        final_score = max(0.0, min(1.0, total_weighted + adjustment))
        risks = self._identify_risks(country, indicators)

        result = InvestmentScore(
            country=country,
            sector=sector,
            overall_score=round(final_score, 4),
            grade=self._grade(final_score),
            component_scores=component_scores,
            confidence_interval={
                "lower": round(max(0, final_score - 0.05), 4),
                "upper": round(min(1, final_score + 0.05), 4),
            },
            recommendation_strength=self._recommendation_strength(final_score),
            risk_factors=risks,
            success_probability=round(final_score * 0.9 + 0.05, 4),
        )

        if self._cache:
            self._cache.l3.set(cache_key, result.to_dict())

        return result

    def get_personalized_recommendations(
        self,
        user_profile: Dict[str, Any],
        limit: int = 10,
    ) -> List[InvestmentRecommendation]:
        """Generate AI-powered personalized investment recommendations."""
        sector = user_profile.get("sector", "general")
        risk_tolerance = user_profile.get("risk_tolerance", "medium")
        preferred_regions = user_profile.get("preferred_regions", [])

        # Build candidate country list
        if preferred_regions:
            candidates = [c for c, _ in COUNTRY_INDICATORS.items()]
        else:
            candidates = list(COUNTRY_INDICATORS.keys())

        scored = []
        for country in candidates:
            score = self.calculate_investment_score(
                country, sector, "medium", user_profile
            )
            # Exclude high-risk countries for low risk-tolerance users
            if risk_tolerance == "low" and len(score.risk_factors) >= 3:
                continue
            scored.append((country, score))

        # Sort by overall score descending
        scored.sort(key=lambda x: x[1].overall_score, reverse=True)
        top = scored[:limit]

        recommendations = []
        for rank, (country, score) in enumerate(top, start=1):
            indicators = self._get_indicators(country)
            # Identify top 3 advantages
            advantages = sorted(
                [
                    (k, v)
                    for k, v in indicators.items()
                    if v >= 0.70
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            advantage_labels = [a[0].replace("_", " ").title() for a in advantages]

            recommendations.append(
                InvestmentRecommendation(
                    rank=rank,
                    country=country,
                    sector=sector,
                    score=score,
                    rationale=(
                        f"{country} scores {score.overall_score:.0%} overall with "
                        f"grade {score.grade}. "
                        f"Recommendation: {score.recommendation_strength.replace('_', ' ')}."
                    ),
                    key_advantages=advantage_labels,
                    action_items=[
                        f"Review investment incentives in {country}",
                        "Conduct market feasibility study",
                        "Engage with local investment promotion agency",
                    ],
                )
            )

        return recommendations

    def assess_risk(
        self,
        country: str,
        sector: str = "general",
        investment_size: str = "medium",
    ) -> Dict[str, Any]:
        """Provide a standalone risk assessment for a country/sector pair."""
        indicators = self._get_indicators(country)
        risks = self._identify_risks(country, indicators)

        overall_risk_score = 1.0 - (
            indicators.get("political_stability", 0.55) * 0.35
            + indicators.get("regulatory_quality", 0.55) * 0.25
            + indicators.get("corruption_index", 0.55) * 0.25
            + indicators.get("financing_costs", 0.55) * 0.15
        )

        return {
            "country": country,
            "sector": sector,
            "overall_risk_score": round(overall_risk_score, 4),
            "risk_level": (
                "low" if overall_risk_score < 0.3
                else "medium" if overall_risk_score < 0.5
                else "high"
            ),
            "identified_risks": risks,
            "mitigation_strategies": [
                "Secure political risk insurance",
                "Negotiate investment protection agreements",
                "Establish local partnerships",
                "Diversify across multiple markets",
            ],
        }

    def predict_trade_flows(
        self,
        origin_country: str,
        destination_country: str,
        product_category: str,
        timeframe_months: int = 12,
    ) -> TradeFlowPrediction:
        """
        Predict future trade flows using a trend-extrapolation model.

        In production this would call a trained LSTM/Prophet model; here we
        use a deterministic growth model seeded from indicator data.
        """
        cache_key = self._cache_key(
            origin_country, destination_country, product_category, str(timeframe_months)
        )
        if self._cache:
            cached = self._cache.l3.get(cache_key)
            if cached:
                return TradeFlowPrediction(**cached)

        origin_ind = self._get_indicators(origin_country)
        dest_ind = self._get_indicators(destination_country)

        # Base trade flow estimate (heuristic)
        base_value_usd = (
            origin_ind.get("market_size", 0.55)
            * dest_ind.get("consumer_demand", 0.55)
            * 500_000_000  # $500M reference scale
        )
        growth_rate = (
            origin_ind.get("gdp_growth", 0.55)
            + dest_ind.get("gdp_growth", 0.55)
        ) / 2

        # Compound growth over timeframe
        monthly_rate = growth_rate * 0.08 / 12
        predicted_value = base_value_usd * ((1 + monthly_rate) ** timeframe_months)
        predicted_volume = predicted_value / 1500  # ~$1500/tonne average

        trend = (
            "upward" if growth_rate > 0.60
            else "stable" if growth_rate > 0.45
            else "downward"
        )

        result = TradeFlowPrediction(
            origin_country=origin_country,
            destination_country=destination_country,
            product_category=product_category,
            timeframe_months=timeframe_months,
            predicted_volume_tonnes=round(predicted_volume, 0),
            predicted_value_usd=round(predicted_value, 0),
            confidence_interval={
                "lower": round(predicted_value * 0.85, 0),
                "upper": round(predicted_value * 1.15, 0),
            },
            key_factors=[
                f"GDP growth: {growth_rate:.0%}",
                f"Market size: {origin_ind.get('market_size', 0.55):.0%}",
                f"Consumer demand: {dest_ind.get('consumer_demand', 0.55):.0%}",
            ],
            risks=[
                "Currency volatility",
                "Policy changes",
                "Infrastructure bottlenecks",
            ],
            opportunities=[
                "AfCFTA tariff elimination",
                "Digital trade facilitation",
                "Regional value chain integration",
            ],
            trend_direction=trend,
        )

        if self._cache:
            self._cache.l3.set(cache_key, result.to_dict())

        return result


# Singleton
_engine: Optional[InvestmentIntelligenceEngine] = None


def get_intelligence_engine() -> InvestmentIntelligenceEngine:
    global _engine
    if _engine is None:
        _engine = InvestmentIntelligenceEngine()
    return _engine
