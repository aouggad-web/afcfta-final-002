"""
Correspondance ISIC Rev.4 (4 chiffres) <-> SH6 HS 2022
========================================================
Le module OEC utilisé par ce projet est en SH 2022. La correspondance ISIC4
est publiée officiellement par l'UNSD en SH 2017 uniquement, donc nous
CHAÎNONS trois tables sources OFFICIELLES et n'inventons AUCUNE ligne :

1. UNSD — CPC Ver.2.1 <-> ISIC Rev.4
   https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_ISIC4/cpc21-isic4.txt
2. UNSD — SH 2017 <-> CPC Ver.2.1
   https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/cpc21-hs2017.csv
3. WCO — Table I : SH 2022 <-> SH 2017 (codes amendés uniquement)
   https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/correlation-tables-hs-2017-2022.aspx
   (fichier PDF officiel du WCO, extrait en CSV pour cette table)

Chaînage :
- SH2022 -> SH2017 via WCO Table I quand le code SH2022 apparaît dans cette
  table (524 codes SH2022 amendés). Pour les autres codes (~5000), le code
  SH2022 est identique au code SH2017 (aucune modification en 2022), donc
  la correspondance SH2017 -> ISIC4 s'applique directement.
- SH2017 -> CPC2.1 (UNSD)
- CPC2.1 -> ISIC4 (UNSD)

Les 3 fichiers sources sont conservés compressés dans `backend/data/unsd/`
pour traçabilité.

Couverture obtenue : 5595 codes SH6 (édition HS 2022) dont 5014 mappés à
au moins une classe ISIC Rev.4 4 chiffres du secteur manufacturier
(divisions 10-33). 231 codes SH6 correspondent à plusieurs classes ISIC4
(le CPC sous-jacent chevauche plusieurs activités) — la fonction
`isic4_for_hs6` retourne alors la liste complète, sans choix arbitraire.

Ce module ne fait AUCUNE estimation de production, de part de marché ou
de besoin national : il fournit uniquement la correspondance de
nomenclature SH6 (édition HS 2022) <-> ISIC Rev.4 4 chiffres, à utiliser
par les services qui joignent des données de production (ISIC4, ex.
`etl/isic4_idsb_data.py`) à des données commerciales SH6 (ex. OEC, qui
utilise HS 2022).
"""

import csv
import gzip
import os
from collections import defaultdict
from functools import lru_cache
from typing import Dict, List

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "unsd")
_CPC_ISIC4_FILE = os.path.join(_DATA_DIR, "cpc21_isic4.txt.gz")
_CPC_HS2017_FILE = os.path.join(_DATA_DIR, "cpc21_hs2017.csv.gz")
_WCO_HS22_HS17_FILE = os.path.join(_DATA_DIR, "wco_hs2022_hs2017_table1.csv.gz")


@lru_cache(maxsize=1)
def _cpc_to_isic4() -> Dict[str, str]:
    """Table officielle UNSD CPC Ver.2.1 -> ISIC Rev.4 (relation 1:1 par code CPC)."""
    mapping = {}
    with gzip.open(_CPC_ISIC4_FILE, mode="rt", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cpc = row["CPC21code"].strip().strip('"')
            isic = row["ISIC4code"].strip().strip('"')
            mapping[cpc] = isic
    return mapping


@lru_cache(maxsize=1)
def _hs2017_to_isic4() -> Dict[str, List[str]]:
    """
    Table dérivée SH2017 -> liste ISIC4, obtenue en joignant les tables
    officielles UNSD SH2017<->CPC2.1 et CPC2.1<->ISIC4 sur le code CPC.
    """
    cpc_to_isic = _cpc_to_isic4()
    result: Dict[str, set] = defaultdict(set)
    with gzip.open(_CPC_HS2017_FILE, mode="rt", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hs6 = row["HS 2017"].replace(".", "").strip()
            cpc = row["CPC Ver. 2.1"].strip()
            isic = cpc_to_isic.get(cpc)
            if isic:
                result[hs6].add(isic)
    return {hs6: sorted(isics) for hs6, isics in result.items()}


@lru_cache(maxsize=1)
def _wco_hs2022_to_hs2017() -> Dict[str, List[str]]:
    """WCO Table I : codes SH2022 amendés -> codes SH2017 sources."""
    result: Dict[str, set] = defaultdict(set)
    with gzip.open(_WCO_HS22_HS17_FILE, mode="rt", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result[row["hs2022"].strip()].add(row["hs2017"].strip())
    return {k: sorted(v) for k, v in result.items()}


@lru_cache(maxsize=1)
def _hs2022_to_isic4() -> Dict[str, List[str]]:
    """
    Table SH2022 -> liste ISIC4, produite en chaînant :
    - les codes SH2022 amendés (WCO Table I) via leurs HS2017 sources
    - les codes SH2022 inchangés (identiques à leur code SH2017) directement.
    """
    hs2017_to_isic = _hs2017_to_isic4()
    hs2022_to_hs2017 = _wco_hs2022_to_hs2017()

    hs2017_touched = {h17 for h17s in hs2022_to_hs2017.values() for h17 in h17s}
    hs2022_amended = set(hs2022_to_hs2017.keys())

    result: Dict[str, set] = defaultdict(set)
    for h22, h17s in hs2022_to_hs2017.items():
        for h17 in h17s:
            for isic in hs2017_to_isic.get(h17, ()):
                result[h22].add(isic)
    for h17, isics in hs2017_to_isic.items():
        if h17 in hs2022_amended or h17 in hs2017_touched:
            continue  # HS2017 code was reallocated to a different HS2022 code
        # Unchanged in HS2022 -> same code, keep the mapping
        for isic in isics:
            result[h17].add(isic)
    return {hs6: sorted(isics) for hs6, isics in result.items()}


@lru_cache(maxsize=1)
def _isic4_to_hs2022() -> Dict[str, List[str]]:
    """Table inverse ISIC4 -> liste de codes SH6 HS 2022."""
    result: Dict[str, set] = defaultdict(set)
    for hs6, isics in _hs2022_to_isic4().items():
        for isic in isics:
            result[isic].add(hs6)
    return {isic: sorted(hs6s) for isic, hs6s in result.items()}


def isic4_for_hs6(hs6_code: str) -> List[str]:
    """
    Retourne la (ou les) classe(s) ISIC Rev.4 4 chiffres correspondant à un
    code SH6 (édition HS 2022 telle qu'utilisée par OEC), d'après le
    chaînage officiel WCO -> UNSD -> UNSD. Liste vide si le code n'a pas
    de correspondant.
    """
    hs6 = hs6_code.replace(".", "").strip()
    return _hs2022_to_isic4().get(hs6, [])


def hs6_for_isic4(isic4_code: str) -> List[str]:
    """
    Retourne la liste des codes SH6 (édition HS 2022) correspondant à une
    classe ISIC Rev.4 4 chiffres donnée.
    """
    return _isic4_to_hs2022().get(isic4_code.strip(), [])


def is_manufacturing_isic4(isic4_code: str) -> bool:
    """Vrai si le code ISIC4 appartient à la Section C (Manufacturing, divisions 10-33)."""
    if len(isic4_code) < 2 or not isic4_code[:2].isdigit():
        return False
    return 10 <= int(isic4_code[:2]) <= 33


def coverage_stats() -> Dict:
    """Statistiques de couverture de la correspondance (pour diagnostic/API)."""
    hs_map = _hs2022_to_isic4()
    manuf = {
        hs: isics for hs, isics in hs_map.items() if any(is_manufacturing_isic4(i) for i in isics)
    }
    ambiguous = {hs: isics for hs, isics in hs_map.items() if len(isics) > 1}
    return {
        "hs_edition": "HS 2022 (édition utilisée par OEC)",
        "total_hs6_mapped": len(hs_map),
        "hs6_mapped_to_manufacturing_isic4": len(manuf),
        "hs6_with_multiple_isic4": len(ambiguous),
        "sources": [
            "WCO Table I: HS 2022 <-> HS 2017 (codes amendés)",
            "UNSD SH 2017 <-> CPC Ver.2.1",
            "UNSD CPC Ver.2.1 <-> ISIC Rev.4",
        ],
    }
