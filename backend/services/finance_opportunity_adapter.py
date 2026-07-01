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
    return {
        "origin_iso3": (origin_iso3 or "").upper(),
        "destination_iso3": (destination_iso3 or "").upper(),
        "amount_usd": amount_usd,
        "trade_finance": get_trade_finance(destination_iso3, transaction_type, amount_usd),
        "payment_coverage": get_payment_coverage(origin_iso3, destination_iso3),
        "country_risk": get_country_risk(destination_iso3, amount_usd),
        "fx": get_fx(origin_iso3, destination_iso3),
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
