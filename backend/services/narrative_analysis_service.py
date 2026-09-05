"""
Narrative analysis service for premium Opportunités reports.

Generates factual, sourced explanatory text for each report component (supply,
market demand, logistics, financing). No fabrication — every figure tagged with
source, institution, year. Omits claims without data (e.g., growth if not
available).

Output: {narrative: str, source: str, year: int} for each volet.
"""

import logging
from typing import Dict, Optional

_log = logging.getLogger(__name__)


def _src(source) -> str:
    """Human-readable source label from a string or {institution, dataset} dict."""
    if source is None:
        return "source interne"
    if isinstance(source, dict):
        parts = [source.get("institution"), source.get("dataset")]
        return " · ".join(p for p in parts if p) or "source interne"
    return str(source)


def _fmt_usd(value: float) -> str:
    """Format a raw USD amount with the correct magnitude label (M$/Md$)."""
    if value is None:
        return "—"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f} Md$"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M$"
    if value >= 1_000:
        return f"{value / 1_000:.0f} k$"
    return f"{value:.0f} $"


def _product_label(hs_code: str, lang: str = "fr") -> str:
    """Real product name from the platform HS dictionary; graceful fallback."""
    try:
        from services.real_trade_data_service import get_product_name

        name = get_product_name((hs_code or "")[:6], lang)
        if name:
            return name
    except Exception:  # pragma: no cover - defensive
        pass
    return f"produit (SH {(hs_code or '')[:4]})"


def analyze_supply(
    origin_iso3: str,
    hs_code: str,
    supply_profile: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Generates a 1–2 sentence narrative explaining supply capacity.

    Supply profile contains: available (bool), subscore, continental_share_pct,
    rank, commodity, source, detail (full output from production_capacity_service).

    Returns: {narrative: str, source: str, year: int | None, available: bool}
    """
    if not supply_profile.get("available"):
        return {
            "available": False,
            "narrative": None,
            "note": supply_profile.get("reason", "Production data unavailable"),
        }

    commodity = supply_profile.get("commodity", "produit")
    share = supply_profile.get("continental_share_pct")
    rank = supply_profile.get("rank")
    source = supply_profile.get("source", "production_capacity_service")

    # Extract year from detail if present
    detail = supply_profile.get("detail", {})
    year = detail.get("year")

    narratives = []
    if rank == 1 and share:
        narratives.append(
            f"{origin_iso3.upper()} est le 1er producteur africain de {commodity.lower()} "
            f"avec {share:.1f} % de la production continentale"
        )
    elif rank and share:
        narratives.append(
            f"{origin_iso3.upper()} est le #{rank} producteur africain de {commodity.lower()} "
            f"({share:.1f} % de part continentale)"
        )
    elif share:
        narratives.append(
            f"{origin_iso3.upper()} produit {commodity.lower()} "
            f"représentant {share:.1f} % de la production continentale"
        )

    # Add trend if available
    trend = detail.get("trend", {})
    if trend.get("growth_pct_annual") is not None:
        growth = trend["growth_pct_annual"]
        period = trend.get("period", "récent")
        direction = "croissance" if growth > 0 else "déclin"
        narratives.append(
            f"avec une tendance de {direction} de {abs(growth):.1f} % annuel ({period})"
        )

    src = _src(source)
    narrative = " ".join(narratives) + (f" ({src} {year})" if year else f" ({src})")

    return {
        "available": True,
        "narrative": narrative,
        "source": src,
        "year": year,
    }


def analyze_market_demand(
    hs_code: str,
    demand_profile: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Generates a narrative explaining African market demand for the product.

    Demand profile contains: available, markets (list), total_import_value_usd,
    source (OEC / UN Comtrade BACI), year (implicit 2022 for OEC).

    Returns: {narrative: str, source: str, year: int | None, available: bool}
    """
    if not demand_profile.get("available"):
        return {
            "available": False,
            "narrative": None,
            "note": demand_profile.get("note", "Market demand data unavailable"),
        }

    source = demand_profile.get("source", "OEC BACI")
    year = demand_profile.get("year")
    total_value = demand_profile.get("total_import_value_usd")
    markets = demand_profile.get("markets", [])

    narratives = []

    # Real product name from the platform's HS dictionary (covers all HS codes).
    commodity = _product_label(hs_code, lang)

    if total_value and year:
        narratives.append(
            f"Les importations africaines de {commodity} atteignent "
            f"{_fmt_usd(total_value)} ({year}, {source})"
        )
    elif total_value:
        narratives.append(
            f"Les importations africaines de {commodity} atteignent "
            f"{_fmt_usd(total_value)} ({source})"
        )

    if len(markets) > 0:
        # Top importer
        top = markets[0]
        top_value = top.get("import_value_usd")
        top_country = top.get("country_name")
        if top_value:
            narratives.append(
                f"{top_country} en est le plus grand importateur ({_fmt_usd(top_value)})"
            )

    full_narrative = ", ".join(narratives) + "."
    if year:
        full_narrative += f" (Source : {source} {year})"
    else:
        full_narrative += f" (Source : {source})"

    return {
        "available": True,
        "narrative": full_narrative,
        "source": source,
        "year": year,
    }


def analyze_logistics(
    origin_iso3: str,
    destination_iso3: str,
    logistics_profile: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Describes logistics feasibility (routes, modes, costs, special zones).

    Logistics profile contains: cheapest_operational_option, freight (with
    options list), free_zones, accessibility_index, source (multimodal_freight_service).

    Returns: {narrative: str, source: str, available: bool}
    """
    if not logistics_profile.get("freight", {}).get("available"):
        return {
            "available": False,
            "narrative": None,
            "note": logistics_profile.get("freight", {}).get("note", "Logistics data unavailable"),
        }

    source = "multimodal_freight_service"
    cheapest = logistics_profile.get("cheapest_operational_option", {})
    freight = logistics_profile.get("freight", {})
    options_count = sum(1 for o in freight.get("options", []) if o.get("available"))
    free_zones = logistics_profile.get("free_zones", {})

    narratives = []

    # Route summary
    narratives.append(
        f"{origin_iso3.upper()} → {destination_iso3.upper()}: "
        f"{options_count} modes opérationnels"
    )

    # Best mode
    if cheapest and cheapest.get("total_cost_usd"):
        mode = cheapest.get("mode", "transport").capitalize()
        cost = cheapest.get("total_cost_usd")
        # Multimodal comparator exposes transit_days_min/max (not estimated_days).
        d_min = cheapest.get("transit_days_min")
        d_max = cheapest.get("transit_days_max")
        if d_min is not None and d_max is not None:
            span = f"{d_min}" if d_min == d_max else f"{d_min}–{d_max}"
            narratives.append(f"{mode} le moins cher : {cost:,.0f} $ ({span} jours)")
        else:
            narratives.append(f"{mode} le moins cher : {cost:,.0f} $")

    # Special zones
    zones = free_zones.get("zones", [])
    if zones and len(zones) > 0:
        zone_names = [z.get("name") for z in zones[:2]]
        narratives.append(f"Zones franches dispo: {', '.join(zone_names)}")

    full_narrative = ". ".join(narratives) + "."

    return {
        "available": True,
        "narrative": full_narrative,
        "source": source,
        "year": None,
    }


def analyze_financing(
    destination_iso3: str,
    finance_profile: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Explains financing feasibility (trade finance, PAPSS, risk, FX).

    Finance profile contains: trade_finance, payment_coverage, country_risk, fx
    (all from finance_opportunity_adapter).

    Returns: {narrative: str, source: str, available: bool}
    """
    # get_finance_profile does not carry a top-level ``available`` flag; base the
    # narrative on whether any real sub-component is present instead.
    if not finance_profile or not any(
        (finance_profile.get(k) or {}).get("available")
        for k in ("trade_finance", "payment_coverage", "country_risk", "fx")
    ):
        return {
            "available": False,
            "narrative": None,
            "note": "Financing data unavailable",
        }

    source = "banking_system + macro_indicators_service"
    narratives = []

    # Trade finance
    tf = finance_profile.get("trade_finance", {})
    if tf.get("available") and tf.get("instruments"):
        insts = [i.get("code", "instrument") for i in tf.get("instruments", [])[:2]]
        narratives.append(f"Trade finance disponible ({', '.join(insts)})")

    # Payment systems
    pay = finance_profile.get("payment_coverage", {})
    if pay.get("available"):
        papss = pay.get("papss_covered")
        if papss:
            narratives.append("PAPSS connecté")
        else:
            narratives.append("Paiement via systèmes régionaux")

    # Country risk
    risk = finance_profile.get("country_risk", {})
    if risk.get("available"):
        alert = risk.get("alert_level", "orange")
        narratives.append(f"Risque pays classé {alert}")

    # FX — show the rate when available; append spread only if actually present
    # (get_fx does not always populate a spread — never fabricate one).
    fx = finance_profile.get("fx", {})
    if fx.get("available") and fx.get("rate"):
        rate = fx.get("rate")
        spread = fx.get("spread")
        if spread is not None:
            narratives.append(f"Taux de change: 1 USD = {rate:.2f} (spread ~{spread:.1f} %)")
        else:
            narratives.append(f"Taux de change: 1 USD = {rate:.2f}")

    full_narrative = (
        ". ".join(narratives) + "." if narratives else "Données financières partielles."
    )

    return {
        "available": True if narratives else False,
        "narrative": full_narrative if narratives else None,
        "source": source,
        "year": None,
    }


def analyze_national_need(
    country_iso3: str,
    need: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Narrative for a market's national need (from demand_estimation_service).

    Clearly states whether the figure is MEASURED (apparent consumption) or
    ESTIMATED (population proxy), with the driving inputs and sources — never
    blurs the two. Surfaces the observed-imports signal when present.
    """
    if not need or not need.get("available"):
        return {
            "available": False,
            "narrative": None,
            "note": (need or {}).get("note", "Besoin national indisponible"),
        }

    value = need.get("value")
    unit = need.get("unit") or "unités"
    commodity = need.get("commodity", "produit")
    level = need.get("estimation_level")
    is_est = need.get("is_estimation")

    if is_est:
        qualifier = f"estimé (niveau {level}, proxy population)"
    else:
        qualifier = "mesuré (consommation apparente)"

    # Portée sectorielle : sans cette mention, un besoin agrégé de tout un
    # secteur (correspondance production au chapitre SH2) passe pour le besoin
    # du seul produit SH6 — cas signalé (ETH, ~3,7 Md$ affichés pour un produit).
    scope_is_sector = (need.get("reference_scope") or "").startswith("secteur")
    subject = (
        f"pour l'ensemble du secteur « {commodity} » (référence au chapitre SH2, "
        "à lire comme plafond sectoriel, pas comme besoin du seul produit)"
        if scope_is_sector
        else f"en {str(commodity).lower()}"
    )

    parts = [
        f"Besoin national {qualifier} de {country_iso3.upper()} {subject} : "
        f"≈ {value:,.0f} {unit}"
    ]

    if need.get("reference_coverage_caveat"):
        parts.append(
            "référence de production à couverture partielle (peu de pays ingérés) — "
            "estimation indicative uniquement"
        )

    # Observed imports (real, USD) as a complementary demand signal.
    obs = need.get("observed_imports")
    if obs and obs.get("import_value_usd"):
        calibrated = (need.get("calibration") or {}).get("applied")
        prefix = (
            "estimation recalée au plancher des importations observées : "
            if calibrated
            else "le pays importe déjà "
        )
        parts.append(
            f"{prefix}{_fmt_usd(obs['import_value_usd'])} de ce produit "
            f"({obs.get('source', 'OEC')})"
        )

    sources = need.get("sources") or []
    src_txt = "; ".join(_src(s) for s in sources[:2]) if sources else "sources internes"
    narrative = ". ".join(parts) + f". (Méthode : {need.get('method', '—')} — {src_txt})"

    return {
        "available": True,
        "narrative": narrative,
        "is_estimation": is_est,
        "estimation_level": level,
        "source": src_txt,
    }


def _fmt_range(lo: float, hi: float, unit: str) -> str:
    """Formate une fourchette avec un arrondi lisible (2 chiffres significatifs)."""

    def _round(x: float) -> float:
        if x >= 100:
            return round(x, -1)
        if x >= 10:
            return round(x)
        return round(x, 1)

    return f"{_round(lo):g}–{_round(hi):g} {unit}"


def _phase1_volume_target(report: Dict) -> Optional[str]:
    """
    Volume cible phase 1 dérivé de la demande RÉELLE du marché cible et du
    ratio valeur/poids du produit — jamais un tonnage forfaitaire.

    L'ancienne recommandation codait en dur « 200–500 MT/mois » quel que soit
    le produit : banal pour des pommes de terre (~1 USD/kg) mais absurde pour
    des médicaments SH 300490 (~60 USD/kg, soit 12–30 M$/mois) sur un corridor
    bilatéral. Ici : 5–10 % des importations annuelles observées du marché de
    destination (OEC), converties en tonnage via l'indice valeur/poids
    (cours mondial ou estimation par chapitre SH). Retourne None si aucune
    importation observée — on ne fabrique pas un tonnage sans donnée.
    """
    need = report.get("national_need") or {}
    obs = need.get("observed_imports") or {}
    annual_usd = obs.get("import_value_usd")
    hs_code = (report.get("inputs") or {}).get("hs_code") or ""
    if not annual_usd or annual_usd <= 0 or not hs_code:
        return None
    try:
        from services.shipment_estimator import usd_per_kg_for_hs

        # Le flux d'importations observé porte déjà valeur ET quantité pour ce
        # SH précis (même source OEC/BACI) : transmis pour affiner le ratio
        # au-delà de l'estimation par chapitre — voir la cascade de
        # usd_per_kg_for_hs (cours mondial > valeur unitaire observée >
        # chapitre SH).
        ratio = usd_per_kg_for_hs(
            hs_code,
            observed_value_usd=annual_usd,
            observed_quantity_tonnes=obs.get("import_quantity_tonnes"),
            observed_basis="importations annuelles observées du marché cible",
            observed_year=obs.get("year"),
            observed_source=obs.get("source"),
        )
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("usd_per_kg_for_hs unavailable: %s", exc)
        return None
    usd_per_kg = ratio.get("usd_per_kg") or 0
    if usd_per_kg <= 0:
        return None

    # 5–10 % des importations annuelles observées, en rythme mensuel.
    lo_usd, hi_usd = annual_usd * 0.05 / 12, annual_usd * 0.10 / 12
    lo_kg, hi_kg = lo_usd / usd_per_kg, hi_usd / usd_per_kg
    if hi_kg >= 1_000:
        volume_txt = _fmt_range(lo_kg / 1_000, hi_kg / 1_000, "MT/mois")
    else:
        volume_txt = _fmt_range(lo_kg, hi_kg, "kg/mois")

    _ratio_src_labels = {
        "cours_mondial": f"cours mondial {ratio.get('benchmark')}",
        "valeur_unitaire_observee": "valeur unitaire réelle observée (OEC/BACI)",
        "estimation_chapitre": "estimation par chapitre SH",
    }
    ratio_src = _ratio_src_labels.get(
        ratio.get("classification_source"), "estimation par chapitre SH"
    )
    return (
        f"Volumes cibles phase 1 : ≈ {volume_txt} "
        f"(≈ {_fmt_usd(lo_usd)}–{_fmt_usd(hi_usd)}/mois, soit 5–10 % des importations "
        f"annuelles observées du marché cible, {_fmt_usd(annual_usd)} — "
        f"ratio ≈ {usd_per_kg:g} USD/kg, {ratio_src}). Estimation de dimensionnement."
    )


def summarize_opportunity(
    report: Dict,
    lang: str = "fr",
) -> Dict:
    """
    Executive summary: 3–5 key findings + priority tier.

    Reads end_to_end_score, segmentation quadrants, and key metrics to produce
    a high-level narrative and recommendation tier.

    Returns: {
        narrative: str,
        priority_tier: "QUICK_WIN" | "STRATEGIC_BET" | "HIGH_REWARD_BET" | "PASS",
        key_findings: [str],
        recommendation: str
    }
    """
    e2e = report.get("composite_indicators", {}).get("end_to_end_score", {})
    score = e2e.get("score")
    supply = report.get("supply", {})
    demand = report.get("demand", {}) if "demand" in report else {}
    logistics = (
        report.get("logistics", {}).get("accessibility_index", {}) if "logistics" in report else {}
    )
    financing = report.get("composite_indicators", {}).get("financing_feasibility_index", {})

    key_findings = []

    # Supply finding
    if supply.get("available") and supply.get("continental_share_pct"):
        share = supply["continental_share_pct"]
        rank = supply.get("rank", "")
        if rank == 1:
            key_findings.append(
                f"Producteur leader africain du produit ({share:.1f} % de part continentale)"
            )
        else:
            key_findings.append(
                f"Producteur significatif africain ({share:.1f} % de part continentale)"
            )

    # Demand finding
    if demand.get("available") and demand.get("total_import_value_usd"):
        total_usd = demand["total_import_value_usd"]
        trend = report.get("market_trend_pct", 0)
        if trend > 2:
            key_findings.append(
                f"Demande africaine croissante ({_fmt_usd(total_usd)}, +{trend:.1f} %/an)"
            )
        else:
            key_findings.append(f"Demande africaine établie ({_fmt_usd(total_usd)})")

    # National-need finding (destination market): measured or estimated, flagged.
    need = report.get("national_need", {})
    if need.get("available") and need.get("value"):
        flag = "estimé" if need.get("is_estimation") else "mesuré"
        obs = need.get("observed_imports") or {}
        extra = (
            f", importe déjà {_fmt_usd(obs['import_value_usd'])}"
            if obs.get("import_value_usd")
            else ""
        )
        key_findings.append(
            f"Besoin du marché {flag} : ≈ {need['value']:,.0f} {need.get('unit', '')}{extra}"
        )

    # Logistics finding
    if logistics.get("available") and logistics.get("index"):
        idx = logistics["index"]
        if idx >= 0.8:
            key_findings.append("Accessibilité logistique excellente (3+ modes opérationnels)")
        elif idx >= 0.6:
            key_findings.append("Accessibilité logistique bonne (2+ modes opérationnels)")

    # Financing finding
    if financing.get("available") and financing.get("index"):
        idx = financing["index"]
        if idx >= 0.75:
            key_findings.append("Financement accessible et risque maîtrisable")
        elif idx >= 0.6:
            key_findings.append("Financement possible; gérer le risque pays")

    # Priority tier (simple heuristic)
    if score and score >= 0.75:
        priority_tier = "QUICK_WIN"
        volume_hint = _phase1_volume_target(report)
        recommendation = "Déployer en priorité. " + (
            volume_hint
            or "Dimensionner les volumes de phase 1 sur la demande réelle du marché "
            "cible (importations observées indisponibles pour ce produit)."
        )
    elif score and score >= 0.65:
        priority_tier = "STRATEGIC_BET"
        recommendation = "Examiner davantage ; analyse complémentaire recommandée."
    elif score and score >= 0.5:
        priority_tier = "HIGH_REWARD_BET"
        recommendation = "Risque modéré compensé par potentiel élevé. Faisable avec préparation."
    else:
        priority_tier = "PASS"
        recommendation = "Non recommandé à court terme."

    return {
        "priority_tier": priority_tier,
        "key_findings": key_findings[:4],  # Top 4
        "recommendation": recommendation,
        "narrative": f"Opportunité classée {priority_tier}. " + " ".join(key_findings[:2]) + ".",
    }
