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
