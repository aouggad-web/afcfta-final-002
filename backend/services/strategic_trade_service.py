"""
Strategic Trade Intelligence Service
====================================

Transforme les *flux d'export bruts* (issus de ``real_substitution_service``,
eux-mêmes assis sur les flux réels OEC) en *flux stratégiques* enrichis, à la
manière de l'application de référence :

    Produit (SH) + Origine -> Destination
      • Rationale stratégique
      • Stratégie de transformation industrielle (intrant -> procédé -> extrant)
      • Avantage ZLECAf : écart tarifaire (NPF vs préférentiel), règles d'origine,
        compétitivité prix
      • Signal « High Growth » quand un projet structurant porte le produit
      • Potentiel (USD) et taux de capture

et une vue agrégée : nombre de flux identifiés, potentiel total, partenaires
régionaux prioritaires, commodités prioritaires.

Chaque enrichissement est défensif : si une source (règles d'origine, tarifs…)
n'est pas disponible dans le contexte d'exécution, le champ vaut ``None`` et le
flux reste produit — jamais bloqué.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from services import industrial_intelligence_service as intel
from services.real_substitution_service import real_substitution_service
from services.substitution_feasibility_service import substitutability_for_hs

logger = logging.getLogger(__name__)


def _normalize_hs(hs_code: Optional[str]) -> str:
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


def _mfn_rate_pct(hs_code: str) -> Optional[float]:
    """
    Taux NPF (proxy continental par chapitre SH) en pourcentage.

    Réutilise la table chapitre->taux, source unique de vérité déjà utilisée
    par le calculateur tarifaire. Import paresseux : ``services`` ne dépend pas
    de ``routes`` au chargement (évite tout import circulaire).
    """
    chapter = _normalize_hs(hs_code)[:2]
    if not chapter:
        return None
    try:
        from routes.tariffs_calculation import get_chapter_rate

        return round(get_chapter_rate(chapter) * 100, 1)
    except Exception:  # pragma: no cover - le moteur ne doit jamais casser là-dessus
        return None


def _ensure_rules_loaded() -> None:
    """
    Garantit que ``RULES_DATA`` est chargé.

    En contexte applicatif, ``routes.__init__`` l'initialise au démarrage. Hors
    application (tâches, tests, scripts), on charge nous-mêmes le référentiel
    ZLECAf pour que l'enrichissement règles d'origine ne dégénère pas en
    « UNKNOWN » silencieux.
    """
    try:
        from pathlib import Path

        from routes import rules_of_origin as roo_mod

        if roo_mod.RULES_DATA:
            return
        import json

        path = Path(__file__).resolve().parent.parent / "data" / "zlecaf_rules_of_origin.json"
        with open(path, "r", encoding="utf-8") as f:
            roo_mod.init_data(json.load(f))
    except Exception:  # pragma: no cover
        pass


def _rules_of_origin(hs_code: str, lang: str) -> Optional[Dict]:
    """Verdict règles d'origine ZLECAf (nom + type) ou None si indisponible."""
    try:
        _ensure_rules_loaded()
        from routes.rules_of_origin import get_rule_of_origin

        roo = get_rule_of_origin(hs_code, lang)
        primary = roo.get("primary_rule") or {}
        return {
            "status": roo.get("status"),
            "rule_name": primary.get("name"),
            "rule_type": primary.get("type"),
        }
    except Exception:  # pragma: no cover
        return None


def _tariff_edge(hs_code: str) -> Dict:
    """
    Avantage tarifaire ZLECAf : NPF (proxy chapitre) vs taux préférentiel cible.

    Sous la ZLECAf, l'écrasante majorité des lignes converge vers 0 % pour les
    marchandises satisfaisant les règles d'origine ; on modélise donc le taux
    préférentiel à 0 % et l'écart = NPF. Explicitement estimatif (proxy par
    chapitre), remplaçable par le calcul authentique par paire pays plus tard.
    """
    mfn = _mfn_rate_pct(hs_code)
    if mfn is None:
        return {
            "mfn_rate_pct": None,
            "afcfta_rate_pct": None,
            "edge_pct": None,
            "is_estimate": True,
        }
    afcfta = 0.0
    return {
        "mfn_rate_pct": mfn,
        "afcfta_rate_pct": afcfta,
        "edge_pct": round(mfn - afcfta, 1),
        "is_estimate": True,
    }


# Lead time mémoïsé par corridor (origine, destination) : il ne dépend pas du
# produit, or le calcul multimodal est coûteux et se répète sur chaque flux.
_LEAD_TIME_CACHE: Dict[tuple, Optional[float]] = {}


def _lead_time_days(origin_iso3: str, dest_iso3: str, hs_code: str) -> Optional[float]:
    """
    Délai de livraison estimé (jours) de l'option opérationnelle la moins chère
    pour le corridor origine -> destination. Mémoïsé par corridor ; dégradation
    silencieuse (None) si le comparateur multimodal est indisponible.
    """
    key = (origin_iso3.upper(), dest_iso3.upper())
    if key in _LEAD_TIME_CACHE:
        return _LEAD_TIME_CACHE[key]
    days: Optional[float] = None
    try:
        from services.logistics_opportunity_adapter import get_logistics_profile

        profile = get_logistics_profile(origin_iso3, dest_iso3, hs_code=hs_code)
        cheapest = profile.get("cheapest_operational_option") or {}
        tmin = cheapest.get("transit_days_min")
        tmax = cheapest.get("transit_days_max")
        if tmin is not None and tmax is not None:
            days = round((tmin + tmax) / 2)
        elif cheapest.get("transit_days") is not None:
            days = round(cheapest["transit_days"])
    except Exception:  # pragma: no cover
        days = None
    _LEAD_TIME_CACHE[key] = days
    return days


# CAGR de demande régionale par défaut pour projeter la trajectoire à 5 ans.
# Repli prudent (~7 %/an) alignant l'ordre de grandeur des trajectoires de
# demande intra-africaine ; explicitement estimatif.
_DEFAULT_DEMAND_CAGR = 0.07


def _growth_trajectory(market_size: int, year: int) -> Dict:
    """
    Trajectoire de demande régionale sur 5 ans [année-3 .. année+1], projetée
    depuis la demande actuelle du marché avec un CAGR régional. Estimative.
    """
    base = float(market_size or 0)
    points = []
    for offset in range(-3, 2):  # year-3 .. year+1 (5 points)
        factor = (1 + _DEFAULT_DEMAND_CAGR) ** offset
        points.append({"year": year + offset, "demand_usd": int(base * factor)})
    return {
        "cagr_pct": round(_DEFAULT_DEMAND_CAGR * 100, 1),
        "points": points,
        "is_estimate": True,
    }


def _transformation(match: Dict) -> Optional[Dict]:
    """Stratégie de transformation industrielle depuis l'intelligence pays."""
    champ = match.get("champion")
    fut = match.get("future_capacity")
    source = champ or fut
    if not source:
        return None
    if champ:
        return {
            "champion": champ.get("name"),
            "sector": champ.get("sector"),
            "input_source": champ.get("input_source"),
            "input_sourcing": champ.get("input_sourcing"),
            "input_target": champ.get("input_capacity"),
            "process": champ.get("process"),
            "output_target": champ.get("capacity"),
            "status": champ.get("status"),
        }
    # capacité future seule (pas encore de champion opérationnel sur ce SH)
    return {
        "champion": fut.get("linked_project"),
        "sector": (fut.get("project_detail") or {}).get("secteur"),
        "input_source": None,
        "input_sourcing": None,
        "process": fut.get("impact"),
        "output_target": {"product": fut.get("product")},
        "status": "future",
    }


def _strategic_rationale(match: Dict, exporter_name: str, market_name: str, product: str) -> str:
    """Compose une rationale stratégique lisible depuis l'intelligence + le marché."""
    champ = match.get("champion")
    fut = match.get("future_capacity")
    parts: List[str] = []
    if champ and champ.get("rationale"):
        parts.append(champ["rationale"])
    if fut and fut.get("rationale"):
        parts.append(fut["rationale"])
    if not parts:
        # Repli générique quand le produit n'est pas encore dans la base curée.
        parts.append(
            f"{exporter_name} dispose d'une capacité d'export réelle sur « {product} », "
            f"et {market_name} en importe des volumes significatifs aujourd'hui sourcés "
            f"en grande partie hors du continent — cible naturelle sous la ZLECAf."
        )
    return " ".join(parts)


def _build_flow(
    exporter_iso3: str,
    exporter_name: str,
    opp: Dict,
    market: Dict,
    match: Dict,
    roo: Optional[Dict],
    lang: str,
    year: int,
) -> Dict:
    product = opp.get("export_product") or {}
    hs6 = product.get("hs_code", "")
    product_name = product.get("name") or f"SH {hs6}"
    market_name = market.get("country_name") or market.get("country_iso3")

    market_size = market.get("market_size", 0) or 0
    capture = market.get("capture_potential", 0) or 0
    potential_usd = int(market_size * capture)

    price_pos = market.get("price_positioning") or {}
    champ = match.get("champion") or {}
    price_competitiveness = champ.get("price_competitiveness") or (
        "Élevée" if price_pos.get("positioning") == "compétitif" else None
    )

    return {
        "hs_code": hs6,
        "product": product_name,
        "from": {"iso3": exporter_iso3, "name": exporter_name},
        "to": {
            "iso3": market.get("country_iso3"),
            "name": market_name,
        },
        "signal": match.get("signal"),  # "High Growth" | "Established" | None
        "potential_usd": potential_usd,
        "market_size_usd": int(market_size),
        "capture_potential": capture,
        "market_match_level": opp.get("market_match_level"),
        "strategic_rationale": _strategic_rationale(
            match, exporter_name, market_name, product_name
        ),
        "transformation": _transformation(match),
        "growth_trajectory": _growth_trajectory(int(market_size), year),
        "advantage": {
            "afcfta_tariff_edge": _tariff_edge(hs6),
            "rules_of_origin": roo,
            "price_competitiveness": price_competitiveness,
            "price_positioning": price_pos or None,
            "lead_time_days": _lead_time_days(exporter_iso3, market.get("country_iso3", ""), hs6),
            "afcfta_note": opp.get("afcfta_advantage"),
        },
        "future_project": match.get("future_capacity"),
        "verified_production": opp.get("verified_production"),
        "binding_constraint": opp.get("binding_constraint"),
    }


def _aggregate(flows: List[Dict], lang: str) -> Dict:
    """Vue agrégée : partenaires prioritaires + commodités prioritaires."""
    partners: Dict[str, Dict] = {}
    commodities: Dict[str, Dict] = {}
    total_potential = 0

    for f in flows:
        total_potential += f["potential_usd"]

        to = f["to"]
        p = partners.setdefault(
            to["iso3"],
            {"iso3": to["iso3"], "name": to["name"], "flow_count": 0, "potential_usd": 0},
        )
        p["flow_count"] += 1
        p["potential_usd"] += f["potential_usd"]

        c = commodities.setdefault(
            f["hs_code"],
            {
                "hs_code": f["hs_code"],
                "product": f["product"],
                "flow_count": 0,
                "potential_usd": 0,
                "signal": f["signal"],
            },
        )
        c["flow_count"] += 1
        c["potential_usd"] += f["potential_usd"]

    top_partners = sorted(partners.values(), key=lambda x: x["potential_usd"], reverse=True)
    priority_commodities = sorted(
        commodities.values(), key=lambda x: x["potential_usd"], reverse=True
    )

    return {
        "identified_flows": len(flows),
        "total_potential_usd": int(total_potential),
        "top_partners": top_partners,
        "priority_commodities": priority_commodities,
    }


def _intelligence_candidate_products(kb: Dict) -> List[tuple]:
    """
    Produits exportables portés par l'intelligence pays : (hs6, product_label,
    is_future). Couvre les extrants des champions opérationnels (Cevital sucre,
    Condor téléviseurs…) ET les capacités futures (Gara Djebilet, El Hadba…).
    """
    out: List[tuple] = []
    for champ in kb.get("champions", []):
        label = champ.get("output_product") or champ.get("name")
        for hs in champ.get("hs_products", []):
            out.append((_normalize_hs(hs), label, False))
    for fut in kb.get("future_capacity", []):
        label = fut.get("product") or ""
        for hs in fut.get("hs_products", []):
            out.append((_normalize_hs(hs), label, True))
    return out


async def _capacity_driven_flows(
    exporter_iso3: str,
    exporter_name: str,
    year: int,
    min_market_size: int,
    lang: str,
    covered_hs: set,
) -> List[Dict]:
    """
    Flux *pilotés par la capacité* : à la différence des flux OEC historiques
    (ce qu'un pays exporte déjà), ceux-ci partent de ce qu'un pays SAIT PRODUIRE
    — extrants de ses champions industriels (Cevital → sucre raffiné, Condor →
    téléviseurs) et de ses projets structurants (Gara Djebilet → minerai de fer).

    C'est la logique de l'app de référence : une capacité de production avérée
    fait d'un produit une opportunité, même si les flux d'export actuels sont
    encore modestes. Aucune offre inventée : la DEMANDE (marchés africains
    importateurs) est réelle (index OEC) ; la capacité d'OFFRE est documentée
    (champion opérationnel ou projet). On saute les produits déjà couverts par un
    vrai flux OEC pour ne pas doublonner.
    """
    kb = intel.get_country_intelligence(exporter_iso3)
    if not kb:
        return []
    candidates = _intelligence_candidate_products(kb)
    if not candidates:
        return []

    try:
        import_index = await real_substitution_service._build_african_import_index(
            year, hs_level="HS6"
        )
    except Exception:  # pragma: no cover
        return []
    if not import_index:
        return []

    from services.real_trade_data_service import get_country_name

    flows: List[Dict] = []
    for hs6, product_label, is_future in candidates:
        if not hs6 or hs6 in covered_hs:
            continue
        covered_hs.add(hs6)

        hs4 = hs6[:4]
        coef = substitutability_for_hs(hs4)["coefficient"]

        # Marchés africains important ce produit (SH6 exact, repli SH4).
        pool = [m for m in import_index.get(hs6, []) if m["iso3"] != exporter_iso3]
        match_level = "hs6"
        if not pool:
            match_level = "hs4"
            by_country: Dict[str, float] = {}
            for k, lst in import_index.items():
                if len(k) >= 4 and k[:4] == hs4:
                    for m in lst:
                        if m["iso3"] == exporter_iso3:
                            continue
                        by_country[m["iso3"]] = by_country.get(m["iso3"], 0) + m["value"]
            pool = [{"iso3": iso, "value": v} for iso, v in by_country.items()]

        markets = []
        for m in pool:
            if m["value"] < min_market_size:
                continue
            addressable = int(m["value"] * coef)
            markets.append(
                {
                    "country_iso3": m["iso3"],
                    "country_name": get_country_name(m["iso3"], lang),
                    "market_size": int(m["value"]),
                    "addressable_market_size": addressable,
                    # Capacité avérée mais flux d'export encore modeste : capture
                    # prudente, plafonnée par la substituabilité du produit.
                    "capture_potential": round(min(coef, 0.25), 2),
                    "price_positioning": None,
                }
            )
        if not markets:
            continue
        markets.sort(key=lambda x: x["market_size"], reverse=True)
        markets = markets[:5]

        # match_for_hs fournit le bon champion/capacité future + signal pour ce SH.
        match = intel.match_for_hs(exporter_iso3, hs6)
        product_name = product_label or f"SH {hs6}"
        synthetic_opp = {
            "export_product": {"hs_code": hs6, "name": product_name},
            "market_match_level": match_level,
            "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
            "binding_constraint": (
                "capacité en cours de mise en service"
                if is_future
                else "montée en puissance des exports"
            ),
            "verified_production": None,
        }
        roo = _rules_of_origin(hs6, lang)
        for market in markets:
            flow = _build_flow(
                exporter_iso3, exporter_name, synthetic_opp, market, match, roo, lang, year
            )
            flow["is_emerging"] = bool(is_future)
            flow["is_capacity_driven"] = True
            flows.append(flow)

    return flows


async def get_strategic_flows(
    exporter_iso3: str,
    year: int = 2022,
    min_market_size: int = 5_000_000,
    lang: str = "fr",
    limit: int = 30,
) -> Dict:
    """
    Point d'entrée du sous-module. Retourne::

        {
          "exporter": {...},
          "year": ...,
          "summary": { identified_flows, total_potential_usd, top_partners,
                       priority_commodities },
          "flows": [ ...flux stratégiques triés par potentiel... ],
          "has_industrial_intelligence": bool,
          "data_source": ...,
        }
    """
    exporter_iso3 = exporter_iso3.upper()

    base = await real_substitution_service.find_export_opportunities(
        exporter_iso3, year=year, min_market_size=min_market_size, lang=lang
    )

    if base.get("error"):
        return {"error": base["error"], "exporter": {"iso3": exporter_iso3}, "flows": []}

    exporter = base.get("exporter", {"iso3": exporter_iso3})
    exporter_name = exporter.get("name", exporter_iso3)

    flows: List[Dict] = []
    covered_hs: set = set()
    for opp in base.get("opportunities", []):
        hs6 = (opp.get("export_product") or {}).get("hs_code", "")
        if not hs6:
            continue
        covered_hs.add(_normalize_hs(hs6))
        match = intel.match_for_hs(exporter_iso3, hs6)
        roo = _rules_of_origin(hs6, lang)
        for market in opp.get("potential_markets", []):
            flow = _build_flow(exporter_iso3, exporter_name, opp, market, match, roo, lang, year)
            flow["is_emerging"] = False
            flows.append(flow)

    # Flux pilotés par la capacité industrielle (champions + projets structurants) :
    # ce que le pays SAIT produire, même si les flux d'export actuels sont modestes.
    flows.extend(
        await _capacity_driven_flows(
            exporter_iso3, exporter_name, year, min_market_size, lang, covered_hs
        )
    )

    # Les flux portant un signal industriel (High Growth puis Established)
    # remontent, puis tri par potentiel — un flux adossé à une capacité réelle
    # prime sur un flux OEC nu de potentiel comparable.
    _signal_rank = {"High Growth": 2, "Established": 1, None: 0}
    flows.sort(
        key=lambda f: (_signal_rank.get(f["signal"], 0), f["potential_usd"]),
        reverse=True,
    )
    if limit:
        flows = flows[:limit]

    summary = _aggregate(flows, lang)

    return {
        "exporter": exporter,
        "year": year,
        "data_source": base.get("data_source", "OEC (BACI) + intelligence industrielle"),
        "has_industrial_intelligence": intel.has_intelligence(exporter_iso3),
        "summary": summary,
        "flows": flows,
        "is_estimation": base.get("is_estimation", False),
    }
