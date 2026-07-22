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
from services.real_trade_data_service import real_trade_service
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
    pour le corridor origine -> destination. Mémoïsé par (corridor, nature vrac) ;
    dégradation silencieuse (None) si le comparateur multimodal est indisponible.

    La clé inclut la nature « vrac » du produit car ``get_logistics_profile``
    adapte les options selon le code SH (une commodité vrac — ciment, minerai —
    exclut l'aérien et bascule la route terrestre en vrac) : réutiliser un délai
    non-vrac pour un produit vrac (ou l'inverse) serait faux.
    """
    try:
        from services.shipment_estimator import classify_bulk_commodity

        is_bulk = bool(classify_bulk_commodity(hs_code)) if hs_code else False
    except Exception:  # pragma: no cover
        is_bulk = False
    key = (origin_iso3.upper(), dest_iso3.upper(), is_bulk)
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


def _strategic_rationale(match: Dict, exporter_name: str, markets: List[Dict], product: str) -> str:
    """Compose une rationale stratégique lisible depuis l'intelligence + les marchés."""
    champ = match.get("champion")
    fut = match.get("future_capacity")
    parts: List[str] = []
    if champ and champ.get("rationale"):
        parts.append(champ["rationale"])
    if fut and fut.get("rationale"):
        parts.append(fut["rationale"])
    if not parts:
        # Repli générique quand le produit n'est pas encore dans la base curée.
        market_txt = _markets_phrase(markets)
        parts.append(
            f"{exporter_name} dispose d'une capacité d'export réelle sur « {product} », "
            f"et {market_txt} en importe{'nt' if len(markets) > 1 else ''} des volumes "
            f"significatifs aujourd'hui sourcés en grande partie hors du continent — "
            f"cible naturelle sous la ZLECAf."
        )
    return " ".join(parts)


def _markets_phrase(markets: List[Dict]) -> str:
    """« l'Égypte » (1 marché) ou « 3 marchés africains (premier : l'Égypte) »."""
    if not markets:
        return "des marchés africains"
    if len(markets) == 1:
        return markets[0].get("name") or markets[0].get("iso3", "")
    first = markets[0].get("name") or markets[0].get("iso3", "")
    return f"{len(markets)} marchés africains (premier : {first})"


def _build_flow(
    exporter_iso3: str,
    exporter_name: str,
    opp: Dict,
    markets: List[Dict],
    match: Dict,
    roo: Optional[Dict],
    lang: str,
    year: int,
) -> Dict:
    """
    Construit UN flux stratégique par PRODUIT (et non par couple produit×marché) :
    tous les marchés africains importateurs du produit sont listés dans
    ``markets`` avec leur volume d'import RÉEL et leur potentiel de capture, au
    lieu de dupliquer une carte par destination.
    """
    product = opp.get("export_product") or {}
    hs6 = product.get("hs_code", "")
    product_name = product.get("name") or f"SH {hs6}"

    market_entries: List[Dict] = []
    total_import = 0
    total_potential = 0
    for m in markets:
        size = int(m.get("market_size", 0) or 0)
        capture = m.get("capture_potential", 0) or 0
        pot = int(size * capture)
        total_import += size
        total_potential += pot
        market_entries.append(
            {
                "iso3": m.get("country_iso3"),
                "name": m.get("country_name") or m.get("country_iso3"),
                "import_usd": size,
                "potential_usd": pot,
                "capture_potential": capture,
                "lead_time_days": _lead_time_days(exporter_iso3, m.get("country_iso3", ""), hs6),
            }
        )
    market_entries.sort(key=lambda x: x["import_usd"], reverse=True)

    champ = match.get("champion") or {}
    # Vocabulaire canonique du champ (base curée : "High"/"Moderate"/"Medium"),
    # neutre en langue.
    price_competitiveness = champ.get("price_competitiveness")

    return {
        "hs_code": hs6,
        "product": product_name,
        "from": {"iso3": exporter_iso3, "name": exporter_name},
        "markets": market_entries,
        "signal": match.get("signal"),  # "High Growth" | "Established" | None
        "potential_usd": total_potential,
        "total_import_usd": total_import,
        "market_match_level": opp.get("market_match_level"),
        "strategic_rationale": _strategic_rationale(
            match, exporter_name, market_entries, product_name
        ),
        "transformation": _transformation(match),
        "advantage": {
            "afcfta_tariff_edge": _tariff_edge(hs6),
            "rules_of_origin": roo,
            "price_competitiveness": price_competitiveness,
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

        markets = f.get("markets") or []
        for m in markets:
            p = partners.setdefault(
                m["iso3"],
                {"iso3": m["iso3"], "name": m["name"], "flow_count": 0, "potential_usd": 0},
            )
            p["flow_count"] += 1  # nombre de produits acheminés vers ce partenaire
            p["potential_usd"] += m["potential_usd"]

        c = commodities.setdefault(
            f["hs_code"],
            {
                "hs_code": f["hs_code"],
                "product": f["product"],
                "market_count": 0,
                "potential_usd": 0,
                "signal": f["signal"],
            },
        )
        c["market_count"] += len(markets)  # nombre de marchés importateurs
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


def _markets_for_product(
    import_index: Dict,
    hs6: str,
    exporter_iso3: str,
    min_market_size: int,
    coef: float,
    lang: str,
) -> tuple:
    """
    Marchés africains importateurs d'un produit (SH6 exact, repli SH4 agrégé),
    hors pays exportateur, au-dessus de la taille minimale. Retourne
    ``(markets[:5], match_level)`` — chaque marché doté d'une capture prudente
    plafonnée par la substituabilité du produit.
    """
    from services.real_trade_data_service import get_country_name

    hs4 = hs6[:4]
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
        markets.append(
            {
                "country_iso3": m["iso3"],
                "country_name": get_country_name(m["iso3"], lang),
                "market_size": int(m["value"]),
                "addressable_market_size": int(m["value"] * coef),
                "capture_potential": round(min(coef, 0.25), 2),
            }
        )
    markets.sort(key=lambda x: x["market_size"], reverse=True)
    return markets[:5], match_level


async def _load_import_index(year: int) -> Dict:
    """
    Index de demande d'import africaine PROFOND (top-400/pays) : les produits
    transformés de milieu de gamme (peintures, carreaux, détergents, farine…)
    ont une demande réelle mais classée au-delà du top-100 des gros postes.
    Dégradation silencieuse (dict vide) hors contexte réseau.
    """
    try:
        return await real_substitution_service._build_african_import_index(
            year, hs_level="HS6", limit=400
        )
    except Exception:  # pragma: no cover
        return {}


async def _export_history_hs4(exporter_iso3: str, year: int) -> set:
    """
    Facteur 4 (voir ``unido_discovery_service``, section « Contrôle de
    plausibilité ») : positions SH4 pour lesquelles le pays a un historique
    d'export RÉEL (OEC/BACI), même modeste — top-100 par valeur.

    Une capacité de division ISIC est un signal macro ; elle ne prouve pas
    qu'un produit précis a déjà, ne serait-ce qu'une fois, quitté le pays.
    Un produit DÉCOUVERT sans aucun historique d'export (jamais vu dans le
    top-100 des exports du pays, tous produits confondus) reste plausible —
    c'est précisément la logique de l'app de référence, une capacité avérée
    vaut opportunité même si les flux actuels sont minimes — mais mérite un
    plafond de potentiel plus prudent qu'un produit déjà marginalement
    exporté. Dégradation silencieuse (ensemble vide -> tous les candidats
    traités comme « jamais exportés », plafond le plus prudent) hors contexte
    réseau : ne bloque jamais le moteur de flux.
    """
    try:
        exports = await real_trade_service.get_oec_exports(
            exporter_iso3, year=year, limit=100, hs_level="HS4"
        )
    except Exception:  # pragma: no cover
        return set()
    return {_normalize_hs(e.get("hs_code")) for e in (exports or []) if e.get("hs_code")}


async def _capacity_driven_flows(
    exporter_iso3: str,
    exporter_name: str,
    year: int,
    min_market_size: int,
    lang: str,
    covered_hs: set,
    import_index: Optional[Dict] = None,
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

    if import_index is None:
        import_index = await _load_import_index(year)
    if not import_index:
        return []

    # Un même champion (ou capacité future) liste souvent plusieurs sous-positions
    # SH6 sous UN SEUL libellé d'extrant (ex. Cevital « Huile de table raffinée &
    # margarine » couvre 6 SH6 : soja 150790, palme 151190, margarine 151710…).
    # Si plusieurs de ces SH6 ont chacun une vraie demande africaine, chacun
    # produisait sa propre carte avec le MÊME titre — redondance visuelle
    # constatée en production. On ne retient donc qu'UNE seule sous-position par
    # libellé (celle à la demande la plus forte) ; même principe que le tiers 3
    # (voir ``_unido_discovered_flows``).
    best_by_label: Dict[str, tuple] = {}  # label -> (max_demand, hs6, is_future)
    for hs6, product_label, is_future in candidates:
        if not hs6 or hs6 in covered_hs:
            continue
        # Marque TOUTE sous-position du panier du champion comme couverte, pas
        # seulement la gagnante : sinon une sous-position perdante (ex. 151190
        # « huile de palme », battue par 150790 pour le même libellé champion)
        # reste visible du tiers 3, qui la redécouvre sous un titre générique
        # différent — un doublon subsiste, juste avec un libellé différent.
        covered_hs.add(hs6)
        hs4 = hs6[:4]
        pool = import_index.get(hs6) or []
        if not pool:
            pool = [
                m for k, lst in import_index.items() if len(k) >= 4 and k[:4] == hs4 for m in lst
            ]
        max_demand = max((m["value"] for m in pool if m["iso3"] != exporter_iso3), default=0)
        label = product_label or hs6
        prev = best_by_label.get(label)
        if prev is None or max_demand > prev[0]:
            best_by_label[label] = (max_demand, hs6, is_future)

    flows: List[Dict] = []
    for label, (_demand, hs6, is_future) in best_by_label.items():
        hs4 = hs6[:4]
        coef = substitutability_for_hs(hs4)["coefficient"]

        # Marchés africains important ce produit (SH6 exact, repli SH4) : capacité
        # avérée mais flux d'export encore modeste -> capture prudente.
        markets, match_level = _markets_for_product(
            import_index, hs6, exporter_iso3, min_market_size, coef, lang
        )
        if not markets:
            continue

        # match_for_hs fournit le bon champion/capacité future + signal pour ce SH.
        match = intel.match_for_hs(exporter_iso3, hs6)
        product_name = label
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
        flow = _build_flow(
            exporter_iso3, exporter_name, synthetic_opp, markets, match, roo, lang, year
        )
        flow["is_emerging"] = bool(is_future)
        flow["is_capacity_driven"] = True
        flows.append(flow)

    return flows


# Nombre maximal de produits DÉCOUVERTS (non curés) par pays : borne le bruit et
# concentre la découverte sur les niches à plus forte demande.
_MAX_DISCOVERED_PRODUCTS = 25

# Plafond de plausibilité (facteur 3) : le potentiel d'export total d'un
# produit DÉCOUVERT (tous marchés confondus) ne peut excéder une fraction de
# la valeur ajoutée RÉELLE de la division ISIC dont il est dérivé.
#
# Sans ce garde-fou, une demande d'import massive sur un seul marché (ex.
# l'Algérie importe des centaines de M$ de lait en poudre) combinée à un taux
# de capture générique produisait un flux Burundi -> Algérie de 246,6 M$ de
# lait en poudre — supérieur à la valeur ajoutée de TOUT le secteur
# alimentaire burundais (191,6 M$, essentiellement café/thé). La capacité de
# division ISIC est un signal macro, pas une preuve de capacité EXCÉDENTAIRE
# exportable sur un produit précis : elle ne peut donc justifier un potentiel
# dépassant une fraction de ce que la division produit déjà, au total, dans le
# pays.
#
# La fraction elle-même est GRADUÉE par le facteur 4 (historique d'export réel,
# voir ``_export_history_hs4``) : un produit que le pays a DÉJÀ exporté, même
# modestement, a une preuve tangible de capacité d'export ; un produit JAMAIS
# vu dans ses exports réels reste un candidat légitime (c'est la thèse même de
# ce tiers — la capacité précède parfois le flux), mais avec un plafond plus
# prudent, faute de tout précédent commercial.
_DISCOVERY_VA_CAP_FRACTION_CORROBORATED = 0.3  # produit déjà exporté (même peu)
_DISCOVERY_VA_CAP_FRACTION_NASCENT = 0.10  # jamais exporté par ce pays


def _fmt_usd_fr(value: float) -> str:
    """Montant USD au format FR compact (Md$/M$/k$), cohérent avec le frontend."""
    v = float(value or 0)
    if v >= 1e9:
        return f"{v/1e9:.1f} Md$"
    if v >= 1e6:
        return f"{v/1e6:.0f} M$"
    if v >= 1e3:
        return f"{v/1e3:.0f} k$"
    return f"{v:.0f} $"


def _unido_transformation_champion(evidence: Dict, product_name: str) -> Dict:
    """
    Fabrique un « champion » synthétique à partir de l'évidence de capacité UNIDO
    (division ISIC + valeur ajoutée), pour narrer la stratégie de transformation
    d'une opportunité découverte via la même mécanique que les champions curés.

    Ne porte PAS de rationale : contrairement à un champion curé (une seule
    narrative fixe et vérifiée), un flux découvert varie selon le MARCHÉ ciblé
    et le niveau de confiance (facteur 4) — la rationale est composée par flux
    dans ``_unido_discovered_flows`` (voir ``_unido_flow_rationale``), pas ici,
    pour éviter un paragraphe identique d'une carte à l'autre (même sur des
    marchés différents).
    """
    sector = evidence.get("isic_label_fr") or "industrie manufacturière"
    return {
        "name": f"Capacité {sector}",
        "sector": sector,
        "input_source": evidence.get("input"),
        "input_sourcing": None,
        "input_capacity": None,
        "process": evidence.get("process"),
        "capacity": {"product": product_name},
        "status": "operational",
        "price_competitiveness": None,
    }


def _unido_flow_rationale(
    exporter_name: str,
    markets: List[Dict],
    product_name: str,
    evidence: Dict,
    has_export_history: bool,
) -> str:
    """
    Rationale stratégique d'un flux DÉCOUVERT (tiers 3), composée par PRODUIT à
    partir de ses marchés réels — pas un modèle unique où seuls le secteur/la
    VA/le produit varient : le premier marché (nom + volume d'import réel), le
    nombre de débouchés et la demande totale, plus le niveau de confiance
    (facteur 4 : produit déjà exporté ou encore jamais) font varier chaque
    carte, sans qu'aucune ne se lise comme la copie d'une autre.
    """
    sector = evidence.get("isic_label_fr") or "industrie manufacturière"
    va_txt = _fmt_usd_fr(evidence.get("value_added_usd") or 0)
    total_import = sum(m.get("import_usd", 0) or 0 for m in markets)
    top = markets[0] if markets else {}
    top_name = top.get("name") or top.get("iso3", "")
    top_txt = _fmt_usd_fr(top.get("import_usd", 0) or 0)

    anchor = (
        f"{exporter_name} a une capacité manufacturière avérée dans « {sector} » "
        f"({va_txt} de valeur ajoutée, UNIDO INDSTAT4), suffisante pour produire "
        f"« {product_name} »."
    )
    if len(markets) <= 1:
        demand = (
            f"{top_name} en importe {top_txt} aujourd'hui, sourcés en grande "
            f"partie hors du continent — un marché accessible sous préférence ZLECAf."
        )
    else:
        demand = (
            f"{len(markets)} marchés africains en importent {_fmt_usd_fr(total_import)} "
            f"au total (premier : {top_name}, {top_txt}), sourcés en grande partie "
            f"hors du continent — autant de débouchés accessibles sous préférence ZLECAf."
        )
    if has_export_history:
        confidence = (
            f"{exporter_name} exporte déjà ce type de produit, même modestement : "
            f"la ZLECAf ouvre la voie à une montée en puissance régionale."
        )
    else:
        confidence = (
            f"Aucun flux d'export significatif n'existe encore sur ce produit "
            f"précis pour {exporter_name} — la capacité de production est avérée, "
            f"sa conversion en flux commercial reste à amorcer."
        )
    return f"{anchor} {demand} {confidence}"


async def _unido_discovered_flows(
    exporter_iso3: str,
    exporter_name: str,
    year: int,
    min_market_size: int,
    lang: str,
    covered_hs: set,
    import_index: Optional[Dict] = None,
    export_history: Optional[set] = None,
) -> List[Dict]:
    """
    Troisième tiers : flux DÉCOUVERTS automatiquement depuis les données UNIDO.

    À la différence des flux curés (champions nommés), ceux-ci n'exigent aucune
    curation : la capacité manufacturière par division ISIC (valeur ajoutée
    UNIDO) est traduite en produits SH exportables (``unido_hs_mapping``), puis
    croisée avec la demande d'import africaine réelle. C'est le moteur qui « se
    développe et s'agrandit de lui-même » — dès qu'un pays a de la valeur ajoutée
    dans une division, ses produits deviennent des candidats à l'export.

    Prudence : ces flux sont adossés à une capacité de division (pas à une usine
    nommée) ; ils sont donc marqués ``discovery_tier="unido"`` et classés sous
    les flux curés. On saute tout SH déjà couvert (OEC ou champion).
    """
    from services import unido_discovery_service as disco

    cap_index = disco.capacity_hs4_index(exporter_iso3)
    if not cap_index:
        return []

    if import_index is None:
        import_index = await _load_import_index(year)
    if not import_index:
        return []

    if export_history is None:
        export_history = await _export_history_hs4(exporter_iso3, year)

    # Candidats : SH6 de la demande d'import dont le SH4 est une capacité avérée
    # du pays et qui n'est pas déjà couvert. Le libellé produit de ce tiers vient
    # du mapping ISIC->SH4 (``unido_hs_mapping``), donc IDENTIQUE pour tous les
    # SH6 partageant un même SH4 (ex. 271111/271121 -> « Gaz de pétrole (GPL) &
    # hydrocarbures gazeux »). Plusieurs sous-positions du même SH4 ayant chacune
    # une vraie demande produisaient donc des cartes au titre identique —
    # redondance visuelle constatée en production. On ne retient qu'UNE seule
    # sous-position par SH4 (celle à la demande la plus forte).
    best_by_hs4: Dict[str, tuple] = {}  # hs4 -> (max_demand, hs6)
    for hs6, importers in import_index.items():
        code = _normalize_hs(hs6)
        if len(code) < 6 or code in covered_hs or code[:4] not in cap_index:
            continue
        max_demand = max(
            (m["value"] for m in importers if m["iso3"] != exporter_iso3),
            default=0,
        )
        if max_demand < min_market_size:
            continue
        hs4 = code[:4]
        prev = best_by_hs4.get(hs4)
        if prev is None or max_demand > prev[0]:
            best_by_hs4[hs4] = (max_demand, code)
    candidates = sorted(best_by_hs4.values(), reverse=True)[:_MAX_DISCOVERED_PRODUCTS]

    flows: List[Dict] = []
    for _demand, hs6 in candidates:
        if hs6 in covered_hs:
            continue
        covered_hs.add(hs6)

        evidence = cap_index[hs6[:4]]
        product_name = evidence.get("product_label") or f"SH {hs6}"
        coef = substitutability_for_hs(hs6[:4])["coefficient"]
        markets, match_level = _markets_for_product(
            import_index, hs6, exporter_iso3, min_market_size, coef, lang
        )
        if not markets:
            continue

        # Plafond de plausibilité (facteur 3), gradué par le facteur 4 : un
        # produit déjà exporté (même modestement) garde le plafond standard ;
        # un produit jamais exporté par ce pays est plafonné plus bas, faute
        # de tout précédent commercial confirmant la capacité EXPORT (par
        # opposition à la seule capacité de PRODUCTION domestique).
        has_export_history = hs6[:4] in export_history
        va_cap_fraction = (
            _DISCOVERY_VA_CAP_FRACTION_CORROBORATED
            if has_export_history
            else _DISCOVERY_VA_CAP_FRACTION_NASCENT
        )
        va = evidence.get("value_added_usd") or 0
        va_cap = va * va_cap_fraction
        raw_total = sum(int(m["market_size"] * m["capture_potential"]) for m in markets)
        if va_cap and raw_total > va_cap:
            scale = va_cap / raw_total
            for m in markets:
                m["capture_potential"] = round(m["capture_potential"] * scale, 4)

        champion = _unido_transformation_champion(evidence, product_name)
        match = {
            "available": True,
            "champion": champion,
            "future_capacity": None,
            "signal": "High Growth",
        }
        synthetic_opp = {
            "export_product": {"hs_code": hs6, "name": product_name},
            "market_match_level": match_level,
            "afcfta_advantage": "Accès préférentiel ZLECAf (droits réduits ou supprimés)",
            "binding_constraint": "montée en puissance des exports (capacité avérée)",
            "verified_production": None,
        }
        roo = _rules_of_origin(hs6, lang)
        flow = _build_flow(
            exporter_iso3, exporter_name, synthetic_opp, markets, match, roo, lang, year
        )
        # Rationale composée par PRODUIT depuis ses marchés réels (premier marché,
        # nombre de débouchés, demande totale, confiance) — voir
        # _unido_flow_rationale : chaque carte porte un texte propre, la liste
        # des marchés (avec volumes) remplaçant les cartes dupliquées.
        flow["strategic_rationale"] = _unido_flow_rationale(
            exporter_name, flow["markets"], product_name, evidence, has_export_history
        )
        flow["is_emerging"] = False
        flow["is_capacity_driven"] = True
        flow["discovery_tier"] = "unido"
        flow["capacity_evidence"] = {
            "isic_code": evidence.get("isic_code"),
            "isic_label": evidence.get("isic_label_fr"),
            "value_added_usd": evidence.get("value_added_usd"),
            "va_year": evidence.get("va_year"),
            "source": "UNIDO INDSTAT4",
            # Traçabilité du système à facteurs multiples (voir
            # unido_discovery_service, section « Contrôle de plausibilité »).
            "input_requirement_checked": evidence.get("input_requirement_checked", False),
            "has_export_history": has_export_history,
            "plausibility_cap_fraction": va_cap_fraction,
        }
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
        markets = opp.get("potential_markets", [])
        if not markets:
            continue
        match = intel.match_for_hs(exporter_iso3, hs6)
        roo = _rules_of_origin(hs6, lang)
        flow = _build_flow(exporter_iso3, exporter_name, opp, markets, match, roo, lang, year)
        flow["is_emerging"] = False
        flows.append(flow)

    # Index de demande d'import africaine chargé UNE fois, partagé par les deux
    # tiers pilotés par la capacité (évite un double appel réseau).
    import_index = await _load_import_index(year)

    # Tiers 2 — flux curés pilotés par la capacité (champions + projets
    # structurants) : ce que le pays SAIT produire, même si les flux actuels
    # sont modestes.
    flows.extend(
        await _capacity_driven_flows(
            exporter_iso3, exporter_name, year, min_market_size, lang, covered_hs, import_index
        )
    )

    # Tiers 3 — flux DÉCOUVERTS depuis les données UNIDO (auto-expansion, sans
    # curation) : valeur ajoutée par division ISIC -> produits SH -> demande.
    # Historique d'export réel (facteur 4) chargé une fois pour ce tiers.
    export_history = await _export_history_hs4(exporter_iso3, year)
    flows.extend(
        await _unido_discovered_flows(
            exporter_iso3,
            exporter_name,
            year,
            min_market_size,
            lang,
            covered_hs,
            import_index,
            export_history,
        )
    )

    # Les flux portant un signal industriel (High Growth puis Established)
    # remontent, puis tri par potentiel — l'objectif étant de faire émerger les
    # plus grosses opportunités réelles, quelle que soit la provenance (flux OEC,
    # champion curé ou découverte UNIDO). La provenance reste tracée par
    # ``discovery_tier`` / ``capacity_evidence`` pour l'affichage (badge de
    # confiance), sans reléguer une grosse niche découverte sous une petite
    # opportunité curée.
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
