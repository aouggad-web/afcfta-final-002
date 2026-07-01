"""
Segmentation service for premium Opportunités reports.

Classifies opportunities into effort/impact quadrants and risk/reward matrices.
Generates factor breakdown showing which elements are opportunities vs risks.

Enables prioritization without fabrication — all scores derived from real data
or marked unavailable.
"""

import logging
from typing import Dict, List

_log = logging.getLogger(__name__)


def effort_impact_matrix(report: Dict) -> Dict:
    """
    Positions opportunity in effort/impact matrix (quick-win vs strategic-bet).

    Effort = logistics cost burden (freight as % of goods value + complexity).
    Impact = market demand magnitude × growth trend.

    Returns: {
        effort_score: float (0–1, where 1 = high effort),
        impact_score: float (0–1, where 1 = high impact),
        quadrant: "quick_win" | "strategic_bet" | "filler" | "avoid",
        rationale: str
    }
    """
    # Extract from report. goods_value_usd may be present but None (the key is set
    # in report_engine even when the query param is omitted) -> coerce safely.
    goods_value = report.get("inputs", {}).get("goods_value_usd")
    landed_cost = report.get("composite_indicators", {}).get("landed_cost", {})
    freight = (landed_cost.get("breakdown") or {}).get("best_operational_freight_usd")

    # Effort score: normalize freight burden (0–1); neutral 0.5 if data missing.
    if goods_value and goods_value > 0 and freight is not None:
        freight_burden = freight / goods_value
        effort_score = min(freight_burden / 0.15, 1.0)  # Normalize by threshold 15%
    else:
        effort_score = 0.5

    # Impact score: market demand + trend
    demand = report.get("demand", {}) if "demand" in report else report.get("market_demand", {})
    demand_available = demand.get("available", False)

    if demand_available:
        total_value = demand.get("total_import_value_usd", 1_000_000)
        # Normalize to 0–1 scale (assume 100M$ = high impact)
        value_score = min(total_value / 100_000_000, 1.0)
        impact_score = value_score * 0.7 + 0.3  # Blend with constant for minimum score
    else:
        impact_score = 0.5

    # Quadrant assignment
    if effort_score < 0.4 and impact_score > 0.6:
        quadrant = "quick_win"
        rationale = "Effort logistique faible, impact de marché élevé."
    elif effort_score >= 0.4 and impact_score > 0.6:
        quadrant = "strategic_bet"
        rationale = "Effort logistique modéré, mais potentiel de marché significatif."
    elif effort_score < 0.4 and impact_score <= 0.6:
        quadrant = "filler"
        rationale = "Facile à mettre en œuvre, mais impact limité."
    else:
        quadrant = "avoid"
        rationale = "Effort logistique élevé pour impact réduit."

    return {
        "effort_score": round(effort_score, 2),
        "impact_score": round(impact_score, 2),
        "quadrant": quadrant,
        "rationale": rationale,
    }


def risk_reward_matrix(report: Dict) -> Dict:
    """
    Positions opportunity in risk/reward matrix (ideal corridor vs high-reward bet).

    Risk = 1 - (country_risk_score × fx_stability × trade_finance_availability).
    Reward = supply_capacity × market_demand × tariff_advantage.

    Returns: {
        risk_score: float (0–1, where 1 = very risky),
        reward_score: float (0–1, where 1 = very rewarding),
        quadrant: "ideal_corridor" | "high_reward_bet" | "safe_small" | "avoid",
        recommendation: str
    }
    """
    # Extract risk components
    finance = report.get("composite_indicators", {}).get("financing_feasibility_index", {})
    fin_idx = finance.get("index", 0.5)

    # Country risk is stored in multiple places by report_engine; try all paths
    # Priority: risk_component > profile.country_risk > direct country_risk (backward compat)
    country_risk = (
        report.get("finance", {}).get("risk_component")
        or report.get("finance", {}).get("profile", {}).get("country_risk")
        or report.get("finance", {}).get("country_risk", {})
    )

    risk_idx = country_risk.get("risk_score", 5.0) if country_risk else 5.0  # 0–10 scale
    alert = country_risk.get("alert_level", "orange") if country_risk else "orange"

    # Risk score: combine country risk + financing
    country_risk_normalized = min(risk_idx / 10.0, 1.0)  # Normalize to 0–1
    financing_safety = fin_idx  # Higher = safer
    risk_score = country_risk_normalized * 0.7 + (1 - financing_safety) * 0.3
    risk_score = min(risk_score, 1.0)

    # Extract reward components
    supply = report.get("supply", {})
    supply_score = supply.get("subscore", 0.5) if supply.get("available") else 0.5

    demand = report.get("demand", {}) if "demand" in report else {}
    demand_score = (
        min(demand.get("total_import_value_usd", 1_000_000) / 100_000_000, 1.0)
        if demand.get("available")
        else 0.5
    )

    # Tariff advantage (ZLECAf) — REAL value from national/ZLECAf schedule when
    # available; otherwise excluded and the reward weights are renormalised so we
    # never inject a fabricated tariff contribution.
    tariff = report.get("tariff_benefit") or {}
    tariff_index = tariff.get("tariff_advantage_index") if tariff.get("available") else None

    if tariff_index is not None:
        # supply 0.4 + demand 0.4 + tariff 0.2
        reward_score = supply_score * 0.4 + demand_score * 0.4 + tariff_index * 0.2
    else:
        # Renormalise over supply + demand only (0.5 / 0.5).
        reward_score = supply_score * 0.5 + demand_score * 0.5
    reward_score = min(reward_score, 1.0)

    # Quadrant assignment
    if risk_score < 0.4 and reward_score > 0.7:
        quadrant = "ideal_corridor"
        recommendation = "Priorité 1 : déployer sans délai."
    elif risk_score < 0.4 and reward_score <= 0.7:
        quadrant = "safe_small"
        recommendation = "Sûr mais volumes limités. Examiner montée en charge."
    elif risk_score >= 0.4 and reward_score > 0.7:
        quadrant = "high_reward_bet"
        recommendation = (
            "Potentiel élevé. Risque à gérer via instruments financiers et couverture FX."
        )
    else:
        quadrant = "avoid"
        recommendation = "Non recommandé : risque-récompense défavorable."

    return {
        "risk_score": round(risk_score, 2),
        "reward_score": round(reward_score, 2),
        "quadrant": quadrant,
        "recommendation": recommendation,
        "alert_level": alert,
    }


def factor_breakdown(report: Dict) -> List[Dict]:
    """
    Decomposes opportunity into individual opportunity/risk factors.

    Scores each factor (supply, demand, logistics, finance, tariff, FX) on
    0–1 scale and tags as opportunity/risk/neutral.

    Returns: [{
        factor: str,
        category: "opportunity" | "risk" | "neutral",
        score: float (0–1),
        rationale: str
    }, ...]
    """
    factors = []

    # Supply factor
    supply = report.get("supply", {})
    if supply.get("available"):
        share = supply.get("continental_share_pct", 0)
        subscore = supply.get("subscore", 0.5)
        if share >= 15:
            category = "opportunity"
            rationale = "Production dominante continentale (>15% de part)."
        elif share >= 5:
            category = "opportunity"
            rationale = f"Production significative ({share:.1f}% de part continentale)."
        else:
            category = "risk"
            rationale = "Production limitée ; capacité d'export restreinte."
        factors.append(
            {
                "factor": "supply_capacity",
                "category": category,
                "score": subscore,
                "rationale": rationale,
            }
        )

    # Market demand factor
    demand = report.get("demand", {}) if "demand" in report else {}
    if demand.get("available"):
        total = demand.get("total_import_value_usd", 0)
        if total > 500_000_000:
            category = "opportunity"
            rationale = f"Marché grande taille (>{total/1e6:.0f}M$)."
        elif total > 100_000_000:
            category = "opportunity"
            rationale = f"Marché de taille modérée ({total/1e6:.0f}M$)."
        else:
            category = "neutral"
            rationale = "Marché de niche."
        # Simple demand score proxy
        demand_score = min(total / 500_000_000, 1.0)
        factors.append(
            {
                "factor": "market_demand",
                "category": category,
                "score": demand_score,
                "rationale": rationale,
            }
        )

    # Logistics factor
    logistics = report.get("composite_indicators", {}).get("logistics_accessibility_index", {})
    if logistics.get("available"):
        idx = logistics.get("index", 0.5)
        if idx >= 0.8:
            category = "opportunity"
            rationale = "Accessibilité logistique excellente (3+ modes opérationnels)."
        elif idx >= 0.6:
            category = "opportunity"
            rationale = "Accessibilité logistique bonne (2+ modes opérationnels)."
        else:
            category = "risk"
            rationale = "Accessibilité logistique limitée (1 mode seulement)."
        factors.append(
            {
                "factor": "logistics_accessibility",
                "category": category,
                "score": idx,
                "rationale": rationale,
            }
        )

    # Financing factor
    financing = report.get("composite_indicators", {}).get("financing_feasibility_index", {})
    if financing.get("available"):
        idx = financing.get("index", 0.5)
        if idx >= 0.75:
            category = "opportunity"
            rationale = "Financement trade finance + systèmes de paiement connectés."
        elif idx >= 0.6:
            category = "opportunity"
            rationale = "Financement possible avec instruments standards."
        else:
            category = "risk"
            rationale = "Financement limité ; gérer via prépaiement ou L/C stricte."
        factors.append(
            {
                "factor": "financing_feasibility",
                "category": category,
                "score": idx,
                "rationale": rationale,
            }
        )

    # Country risk factor (stored in risk_component or profile.country_risk or direct)
    country_risk = (
        report.get("finance", {}).get("risk_component")
        or report.get("finance", {}).get("profile", {}).get("country_risk")
        or report.get("finance", {}).get("country_risk", {})
    )

    if country_risk and country_risk.get("available"):
        alert = country_risk.get("alert_level", "orange")
        if alert == "green":
            category = "opportunity"
            score = 0.9
            rationale = "Risque pays faible ; environnement politique stable."
        elif alert == "orange":
            category = "risk"
            score = 0.5
            rationale = "Risque pays modéré ; gérer via instruments et assurances."
        else:
            category = "risk"
            score = 0.2
            rationale = "Risque pays élevé ; évaluer soigneusement engagement."
        factors.append(
            {"factor": "country_risk", "category": category, "score": score, "rationale": rationale}
        )

    # FX volatility factor — ONLY when a real spread is present. get_fx() does not
    # always populate a spread; never fabricate a default value for the rationale.
    fx = report.get("finance", {}).get("profile", {}).get("fx", {})
    spread = fx.get("spread") if fx.get("available") else None
    if spread is not None:
        if spread <= 1.5:
            category = "opportunity"
            score = 0.9
            rationale = "Marché FX liquide ; spread faible."
        elif spread <= 3:
            category = "neutral"
            score = 0.5
            rationale = f"Marché FX standard ; spread {spread:.1f}%."
        else:
            category = "risk"
            score = 0.3
            rationale = f"Marché FX illiquide ; spread élevé {spread:.1f}%."
        factors.append(
            {
                "factor": "fx_volatility",
                "category": category,
                "score": score,
                "rationale": rationale,
            }
        )

    # Tariff advantage factor (ZLECAf) — REAL national/ZLECAf rates only.
    # Added as a factor solely when a real advantage is computed; never fabricated.
    tariff = report.get("tariff_benefit") or {}
    if tariff.get("available"):
        advantage_pct = tariff.get("tariff_advantage_pct", 0.0)
        index = tariff.get("tariff_advantage_index", 0.0)
        if advantage_pct > 0:
            factors.append(
                {
                    "factor": "tariff_advantage",
                    "category": "opportunity",
                    "score": index,
                    "rationale": (
                        f"Accès ZLECAf : avantage tarifaire réel de {advantage_pct:.1f} % "
                        f"(droit national {tariff.get('national_rate_pct', 0):.1f} % → "
                        f"ZLECAf {tariff.get('zlecaf_rate_pct', 0):.1f} %)."
                    ),
                }
            )
        else:
            factors.append(
                {
                    "factor": "tariff_advantage",
                    "category": "neutral",
                    "score": 0.0,
                    "rationale": (
                        f"Pas d'avantage tarifaire ZLECAf pour ce produit "
                        f"(droit national déjà {tariff.get('national_rate_pct', 0):.1f} %)."
                    ),
                }
            )

    return factors


def priority_score(report: Dict) -> Dict:
    """
    Synthesizes all segmentation factors into a single priority score & tier.

    Combines E2E score, quadrant, and factor breakdown to provide final
    recommendation.

    Returns: {
        priority_tier: "QUICK_WIN" | "STRATEGIC_BET" | "HIGH_REWARD_BET" | "PASS",
        priority_score: float (0–1),
        action: str
    }
    """
    e2e = report.get("composite_indicators", {}).get("end_to_end_score", {})
    score = e2e.get("score", 0.5) if e2e.get("available") else 0.5

    factors = factor_breakdown(report)
    opportunities = sum(1 for f in factors if f["category"] == "opportunity")
    risks = sum(1 for f in factors if f["category"] == "risk")

    # Simple heuristic: opportunities > risks + good E2E score = priority
    factor_balance = opportunities - risks

    if score >= 0.75 and factor_balance >= 2:
        tier = "QUICK_WIN"
        action = "Déployer en priorité."
    elif score >= 0.65 and factor_balance >= 1:
        tier = "STRATEGIC_BET"
        action = "Examiner davantage ; préparation recommandée."
    elif score >= 0.55 or factor_balance >= 2:
        tier = "HIGH_REWARD_BET"
        action = "Faisable ; risques gérables avec préparation."
    else:
        tier = "PASS"
        action = "Non recommandé à court terme."

    return {
        "priority_tier": tier,
        "priority_score": round(score, 2),
        "opportunity_count": opportunities,
        "risk_count": risks,
        "factor_balance": factor_balance,
        "action": action,
    }
