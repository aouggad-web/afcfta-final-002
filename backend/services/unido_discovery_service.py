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

Le service est purement lecture : il lit la valeur ajoutée UNIDO via
``production_data`` (source d'autorité) et ne fait aucun appel réseau. Il
échoue silencieusement (index vide) si les données sont absentes, afin de ne
jamais bloquer le moteur de flux.
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
# Corroboration par l'INTRANT (production réelle FAOSTAT/USGS) pour les SH4 où
# la seule valeur ajoutée de division ISIC est trop grossière pour justifier le
# produit précis.
#
# Cas constaté : la division ISIC 10 « Manufacture of food products » couvre
# aussi bien la torréfaction café/thé que la transformation laitière — deux
# filières industrielles sans rapport, aux intrants et équipements totalement
# différents. Un pays dont la VA « alimentaire » vient du café (ex. Burundi,
# 191,6 M$, essentiellement café/thé) hérite alors à tort d'une capacité
# laitière plausible sur le seul critère de la division, ce qui a fait
# émerger un flux fictif de lait en poudre Burundi -> Algérie à 246,6 M$ —
# supérieur à TOUT le secteur alimentaire burundais, et sans rapport avec sa
# collecte de lait cru réelle (~40 500 t/an FAOSTAT 2024, en repli). Vérifié :
# le marché laitier burundais total (essentiellement UHT frais, un seul
# opérateur, Modern Dairy Burundi) est projeté à ~73 M$ à horizon 2028 — la
# filière poudre de lait industrielle n'existe pas.
#
# Avant d'admettre un SH4 laitier comme candidat, on exige donc une collecte
# de lait cru (FAOSTAT, commodité « Cattle milk ») au-dessus d'un plancher.
# 300 000 t/an est un repère grossier (delta net entre le Burundi ~40 000 t et
# des producteurs laitiers établis comme le Nigeria ~528 000 t ou le Mali
# ~307 000 t) — pas un seuil calibré finement, mais suffisant pour écarter les
# cas manifestement disproportionnés comme celui constaté.
_DAIRY_HS4 = {"0402", "0406"}
_MIN_RAW_MILK_TONNES = 300_000


@lru_cache(maxsize=64)
def _has_dairy_input(iso3: str) -> bool:
    """Le pays collecte-t-il assez de lait cru pour justifier un SH4 laitier ?"""
    try:
        from production_data import get_agriculture_production
    except Exception:  # pragma: no cover
        return False
    latest_year = None
    latest_value = 0.0
    for rec in get_agriculture_production(country_iso3=iso3):
        if rec.get("commodity_label") != "Cattle milk":
            continue
        year = rec.get("year") or 0
        if latest_year is None or year > latest_year:
            latest_year, latest_value = year, rec.get("value") or 0
    return latest_value >= _MIN_RAW_MILK_TONNES


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
            if hs4 in _DAIRY_HS4 and not _has_dairy_input(iso3):
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
