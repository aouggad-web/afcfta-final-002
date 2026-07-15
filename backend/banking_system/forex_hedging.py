"""
FX hedging strategies and recommendations for AfCFTA trade.

Provides hedging recommendations based on:
- Currency convertibility and volatility
- Country risk profile
- Transaction size and horizon
- Cost-benefit analysis
"""

from typing import Dict, List

from .foreign_exchange import get_currency_meta
from .risk_assessment import get_country_risk


class HedgingStrategy:
    """FX hedging strategy recommendation"""

    def __init__(self, name: str, cost_pct: float, effectiveness_pct: float, risk_reduction: str):
        self.name = name
        self.cost_pct = cost_pct
        self.effectiveness_pct = effectiveness_pct
        self.risk_reduction = risk_reduction  # "high" | "medium" | "low"
        self.net_benefit_pct = effectiveness_pct - cost_pct

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "cost_pct": self.cost_pct,
            "effectiveness_pct": self.effectiveness_pct,
            "risk_reduction": self.risk_reduction,
            "net_benefit_pct": self.net_benefit_pct,
        }


# ─────────────────────────────────────────────────────────────────────────────
# HEDGING STRATEGIES CATALOG
# ─────────────────────────────────────────────────────────────────────────────

HEDGING_STRATEGIES = {
    "forward_contract": HedgingStrategy(
        name="Forward Contract (Fixed Rate Lock)",
        cost_pct=0.3,  # 0.3% cost
        effectiveness_pct=100.0,  # Fully locks rate
        risk_reduction="high",
    ),
    "fx_option_put": HedgingStrategy(
        name="FX Put Option (Price Floor)",
        cost_pct=2.0,  # 2% option premium
        effectiveness_pct=100.0,  # Full protection with upside
        risk_reduction="high",
    ),
    "money_market_hedge": HedgingStrategy(
        name="Money Market Hedge (Borrow/Invest)",
        cost_pct=1.5,  # Interest rate differential
        effectiveness_pct=95.0,  # Near-perfect hedge
        risk_reduction="high",
    ),
    "natural_hedge": HedgingStrategy(
        name="Natural Hedge (Offsetting Flows)",
        cost_pct=0.0,  # No cost if internal flows exist
        effectiveness_pct=80.0,  # Partial protection
        risk_reduction="medium",
    ),
    "currency_swap": HedgingStrategy(
        name="Currency Swap (Exchange Currencies)",
        cost_pct=0.75,  # Swap spread
        effectiveness_pct=100.0,  # Full hedge for swapped period
        risk_reduction="high",
    ),
    "no_hedge": HedgingStrategy(
        name="No Hedge (Accept FX Risk)",
        cost_pct=0.0,  # No cost
        effectiveness_pct=0.0,  # No protection
        risk_reduction="low",
    ),
}


def recommend_hedging_strategy(
    country_code: str,
    amount_usd: float,
    transaction_days: int = 90,
    transaction_type: str = "export",
) -> Dict:
    """
    Recommend FX hedging strategy for a trade transaction.

    Args:
        country_code: ISO2 code of counterparty
        amount_usd: Transaction value
        transaction_days: Horizon in days (default 90)
        transaction_type: "export" or "import"

    Returns:
        Hedging recommendation with ranked strategies
    """
    country_code = country_code.upper()

    # Get currency and risk info
    currency_code, currency_name, convertibility = get_currency_meta(country_code)
    risk_profile = get_country_risk(country_code)

    # Determine hedging necessity
    hedging_necessity = _assess_hedging_necessity(
        convertibility, risk_profile.forex_risk, transaction_days, amount_usd
    )

    # Rank strategies
    ranked_strategies = _rank_strategies(
        hedging_necessity,
        amount_usd,
        transaction_days,
        convertibility,
    )

    return {
        "country_code": country_code,
        "currency": {
            "code": currency_code,
            "name": currency_name,
            "convertibility": convertibility,
        },
        "risk_factors": {
            "forex_risk": risk_profile.forex_risk,
            "political_risk": risk_profile.political_risk,
            "hedging_necessity": hedging_necessity,
        },
        "transaction": {
            "amount_usd": amount_usd,
            "horizon_days": transaction_days,
            "type": transaction_type,
        },
        "recommended_strategy": ranked_strategies[0]["name"] if ranked_strategies else "No hedge",
        "all_strategies_ranked": ranked_strategies,
        "explanation": _build_explanation(hedging_necessity, currency_code),
    }


def get_hedging_cost_comparison(
    country_code: str,
    amount_usd: float,
    transaction_days: int = 90,
) -> Dict:
    """
    Compare cost of different hedging strategies for a transaction.

    Useful for cost-benefit analysis.
    """
    strategies_with_costs = []

    for strategy_key, strategy in HEDGING_STRATEGIES.items():
        # Calculate actual costs in USD
        total_cost_usd = amount_usd * (strategy.cost_pct / 100.0)

        # Calculate potential FX loss protected
        risk_profile = get_country_risk(country_code)
        forex_volatility = _estimate_volatility(risk_profile.forex_risk)
        potential_loss = amount_usd * (forex_volatility / 100.0)
        protected_loss = potential_loss * (strategy.effectiveness_pct / 100.0)

        net_benefit = protected_loss - total_cost_usd

        strategies_with_costs.append(
            {
                "strategy": strategy.name,
                "cost_usd": round(total_cost_usd, 2),
                "potential_fx_loss_usd": round(potential_loss, 2),
                "protected_loss_usd": round(protected_loss, 2),
                "net_benefit_usd": round(net_benefit, 2),
                "cost_pct": strategy.cost_pct,
                "effectiveness_pct": strategy.effectiveness_pct,
                "break_even_fx_move_pct": _calculate_breakeven(
                    strategy.cost_pct, strategy.effectiveness_pct
                ),
            }
        )

    # Sort by net benefit
    strategies_with_costs.sort(key=lambda x: x["net_benefit_usd"], reverse=True)

    return {
        "country_code": country_code.upper(),
        "amount_usd": amount_usd,
        "horizon_days": transaction_days,
        "strategies": strategies_with_costs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


def _assess_hedging_necessity(
    convertibility: str,
    forex_risk: str,
    horizon_days: int,
    amount_usd: float,
) -> str:
    """Assess how critical hedging is for this transaction."""

    # Freely convertible = low necessity
    if convertibility == "freely_convertible" and forex_risk == "low":
        return "low"

    # Non-convertible / partially convertible + high risk = critical
    if convertibility in ["non_convertible", "partially_convertible"] and forex_risk in [
        "high",
        "very_high",
    ]:
        return "critical"

    # Large amounts need hedging
    if amount_usd > 1_000_000:
        if forex_risk in ["high", "very_high"]:
            return "critical"
        elif forex_risk == "moderate":
            return "high"

    # Long horizons need hedging
    if horizon_days > 180 and forex_risk != "low":
        return "high"

    return "moderate"


def _rank_strategies(
    necessity: str,
    amount_usd: float,
    horizon_days: int,
    convertibility: str,
) -> List[Dict]:
    """Rank hedging strategies for the scenario."""

    if necessity == "low":
        # For low necessity: prioritize no-cost options
        ranking = [
            "natural_hedge",
            "forward_contract",
            "no_hedge",
            "fx_option_put",
            "money_market_hedge",
            "currency_swap",
        ]
    elif necessity == "critical":
        # For critical: prioritize full protection
        ranking = [
            "forward_contract",
            "money_market_hedge",
            "currency_swap",
            "fx_option_put",
            "natural_hedge",
            "no_hedge",
        ]
    else:  # moderate or high
        # Balance cost and protection
        ranking = [
            "forward_contract",
            "fx_option_put",
            "natural_hedge",
            "money_market_hedge",
            "currency_swap",
            "no_hedge",
        ]

    # Adjust for large amounts (need liquid instruments)
    if amount_usd > 2_000_000:
        # Currency swaps preferred for large amounts
        if "currency_swap" in ranking:
            ranking.remove("currency_swap")
            ranking.insert(0, "currency_swap")

    result = []
    for strategy_key in ranking:
        if strategy_key in HEDGING_STRATEGIES:
            strategy = HEDGING_STRATEGIES[strategy_key]
            result.append(
                {
                    "key": strategy_key,
                    "name": strategy.name,
                    "cost_pct": strategy.cost_pct,
                    "effectiveness_pct": strategy.effectiveness_pct,
                    "risk_reduction": strategy.risk_reduction,
                    "net_benefit_pct": strategy.net_benefit_pct,
                }
            )

    return result


def _estimate_volatility(forex_risk: str) -> float:
    """Estimate currency volatility based on risk level."""
    volatility_map = {
        "low": 2.0,
        "moderate": 5.0,
        "high": 10.0,
        "very_high": 20.0,
    }
    return volatility_map.get(forex_risk, 5.0)


def _calculate_breakeven(cost_pct: float, effectiveness_pct: float) -> float:
    """Calculate FX move % where hedging breaks even."""
    if effectiveness_pct == 0:
        return 999.0  # No breakeven
    return cost_pct / (effectiveness_pct / 100.0)


def _build_explanation(necessity: str, currency_code: str) -> str:
    """Build explanation for the recommendation."""

    explanations = {
        "low": f"Currency {currency_code} is stable and freely convertible. Hedging is optional.",
        "moderate": f"Moderate FX risk for {currency_code}. Consider hedging for transactions > USD 250k.",
        "high": f"High FX volatility for {currency_code}. Hedging recommended for transactions > USD 100k.",
        "critical": f"Critical FX risk for {currency_code}. Hedging strongly recommended for all transactions.",
    }

    return explanations.get(necessity, "Assess hedging needs based on transaction details.")
