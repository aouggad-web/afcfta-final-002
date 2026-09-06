"""
Déduplication canonique des indicateurs de production (FAOSTAT / UNIDO / USGS)
==============================================================================

Garde-fou d'ingestion pour ``data/json/production_africaine.json``.

Problème visé
-------------
Deux situations distinctes ne doivent JAMAIS être traitées par une somme
mécanique (double comptage) :

1. **Doublons exacts** — le même point de donnée source émis deux fois
   (re-parse du bulk, zone homonyme résolue deux fois vers le même ISO3,
   réingestion incrémentale). → garder UNE occurrence.
2. **Collisions de libellé FAOSTAT** — deux items FAOSTAT distincts (ancien /
   nouveau nom, ex. ``Groundnuts, excluding shelled`` + ``Groundnuts, with
   shell`` → ``Groundnuts`` ; ``Agrumes`` + ``Oranges`` → ``Citrus fruits``)
   normalisés vers le même ``commodity_label`` décrivent la MÊME mesure
   publiée. → garder UNE valeur, jamais la somme.

Clés canoniques par dimension :

======================  ====================================================
Dimension               Clé d'unicité
======================  ====================================================
agri_faostat            (country_iso3, commodity_code, element_code, year)
agri_faostat (libellé)  (country_iso3, commodity_label, year)
manufacturing_unido     (country_iso3, isic_code ou sector_detail, year)
mining_usgs             (country_iso3, commodity_code, commodity_label, year)
value_added_macro       (country_iso3, indicator_code, year)
======================  ====================================================

Règles de conservation (keep-best, déterministe) :

* ``prefer_official`` : un record officiel (``is_estimation`` falsy) prime sur
  une estimation ;
* à statut égal, la valeur **max** l'emporte — défendable pour des révisions
  FAOSTAT et pour les collisions d'agrégats (``Agrumes`` ⊃ ``Oranges``), et
  jamais inférieure à une somme indue ;
* à valeurs égales, la **première occurrence** reste (ordre FAOSTAT = stable).

Aucune fonction de ce module ne somme des valeurs.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ── Clés canoniques par dimension du dataset production_africaine.json ────────
CANONICAL_KEYS: Dict[str, Tuple[str, ...]] = {
    "agri_faostat": ("country_iso3", "commodity_code", "element_code", "year"),
    "manufacturing_unido": ("country_iso3", "isic_code", "sector_detail", "year"),
    "mining_usgs": ("country_iso3", "commodity_code", "commodity_label", "year"),
    "value_added_macro": ("country_iso3", "indicator_code", "year"),
}

# Clé libellé FAOSTAT : items distincts normalisés vers le même libellé.
AGRI_LABEL_KEY: Tuple[str, ...] = ("country_iso3", "commodity_label", "year")


def dedup_key(record: Dict, key_fields: Sequence[str]) -> Tuple:
    """Clé de déduplication d'un enregistrement (champs manquants → None)."""
    return tuple(record.get(f) for f in key_fields)


def _is_estimation(record: Dict) -> bool:
    return bool(record.get("is_estimation"))


def _prefer(new: Dict, cur: Dict, prefer_official: bool) -> bool:
    """True si ``new`` doit remplacer ``cur`` comme record conservé."""
    if prefer_official and _is_estimation(new) != _is_estimation(cur):
        return not _is_estimation(new)
    new_val = new.get("value")
    cur_val = cur.get("value")
    new_num = isinstance(new_val, (int, float))
    cur_num = isinstance(cur_val, (int, float))
    if new_num != cur_num:
        return new_num  # une valeur mesurée prime sur une absence de valeur
    if new_num and cur_num:
        return new_val > cur_val
    return False


def deduplicate(
    records: List[Dict],
    key_fields: Sequence[str],
    prefer_official: bool = False,
    label: str = "",
) -> Tuple[List[Dict], Dict]:
    """
    Déduplique ``records`` sur ``key_fields`` en gardant le MEILLEUR record de
    chaque clé — jamais de somme. Conserve l'ordre de première apparition.

    Returns:
        (records_dédupliqués, statistiques)
    """
    best: Dict[Tuple, Dict] = {}
    order: List[Tuple] = []
    conflicts: List[Tuple] = []
    for record in records:
        key = dedup_key(record, key_fields)
        if key not in best:
            best[key] = record
            order.append(key)
        else:
            cur = best[key]
            if record.get("value") != cur.get("value"):
                conflicts.append(key)
            if _prefer(record, cur, prefer_official):
                best[key] = record
    kept = [best[k] for k in order]
    stats = {
        "dimension": label,
        "input": len(records),
        "output": len(kept),
        "duplicates_removed": len(records) - len(kept),
        "value_conflicts": len(conflicts),
    }
    if stats["duplicates_removed"]:
        sample = [str(k) for k in conflicts[:5] or order[-3:]]
        logger.warning(
            "production_dedup[%s]: %d doublon(s) retiré(s) sur %d records "
            "(conflits de valeur: %d) — ex: %s",
            label,
            stats["duplicates_removed"],
            len(records),
            stats["value_conflicts"],
            sample,
        )
    return kept, stats


def dedup_agri(records: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Déduplication agriculture FAOSTAT, deux passes :

    1. clé stricte (iso3, code item, élément, année) — doublons d'ingestion ;
    2. libellé (iso3, label, year) — items FAOSTAT anciens/nouveaux normalisés
       vers le même ``commodity_label`` : garder la valeur agrégat (max),
       JAMAIS sommer (ex. arachides coques décortiquées + non décortiquées).
    """
    step1, stats1 = deduplicate(
        records, CANONICAL_KEYS["agri_faostat"], label="agri_faostat_exact"
    )
    step2, stats2 = deduplicate(
        step1, AGRI_LABEL_KEY, label="agri_faostat_label"
    )
    merged_stats = {
        "dimension": "agri_faostat",
        "input": stats1["input"],
        "output": stats2["output"],
        "duplicates_removed": stats1["duplicates_removed"] + stats2["duplicates_removed"],
        "value_conflicts": stats1["value_conflicts"] + stats2["value_conflicts"],
        "steps": [stats1, stats2],
    }
    return step2, merged_stats


def dedup_unido(records: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Déduplication UNIDO sur (iso3, isic, sector_detail, year).

    Un record officiel prime sur une estimation ; à statut égal, valeur max.
    """
    return deduplicate(
        records, CANONICAL_KEYS["manufacturing_unido"], prefer_official=True,
        label="manufacturing_unido",
    )


def dedup_dataset(data: Dict) -> Tuple[Dict, Dict[str, Dict]]:
    """
    Déduplique défensivement toutes les dimensions d'un dataset chargé.

    Ne modifie pas ``data`` en place : retourne une copie dédupliquée + les
    statistiques par dimension (les dimensions inconnues sont copiées telles
    quelles).
    """
    out = dict(data)
    stats: Dict[str, Dict] = {}
    for section in ("agri_faostat", "manufacturing_unido", "mining_usgs", "value_added_macro"):
        records = data.get(section)
        if not isinstance(records, list):
            continue
        if section == "agri_faostat":
            kept, s = dedup_agri(records)
        else:
            kept, s = deduplicate(
                records, CANONICAL_KEYS[section], prefer_official=(section == "manufacturing_unido"),
                label=section,
            )
        out[section] = kept
        stats[section] = s
    return out, stats


def count_duplicates(records: List[Dict], key_fields: Sequence[str]) -> int:
    """Nombre de records en trop (sans modifier la liste) — pour audit."""
    seen: set = set()
    duplicates = 0
    for record in records:
        key = dedup_key(record, key_fields)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates
