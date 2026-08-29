"""
Signal d'assemblage par proxy d'intrants (compresseurs → réfrigérateurs, modules
d'affichage → téléviseurs, etc.)
====================================================================================
Problème : FAOSTAT (agriculture) et USGS (mines) mesurent une production physique
réelle ; UNIDO (INDSTAT4) mesure une valeur ajoutée manufacturière par secteur ISIC,
mais notre ingestion actuelle ne couvre pas les biens d'équipement électroménager
(réfrigérateurs, téléviseurs...) — aucune institution ne publie non plus, pour la
plupart des pays africains, un nombre d'UNITÉS assemblées localement. Résultat :
`production_capacity_service` renvoie `available: False` pour ces codes HS et le
module Opportunités perd tout ancrage réel sur ce segment.

Méthode alternative (courante en intelligence économique et douanière) : un pays
qui importe massivement un composant-clé nécessaire à l'assemblage d'un produit fini
(ex. compresseurs HS 841430 pour les réfrigérateurs/climatiseurs, modules
d'affichage HS 852990 pour les téléviseurs) opère très probablement un assemblage
local CKD/SKD de ce produit — c'est le principe même du "component trade" utilisé
par l'OMC/CNUCED pour cartographier les chaînes de valeur mondiales.

Garde-fous « zéro fabrication » :
- Les volumes utilisés sont des flux commerciaux RÉELS (OEC/UN Comtrade), jamais
  inventés ni extrapolés.
- Le résultat est explicitement qualifié de SIGNAL INDIRECT ("input_proxy_estimate"),
  jamais présenté comme une production mesurée — aucun champ ne s'appelle "rang de
  production" ou "part de production" ici.
- Une méthodologie et une mise en garde explicites accompagnent chaque réponse pour
  que le LLM et le frontend ne confondent jamais ce signal avec les données
  FAOSTAT/USGS/UNIDO de `production_capacity_service`.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from services.oec_trade_service import DEFAULT_YEAR, oec_service
from services.real_trade_data_service import real_trade_service

_METHOD_NOTE = (
    "Signal INDIRECT d'assemblage local, dérivé des importations réelles d'un "
    "composant-clé (component trade). Ce n'est PAS une production mesurée : aucune "
    "institution ne publie un volume d'unités assemblées pour ce produit dans la "
    "plupart des pays africains. Un import élevé du composant suggère un "
    "assemblage CKD/SKD local, mais peut aussi refléter un simple usage comme "
    "pièce détachée / après-vente. À présenter comme estimation d'ordre de "
    "grandeur, jamais comme un rang ou une part de production."
)

# output HS4 (produit fini assemblé) -> intrant(s)-clé(s) dont le volume importé
# sert de signal d'assemblage local. Un même intrant peut servir plusieurs sorties
# (ex. les compresseurs alimentent aussi bien réfrigérateurs que climatiseurs).
_INPUT_PROXY_CHAPTERS: Dict[str, Dict] = {
    "8418": {
        "output_label": "Réfrigérateurs, congélateurs et matériel frigorifique",
        "inputs": [
            {
                "hs6": "841430",
                "label": "Compresseurs pour équipement frigorifique",
            }
        ],
    },
    "8415": {
        "output_label": "Machines et appareils pour le conditionnement de l'air",
        "inputs": [
            {
                "hs6": "841430",
                "label": "Compresseurs pour équipement frigorifique",
            }
        ],
    },
    "8528": {
        "output_label": "Téléviseurs et moniteurs",
        "inputs": [
            {
                "hs6": "852990",
                "label": "Parties et modules d'affichage pour appareils de télévision/moniteurs",
            }
        ],
    },
}


def list_proxy_chapters() -> List[Dict]:
    """Univers des codes HS couverts par le proxy d'intrants (pour l'UI)."""
    return [
        {"hs_code": hs4, "output_label": meta["output_label"], "inputs": meta["inputs"]}
        for hs4, meta in _INPUT_PROXY_CHAPTERS.items()
    ]


def _match_proxy(hs_code: str) -> Optional[tuple]:
    clean = "".join(ch for ch in str(hs_code or "") if ch.isdigit())
    for length in (6, 4):
        prefix = clean[:length]
        if len(prefix) == length and prefix[:4] in _INPUT_PROXY_CHAPTERS:
            return prefix[:4], _INPUT_PROXY_CHAPTERS[prefix[:4]]
    if clean[:4] in _INPUT_PROXY_CHAPTERS:
        return clean[:4], _INPUT_PROXY_CHAPTERS[clean[:4]]
    return None


async def _country_input_imports(country_iso3: str, input_hs6: str) -> Dict:
    for year in (DEFAULT_YEAR, DEFAULT_YEAR - 1, DEFAULT_YEAR - 2):
        result = await real_trade_service.get_country_product_imports(
            country_iso3, input_hs6, year=year
        )
        if result.get("available"):
            return result
    return {"available": False}


async def _continental_ranking(input_hs6: str, country_iso3: str, year: Optional[int]) -> Dict:
    try:
        data = await oec_service.get_top_african_importers(input_hs6, year or DEFAULT_YEAR)
    except Exception:
        return {"available": False}
    # get_top_african_importers() renvoie déjà les importateurs africains
    # triés par valeur décroissante dans "data".
    ranked = (data or {}).get("data") or []
    if not ranked:
        return {"available": False}
    total = len(ranked)
    rank = next(
        (
            i + 1
            for i, r in enumerate(ranked)
            if (r.get("country_iso3") or "").upper() == country_iso3
        ),
        None,
    )
    top5 = [
        {"country_iso3": r.get("country_iso3"), "country_name": r.get("country_name")}
        for r in ranked[:5]
    ]
    return {"available": True, "rank": rank, "total_countries": total, "top_importers": top5}


async def estimate_assembly_signal(country_iso3: str, hs_code: str) -> Dict:
    """
    Signal d'assemblage local pour un produit fini (ex. réfrigérateurs, téléviseurs)
    dérivé des importations réelles de son composant-clé. Retourne
    {available: False, reason: "no_proxy_mapping"} si le code HS n'est pas couvert.
    """
    iso3 = (country_iso3 or "").strip().upper()
    match = _match_proxy(hs_code)
    if not match:
        return {"available": False, "reason": "no_proxy_mapping", "hs_code": hs_code}

    output_hs4, meta = match
    input_signals = []
    any_available = False
    for inp in meta["inputs"]:
        imports = await _country_input_imports(iso3, inp["hs6"])
        ranking = (
            await _continental_ranking(inp["hs6"], iso3, imports.get("year"))
            if imports.get("available")
            else {"available": False}
        )
        if imports.get("available"):
            any_available = True
        input_signals.append(
            {
                "input_hs6": inp["hs6"],
                "input_label": inp["label"],
                "country_import_usd": imports.get("import_value_usd"),
                "year": imports.get("year"),
                "source": imports.get("source"),
                "continental_ranking": ranking,
            }
        )

    return {
        "available": any_available,
        "method": "input_proxy_estimate",
        "hs_code": output_hs4,
        "output_label": meta["output_label"],
        "country_iso3": iso3,
        "input_signals": input_signals,
        "methodology": _METHOD_NOTE,
    }
