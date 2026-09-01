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

import asyncio
import logging
from typing import Awaitable, Callable, Dict, List, Optional

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


# Profil logistique mémoïsé par corridor (origine, destination, nature vrac) :
# un seul appel au comparateur multimodal par corridor, réutilisé pour DEUX
# usages — le délai de livraison (déjà affiché) ET l'indice d'accessibilité
# logistique (infrastructure de transport : nombre de modes réellement
# opérationnels — route, rail, mer, air — et faisabilité de l'option la moins
# chère). Un pays enclavé (ex. RCA, dépendant de la route vers un port
# étranger) peut afficher une capacité manufacturière réelle SANS pour autant
# avoir l'accès logistique qui permettrait d'en exporter le volume — c'est un
# frein aussi réel que la capacité de production elle-même, jusqu'ici jamais
# intégré à l'analyse stratégique.
_LOGISTICS_PROFILE_CACHE: Dict[tuple, Dict] = {}


def _logistics_profile_for_corridor(origin_iso3: str, dest_iso3: str, hs_code: str) -> Dict:
    """
    Profil logistique mémoïsé pour un corridor : ``{"lead_time_days", "accessibility"}``.
    Dégradation silencieuse (valeurs ``None``) si le comparateur multimodal est
    indisponible — jamais bloquant pour le flux stratégique.

    La clé inclut la nature « vrac » du produit car ``get_logistics_profile``
    adapte les options selon le code SH (une commodité vrac — ciment, minerai —
    exclut l'aérien et bascule la route terrestre en vrac) : réutiliser un profil
    non-vrac pour un produit vrac (ou l'inverse) serait faux.
    """
    try:
        from services.shipment_estimator import classify_bulk_commodity

        is_bulk = bool(classify_bulk_commodity(hs_code)) if hs_code else False
    except Exception:  # pragma: no cover
        is_bulk = False
    key = (origin_iso3.upper(), dest_iso3.upper(), is_bulk)
    if key in _LOGISTICS_PROFILE_CACHE:
        return _LOGISTICS_PROFILE_CACHE[key]
    result: Dict = {"lead_time_days": None, "accessibility": None}
    try:
        from services.logistics_opportunity_adapter import (
            get_logistics_profile,
            summarize_logistics_accessibility,
        )

        profile = get_logistics_profile(origin_iso3, dest_iso3, hs_code=hs_code)
        cheapest = profile.get("cheapest_operational_option") or {}
        tmin = cheapest.get("transit_days_min")
        tmax = cheapest.get("transit_days_max")
        if tmin is not None and tmax is not None:
            result["lead_time_days"] = round((tmin + tmax) / 2)
        elif cheapest.get("transit_days") is not None:
            result["lead_time_days"] = round(cheapest["transit_days"])
        result["accessibility"] = summarize_logistics_accessibility(profile)
    except Exception:  # pragma: no cover
        pass
    _LOGISTICS_PROFILE_CACHE[key] = result
    return result


def _lead_time_days(origin_iso3: str, dest_iso3: str, hs_code: str) -> Optional[float]:
    """Délai de livraison estimé (jours) de l'option opérationnelle la moins
    chère pour le corridor origine -> destination. Voir
    :func:`_logistics_profile_for_corridor`."""
    return _logistics_profile_for_corridor(origin_iso3, dest_iso3, hs_code).get("lead_time_days")


def _logistics_accessibility(origin_iso3: str, dest_iso3: str, hs_code: str) -> Optional[Dict]:
    """
    Accessibilité logistique réelle du corridor (route/rail/mer/air) : nombre
    de modes opérationnels + faisabilité de l'option la moins chère (voir
    ``logistics_opportunity_adapter.summarize_logistics_accessibility``).
    ``None`` si le comparateur multimodal est indisponible.
    """
    return _logistics_profile_for_corridor(origin_iso3, dest_iso3, hs_code).get("accessibility")


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
                # Infrastructure de transport réelle du corridor (route/rail/mer/
                # air) : un pays enclavé ou mal connecté peut avoir la capacité de
                # PRODUIRE sans avoir l'accès pour EXPORTER le volume — un frein
                # aussi réel que la capacité manufacturière, jamais silencieux.
                "logistics_accessibility": _logistics_accessibility(
                    exporter_iso3, m.get("country_iso3", ""), hs6
                ),
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


# ---------------------------------------------------------------------------
# Garde-fou « besoin national » (facteur 5)
# ---------------------------------------------------------------------------
# Une capacité de PRODUCTION ne vaut pas capacité d'EXPORT : un pays n'exporte
# qu'un EXCÉDENT — ce que sa production couvre AU-DELÀ de sa demande intérieure.
# Or les tiers pilotés par la capacité (champions curés ET découverte UNIDO)
# partent de la seule capacité de production ; ils faisaient donc ressortir, à
# tort, des produits dont le pays est lui-même un gros IMPORTATEUR NET — sa
# production ne suffit même pas à son marché national, il n'a aucun excédent à
# exporter.
#
# Cas réel signalé : l'Algérie ressortait comme exportatrice de lait en poudre
# (SH 040210) alors qu'elle en IMPORTE >1 Md$/an. Sa production laitière est
# pourtant réelle (facteur 2 « intrant corroboré » satisfait) — mais très loin
# de couvrir la demande intérieure : même avec le projet Baladna (~300 000
# vaches), l'Algérie reste structurellement importatrice nette. La capacité
# existe, l'excédent exportable non.
#
# Règle : sur les tiers capacité, on EXCLUT un produit dont le pays exportateur
# est un importateur net MAJEUR — imports du produit nettement supérieurs à ses
# exports ET matériels en valeur absolue. La position nette est mesurée au SH6
# (pas au SH4) pour ne pas confondre l'INTRANT importé et l'EXTRANT exporté
# d'une même position à 4 chiffres (ex. sucre brut importé 170114 vs sucre
# raffiné exporté 170199, tous deux sous 1701) : un raffineur véritablement
# exportateur de 170199 ne doit pas être écarté parce qu'il importe le brut.
#
# Source de la position nette : données OEC/BACI par pays (les mêmes que le
# sous-module statistique « SH6 par pays »), bornées au top-100 de chaque flux.
# Un déficit d'import massif y figure toujours ; les déficits marginaux (hors
# top-100) restent tolérés — l'objectif est d'écarter les cas structurels et
# flagrants, pas les demi-teintes.
_NATIONAL_DEMAND_MIN_IMPORT_USD = 20_000_000
_NATIONAL_DEMAND_NET_RATIO = 2.0


async def _national_net_position(exporter_iso3: str, year: int) -> Dict[str, Dict[str, float]]:
    """
    Position commerciale nette du PAYS EXPORTATEUR lui-même, par sous-position
    SH6 : ``{hs6: {"exports": usd, "imports": usd}}`` (top-100 de chaque flux,
    OEC/BACI). Alimente le garde-fou « besoin national » (facteur 5, voir les
    constantes ci-dessus). Dégradation silencieuse (dict vide) hors contexte
    réseau : le garde-fou ne bloque alors aucun flux (fail-open), il ne peut
    qu'écarter sur preuve d'un déficit national réel.
    """

    async def _values(flow: str) -> List[Dict]:
        try:
            if flow == "imports":
                return await real_trade_service.get_oec_imports(
                    exporter_iso3, year=year, limit=100, hs_level="HS6"
                )
            return await real_trade_service.get_oec_exports(
                exporter_iso3, year=year, limit=100, hs_level="HS6"
            )
        except Exception:  # pragma: no cover
            return []

    exports, imports = await asyncio.gather(_values("exports"), _values("imports"))
    pos: Dict[str, Dict[str, float]] = {}
    for e in exports or []:
        code = _normalize_hs(e.get("hs_code"))
        if code:
            pos.setdefault(code, {"exports": 0.0, "imports": 0.0})["exports"] += float(
                e.get("trade_value") or 0
            )
    for m in imports or []:
        code = _normalize_hs(m.get("hs_code"))
        if code:
            pos.setdefault(code, {"exports": 0.0, "imports": 0.0})["imports"] += float(
                m.get("trade_value") or 0
            )
    return pos


def _is_national_demand_product(net_position: Dict[str, Dict[str, float]], hs6: str) -> bool:
    """
    True si le pays exportateur est un IMPORTATEUR NET MAJEUR du produit (SH6) :
    sa demande intérieure absorbe et dépasse largement sa production — la
    capacité repérée doit d'abord servir le marché national, elle ne fonde pas
    un flux d'export. Absence de preuve -> False (ne bloque jamais un flux).
    """
    row = net_position.get(_normalize_hs(hs6))
    if not row:
        return False
    imp = row.get("imports", 0.0)
    exp = row.get("exports", 0.0)
    return imp >= _NATIONAL_DEMAND_MIN_IMPORT_USD and imp >= exp * _NATIONAL_DEMAND_NET_RATIO


async def _capacity_driven_flows(
    exporter_iso3: str,
    exporter_name: str,
    year: int,
    min_market_size: int,
    lang: str,
    covered_hs: set,
    import_index: Optional[Dict] = None,
    net_position_loader: Optional[Callable[[], Awaitable[Dict]]] = None,
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

    # Chargée seulement ici (jamais plus tôt) : ce tier a désormais confirmé
    # qu'il a des candidats réels à filtrer, pas seulement une intelligence
    # pays vide. `net_position_loader` (voir get_strategic_flows) mémoïse
    # l'appel OEC pour le partager avec le tiers 3 sans le déclencher pour un
    # pays qui n'atteint jamais ce point (pas d'intelligence industrielle).
    net_position = (
        await net_position_loader()
        if net_position_loader
        else await _national_net_position(exporter_iso3, year)
    )

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

        # Garde-fou « besoin national » (facteur 5) : le pays est lui-même un
        # importateur net majeur de ce SH6 -> capacité de production réelle,
        # mais absorbée par la demande intérieure, aucun excédent exportable.
        if _is_national_demand_product(net_position, hs6):
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

    Deux garde-fous de réalisme (signalés explicitement, jamais silencieux) :

    - **Demande brute vs potentiel réaliste** : ``import_usd`` (demande totale
      du marché, TOUTES origines) est un chiffre macro sans rapport garanti
      avec ce qu'un seul nouvel entrant peut espérer capter. ``potentiel_usd``
      (borné en amont par le plafond de plausibilité — facteur 3/4, une
      fraction de la VA sectorielle) est le chiffre RÉALISTE mis en avant ;
      sans cette distinction, un texte annonçant une capacité de 103 M$
      « suffisante » à côté d'une demande de 176 M$ laisse croire, à tort,
      que ce dernier chiffre est atteignable.
    - **Accessibilité logistique** : une VA sectorielle avérée ne dit rien de
      la capacité à EXPORTER physiquement le volume — un pays enclavé ou mal
      connecté au marché visé (peu de modes de transport opérationnels) a un
      frein réel, indépendant de sa capacité de production, signalé quand
      l'indice d'accessibilité du premier marché est faible.
    """
    sector = evidence.get("isic_label_fr") or "industrie manufacturière"
    va_txt = _fmt_usd_fr(evidence.get("value_added_usd") or 0)
    total_import = sum(m.get("import_usd", 0) or 0 for m in markets)
    total_potential = sum(m.get("potential_usd", 0) or 0 for m in markets)
    top = markets[0] if markets else {}
    top_name = top.get("name") or top.get("iso3", "")
    top_import_txt = _fmt_usd_fr(top.get("import_usd", 0) or 0)
    potential_txt = _fmt_usd_fr(total_potential)

    # « Recensée », pas « suffisante » : la VA UNIDO est un agrégat SECTORIEL
    # (toute la division ISIC, ex. « Produits alimentaires » couvre pain,
    # laitages, huiles... pas seulement le produit visé) — elle documente une
    # activité manufacturière réelle, jamais une preuve d'excédent exportable
    # garanti pour CE produit précis (c'est tout l'objet du plafond ci-dessous).
    anchor = (
        f"{exporter_name} a une activité manufacturière recensée dans « {sector} » "
        f"({va_txt} de valeur ajoutée, UNIDO INDSTAT4 — un agrégat sectoriel, "
        f"pas une mesure dédiée à « {product_name} »), pouvant s'appliquer à sa "
        f"production."
    )
    if len(markets) <= 1:
        demand = (
            f"{top_name} importe {top_import_txt} aujourd'hui (toutes origines) ; "
            f"potentiel de capture RÉALISTE pour {exporter_name}, borné par sa "
            f"capacité documentée : ≈ {potential_txt}."
        )
    else:
        demand = (
            f"{len(markets)} marchés africains importent {_fmt_usd_fr(total_import)} "
            f"au total (premier : {top_name}, {top_import_txt}, toutes origines) ; "
            f"potentiel de capture RÉALISTE pour {exporter_name}, borné par sa "
            f"capacité documentée : ≈ {potential_txt} — pas le total de la demande."
        )
    if has_export_history:
        confidence = (
            f"{exporter_name} exporte déjà ce type de produit, même modestement : "
            f"la ZLECAf ouvre la voie à une montée en puissance régionale."
        )
    else:
        confidence = (
            f"Aucun flux d'export significatif n'existe encore sur ce produit "
            f"précis pour {exporter_name} — l'activité de production est "
            f"recensée, sa conversion en flux commercial reste à amorcer."
        )

    # Accessibilité logistique du premier marché : un frein réel et distinct
    # de la capacité de production — jamais fabriqué, jamais silencieux.
    top_access = top.get("logistics_accessibility") or {}
    transport_note = ""
    if top_access.get("available") and (top_access.get("index") or 0) < 0.35:
        modes = top_access.get("operational_modes")
        feas = top_access.get("cheapest_feasibility")
        modes_txt = f"{modes} mode(s)" if modes is not None else "aucun mode confirmé"
        feas_txt = f", faisabilité {feas}" if feas else ""
        transport_note = (
            f" Accès logistique limité vers {top_name} : {modes_txt} de transport "
            f"opérationnel{feas_txt} — un frein réel à la montée en volume, "
            "indépendant de la capacité de production, à évaluer avant d'investir "
            "dans cette filière."
        )

    return f"{anchor} {demand} {confidence}{transport_note}"


async def _unido_discovered_flows(
    exporter_iso3: str,
    exporter_name: str,
    year: int,
    min_market_size: int,
    lang: str,
    covered_hs: set,
    import_index: Optional[Dict] = None,
    export_history: Optional[set] = None,
    net_position_loader: Optional[Callable[[], Awaitable[Dict]]] = None,
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

    # Chargée seulement ici (jamais plus tôt) : ce tier a désormais confirmé
    # une capacité UNIDO réelle. `net_position_loader` (voir get_strategic_flows)
    # mémoïse l'appel OEC — partagé avec le tiers 2 sans le déclencher pour un
    # pays qui n'atteint jamais ce point (pas de capacité manufacturière).
    net_position = (
        await net_position_loader()
        if net_position_loader
        else await _national_net_position(exporter_iso3, year)
    )

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

        # Garde-fou « besoin national » (facteur 5, voir _is_national_demand_product) :
        # le pays est lui-même un importateur net majeur de ce SH6 -> sa
        # production, même avérée, sert d'abord le marché intérieur.
        if _is_national_demand_product(net_position, hs6):
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
            # Portée de la donnée : la VA UNIDO couvre TOUTE la division ISIC
            # (ex. « Produits alimentaires » = pain, laitages, huiles, sucreries...
            # confondus), pas seulement le produit visé — jamais une mesure de
            # capacité EXCÉDENTAIRE dédiée. C'est précisément pourquoi le potentiel
            # exportable (``potential_usd`` par marché) est plafonné à une fraction
            # de cette VA plutôt que présenté comme équivalent à la demande totale.
            "is_sector_aggregate": True,
            "scope_note": (
                f"Valeur ajoutée de TOUTE la division « {evidence.get('isic_label_fr') or 'du secteur'} », "
                "pas une mesure dédiée à ce produit précis."
            ),
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
    # tiers pilotés par la capacité (évite les doubles appels réseau).
    import_index = await _load_import_index(year)

    # Position commerciale nette du pays exportateur (facteur 5, garde-fou
    # « besoin national ») : chargée PARESSEUSEMENT et mémoïsée. Ni tier 2 ni
    # tier 3 n'a besoin de cet appel OEC (2 requêtes HTTP) si le pays n'a ni
    # intelligence industrielle curée ni capacité UNIDO — un cas fréquent qui
    # ne doit pas payer une latence réseau inutile. `net_position_loader` est
    # partagé aux deux tiers pour qu'un SEUL appel serve les deux, s'ils en
    # ont besoin l'un et l'autre.
    _net_position_cache: List[Dict] = []

    async def net_position_loader() -> Dict:
        if not _net_position_cache:
            _net_position_cache.append(await _national_net_position(exporter_iso3, year))
        return _net_position_cache[0]

    # Tiers 2 — flux curés pilotés par la capacité (champions + projets
    # structurants) : ce que le pays SAIT produire, même si les flux actuels
    # sont modestes.
    flows.extend(
        await _capacity_driven_flows(
            exporter_iso3,
            exporter_name,
            year,
            min_market_size,
            lang,
            covered_hs,
            import_index,
            net_position_loader,
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
            net_position_loader,
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
