"""
Intelligent banking recommendations for AfCFTA trade operations.

Recommends optimal combination of:
- Trade finance instruments (LC, D/C, etc.)
- Banks and banking partners
- Insurance products and insurers
- FX hedging strategies

Based on: country risk + transaction amount + sector + payment terms
"""

from typing import Dict, List, Optional

from .banks_registry import get_country_banks
from .insurance_registry import get_country_insurance_profile
from .models import TradeFinanceInstrument
from .risk_assessment import get_country_risk
from .trade_finance import TRADE_FINANCE_INSTRUMENTS


class TradeFinanceRecommendation:
    """Recommendation bundle for a trade operation"""

    def __init__(self, country_code: str, amount_usd: float, sector: Optional[str] = None):
        self.country_code = country_code.upper()
        self.amount_usd = amount_usd
        self.sector = sector
        self.risk_profile = get_country_risk(country_code)
        self.insurance_profile = get_country_insurance_profile(country_code)

    def get_recommended_instruments(self) -> List[Dict]:
        """Recommend trade finance instruments ranked by suitability."""
        instruments = self.risk_profile.recommended_instruments

        recommendations = []
        for instrument_code in instruments:
            # Find full instrument details
            instrument = next(
                (i for i in TRADE_FINANCE_INSTRUMENTS if i.code == instrument_code), None
            )
            if not instrument:
                continue

            # Calculate score based on risk level
            score = self._score_instrument(instrument)

            recommendations.append(
                {
                    "code": instrument.code,
                    "name": instrument.name,
                    "name_fr": instrument.name_fr,
                    "description": instrument.description,
                    "typical_cost_pct": instrument.typical_cost_pct,
                    "typical_duration_days": instrument.typical_duration_days,
                    "risk_coverage": instrument.risk_coverage,
                    "recommendation_score": score,
                    "reason": self._reason_for_instrument(instrument),
                }
            )

        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations

    def get_recommended_insurance(self) -> Dict:
        """Recommend insurance product + insurer combination."""
        if not self.insurance_profile:
            return {"error": "Insurance not available for this country"}

        insurance_products = self.insurance_profile.available_products
        if not insurance_products:
            return {"error": "No insurance products available"}

        # Recommend export credit insurance as primary
        export_credit_products = [
            p for p in insurance_products if p.product_type.value == "export_credit"
        ]

        if not export_credit_products:
            # Fallback to first available product
            product = insurance_products[0]
        else:
            # Pick comprehensive over single buyer for larger amounts
            if self.amount_usd > 500_000:
                comprehensive = [
                    p for p in export_credit_products if p.coverage_scope.value == "comprehensive"
                ]
                product = comprehensive[0] if comprehensive else export_credit_products[0]
            else:
                product = export_credit_products[0]

        # Recommend insurer(s)
        insurers = self.insurance_profile.available_insurers[:3]  # Top 3

        return {
            "product_type": product.product_type.value,
            "product_name_en": product.name_en,
            "product_name_fr": product.name_fr,
            "coverage_percent": product.coverage_percent,
            "typical_premium_rate_pct": product.premium_rate_basis_points / 100.0,
            "recommended_insurers": [
                {
                    "name": ins.name,
                    "abbreviation": ins.abbreviation,
                    "rating": ins.credit_rating,
                    "capacity_usd_bn": ins.total_capacity_usd_bn,
                }
                for ins in insurers
            ],
            "risk_level": self.insurance_profile.risk_level.value,
            "market_confidence": self.insurance_profile.market_confidence,
        }

    def get_recommended_banks(self) -> List[Dict]:
        """Recommend commercial banks for the operation."""
        banking_info = get_country_banks(self.country_code)
        if not banking_info or not banking_info.commercial_banks:
            return []

        # Score banks by suitability
        scored_banks = []
        for bank in banking_info.commercial_banks:
            if not bank.trade_finance:
                continue

            score = self._score_bank(bank)

            scored_banks.append(
                {
                    "name": bank.name,
                    "abbreviation": bank.abbreviation,
                    "swift_code": bank.swift_code,
                    "website": bank.website,
                    "services": bank.services,
                    "correspondent_banks": bank.correspondent_banks,
                    "recommendation_score": score,
                    "suitability": self._bank_suitability(score),
                }
            )

        # Sort by score
        scored_banks.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return scored_banks[:5]  # Return top 5

    def get_operation_summary(self) -> Dict:
        """Get complete recommendation summary."""
        return {
            "operation": {
                "country_code": self.country_code,
                "country_name": self.risk_profile.country_name,
                "amount_usd": self.amount_usd,
                "sector": self.sector,
            },
            "risk_assessment": {
                "country_risk_rating": self.risk_profile.country_risk_rating,
                "forex_risk": self.risk_profile.forex_risk,
                "political_risk": self.risk_profile.political_risk,
                "transfer_risk": self.risk_profile.transfer_risk,
                "max_exposure_usd": self.risk_profile.max_exposure_usd,
            },
            "recommended_instruments": self.get_recommended_instruments(),
            "recommended_insurance": self.get_recommended_insurance(),
            "recommended_banks": self.get_recommended_banks(),
            "compliance_requirements": self._get_compliance_requirements(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _score_instrument(self, instrument: TradeFinanceInstrument) -> float:
        """Score an instrument based on risk profile and amount."""
        score = 5.0  # Base score

        # Risk rating affects score
        risk_scores = {"A1": 10, "A2": 9, "A3": 8, "A4": 7, "B": 5, "C": 3, "D": 1}
        risk_score = risk_scores.get(self.risk_profile.country_risk_rating, 5)

        # Match recommended instruments more highly
        if instrument.code in self.risk_profile.recommended_instruments:
            score += 3.0

        # Lower cost instruments get slight boost for lower-risk countries
        if risk_score >= 7 and instrument.typical_cost_pct < 2.0:
            score += 1.0

        # Full coverage preferred for high-risk
        if risk_score <= 3 and instrument.risk_coverage == "full":
            score += 2.0

        return score

    def _reason_for_instrument(self, instrument: TradeFinanceInstrument) -> str:
        """Explain why this instrument is recommended."""
        if instrument.code not in self.risk_profile.recommended_instruments:
            return "Alternative option"

        risk = self.risk_profile.country_risk_rating
        if risk in ["C", "D"]:
            return f"High-risk country ({risk}). Full coverage essential."
        elif risk == "B":
            return "Moderate risk. Balances cost and protection."
        else:
            return "Low-risk country. Cost-effective option."

    def _score_bank(self, bank) -> float:
        """Score a bank for this operation."""
        score = 5.0

        # Presence of correspondent banks = higher score
        if bank.correspondent_banks:
            score += len(bank.correspondent_banks) * 0.5

        # Services availability
        score += len(bank.services) * 0.3

        return min(score, 10.0)

    def _bank_suitability(self, score: float) -> str:
        """Describe bank suitability."""
        if score >= 8.0:
            return "Excellent"
        elif score >= 6.0:
            return "Good"
        elif score >= 4.0:
            return "Acceptable"
        else:
            return "Limited"

    def _get_compliance_requirements(self) -> List[str]:
        """Get compliance requirements for operation."""
        reqs = []

        # Country-specific requirements
        if self.country_code in ["NG", "ET", "DZ", "AO"]:
            reqs.append("Documentary Letter of Credit mandatory per central bank rules")

        if self.country_code in ["DZ", "ET"]:
            reqs.append("Form M (Import Declaration Form) required")

        if self.risk_profile.forex_risk in ["high", "very_high"]:
            reqs.append("FX hedging strategy recommended")

        if self.risk_profile.political_risk in ["high", "very_high"]:
            reqs.append("Political risk insurance highly recommended")

        # Sector-specific
        if self.sector and self.sector.lower() in ["arms", "weapons", "nuclear"]:
            reqs.append("Restricted sector - additional compliance checks required")

        return reqs


def get_trade_recommendations(
    country_code: str,
    amount_usd: float,
    sector: Optional[str] = None,
) -> Dict:
    """
    Quick recommendation API for trade operations.

    Args:
        country_code: ISO2 code of trade partner country
        amount_usd: Transaction value in USD
        sector: Business sector (optional)

    Returns:
        Complete recommendation bundle
    """
    recommender = TradeFinanceRecommendation(country_code, amount_usd, sector)
    return recommender.get_operation_summary()
