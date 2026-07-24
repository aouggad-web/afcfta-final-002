"""
Finance adapter for the premium Opportunités report engine.

Thin wrapper over the platform's *existing* banking / currency / macro modules —
it does not duplicate their logic, it composes them into a single
"can this deal be financed and paid, and how risky is it?" view for a
(origin exporter → destination market) pair.

Angles composed:
  - Trade finance instruments recommended for the transaction (banking_system).
  - Regional payment-system coverage between the two countries, incl. PAPSS.
  - Destination country risk assessment (banking_system).
  - Live FX rate between the two national currencies (exchange_rates), when the
    rate provider is reachable.
  - Macro indicators of the destination importer: GAI, gold/FX reserves and
    import cover (macro_indicators_service) — a market's reserves and import
    cover speak to its capacity to pay for imports.

Every angle degrades gracefully: an unavailable module/provider yields
``None``/``available: False`` with a note, never a fabricated value.
Banking modules key on ISO2; this adapter accepts ISO3 and converts.
"""

import dataclasses
import logging
from typing import Dict, List, Optional

from services import macro_indicators_service as macro

_log = logging.getLogger(__name__)


def _iso2(country_code: str) -> str:
    try:
        from currencies.service import to_iso2

        return to_iso2(country_code)
    except Exception:  # pragma: no cover - defensive
        code = (country_code or "").strip().upper()
        return code[:2]


def _serialize(obj):
    """Best-effort serialization of dataclass / pydantic / plain objects."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_serialize(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if dataclasses.is_dataclass(obj):
        return _serialize(dataclasses.asdict(obj))
    if hasattr(obj, "model_dump"):
        return _serialize(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return _serialize(vars(obj))
    return obj


def _currency_code(country_iso: str) -> Optional[str]:
    try:
        from currencies.service import get_by_country

        info = get_by_country(country_iso)
        return getattr(info, "currency_code", None) if info else None
    except Exception:  # pragma: no cover - defensive
        return None


def get_trade_finance(
    destination_iso3: str, transaction_type: str = "export", amount_usd: float = 0.0
) -> Dict:
    """Recommended trade-finance instruments for the transaction."""
    try:
        from banking_system import recommend_instruments

        instruments = recommend_instruments(_iso2(destination_iso3), transaction_type, amount_usd)
        return {"available": True, "instruments": _serialize(instruments)}
    except Exception as exc:
        _log.warning("trade finance unavailable: %s", exc)
        return {"available": False, "instruments": [], "note": str(exc)}


def get_payment_coverage(origin_iso3: str, destination_iso3: str) -> Dict:
    """Regional payment systems connecting both countries (PAPSS highlighted)."""
    try:
        from banking_system import get_payment_systems

        o2, d2 = _iso2(origin_iso3), _iso2(destination_iso3)
        systems = _serialize(get_payment_systems()) or []
        shared = []
        for s in systems:
            members = s.get("member_countries") or []
            if o2 in members and d2 in members:
                shared.append(s)
        papss = any((s.get("code") or "").upper() == "PAPSS" for s in shared)
        return {
            "available": True,
            "shared_systems": shared,
            "papss_covered": papss,
        }
    except Exception as exc:
        _log.warning("payment systems unavailable: %s", exc)
        return {"available": False, "shared_systems": [], "papss_covered": None, "note": str(exc)}


def get_country_risk(destination_iso3: str, amount_usd: float = 0.0) -> Dict:
    """Destination country risk assessment."""
    try:
        from banking_system import assess_transaction_risk

        res = assess_transaction_risk(_iso2(destination_iso3), amount_usd, "export")
        return {"available": True, **_serialize(res)}
    except Exception as exc:
        _log.warning("risk assessment unavailable: %s", exc)
        return {"available": False, "note": str(exc)}


def get_fx(origin_iso3: str, destination_iso3: str) -> Dict:
    """Live FX rate between the two national currencies, if the provider answers."""
    o_cur = _currency_code(origin_iso3)
    d_cur = _currency_code(destination_iso3)
    result = {"origin_currency": o_cur, "destination_currency": d_cur, "available": False}
    if not o_cur or not d_cur:
        result["note"] = "Devise nationale introuvable."
        return result
    if o_cur == d_cur:
        result.update({"available": True, "rate": 1.0, "note": "Même devise (union monétaire)."})
        return result
    try:
        from exchange_rates import get_service

        rate = get_service().get_rate(o_cur, d_cur)
        if rate is None:
            result["note"] = "Taux indisponible (fournisseur injoignable)."
            return result
        result.update(
            {
                "available": True,
                "rate": getattr(rate, "rate", None),
                "timestamp": getattr(rate, "timestamp", None),
                "source": getattr(rate, "source", None),
            }
        )
        return result
    except Exception as exc:
        _log.warning("fx rate unavailable: %s", exc)
        result["note"] = str(exc)
        return result


def get_finance_profile(
    origin_iso3: str,
    destination_iso3: str,
    amount_usd: float = 0.0,
    transaction_type: str = "export",
) -> Dict:
    """Compose the full finance view for an origin → destination deal."""
    trade_finance = get_trade_finance(destination_iso3, transaction_type, amount_usd)
    payment_coverage = get_payment_coverage(origin_iso3, destination_iso3)
    country_risk = get_country_risk(destination_iso3, amount_usd)
    fx = get_fx(origin_iso3, destination_iso3)
    return {
        "origin_iso3": (origin_iso3 or "").upper(),
        "destination_iso3": (destination_iso3 or "").upper(),
        "amount_usd": amount_usd,
        # Top-level flag: true when at least one angle resolved (consumers such as
        # the narrative layer can rely on it directly).
        "available": any(
            (a or {}).get("available") for a in (trade_finance, payment_coverage, country_risk, fx)
        ),
        "trade_finance": trade_finance,
        "payment_coverage": payment_coverage,
        "country_risk": country_risk,
        "fx": fx,
        "destination_macro": macro.get_macro_profile(destination_iso3),
    }


def summarize_financing_feasibility(profile: Dict) -> Dict:
    """
    Transparent, rule-based financing-feasibility index in [0, 1].

    Components (each contributes only when its data is available):
      - trade-finance instruments recommended  -> +0.30
      - PAPSS / shared payment system coverage  -> +0.20
      - destination risk (alert green/orange/red) -> up to +0.30
      - destination import cover (>=3 months healthy) -> up to +0.20

    ``components`` lists exactly what was counted so the score is never a black
    box; ``available`` is False when no component could be evaluated.
    """
    components: List[Dict] = []
    score = 0.0
    max_score = 0.0

    tf = profile.get("trade_finance") or {}
    if tf.get("available"):
        max_score += 0.30
        has = bool(tf.get("instruments"))
        gained = 0.30 if has else 0.0
        score += gained
        components.append({"factor": "trade_finance_instruments", "weight": 0.30, "gained": gained})

    pay = profile.get("payment_coverage") or {}
    if pay.get("available"):
        max_score += 0.20
        gained = 0.20 if pay.get("papss_covered") else (0.10 if pay.get("shared_systems") else 0.0)
        score += gained
        components.append({"factor": "payment_coverage", "weight": 0.20, "gained": gained})

    risk = profile.get("country_risk") or {}
    if risk.get("available"):
        max_score += 0.30
        alert = (risk.get("alert_level") or "").lower()
        gained = {"green": 0.30, "orange": 0.15, "red": 0.05}.get(alert, 0.0)
        score += gained
        components.append(
            {"factor": "country_risk", "weight": 0.30, "gained": gained, "alert_level": alert}
        )

    cover = ((profile.get("destination_macro") or {}).get("import_cover")) or {}
    if cover.get("available"):
        max_score += 0.20
        months = cover.get("months") or 0
        gained = 0.20 if months >= 3 else round(0.20 * (months / 3.0), 3)
        score += gained
        components.append(
            {"factor": "import_cover", "weight": 0.20, "gained": gained, "months": months}
        )

    if max_score == 0.0:
        return {"available": False, "index": None, "components": components}

    return {
        "available": True,
        "index": round(score / max_score, 3),
        "raw_score": round(score, 3),
        "max_possible": round(max_score, 3),
        "components": components,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BANKING ENHANCEMENTS (OPTIONS 1-4)
# ─────────────────────────────────────────────────────────────────────────────


def get_intelligent_recommendations(
    destination_iso3: str,
    amount_usd: float = 0.0,
    sector: Optional[str] = None,
    transaction_type: str = "export",
) -> Dict:
    """
    OPTION 1: Intelligent banking recommendations.

    Complete recommendation bundle for a trade operation:
    - Ranked trade finance instruments
    - Suitable insurance products
    - Recommended banks scored by suitability
    - Country-specific compliance requirements
    """
    try:
        from banking_system import get_trade_recommendations

        recommendations = get_trade_recommendations(_iso2(destination_iso3), amount_usd, sector)
        return {"available": True, "recommendations": _serialize(recommendations)}
    except Exception as exc:
        _log.warning("intelligent recommendations unavailable: %s", exc)
        return {"available": False, "recommendations": None, "note": str(exc)}


def get_bank_scoring(
    destination_iso3: str,
    amount_usd: float = 0.0,
    transaction_type: str = "export",
    sector: Optional[str] = None,
    limit: int = 5,
) -> Dict:
    """
    OPTION 2: Enhanced bank scoring and ranking.

    Score banks by multi-factor suitability:
    - Geographic presence & regional expertise (30%)
    - Service offering alignment (25%)
    - Correspondent network quality (25%)
    - Transaction amount suitability (10%)
    - Specialization match (10%)
    """
    try:
        from banking_system import get_country_banks
        from banking_system.bank_scoring import score_banks_for_transaction

        banking_info = get_country_banks(_iso2(destination_iso3))
        if not banking_info or not banking_info.commercial_banks:
            return {"available": False, "banks": [], "note": "No banks found"}

        scored_banks = score_banks_for_transaction(
            banking_info.commercial_banks,
            _iso2(destination_iso3),
            transaction_type=transaction_type,
            amount_usd=amount_usd,
            sector=sector,
        )

        # Limit results
        scored_banks = scored_banks[:limit]

        return {
            "available": True,
            "country": banking_info.country_name,
            "banks_scored": len(scored_banks),
            "banks": _serialize(scored_banks),
            "top_bank": (scored_banks[0]["name"] if scored_banks else None),
        }
    except Exception as exc:
        _log.warning("bank scoring unavailable: %s", exc)
        return {"available": False, "banks": [], "note": str(exc)}


def get_fx_hedging_strategy(
    destination_iso3: str,
    amount_usd: float = 0.0,
    transaction_days: int = 90,
    transaction_type: str = "export",
) -> Dict:
    """
    OPTION 3: FX hedging strategy recommendations.

    Evaluates hedging necessity and ranks strategies:
    - Forward contracts
    - FX options
    - Money market hedges
    - Natural hedges
    - Currency swaps
    - No hedge (for reference)

    Includes cost-benefit analysis and break-even calculations.
    """
    try:
        from banking_system.forex_hedging import (
            get_hedging_cost_comparison,
            recommend_hedging_strategy,
        )

        recommendation = recommend_hedging_strategy(
            _iso2(destination_iso3),
            amount_usd,
            transaction_days=transaction_days,
            transaction_type=transaction_type,
        )

        cost_comparison = get_hedging_cost_comparison(
            _iso2(destination_iso3),
            amount_usd,
            transaction_days=transaction_days,
        )

        return {
            "available": True,
            "hedging_necessity": recommendation["risk_factors"]["hedging_necessity"],
            "recommended_strategy": recommendation["recommended_strategy"],
            "explanation": recommendation["explanation"],
            "all_strategies": _serialize(recommendation["all_strategies_ranked"]),
            "cost_comparison": _serialize(cost_comparison["strategies"]),
        }
    except Exception as exc:
        _log.warning("fx hedging unavailable: %s", exc)
        return {
            "available": False,
            "hedging_necessity": None,
            "recommended_strategy": None,
            "note": str(exc),
        }


def get_financing_matrix_analysis(
    destination_iso3: str,
    amount_usd: float = 0.0,
    risk_rating: Optional[str] = None,
) -> Dict:
    """
    OPTION 4: Financing matrix and comparative analysis.

    Provides:
    - Instrument comparison (cost, protection, speed, suitability)
    - Risk-based recommendations (A1-D ratings)
    - Transaction size recommendations (micro-mega brackets)
    - Cost-benefit analysis for specific transaction
    - Interactive decision tree
    """
    try:
        from banking_system.financing_matrix import FinancingMatrix

        # Get cost-benefit analysis if amount provided
        cost_benefit = None
        if amount_usd > 10000:
            cost_benefit = FinancingMatrix.get_cost_benefit_analysis(
                _iso2(destination_iso3), amount_usd
            )

        return {
            "available": True,
            "instruments_matrix": _serialize(FinancingMatrix.get_instrument_comparison()),
            "risk_matrix": _serialize(FinancingMatrix.get_risk_based_matrix()),
            "size_matrix": _serialize(FinancingMatrix.get_transaction_size_matrix()),
            "decision_tree": _serialize(FinancingMatrix.get_quick_decision_tree()),
            "cost_benefit_analysis": (_serialize(cost_benefit) if cost_benefit else None),
        }
    except Exception as exc:
        _log.warning("financing matrix unavailable: %s", exc)
        return {"available": False, "note": str(exc)}


def get_enhanced_finance_profile(
    origin_iso3: str,
    destination_iso3: str,
    amount_usd: float = 0.0,
    sector: Optional[str] = None,
    transaction_type: str = "export",
    include_enhancements: bool = True,
) -> Dict:
    """
    Enhanced finance profile combining base profile + 4 banking enhancements.

    When include_enhancements=True, adds:
    - Option 1: Intelligent recommendations
    - Option 2: Bank scoring
    - Option 3: FX hedging strategy
    - Option 4: Financing matrix analysis

    Gracefully degrades if enhancement modules unavailable.
    """
    # Base profile (existing)
    profile = get_finance_profile(origin_iso3, destination_iso3, amount_usd, transaction_type)

    # Add enhancements if requested
    if include_enhancements:
        profile["enhancements"] = {
            "intelligent_recommendations": get_intelligent_recommendations(
                destination_iso3, amount_usd, sector, transaction_type
            ),
            "bank_scoring": get_bank_scoring(
                destination_iso3, amount_usd, transaction_type, sector, limit=5
            ),
            "fx_hedging": get_fx_hedging_strategy(
                destination_iso3, amount_usd, transaction_days=90, transaction_type=transaction_type
            ),
            "financing_matrix": get_financing_matrix_analysis(destination_iso3, amount_usd),
        }

    return profile
