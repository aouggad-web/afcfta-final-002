"""
Report engine — orchestrator for the premium Opportunités module.

Composes the platform's real-data angles (production/supply, logistics, finance
& macro) into a single bilateral product-opportunity report and computes the
transparent composite indicators described in
``docs/MODULE_OPPORTUNITES_PLAN_PREMIUM.md``:

  - **Landed cost** = goods value (FOB) + cheapest operational freight.
  - **Financing-feasibility index** (from the finance adapter).
  - **Logistics-accessibility index** (from the logistics adapter).
  - **End-to-end opportunity score** = transparent weighted blend of the
    available component sub-scores. Weights are returned in the payload and are
    caller-overridable — never a black box.

No-fabrication discipline throughout: a component whose real source is
unreachable (e.g. OEC per-product flows, blocked by egress policy here) is
reported with ``available: False`` and simply excluded from the weighted score,
which is renormalised over the components that *do* have data.
"""

import logging
from typing import Dict, Optional

from services import finance_opportunity_adapter as finance
from services import logistics_opportunity_adapter as logistics

_log = logging.getLogger(__name__)

# Default weights for the end-to-end score. Callers may override any subset.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "market_potential": 0.25,  # OEC per-product demand — unavailable w/o paid API
    "supply_capacity": 0.25,  # production_capacity_service (FAO/USGS/UNIDO)
    "logistics_accessibility": 0.20,  # multimodal freight comparator
    "financing_feasibility": 0.20,  # banking + macro
    "country_risk": 0.10,  # banking risk assessment
}


def _supply_component(origin_iso3: str, hs_code: str) -> Dict:
    """Supply capacity sub-score from real production data (or unavailable)."""
    try:
        from services.production_capacity_service import get_capacity

        cap = get_capacity(origin_iso3, hs_code)
    except Exception as exc:
        _log.warning("production capacity unavailable: %s", exc)
        return {"available": False, "subscore": None, "note": str(exc)}

    if not cap.get("available"):
        return {"available": False, "subscore": None, "reason": cap.get("reason"), "detail": cap}

    share = (cap.get("continental") or {}).get("country_share_pct")
    if share is not None:
        # >=25% continental share => dominant supplier (subscore 1.0).
        subscore = round(min(share / 25.0, 1.0), 3)
    else:
        subscore = 0.5 if cap.get("latest_value") else 0.0
    return {
        "available": True,
        "subscore": subscore,
        "continental_share_pct": share,
        "rank": (cap.get("continental") or {}).get("rank"),
        "commodity": cap.get("commodity"),
        "source": cap.get("source"),
        "detail": cap,
    }


def _risk_component(country_risk: Dict) -> Dict:
    """Country-risk sub-score (1 = safest) from the finance risk assessment."""
    if not country_risk.get("available"):
        return {"available": False, "subscore": None}
    score = country_risk.get("risk_score")
    if score is None:
        return {"available": False, "subscore": None}
    return {
        "available": True,
        "subscore": round(max(0.0, 1.0 - score / 10.0), 3),
        "risk_score": score,
        "alert_level": country_risk.get("alert_level"),
    }


def _landed_cost(goods_value_usd: Optional[float], best_freight_usd: Optional[float]) -> Dict:
    """FOB + freight landed cost, with decomposition; null if a leg is missing."""
    if goods_value_usd is None or best_freight_usd is None:
        return {
            "available": False,
            "value_usd": None,
            "note": (
                "Coût rendu indisponible : "
                + (
                    "valeur des marchandises non fournie"
                    if goods_value_usd is None
                    else "coût de fret opérationnel indisponible"
                )
            ),
        }
    return {
        "available": True,
        "value_usd": round(goods_value_usd + best_freight_usd, 2),
        "breakdown": {
            "goods_value_fob_usd": goods_value_usd,
            "best_operational_freight_usd": best_freight_usd,
        },
        "note": "FX inclus séparément (voir volet finance). Fret = option opérationnelle la moins chère.",
    }


def _end_to_end_score(components: Dict[str, Dict], weights: Dict[str, float]) -> Dict:
    """Weighted blend over *available* components, renormalised transparently."""
    breakdown = []
    weighted_sum = 0.0
    weight_used = 0.0
    for key, weight in weights.items():
        comp = components.get(key) or {}
        sub = comp.get("subscore")
        if comp.get("available") and sub is not None:
            weighted_sum += weight * sub
            weight_used += weight
            breakdown.append({"component": key, "weight": weight, "subscore": sub, "counted": True})
        else:
            breakdown.append(
                {"component": key, "weight": weight, "subscore": None, "counted": False}
            )
    if weight_used == 0.0:
        return {"available": False, "score": None, "breakdown": breakdown}
    return {
        "available": True,
        "score": round(weighted_sum / weight_used, 3),
        "weight_coverage": round(weight_used, 3),
        "breakdown": breakdown,
        "note": "Score = moyenne pondérée des composantes disponibles, renormalisée.",
    }


def get_opportunity_report(
    hs_code: str,
    origin_iso3: str,
    destination_iso3: str,
    goods_value_usd: Optional[float] = None,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
    weights: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Bilateral product-opportunity report: origin exports ``hs_code`` to
    destination. Combines supply, logistics, finance/macro and a transparent
    end-to-end score.
    """
    origin_iso3 = (origin_iso3 or "").upper()
    destination_iso3 = (destination_iso3 or "").upper()
    amount = goods_value_usd or 0.0
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    log_profile = logistics.get_logistics_profile(
        origin_iso3, destination_iso3, weight_kg, volume_m3
    )
    fin_profile = finance.get_finance_profile(origin_iso3, destination_iso3, amount, "export")

    supply = _supply_component(origin_iso3, hs_code)
    log_access = logistics.summarize_logistics_accessibility(log_profile)
    fin_feasibility = finance.summarize_financing_feasibility(fin_profile)
    risk = _risk_component(fin_profile.get("country_risk") or {})

    components = {
        "market_potential": {
            "available": False,
            "subscore": None,
            "note": "Requiert OEC (API payante)",
        },
        "supply_capacity": {
            "available": supply.get("available"),
            "subscore": supply.get("subscore"),
        },
        "logistics_accessibility": {
            "available": log_access.get("available"),
            "subscore": log_access.get("index"),
        },
        "financing_feasibility": {
            "available": fin_feasibility.get("available"),
            "subscore": fin_feasibility.get("index"),
        },
        "country_risk": {"available": risk.get("available"), "subscore": risk.get("subscore")},
    }

    return {
        "report_type": "bilateral_product_opportunity",
        "inputs": {
            "hs_code": hs_code,
            "origin_iso3": origin_iso3,
            "destination_iso3": destination_iso3,
            "goods_value_usd": goods_value_usd,
            "weight_kg": weight_kg,
            "volume_m3": volume_m3,
        },
        "supply": supply,
        "logistics": {
            "profile": log_profile,
            "accessibility_index": log_access,
        },
        "finance": {
            "profile": fin_profile,
            "financing_feasibility_index": fin_feasibility,
            "risk_component": risk,
        },
        "composite_indicators": {
            "landed_cost": _landed_cost(
                goods_value_usd, log_profile.get("best_operational_cost_usd")
            ),
            "financing_feasibility_index": fin_feasibility,
            "logistics_accessibility_index": log_access,
            "end_to_end_score": _end_to_end_score(components, active_weights),
        },
        "weights": active_weights,
        "data_quality": {
            "is_estimation": False,
            "note": (
                "Chiffres issus de sources réelles ou marqués indisponibles ; "
                "aucune valeur inventée. Les flux OEC par produit (potentiel de "
                "marché) nécessitent une API payante et sont exclus ici."
            ),
        },
    }


def _demand_side(importers: list) -> Dict:
    """Shape the OEC importers list into a demand block (or unavailable)."""
    if not importers:
        return {
            "available": False,
            "markets": [],
            "note": (
                "Statistiques d'importation par produit indisponibles : l'API OEC "
                "est requise (bloquée dans cet environnement / plan payant)."
            ),
            "source": "OEC / UN Comtrade (BACI)",
        }
    total = sum((m.get("import_value") or 0) for m in importers)
    markets = [
        {
            "country_iso3": m.get("country_iso3"),
            "country_name": m.get("country_name"),
            "import_value_usd": m.get("import_value"),
            "share_pct": (
                round((m.get("import_value") or 0) / total * 100.0, 1) if total else None
            ),
        }
        for m in importers
    ]
    return {
        "available": True,
        "markets": markets,
        "total_import_value_usd": total or None,
        "source": "OEC / UN Comtrade (BACI)",
    }


def _supply_side(hs_code: str) -> Dict:
    """Continental producers of the product from real production data."""
    try:
        from services.production_capacity_service import get_continental_producers

        prod = get_continental_producers(hs_code)
    except Exception as exc:
        _log.warning("continental producers unavailable: %s", exc)
        return {"available": False, "producers": [], "note": str(exc)}

    if not prod.get("available"):
        return {"available": False, "producers": [], "reason": prod.get("reason")}
    return {
        "available": True,
        "commodity": prod.get("commodity"),
        "producers": prod.get("top_producers", []),
        "continental_total": prod.get("continental_total"),
        "unit": prod.get("unit"),
        "year": prod.get("year"),
        "source": prod.get("source"),
    }


async def get_market_seeking_report(hs_code: str, year: int = 2022, lang: str = "fr") -> Dict:
    """
    Market-seeking report for a producer: for a product (HS6/HS4), which African
    markets *import* it (demand, via OEC) and who *produces* it on the continent
    (supply, via real production data).

    Demand degrades gracefully when OEC is unreachable; supply is local/real.
    """
    hs_code = (hs_code or "").strip()

    product_name = None
    importers = []
    try:
        from services.real_trade_data_service import get_product_name, real_trade_service

        product_name = get_product_name(hs_code, lang)
        importers = await real_trade_service.get_african_importers_for_product(hs_code, year)
    except Exception as exc:
        _log.warning("importers-for-product unavailable: %s", exc)

    return {
        "report_type": "market_seeking",
        "inputs": {"hs_code": hs_code, "year": year},
        "product_name": product_name,
        "demand": _demand_side(importers),
        "supply": _supply_side(hs_code),
        "data_quality": {
            "is_estimation": False,
            "note": (
                "Demande = importations réelles par pays (OEC) ; offre = production "
                "continentale réelle (FAO/USGS/UNIDO). Aucune valeur inventée ; "
                "les champs sans source sont marqués indisponibles."
            ),
        },
    }
