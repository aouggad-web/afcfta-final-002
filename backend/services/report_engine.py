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

from services import benchmarking_service, demand_estimation_service
from services import finance_opportunity_adapter as finance
from services import logistics_opportunity_adapter as logistics
from services import narrative_analysis_service, segmentation_service

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


def get_opportunity_report_ultra_fine(
    hs_code: str,
    origin_iso3: str,
    destination_iso3: str,
    goods_value_usd: Optional[float] = None,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
    weights: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Ultra-fine bilateral report: adds narrative analysis, benchmarking,
    segmentation matrices, and detailed factor breakdown.

    Builds on get_opportunity_report and enriches with:
    - narrative_analysis (supply, market, logistics, financing)
    - benchmarking (top producers, competitive position, cost comparison)
    - segmentation (effort/impact, risk/reward matrices, factor breakdown)
    - priority tier (QUICK_WIN, STRATEGIC_BET, etc.)

    No fabrication: all narratives sourced, all scores from real data.
    """
    # Base report
    base = get_opportunity_report(
        hs_code, origin_iso3, destination_iso3, goods_value_usd, weight_kg, volume_m3, weights
    )

    # Add narrative analyses
    supply_narrative = narrative_analysis_service.analyze_supply(
        origin_iso3, hs_code, base.get("supply", {})
    )
    logistics_narrative = narrative_analysis_service.analyze_logistics(
        origin_iso3, destination_iso3, base.get("logistics", {}).get("profile", {})
    )
    financing_narrative = narrative_analysis_service.analyze_financing(
        destination_iso3, base.get("finance", {}).get("profile", {})
    )

    # Add benchmarking
    top_producers = benchmarking_service.get_top_producers(hs_code, n=5)
    cost_benchmark = benchmarking_service.benchmark_cost(
        origin_iso3,
        hs_code,
        destination_iso3,
        base.get("composite_indicators", {}).get("landed_cost", {}).get("value_usd"),
    )
    infrastructure_bench = benchmarking_service.benchmark_infrastructure(destination_iso3)
    tariff_benefit = benchmarking_service.tariff_benefit_analysis(
        origin_iso3, destination_iso3, hs_code
    )

    # Inject the REAL tariff advantage into the report so the segmentation layer
    # scores it from actual national/ZLECAf rates instead of a hardcoded value.
    base["tariff_benefit"] = tariff_benefit

    # National need of the DESTINATION market (S3): how much this market needs the
    # product. Measured (apparent consumption) when possible, otherwise a
    # transparent population-proxy estimate — always flagged, never fabricated.
    national_need = demand_estimation_service.estimate_national_need(hs_code, destination_iso3)
    base["national_need"] = national_need
    need_narrative = narrative_analysis_service.analyze_national_need(
        destination_iso3, national_need
    )

    # Executive summary is recomputed so it can surface the national-need finding.
    executive_summary = narrative_analysis_service.summarize_opportunity(base)

    # Add segmentation
    effort_impact = segmentation_service.effort_impact_matrix(base)
    risk_reward = segmentation_service.risk_reward_matrix(base)
    factors = segmentation_service.factor_breakdown(base)
    priority = segmentation_service.priority_score(base)

    # Assemble ultra-fine report
    return {
        **base,  # Include all base report fields
        "report_tier": "ultra_fine",
        "executive_summary": {
            "priority_tier": executive_summary.get("priority_tier"),
            "key_findings": executive_summary.get("key_findings"),
            "recommendation": executive_summary.get("recommendation"),
            "narrative": executive_summary.get("narrative"),
        },
        "narrative_analysis": {
            "supply": supply_narrative,
            "logistics": logistics_narrative,
            "financing": financing_narrative,
            "national_need": need_narrative,
        },
        "national_need": national_need,
        "benchmarking": {
            "top_producers": top_producers,
            "cost_comparison": cost_benchmark,
            "infrastructure": infrastructure_bench,
            "tariff_benefit": tariff_benefit,
        },
        "segmentation": {
            "effort_impact_matrix": effort_impact,
            "risk_reward_matrix": risk_reward,
            "factor_breakdown": factors,
            "priority_score": priority,
        },
    }


def _gross_value_added(
    input_value_usd: Optional[float], finished_value_usd: Optional[float]
) -> Dict:
    """
    Gross value-added of the transformation = finished value − input value.

    Explicitly PARTIAL: excludes processing costs (labour, energy, capital,
    wastage) which the platform does not hold. Never presented as net profit.
    """
    if input_value_usd is None or finished_value_usd is None:
        return {
            "available": False,
            "note": "Valeurs de l'intrant et du produit fini requises pour la valeur ajoutée.",
        }
    gross = finished_value_usd - input_value_usd
    margin_pct = round(gross / finished_value_usd * 100, 1) if finished_value_usd else None
    return {
        "available": True,
        "is_estimation": False,
        "gross_value_added_usd": round(gross, 2),
        "gross_margin_pct": margin_pct,
        "inputs": {
            "input_value_usd": input_value_usd,
            "finished_value_usd": finished_value_usd,
        },
        "note": (
            "Valeur ajoutée BRUTE (produit fini − intrant). Exclut les coûts de "
            "transformation (main-d'œuvre, énergie, capital, pertes) non disponibles "
            "sur la plateforme ; ne pas interpréter comme un profit net."
        ),
    }


def get_transformation_scenario(
    input_hs_code: str,
    input_origin_iso3: str,
    producer_iso3: str,
    finished_hs_code: str,
    destination_iso3: str,
    input_value_usd: Optional[float] = None,
    finished_value_usd: Optional[float] = None,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
) -> Dict:
    """
    Scenario **S1 — import inputs → local production → export**.

    Chains the platform's real-data bricks along a transformation value chain:

      Leg 1 (import inputs): logistics + real input tariff at the producing
             country + landed cost of the imported inputs.
      Leg 2 (production): the producer's real production capacity for the
             finished good (FAO/USGS/UNIDO).
      Leg 3 (export): the full bilateral opportunity report for the finished
             good from the producer to the destination market.

    Plus a transparent, PARTIAL gross value-added (finished − input), clearly
    flagged as excluding transformation costs. No fabrication throughout.
    """
    input_origin_iso3 = (input_origin_iso3 or "").upper()
    producer_iso3 = (producer_iso3 or "").upper()
    destination_iso3 = (destination_iso3 or "").upper()

    # ── Leg 1: import the inputs into the producing country ──────────────────
    input_logistics = logistics.get_logistics_profile(
        input_origin_iso3, producer_iso3, weight_kg, volume_m3
    )
    input_tariff = benchmarking_service.tariff_benefit_analysis(
        input_origin_iso3, producer_iso3, input_hs_code
    )
    input_freight = input_logistics.get("best_operational_cost_usd")
    input_landed = _landed_cost(input_value_usd, input_freight)

    # ── Leg 2: local production capacity for the finished good ───────────────
    production = _supply_component(producer_iso3, finished_hs_code)

    # ── Leg 3: export the finished good to the destination market ────────────
    export_report = get_opportunity_report(
        finished_hs_code,
        producer_iso3,
        destination_iso3,
        finished_value_usd,
        weight_kg,
        volume_m3,
    )

    value_added = _gross_value_added(input_value_usd, finished_value_usd)

    # Feasibility flags (transparent, boolean facts, not a black-box score).
    can_produce = bool(production.get("available"))
    export_score = (
        export_report.get("composite_indicators", {}).get("end_to_end_score", {}).get("score")
    )

    return {
        "report_type": "value_chain_transformation",
        "scenario": "S1_import_inputs_produce_export",
        "inputs": {
            "input_hs_code": input_hs_code,
            "input_origin_iso3": input_origin_iso3,
            "producer_iso3": producer_iso3,
            "finished_hs_code": finished_hs_code,
            "destination_iso3": destination_iso3,
            "input_value_usd": input_value_usd,
            "finished_value_usd": finished_value_usd,
        },
        "leg1_input_import": {
            "logistics": input_logistics,
            "tariff": input_tariff,
            "landed_cost": input_landed,
        },
        "leg2_production": production,
        "leg3_export": export_report,
        "value_added": value_added,
        "feasibility": {
            "can_produce_locally": can_produce,
            "export_end_to_end_score": export_score,
            "note": (
                "Faisabilité indicative : la production locale du produit fini est "
                + (
                    "confirmée par les données de production."
                    if can_produce
                    else "NON confirmée (pas de capacité de production détectée)."
                )
            ),
        },
        "data_quality": {
            "is_estimation": False,
            "note": (
                "Chaîne de valeur composée de briques réelles (logistique, tarif "
                "national/ZLECAf, production, export). Valeur ajoutée BRUTE seulement "
                "(coûts de transformation non disponibles). Aucune valeur inventée."
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
