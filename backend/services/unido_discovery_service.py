"""
UNIDO-driven export-opportunity discovery
==========================================

Moteur de découverte *piloté par les données*, sans curation manuelle.

Principe (la « recherche de niche » demandée) : la valeur ajoutée
manufacturière UNIDO par division ISIC prouve, pays par pays, dans quels
secteurs une capacité industrielle existe réellement. On traduit cette capacité
en **produits SH exportables** (via ``unido_hs_mapping``), puis le moteur
stratégique croise ces produits avec la **demande d'import africaine réelle**
(index OEC). Une opportunité émerge quand les trois se rencontrent ::

    Capacité UNIDO (le pays SAIT produire le secteur)
        ∩  Produit SH de la division (extrant échangeable)
        ∩  Demande d'import africaine (un marché l'achète hors du continent)
    = opportunité d'export « pilotée par la capacité » sous la ZLECAf

À la différence de la base curée (champions nommés : Cevital, OCP, Dangote…),
cette couche se déploie et s'agrandit d'elle-même : dès que les données UNIDO /
commerciales se mettent à jour, les opportunités se recalculent — y compris pour
des pays et des produits jamais curés à la main.

Contrôle de plausibilité — système à facteurs multiples
---------------------------------------------------------
Une VA de division ISIC seule est un signal MACRO, trop grossier pour
justifier un produit SH précis (une division peut mélanger des filières sans
rapport — café/thé et lait sous « alimentaire », par exemple). Ce module
applique donc, avant d'admettre un candidat, une chaîne de facteurs
indépendants et inspectables (voir ``strategic_trade_service`` pour les
facteurs 3-4, appliqués en aval sur les flux) :

1. **Plancher de VA** (``_MIN_SECTOR_VA_USD``) — la division doit peser assez
   pour être une capacité réelle, pas du bruit statistique.
2. **Corroboration par l'intrant** (``_INPUT_REQUIREMENTS`` / rejet dur) —
   pour les produits dont l'intrant primaire ne s'échange pas économiquement à
   l'échelle d'une petite économie (lait, canne, oléagineux, minerai brut), la
   production domestique réelle de cet intrant (FAOSTAT/USGS) doit franchir un
   plancher. Motivé par un bug réel : le Burundi (VA « alimentaire » 191,6 M$,
   en réalité manioc/café) avait hérité d'une fausse capacité laitière,
   produisant un flux fictif de lait en poudre à 246,6 M$ vers l'Algérie —
   supérieur à TOUT son secteur alimentaire. Vérifié sur internet : le marché
   laitier burundais total est projeté à ~73 M$ à horizon 2028, aucune filière
   industrielle exportatrice n'existe.
3. **Plafond de plausibilité VA** (``strategic_trade_service._DISCOVERY_VA_CAP_FRACTION``)
   — le potentiel d'export d'un produit ne peut excéder une fraction de la VA
   réelle de sa division (garde-fou générique, au-delà des produits couverts
   par le facteur 2).
4. **Historique d'export réel** (``strategic_trade_service._export_history_hs4``)
   — un produit jamais exporté par le pays (même en faible volume) obtient un
   plafond de plausibilité plus strict qu'un produit au moins déjà marginalement
   exporté : la capacité de DIVISION ne vaut pas preuve d'export imminent.

Le service reste purement lecture : il lit la valeur ajoutée UNIDO et la
production réelle via ``production_data`` (source d'autorité) et ne fait
aucun appel réseau lui-même. Il échoue silencieusement (index vide / facteur
non concluant) si les données sont absentes, afin de ne jamais bloquer le
moteur de flux.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List

from services import unido_hs_mapping as hsmap

logger = logging.getLogger(__name__)

# Plancher de valeur ajoutée d'un secteur pour être jugé « capacité réelle ».
# 15 M$ laisse passer les petites économies (dont le secteur phare tourne autour
# de 20-70 M$) tout en écartant le bruit résiduel.
_MIN_SECTOR_VA_USD = 15_000_000

# Nombre maximal de secteurs retenus par pays (les plus intenses en valeur
# ajoutée). Borne la combinatoire produit et concentre la découverte sur les
# filières où la capacité est la plus crédible.
_MAX_SECTORS = 6

# --------------------------------------------------------------------------- #
# FACTEUR 2 — Corroboration par l'INTRANT (production réelle FAOSTAT/USGS) pour
# les SH4 où la seule valeur ajoutée de division ISIC est trop grossière pour
# justifier le produit précis.
#
# Cas constaté ayant motivé ce garde-fou : la division ISIC 10 « Manufacture of
# food products » couvre aussi bien la torréfaction café/thé que la
# transformation laitière — deux filières industrielles sans rapport, aux
# intrants et équipements totalement différents. Un pays dont la VA
# « alimentaire » vient du manioc/café (ex. Burundi, 191,6 M$) hérite alors à
# tort d'une capacité laitière plausible sur le seul critère de la division, ce
# qui a fait émerger un flux fictif de lait en poudre Burundi -> Algérie à
# 246,6 M$ — supérieur à TOUT le secteur alimentaire burundais, et sans rapport
# avec sa collecte de lait cru réelle (~40 500 t/an FAOSTAT 2024, en repli).
# Vérifié sur internet : le marché laitier burundais total (essentiellement
# UHT frais, un seul opérateur, Modern Dairy Burundi) est projeté à ~73 M$ à
# horizon 2028 — la filière poudre de lait industrielle n'existe pas.
#
# Portée DÉLIBÉRÉMENT ÉTROITE — pourquoi ce facteur ne couvre QUE le laitier.
#
# Une première version généralisait ce gate à ~15 SH4 (sucre, huiles, blé,
# coton, métaux de base, raffinage, engrais) sur la même logique « intrant
# domestique requis ». Deux défauts réels l'ont fait échouer en test avant
# même d'atteindre la production :
#
# 1) FAUX NÉGATIFS sur des cas déjà VÉRIFIÉS. Le sucre et les huiles de table
#    en Afrique sont très souvent des industries de RAFFINAGE PORTUAIRE sur
#    matière première IMPORTÉE, pas de transformation d'une culture locale —
#    c'est exactement le modèle du champion curé « Raffinage de sucre
#    (Cevital & filière) » de ce dépôt (sucre de canne brut importé, raffiné
#    à Béjaïa) : l'Algérie ne cultive quasiment pas de canne à sucre. Gater
#    1701 sur la production domestique de canne aurait exclu à tort un cas
#    que j'avais moi-même vérifié sur OEC. Même logique pour la sidérurgie
#    (Tosyali Algérie transforme des billettes/ferrailles importées, pas le
#    minerai de Gara Djebilet, pas encore en production) et le raffinage
#    pétrolier (nombreux pays raffinent du brut importé sans champ pétrolier).
#    Le lait est un cas GENUINEMENT différent : contrairement au sucre, aux
#    huiles ou au minerai, le lait cru ne s'échange quasiment pas à l'échelle
#    internationale pour retransformation (périssable, faible densité de
#    valeur) — une filière laitière industrielle suppose donc, presque
#    toujours, une collecte locale réelle. C'est une propriété du PRODUIT, pas
#    généralisable aux autres intrants agricoles/miniers largement échangés.
#
# 2) UNITÉS HÉTÉROGÈNES entre commodités USGS/EIA, invalidant un seuil
#    uniforme copié depuis les commodités en tonnes : le brut algérien est
#    mesuré en « 1000 b/d » (valeur ~1000) et le gaz naturel en « bcm »
#    (valeur ~100) — un plancher de 1 000 000 (calibré sur des tonnages)
#    aurait exclu à tort l'un des plus gros producteurs de gaz d'Afrique.
#    Calibrer correctement exigerait une conversion par commodité, source
#    d'erreur supplémentaire pour un bénéfice marginal face au filet de
#    sécurité déjà générique du facteur 4 (historique d'export réel).
#
# Le lait reste corroboré parce que (a) sa non-échangeabilité en fait un cas
# structurellement différent et (b) le seuil est en tonnes, cohérent avec la
# seule autre commodité FAOSTAT comparée (pas de conversion d'unité).
# Pour tous les AUTRES produits découverts, les facteurs 3 (plafond VA) et 4
# (historique d'export réel, voir ``strategic_trade_service``) suffisent : ils
# sont fondés sur des données de commerce RÉELLES plutôt que sur une hypothèse
# — par produit — de non-échangeabilité de l'intrant, hypothèse qui s'est
# révélée fausse pour la majorité des cas testés ci-dessus.
_InputRequirement = Dict[str, object]
_INPUT_REQUIREMENTS: Dict[str, _InputRequirement] = {
    # Laitier (0402 poudre/concentré, 0406 fromages) -> lait cru (FAOSTAT).
    # 300 000 t/an : Burundi ~40 000 t (disqualifié, cas réel corrigé) vs
    # Nigeria ~528 000 t, Mali ~307 000 t (producteurs établis).
    "0402": {"dataset": "agri", "commodity": "Cattle milk", "min": 300_000},
    "0406": {"dataset": "agri", "commodity": "Cattle milk", "min": 300_000},
}


@lru_cache(maxsize=512)
def _latest_commodity_value(iso3: str, dataset: str, commodity: str) -> float:
    """Dernière valeur de production réelle (FAOSTAT ou USGS) d'une commodité."""
    try:
        if dataset == "agri":
            from production_data import get_agriculture_production as getter
        else:
            from production_data import get_mining_production as getter
    except Exception:  # pragma: no cover
        return 0.0
    latest_year = None
    latest_value = 0.0
    for rec in getter(country_iso3=iso3):
        if rec.get("commodity_label") != commodity:
            continue
        year = rec.get("year") or 0
        if latest_year is None or year > latest_year:
            latest_year, latest_value = year, rec.get("value") or 0
    return latest_value


def _input_corroborated(iso3: str, hs4: str) -> bool:
    """
    Facteur 2 : le pays produit-il réellement l'intrant nécessaire à ce SH4 ?

    Retourne ``True`` si aucune exigence n'est définie pour ce SH4 (le facteur
    ne s'applique pas — silence, pas un rejet), sinon le résultat de la
    corroboration contre la production réelle. Quand plusieurs commodités sont
    acceptées (ex. brut OU gaz pour le raffinage), une seule suffit.
    """
    req = _INPUT_REQUIREMENTS.get(hs4)
    if not req:
        return True
    commodities = req["commodity"]
    if isinstance(commodities, str):
        commodities = (commodities,)
    threshold = req["min"]
    return any(_latest_commodity_value(iso3, req["dataset"], c) >= threshold for c in commodities)


def _sector_value_added(iso3: str) -> Dict[str, Dict]:
    """
    Valeur ajoutée manufacturière par division ISIC pour un pays (année la plus
    récente disponible). Retourne ``{isic_code: {value, year, isic_label}}``.
    """
    try:
        from production_data import get_manufacturing_production
    except Exception:  # pragma: no cover
        return {}
    out: Dict[str, Dict] = {}
    for rec in get_manufacturing_production(country_iso3=iso3):
        isic = str(rec.get("isic_code") or "")
        val = rec.get("value")
        year = rec.get("year")
        if not isic or not val:
            continue
        # Une division peut avoir plusieurs années : on garde la plus récente.
        prev = out.get(isic)
        if prev is None or (year or 0) > (prev.get("year") or 0):
            out[isic] = {
                "value": val,
                "year": year,
                "isic_label": rec.get("isic_label"),
            }
    return out


@lru_cache(maxsize=64)
def capacity_hs4_index(iso3: str) -> Dict[str, Dict]:
    """
    Index des positions SH4 qu'un pays est en capacité de produire, dérivé de sa
    valeur ajoutée manufacturière UNIDO.

    Retourne ``{hs4: {isic_code, isic_label_fr, value_added_usd, va_year,
    product_label, input, process}}``. Quand plusieurs divisions retenues
    couvrent un même SH4, on garde la division la plus intense en valeur ajoutée.
    """
    iso3 = (iso3 or "").upper()
    sectors = _sector_value_added(iso3)
    if not sectors:
        return {}

    # Secteurs éligibles : au-dessus du plancher, triés par valeur ajoutée, cap.
    eligible = [
        (isic, meta)
        for isic, meta in sectors.items()
        if (meta.get("value") or 0) >= _MIN_SECTOR_VA_USD and isic in hsmap.ISIC_HS
    ]
    eligible.sort(key=lambda kv: kv[1].get("value") or 0, reverse=True)
    eligible = eligible[:_MAX_SECTORS]

    index: Dict[str, Dict] = {}
    for isic, meta in eligible:
        transf = hsmap.transformation_for_isic(isic)
        va = meta.get("value") or 0
        for hs4, label in hsmap.products_for_isic(isic).items():
            # Facteur 2 (voir _INPUT_REQUIREMENTS) : rejet dur si l'intrant
            # requis n'est pas produit domestiquement en quantité plausible.
            if not _input_corroborated(iso3, hs4):
                continue
            prev = index.get(hs4)
            if prev is not None and (prev.get("value_added_usd") or 0) >= va:
                continue
            index[hs4] = {
                "isic_code": isic,
                "isic_label_fr": transf.get("isic_label_fr"),
                "isic_label_en": transf.get("isic_label_en"),
                "value_added_usd": va,
                "va_year": meta.get("year"),
                "product_label": label,
                "input": transf.get("input"),
                "process": transf.get("process"),
                # True si ce SH4 avait une exigence d'intrant VÉRIFIÉE ET
                # satisfaite (preuve plus forte que la seule VA de division) ;
                # False si aucune exigence n'était définie pour ce SH4 (le
                # facteur ne s'applique pas — silence, pas un rejet, mais
                # l'évidence repose alors uniquement sur la VA macro).
                "input_requirement_checked": hs4 in _INPUT_REQUIREMENTS,
            }
    return index


def capacity_for_hs(iso3: str, hs_code: str) -> Dict:
    """
    Évidence de capacité pour un (pays, code SH), au niveau SH4.

    Retourne ``{available, hs4, isic_code, isic_label_fr, value_added_usd,
    product_label, input, process}``. ``available=False`` si aucune division
    manufacturière avérée du pays ne couvre ce produit.
    """
    code = hsmap._norm(hs_code)
    empty = {"available": False}
    if len(code) < 4:
        return empty
    hit = capacity_hs4_index(iso3).get(code[:4])
    if not hit:
        return empty
    return {"available": True, "hs4": code[:4], **hit}


def discover(iso3: str) -> Dict:
    """
    Vue de découverte d'un pays (secteurs UNIDO retenus + produits SH candidats +
    produits phares curés). Utilitaire de diagnostic / exposition API.
    """
    iso3 = (iso3 or "").upper()
    index = capacity_hs4_index(iso3)
    products: List[Dict] = [
        {
            "hs4": hs4,
            "product": meta["product_label"],
            "isic_code": meta["isic_code"],
            "isic_label": meta["isic_label_fr"],
            "value_added_usd": meta["value_added_usd"],
            "input_requirement_checked": meta.get("input_requirement_checked", False),
        }
        for hs4, meta in sorted(
            index.items(), key=lambda kv: kv[1]["value_added_usd"], reverse=True
        )
    ]
    key_products: List[str] = []
    try:
        from production_data import get_manufacturing_key_products

        key_products = get_manufacturing_key_products(iso3)
    except Exception:  # pragma: no cover
        pass
    return {
        "country_iso3": iso3,
        "candidate_products": products,
        "candidate_count": len(products),
        "key_products": key_products,
    }
