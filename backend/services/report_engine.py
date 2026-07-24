"""
Report engine — orchestrator for the premium Opportunités module.

Composes the platform's real-data angles (production/supply, logistics, finance
& macro) into a single bilateral product-opportunity report and computes the
transparent composite indicators described in
``docs/MODULE_OPPORTUNITES_PLAN_PREMIUM.md``:

  - **Landed cost** = goods value (FOB) + cheapest operational freight (frais
    portuaires inclus dans le fret et remontés séparément) + assurance cargo
    estimée (convention CIF+10 %) + frais de l'instrument bancaire recommandé.
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
from services import narrative_analysis_service, segmentation_service, shipment_estimator

_log = logging.getLogger(__name__)

# Default weights for the end-to-end score. Callers may override any subset.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "market_potential": 0.25,  # OEC per-product demand — unavailable w/o paid API
    "supply_capacity": 0.25,  # production_capacity_service (FAO/USGS/UNIDO)
    "logistics_accessibility": 0.20,  # multimodal freight comparator
    "financing_feasibility": 0.20,  # banking + macro
    "country_risk": 0.10,  # banking risk assessment
}

# Assurance cargo : convention de marché transparente « CIF + 10 % »
# (Institute Cargo Clauses (A) : valeur assurée = 110 % de la valeur CIF),
# prime tous-risques typique 0,3–0,8 % sur les corridors africains — 0,5 %
# retenu comme point médian. Toujours flaggé is_estimation, jamais caché.
CARGO_INSURANCE_RATE_PCT = 0.5
CARGO_INSURANCE_INSURED_VALUE_FACTOR = 1.1
CARGO_INSURANCE_SOURCE = (
    "Prime tous-risques cargo typique 0,3–0,8 % (Institute Cargo Clauses (A) ; "
    "UNCTAD Review of Maritime Transport) — 0,5 % retenu, "
    "valeur assurée = 110 % × (FOB + fret)."
)


def _insurance_component(goods_value_usd: float, total_freight_usd: float) -> Dict:
    """Assurance cargo ESTIMÉE pour le coût rendu — convention CIF+10 %.

    Prime = taux typique × valeur assurée, où valeur assurée = 110 % ×
    (FOB + fret) selon la convention Institute Cargo Clauses. Explicitement
    marquée ``is_estimation`` : c'est un ordre de grandeur de marché, pas un
    devis d'assureur.
    """
    insured_value = round(
        (goods_value_usd + total_freight_usd) * CARGO_INSURANCE_INSURED_VALUE_FACTOR, 2
    )
    premium = round(insured_value * CARGO_INSURANCE_RATE_PCT / 100.0, 2)
    return {
        "available": True,
        "is_estimation": True,
        "premium_usd": premium,
        "rate_pct": CARGO_INSURANCE_RATE_PCT,
        "insured_value_usd": insured_value,
        "insured_value_basis": "110 % × (FOB + fret) — convention Institute Cargo Clauses",
        "source": CARGO_INSURANCE_SOURCE,
    }


def _recommended_instrument_fee(trade_finance: Optional[Dict], goods_value_usd: float) -> Dict:
    """Frais bancaires de l'instrument trade finance RECOMMANDÉ.

    Applique le coût typique (% du montant) du premier instrument recommandé
    par ``banking_system.recommend_instruments`` (le mieux adapté à la
    transaction) à la valeur FOB. Indisponible — et exclu du total, jamais
    inventé — quand aucune recommandation n'est résolue.
    """
    instruments = (trade_finance or {}).get("instruments") or []
    top = next((i for i in instruments if (i or {}).get("typical_cost_pct") is not None), None)
    if not (trade_finance or {}).get("available") or top is None:
        return {
            "available": False,
            "fee_usd": None,
            "note": "Aucun instrument bancaire recommandé résolu — frais exclus du coût rendu.",
        }
    fee = round(goods_value_usd * float(top["typical_cost_pct"]) / 100.0, 2)
    return {
        "available": True,
        "fee_usd": fee,
        "instrument_code": top.get("code"),
        "instrument_name": top.get("name_fr") or top.get("name"),
        "typical_cost_pct": top.get("typical_cost_pct"),
        "source": (
            "banking_system — catalogue trade finance (coût typique en % du montant, "
            "instrument recommandé le mieux adapté)"
        ),
    }


def _port_fees_component(cheapest_option: Optional[Dict], n_containers: int = 1) -> Dict:
    """Frais portuaires de l'option de fret retenue — déjà INCLUS dans le fret.

    Le module maritime intègre les THC origine/destination dans le coût total
    (et le vraquier ses frais de chargement/déchargement) : on les remonte ici
    séparément pour la transparence du coût rendu, sans JAMAIS les
    ré-additionner au total. Modes sans décomposition portuaire (aérien,
    terrestre, multimodal) → non séparables, flaggés indisponibles.
    """
    pf = (cheapest_option or {}).get("port_fees") or {}
    if not pf or pf.get("total_usd") is None:
        return {
            "available": False,
            "total_usd": None,
            "note": (
                "Frais portuaires non séparables pour ce mode (inclus dans le "
                "tarif de fret le cas échéant)."
            ),
        }
    if pf.get("basis") == "per_container":
        n = max(1, int(n_containers or 1))
        loading = round((pf.get("origin_thc_usd") or 0) * n, 2)
        discharge = round((pf.get("destination_thc_usd") or 0) * n, 2)
        total = round((pf.get("total_usd") or 0) * n, 2)
        detail = {
            "origin_thc_usd_per_container": pf.get("origin_thc_usd"),
            "destination_thc_usd_per_container": pf.get("destination_thc_usd"),
            "containers": n,
        }
    else:
        tonnes = (pf.get("total_usd") or 0) / (
            (pf.get("load_usd_per_t") or 0) + (pf.get("discharge_usd_per_t") or 0) or 1
        )
        loading = round((pf.get("load_usd_per_t") or 0) * tonnes, 2)
        discharge = round((pf.get("discharge_usd_per_t") or 0) * tonnes, 2)
        total = round(pf.get("total_usd") or 0, 2)
        detail = {
            "load_usd_per_t": pf.get("load_usd_per_t"),
            "discharge_usd_per_t": pf.get("discharge_usd_per_t"),
        }
    return {
        "available": True,
        "loading_usd": loading,
        "discharge_usd": discharge,
        "total_usd": total,
        "included_in_freight": True,
        "basis": pf.get("basis"),
        "detail": detail,
        "source": pf.get("source"),
        "note": (
            "Chargement (port d'origine) + déchargement (port de destination) — "
            "compris dans le tarif de fret tout-inclus, décomposés ici comme "
            "lignes du coût rendu (non ré-additionnés au total)."
        ),
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


def _market_component(market_imports: Optional[Dict]) -> Dict:
    """
    Market-potential sub-score from the destination's REAL imports of the product
    (OEC). Transparent normalisation: 100 M$ of annual imports -> 1.0.

    Returns ``available: False`` (excluded from the score, never fabricated) when
    OEC data was not provided/reachable.
    """
    if not market_imports or not market_imports.get("available"):
        return {
            "available": False,
            "subscore": None,
            "note": "Demande OEC par produit indisponible (OEC requis).",
        }
    value = market_imports.get("import_value_usd") or 0.0
    subscore = round(min(value / 100_000_000, 1.0), 3)  # 100 M$ -> 1.0
    return {
        "available": True,
        "subscore": subscore,
        "import_value_usd": value,
        "import_quantity_tonnes": market_imports.get("import_quantity_tonnes"),
        "source": market_imports.get("source", "OEC / UN Comtrade (BACI)"),
        "note": "Normalisation transparente : 100 M$ d'imports annuels = 1.0.",
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


def _resolve_logistics_and_landed(
    origin_iso3: str,
    destination_iso3: str,
    goods_value_usd: Optional[float],
    hs_code: Optional[str],
    weight_kg: float,
    volume_m3: float,
    shipment: Optional[Dict],
    trade_finance: Optional[Dict] = None,
) -> tuple:
    """Compute the logistics profile + landed cost with UNIFORM cargo handling.

    Single source of truth for the container-vs-vraquier décision, shared by
    the bilateral report and the value-chain legs so the démarche is identical
    everywhere:

    - **Vrac sec au-dessus du seuil** : la logistique est calculée sur le
      TONNAGE COMPLET (l'option d'affrètement vraquier ``sea_bulk`` remonte
      alors), et le coût rendu utilise le total d'affrètement directement.
    - **Sinon** : logistique d'UN conteneur (× nombre de conteneurs dans le
      coût rendu), comportement historique inchangé.
    """
    bulk = shipment_estimator.classify_bulk_commodity(hs_code) if hs_code else None
    total_weight_kg = None
    if shipment and shipment.get("available"):
        total_weight_kg = float(shipment.get("weight_kg") or 0)

    threshold_kg = (bulk or {}).get("container_threshold_tonnes", 0) * 1000.0 if bulk else 0
    use_bulk = bool(
        bulk
        and not bulk.get("is_liquid")
        and total_weight_kg is not None
        and total_weight_kg >= threshold_kg > 0
    )

    if use_bulk:
        # Tonnage complet : c'est ici que l'affrètement vraquier devient éligible.
        log_profile = logistics.get_logistics_profile(
            origin_iso3,
            destination_iso3,
            total_weight_kg,
            volume_m3,
            hs_code=hs_code,
        )
    elif shipment and shipment.get("available"):
        one_container_kg = min(
            float(shipment["weight_kg"]), float(shipment["container_capacity_kg"])
        )
        log_profile = logistics.get_logistics_profile(
            origin_iso3,
            destination_iso3,
            one_container_kg,
            volume_m3,
            container_type=shipment["container_type"],
            hs_code=hs_code,
        )
    else:
        log_profile = logistics.get_logistics_profile(
            origin_iso3, destination_iso3, weight_kg, volume_m3, hs_code=hs_code
        )

    cheapest = log_profile.get("cheapest_operational_option") or {}
    landed = _landed_cost(
        goods_value_usd,
        log_profile.get("best_operational_cost_usd"),
        shipment,
        cheapest,
        trade_finance,
    )
    return log_profile, landed


def _landed_cost(
    goods_value_usd: Optional[float],
    freight_usd: Optional[float],
    shipment: Optional[Dict] = None,
    cheapest_option: Optional[Dict] = None,
    trade_finance: Optional[Dict] = None,
) -> Dict:
    """Coût rendu = FOB + fret + assurance estimée + frais bancaires ; null si une jambe manque.

    Deux régimes de fret, choisis selon le mode opérationnel le moins cher :

    - **Affrètement vraquier** (``mode == "sea_bulk"``) : ``freight_usd`` est déjà
      le coût TOTAL de l'affrètement pour le tonnage complet (USD/t × tonnage).
      On ne multiplie jamais par un nombre de conteneurs et on n'affiche jamais
      « conteneurs nécessaires » — le lot voyage en vrac, pas en boîtes.
    - **Conteneur** (défaut) : ``freight_usd`` est le coût d'UN conteneur ; le
      total multiplie par le nombre de conteneurs nécessaires (estimé à partir
      du poids déduit de la valeur FOB — cf. shipment_estimator).

    S'ajoutent au total, quel que soit le régime :

    - **Assurance cargo estimée** (convention CIF+10 %, cf.
      ``_insurance_component``) — toujours flaggée estimation.
    - **Frais de l'instrument bancaire recommandé** (coût typique % × FOB,
      cf. ``_recommended_instrument_fee``) — exclus si aucune recommandation.
    - **Frais portuaires** : déjà inclus dans le fret (THC conteneur /
      manutention vrac) ; remontés séparément pour transparence, jamais
      ré-additionnés.
    """
    if goods_value_usd is None or freight_usd is None:
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

    is_charter = (cheapest_option or {}).get("mode") == "sea_bulk"
    if is_charter:
        # Vrac affrété : freight_usd = coût total pour tout le tonnage.
        total_freight = round(freight_usd, 2)
        n_containers = 1
        breakdown = {
            "goods_value_fob_usd": goods_value_usd,
            "freight_mode": "sea_bulk",
            "vessel_class": (cheapest_option or {}).get("vessel_class"),
            "best_operational_freight_usd": total_freight,
            "estimated_weight_kg": (shipment or {}).get("weight_kg"),
            "weight_source": (shipment or {}).get("weight_source"),
        }
        note = (
            "FX inclus séparément (voir volet finance). Fret = affrètement "
            "vraquier (coût total pour le tonnage complet, USD/t × tonnage) — "
            "pas de découpage en conteneurs."
        )
        if (cheapest_option or {}).get("notes"):
            note += " " + cheapest_option["notes"]
        if shipment and shipment.get("value_to_weight"):
            vtw = shipment["value_to_weight"]
            if vtw.get("classification_source") == "cours_mondial":
                note += (
                    f" Poids estimé via le cours mondial de {vtw.get('commodity', 'la matière première')} "
                    f"({vtw['usd_per_kg']} USD/kg, {vtw.get('benchmark', '?')}, {vtw.get('as_of', '?')})."
                )
            else:
                note += (
                    f" Poids estimé via un ratio {vtw['usd_per_kg']} USD/kg "
                    f"(chapitre SH {vtw.get('hs_chapter', '?')}, estimation de dimensionnement)."
                )
    else:
        per_container_freight_usd = freight_usd
        n_containers = 1
        if shipment and shipment.get("available") and shipment.get("containers_needed"):
            n_containers = max(1, int(shipment["containers_needed"]))
        total_freight = round(per_container_freight_usd * n_containers, 2)
        breakdown = {
            "goods_value_fob_usd": goods_value_usd,
            "freight_per_container_usd": per_container_freight_usd,
            "containers_needed": n_containers,
            "container_type": (shipment or {}).get("container_type"),
            "best_operational_freight_usd": total_freight,
            "estimated_weight_kg": (shipment or {}).get("weight_kg"),
            "weight_source": (shipment or {}).get("weight_source"),
        }
        note = (
            "FX inclus séparément (voir volet finance). Fret = option opérationnelle "
            "la moins chère × nombre de conteneurs."
        )
        if shipment and shipment.get("value_to_weight"):
            vtw = shipment["value_to_weight"]
            if vtw.get("classification_source") == "cours_mondial":
                note += (
                    f" Poids estimé via le cours mondial de {vtw.get('commodity', 'la matière première')} "
                    f"({vtw['usd_per_kg']} USD/kg, {vtw.get('benchmark', '?')}, {vtw.get('as_of', '?')}) "
                    "— repère non contractuel, cf. garde-fou de négociation."
                )
            else:
                note += (
                    f" Poids estimé via un ratio {vtw['usd_per_kg']} "
                    f"USD/kg (chapitre SH {vtw.get('hs_chapter', '?')}, "
                    f"estimation de dimensionnement — non contractuel)."
                )

    # ── Composantes communes aux deux régimes ────────────────────────────────
    insurance = _insurance_component(goods_value_usd, total_freight)
    instrument = _recommended_instrument_fee(trade_finance, goods_value_usd)
    port_fees = _port_fees_component(cheapest_option, n_containers)

    breakdown["insurance_usd"] = insurance["premium_usd"]
    breakdown["trade_finance_fee_usd"] = instrument.get("fee_usd")
    breakdown["trade_finance_instrument"] = instrument.get("instrument_name")
    # Frais portuaires décomposés en lignes chargement / déchargement. Ils sont
    # compris dans le tarif de fret tout-inclus : le fret est donc aussi exposé
    # HORS frais portuaires pour que les lignes s'additionnent sans doublon.
    breakdown["port_fees_loading_usd"] = port_fees.get("loading_usd")
    breakdown["port_fees_discharge_usd"] = port_fees.get("discharge_usd")
    breakdown["port_fees_included_usd"] = port_fees.get("total_usd")
    if port_fees.get("available"):
        breakdown["freight_excl_port_fees_usd"] = round(
            total_freight - (port_fees.get("total_usd") or 0), 2
        )

    note += (
        f" Assurance cargo estimée ({CARGO_INSURANCE_RATE_PCT} % de la valeur "
        "assurée CIF+10 %) incluse."
    )
    if instrument.get("available"):
        note += (
            f" Frais bancaires de l'instrument recommandé inclus "
            f"({instrument['instrument_name']}, {instrument['typical_cost_pct']} % du FOB)."
        )
    if port_fees.get("available"):
        note += (
            f" Frais portuaires inclus : chargement {port_fees['loading_usd']} USD "
            f"+ déchargement {port_fees['discharge_usd']} USD (compris dans le "
            "tarif de fret tout-inclus, décomposés sans double comptage)."
        )

    total = round(
        goods_value_usd
        + total_freight
        + insurance["premium_usd"]
        + (instrument.get("fee_usd") or 0.0),
        2,
    )
    return {
        "available": True,
        "value_usd": total,
        "breakdown": breakdown,
        "components": {
            "insurance": insurance,
            "trade_finance": instrument,
            "port_fees": port_fees,
        },
        "shipment_sizing": shipment,
        "note": note,
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
    market_imports: Optional[Dict] = None,
) -> Dict:
    """
    Bilateral product-opportunity report: origin exports ``hs_code`` to
    destination. Combines supply, logistics, finance/macro and a transparent
    end-to-end score.

    ``market_imports`` (optional): the destination's real OEC imports of the
    product (from ``get_country_product_imports``). When provided, the
    market-potential component is activated in the score; otherwise it stays
    excluded (never fabricated).
    """
    origin_iso3 = (origin_iso3 or "").upper()
    destination_iso3 = (destination_iso3 or "").upper()
    amount = goods_value_usd or 0.0
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    # Profil finance d'abord : ses instruments trade finance recommandés
    # alimentent les frais bancaires du coût rendu.
    fin_profile = finance.get_finance_profile(origin_iso3, destination_iso3, amount, "export")

    # Dimensionnement de l'expédition : à partir de la valeur FOB et du produit,
    # estimer le poids → type et nombre de conteneurs. Le choix conteneur (coût
    # d'un conteneur × nombre) vs vraquier (affrètement au tonnage complet) est
    # centralisé dans _resolve_logistics_and_landed pour une démarche uniforme.
    shipment = shipment_estimator.estimate_shipment(goods_value_usd, hs_code)
    log_profile, landed_cost = _resolve_logistics_and_landed(
        origin_iso3,
        destination_iso3,
        goods_value_usd,
        hs_code,
        weight_kg,
        volume_m3,
        shipment,
        trade_finance=fin_profile.get("trade_finance"),
    )

    supply = _supply_component(origin_iso3, hs_code)
    log_access = logistics.summarize_logistics_accessibility(log_profile)
    fin_feasibility = finance.summarize_financing_feasibility(fin_profile)
    risk = _risk_component(fin_profile.get("country_risk") or {})
    market = _market_component(market_imports)

    components = {
        "market_potential": {
            "available": market.get("available"),
            "subscore": market.get("subscore"),
            "note": market.get("note"),
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
        "market_potential": market,
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
            "landed_cost": landed_cost,
            "financing_feasibility_index": fin_feasibility,
            "logistics_accessibility_index": log_access,
            "end_to_end_score": _end_to_end_score(components, active_weights),
        },
        "weights": active_weights,
        "data_quality": {
            "is_estimation": False,
            "note": (
                "Chiffres issus de sources réelles ou marqués indisponibles ; "
                "aucune valeur inventée."
                + (
                    " Potentiel de marché activé via les imports OEC réels du marché."
                    if market.get("available")
                    else " Le potentiel de marché (flux OEC par produit) est indisponible"
                    " ici et exclu du score (jamais estimé)."
                )
            ),
        },
    }


def _intra_african_profile(iso3: str) -> Dict:
    """Profil de commerce intra-africain d'un pays — données réelles sourcées
    Afreximbank (African Trade Report 2026). Retourne available:False si le pays
    n'est pas couvert, jamais de valeur inventée."""
    from services import afreximbank_data

    iso3 = (iso3 or "").upper()
    intra = afreximbank_data.get_country_intra_african(iso3)
    exports = afreximbank_data.get_country_merchandise_exports(iso3)
    if not intra and not exports:
        return {"available": False, "iso3": iso3, "note": "Pays non couvert par l'ATR 2026."}

    def _trend(series):
        """Croissance 2021→2025 (%) à partir de la série 5 ans, si exploitable."""
        if not series or len(series) < 2 or not series[0]:
            return None
        return round((series[-1] / series[0] - 1.0) * 100.0, 1)

    block = {
        "available": True,
        "iso3": iso3,
        "name": (intra or {}).get("name"),
        "source": afreximbank_data.SOURCE,
        "reference_year": 2025,
    }
    if intra:
        block["intra_african_trade"] = {
            "value_2025_busd": intra.get("intra_african_2025_busd"),
            "share_2025_pct": intra.get("share_2025_pct"),
            "series_2021_2025": intra.get("series_2021_2025"),
            "growth_2021_2025_pct": _trend(intra.get("series_2021_2025")),
            "continental_total_2025_busd": afreximbank_data.get_intra_african_total_busd(),
        }
    if exports:
        block["merchandise_exports"] = {
            "value_2025_busd": exports.get("value_2025_busd"),
            "share_2025_pct": exports.get("share_2025_pct"),
            "series_2021_2025": exports.get("series_2021_2025"),
            "growth_2021_2025_pct": _trend(exports.get("series_2021_2025")),
            "continental_total_2025_busd": afreximbank_data.get_merchandise_exports_total_busd(),
        }
    return block


def get_intra_african_context(origin_iso3: str, destination_iso3: str) -> Dict:
    """Contexte de commerce intra-africain (Afreximbank ATR 2026) pour la paire
    origine/destination : dynamisme export de l'origine + ouverture intra-africaine
    du marché de destination. Contexte sourcé, hors score (jamais fabriqué)."""
    from services import afreximbank_data

    ci = afreximbank_data.get_continental_indicators()
    return {
        "available": True,
        "source": afreximbank_data.SOURCE,
        "origin": _intra_african_profile(origin_iso3),
        "destination": _intra_african_profile(destination_iso3),
        "continental_2025": {
            "intra_african_trade_busd": afreximbank_data.get_intra_african_total_busd(),
            "intra_african_trade_growth_pct": ci.get("intra_african_trade_growth_pct"),
            "real_gdp_growth_pct": ci.get("real_gdp_growth_pct"),
            "note": "Contexte macro-commercial réel ; complète le score sans l'alimenter.",
        },
    }


async def get_opportunity_report_ultra_fine(
    hs_code: str,
    origin_iso3: str,
    destination_iso3: str,
    goods_value_usd: Optional[float] = None,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
    weights: Optional[Dict[str, float]] = None,
    market_imports: Optional[Dict] = None,
) -> Dict:
    """
    Ultra-fine bilateral report: adds narrative analysis, benchmarking,
    segmentation matrices, and detailed factor breakdown.

    Builds on get_opportunity_report and enriches with:
    - narrative_analysis (supply, market, logistics, financing)
    - benchmarking (top producers, competitive position, cost comparison)
    - segmentation (effort/impact, risk/reward matrices, factor breakdown)
    - priority tier (QUICK_WIN, STRATEGIC_BET, etc.)

    ``market_imports`` (optional) activates the market-potential component in the
    score (real OEC demand). No fabrication: all narratives sourced, scores real.
    """
    # Base report
    base = get_opportunity_report(
        hs_code,
        origin_iso3,
        destination_iso3,
        goods_value_usd,
        weight_kg,
        volume_m3,
        weights,
        market_imports=market_imports,
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

    # Repli automatique : aucune production continentale de référence pour ce SH
    # (ex. instruments médicaux SH90) -> imports réels du pays lui-même (canal
    # OEC partagé, moyennés sur plusieurs années pour les biens durables/longue
    # conservation). Un seul appel réseau, uniquement quand le repli local échoue.
    if (
        not national_need.get("available")
        and national_need.get("reason") == "no_continental_production_reference"
    ):
        try:
            from services.real_trade_data_service import real_trade_service

            history = await real_trade_service.get_country_product_import_history(
                destination_iso3, hs_code
            )
            if history and history.get("available") and history.get("imports"):
                national_need = demand_estimation_service.estimate_national_need(
                    hs_code, destination_iso3, own_imports_history=history["imports"]
                )
        except Exception as e:  # OEC indisponible -> le message "impossible" est conservé
            _log.warning(
                "own-imports fallback (ultra-fine report) failed for %s/%s: %s",
                destination_iso3,
                hs_code,
                e,
            )

    base["national_need"] = national_need

    # Faisabilité de substitution : part de la demande du marché de destination
    # réalistement adressable par une offre africaine, compte tenu des barrières
    # non tarifaires (effet marque pour les véhicules, branding/technologie pour
    # la téléphonie et l'informatique, certification pour la pharma...). Un
    # besoin national de X $ ne signifie pas X $ captables — le rapport dit
    # explicitement quelle fraction l'est, et pourquoi.
    from services.substitution_feasibility_service import substitutability_for_hs

    substitution_feasibility = substitutability_for_hs(hs_code)
    base["substitution_feasibility"] = substitution_feasibility

    # Intra-African trade context (Afreximbank ATR 2026): export dynamism of the
    # origin + intra-African openness of the destination market. Real, sourced
    # context that frames the corridor — kept OUT of the score (no fabrication).
    intra_african_context = get_intra_african_context(origin_iso3, destination_iso3)
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
        "substitution_feasibility": substitution_feasibility,
        "intra_african_context": intra_african_context,
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
    # Même démarche que le rapport bilatéral : conteneur vs vraquier tranché de
    # façon uniforme par _resolve_logistics_and_landed (au tonnage complet pour
    # un vrac au-dessus du seuil).
    input_shipment = shipment_estimator.estimate_shipment(input_value_usd, input_hs_code)
    # Instruments bancaires recommandés pour l'IMPORT des intrants par le
    # producteur : leurs frais typiques entrent dans le coût rendu de la jambe 1.
    input_trade_finance = finance.get_trade_finance(producer_iso3, "import", input_value_usd or 0.0)
    input_logistics, input_landed = _resolve_logistics_and_landed(
        input_origin_iso3,
        producer_iso3,
        input_value_usd,
        input_hs_code,
        weight_kg,
        volume_m3,
        input_shipment,
        trade_finance=input_trade_finance,
    )
    input_tariff = benchmarking_service.tariff_benefit_analysis(
        input_origin_iso3, producer_iso3, input_hs_code
    )

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


def _african_candidate_markets(exclude_iso3: str) -> list:
    """African markets (ISO3) to consider as export destinations, minus origin."""
    try:
        from constants import AFRICAN_COUNTRIES

        return [
            c["iso3"]
            for c in AFRICAN_COUNTRIES
            if c.get("iso3") and c.get("population") and c["iso3"] != exclude_iso3
        ]
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("candidate markets unavailable: %s", exc)
        return []


def get_direct_export_scenario(
    hs_code: str,
    producer_iso3: str,
    candidate_destinations: Optional[list] = None,
    top_k: int = 5,
    goods_value_usd: Optional[float] = None,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
) -> Dict:
    """
    Scenario **S2 — national production → direct export**.

    For a producer that already makes ``hs_code``, rank the African markets worth
    exporting to. Two stages, both real-data:

      1. Cheap pass over all candidate markets: estimate each market's national
         need (population proxy / apparent consumption) to size the demand.
      2. Deep-dive the ``top_k`` largest-need markets with the full bilateral
         opportunity report (logistics, finance, tariff, end-to-end score) and
         rank them by that score.

    Returns the producer's own supply profile plus a ranked list of destination
    opportunities. No fabrication: unavailable angles are flagged, not invented.
    """
    producer_iso3 = (producer_iso3 or "").upper()

    # Producer's own production capacity for the product (the whole scenario is
    # only meaningful if the producer actually makes it).
    supply = _supply_component(producer_iso3, hs_code)

    # Candidate destination markets. An explicit list (even empty) is respected;
    # only ``None`` falls back to the full African market set.
    if candidate_destinations is not None:
        candidates = [c.upper() for c in candidate_destinations if c and c.upper() != producer_iso3]
    else:
        candidates = _african_candidate_markets(producer_iso3)

    # Stage 1 — size demand per candidate (cheap, local estimate).
    sized = []
    for dest in candidates:
        need = demand_estimation_service.estimate_national_need(hs_code, dest)
        sized.append({"destination_iso3": dest, "market_need": need})
    sized.sort(key=lambda s: (s["market_need"].get("value") or 0), reverse=True)

    # Stage 2 — deep-dive the top_k largest-need markets with a full report.
    opportunities = []
    for entry in sized[: max(top_k, 0)]:
        dest = entry["destination_iso3"]
        report = get_opportunity_report(
            hs_code, producer_iso3, dest, goods_value_usd, weight_kg, volume_m3
        )
        ci = report.get("composite_indicators", {})
        e2e = ci.get("end_to_end_score", {})
        opportunities.append(
            {
                "destination_iso3": dest,
                "market_need": entry["market_need"],
                "end_to_end_score": e2e.get("score"),
                "score_available": e2e.get("available"),
                "landed_cost": ci.get("landed_cost", {}),
                "logistics_accessibility": ci.get("logistics_accessibility_index", {}),
                "financing_feasibility": ci.get("financing_feasibility_index", {}),
                "tariff_benefit": benchmarking_service.tariff_benefit_analysis(
                    producer_iso3, dest, hs_code
                ),
            }
        )

    # Final ranking: by export score (desc), then by market need (desc).
    opportunities.sort(
        key=lambda o: ((o["end_to_end_score"] or 0), (o["market_need"].get("value") or 0)),
        reverse=True,
    )

    return {
        "report_type": "value_chain_direct_export",
        "scenario": "S2_produce_export_direct",
        "inputs": {
            "hs_code": hs_code,
            "producer_iso3": producer_iso3,
            "goods_value_usd": goods_value_usd,
            "top_k": top_k,
        },
        "producer_supply": supply,
        "ranked_opportunities": opportunities,
        "candidates_considered": len(candidates),
        "deep_dived": len(opportunities),
        "data_quality": {
            "is_estimation": False,
            "note": (
                "Marchés classés par besoin estimé (proxy population / consommation "
                "apparente) puis par score d'opportunité de bout en bout (production, "
                "logistique, financement, risque pays). L'avantage tarifaire est "
                "fourni séparément par marché (hors score). Les besoins sont des "
                "estimations transparentes ; les scores reposent sur des données "
                "réelles ou marquées indisponibles."
            ),
        },
    }


def get_import_opportunities_scenario(
    destination_iso3: str,
    top_k: int = 8,
    goods_value_usd: float = 50000.0,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
) -> Dict:
    """
    Scenario **S4 — best IMPORT opportunities for a country** (mirror of S2).

    For a destination country, answer: *which products should it source from
    Africa, from whom, and with what AfCFTA advantage?* — interconnecting the
    platform's modules: production (FAOSTAT/USGS/UNIDO supply), statistics
    (needs), calculator (real preferential regime per origin), logistics and
    finance (end-to-end bilateral score). Two stages, both real-data:

      1. Cheap pass over every tracked product: estimate the destination's
         national need, its own recorded production, and the continental
         suppliers. Rank by unmet-need share, then by import pressure
         (need / continental supply — unitless, comparable across products).
      2. Deep-dive the ``top_k`` products: pick the best supplier among the top
         continental producers using the REAL preferential regime (same source
         of truth as the calculator — e.g. Algeria's 9 active AfCFTA partners),
         then run the full bilateral opportunity report for that corridor.

    No fabrication: needs are transparent estimates (flagged), local production
    absent from the dataset is labelled "not recorded", never assumed zero.
    """
    from services import production_capacity_service

    dest = (destination_iso3 or "").upper()

    # Stage 1 — scan every tracked product (all local, cheap).
    candidates = []
    products = production_capacity_service.list_tracked_products()
    for prod in products:
        hs = prod["hs_code"]
        producers = production_capacity_service.get_continental_producers(hs)
        if not producers.get("available"):
            continue
        suppliers = [
            p for p in producers.get("top_producers", []) if p.get("country_iso3") != dest
        ][:3]
        if not suppliers:
            continue

        need = demand_estimation_service.estimate_national_need(hs, dest)
        need_value = need.get("value") if need.get("available") else None
        if not need_value or need_value <= 0:
            continue

        local = production_capacity_service.get_capacity(dest, hs)
        local_recorded = bool(local.get("available")) and local.get("latest_value") is not None
        local_value = float(local.get("latest_value") or 0.0) if local_recorded else None

        if local_recorded:
            deficit = max(need_value - local_value, 0.0)
            deficit_share = round(deficit / need_value, 4) if need_value else None
            deficit_note = None
        else:
            # Production locale non enregistrée dans le référentiel : le besoin
            # entier est traité comme non couvert, mais c'est étiqueté (jamais
            # présenté comme un zéro mesuré).
            deficit = need_value
            deficit_share = 1.0
            deficit_note = "Production locale non enregistrée dans le référentiel (borne haute)."

        continental_total = producers.get("continental_total") or 0
        import_pressure = round(need_value / continental_total, 4) if continental_total else None

        candidates.append(
            {
                "hs_code": hs,
                "commodity": producers.get("commodity"),
                "dimension": producers.get("dimension"),
                "unit": producers.get("unit"),
                "market_need": need,
                "local_production": {
                    "recorded": local_recorded,
                    "value": local_value,
                    "year": local.get("latest_year") if local_recorded else None,
                },
                "unmet_need": round(deficit, 2),
                "unmet_need_share": deficit_share,
                "unmet_need_note": deficit_note,
                "import_pressure": import_pressure,
                "suppliers_pool": suppliers,
                "supply_source": producers.get("source"),
            }
        )

    candidates.sort(
        key=lambda c: ((c["unmet_need_share"] or 0), (c["import_pressure"] or 0)),
        reverse=True,
    )

    # Stage 2 — deep-dive the top_k products: best supplier by REAL preferential
    # regime (calculator's source of truth), then full bilateral report.
    opportunities = []
    for cand in candidates[: max(top_k, 0)]:
        hs = cand["hs_code"]
        judged_suppliers = []
        for sup in cand["suppliers_pool"]:
            tariff = benchmarking_service.tariff_benefit_analysis(sup["country_iso3"], dest, hs)
            judged_suppliers.append(
                {
                    "country_iso3": sup["country_iso3"],
                    "country_name": sup.get("country_name"),
                    "production_share_pct": sup.get("share_pct"),
                    "tariff_advantage_pct": (
                        tariff.get("tariff_advantage_pct") if tariff.get("available") else None
                    ),
                    "trade_regime": tariff.get("trade_regime"),
                    "trade_regime_note": tariff.get("trade_regime_note"),
                    # Bloc tarif complet conservé pour éviter un recalcul du
                    # meilleur fournisseur plus bas (non sérialisé dans la réponse).
                    "_tariff": tariff,
                }
            )
        # Meilleur fournisseur : avantage tarifaire réel d'abord (le régime
        # préférentiel dépend de l'ORIGINE — ex. réciprocité algérienne),
        # puis poids dans la production continentale.
        best = max(
            judged_suppliers,
            key=lambda s: (
                (s["tariff_advantage_pct"] or 0),
                (s["production_share_pct"] or 0),
            ),
        )
        best_tariff = best.pop("_tariff")
        # Retirer le bloc tarif complet des autres fournisseurs (réponse allégée).
        for s in judged_suppliers:
            s.pop("_tariff", None)

        report = get_opportunity_report(
            hs, best["country_iso3"], dest, goods_value_usd, weight_kg, volume_m3
        )
        ci = report.get("composite_indicators", {})
        e2e = ci.get("end_to_end_score", {})
        opportunities.append(
            {
                **{k: v for k, v in cand.items() if k != "suppliers_pool"},
                "suppliers_considered": judged_suppliers,
                "best_supplier": best,
                "end_to_end_score": e2e.get("score"),
                "score_available": e2e.get("available"),
                "landed_cost": ci.get("landed_cost", {}),
                "logistics_accessibility": ci.get("logistics_accessibility_index", {}),
                "financing_feasibility": ci.get("financing_feasibility_index", {}),
                "tariff_benefit": best_tariff,  # réutilisé (déjà calculé ci-dessus)
            }
        )

    # Classement final : par score de bout en bout (corridor exécutable),
    # puis par pression d'import — même logique que S2.
    opportunities.sort(
        key=lambda o: ((o["end_to_end_score"] or 0), (o["import_pressure"] or 0)),
        reverse=True,
    )

    return {
        "report_type": "import_opportunities",
        "scenario": "S4_best_imports_for_country",
        "inputs": {
            "destination_iso3": dest,
            "top_k": top_k,
            "goods_value_usd": goods_value_usd,
        },
        "ranked_opportunities": opportunities,
        "products_scanned": len(products),
        "candidates_retained": len(candidates),
        "deep_dived": len(opportunities),
        "data_quality": {
            "is_estimation": True,
            "note": (
                "Produits classés par part de besoin non couvert (besoin estimé − "
                "production locale enregistrée) puis par pression d'import (besoin / "
                "offre continentale, sans unité). Le meilleur fournisseur est choisi "
                "par avantage tarifaire RÉEL (même moteur que le calculateur : "
                "réciprocité, unions douanières) puis par poids de production. Les "
                "besoins sont des estimations transparentes ; production locale "
                "absente du référentiel = étiquetée non enregistrée, jamais un zéro "
                "mesuré."
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
            "import_quantity_tonnes": m.get("import_quantity") or None,
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
        "quantity_unit": "tonnes",  # BACI : poids net
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
        "coverage_caveat": prod.get("coverage_caveat"),
    }


async def get_market_seeking_report(hs_code: str, lang: str = "fr") -> Dict:
    """
    Market-seeking report for a producer: for a product (HS6/HS4), which African
    markets *import* it (demand, via OEC) and who *produces* it on the continent
    (supply, via real production data).

    Always uses the latest available data year (no year parameter exposed to
    callers): both demand (OEC trade flows) and supply (continental production)
    already resolve to the most recent year internally — a producer looking for
    markets has no reason to pin an arbitrary past year.

    Demand degrades gracefully when OEC is unreachable; supply is local/real.
    """
    hs_code = (hs_code or "").strip()
    from services.oec_trade_service import DEFAULT_YEAR

    product_name = None
    importers = []
    try:
        from services.real_trade_data_service import get_product_name, real_trade_service

        product_name = get_product_name(hs_code, lang)
        importers = await real_trade_service.get_african_importers_for_product(
            hs_code, DEFAULT_YEAR
        )
    except Exception as exc:
        _log.warning("importers-for-product unavailable: %s", exc)

    return {
        "report_type": "market_seeking",
        "inputs": {"hs_code": hs_code, "year": DEFAULT_YEAR},
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
