"""
Industrial Intelligence Service
================================

Charge la base de connaissance d'intelligence industrielle
(``data/json/industrial_capacity_intelligence.json``) et l'expose sous une
forme indexée par pays et par code SH.

Cette couche fournit le "pourquoi" stratégique qui manque aux seuls flux OEC :
- les *champions industriels* d'un pays (Sorfert, Cevital, Condor…) et leur
  chaîne de transformation (intrant -> procédé -> extrant) ;
- les *capacités futures* adossées aux projets structurants
  (Gara Djebilet, Bled El Hadba…), qui portent le signal « High Growth ».

Le service reste purement lecture/enrichissement : il ne fait aucun appel
réseau et échoue silencieusement (dictionnaires vides) si les fichiers de
données sont absents, afin de ne jamais bloquer le moteur de flux.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Le répertoire de données canonique du dépôt est ``<repo>/data/json`` (soit
# ``backend/../data/json``), là où vivent déjà production_africaine.json et
# projets_structurants_afrique.json.
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "json"
_KB_FILE = _DATA_DIR / "industrial_capacity_intelligence.json"
_PROJECTS_FILE = _DATA_DIR / "projets_structurants_afrique.json"


def _normalize_hs(hs_code: Optional[str]) -> str:
    """Ne conserver que les chiffres d'un code SH (comme production_capacity)."""
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


@lru_cache(maxsize=1)
def _load_kb() -> Dict:
    """Charge la base de connaissance (mémoïsée)."""
    try:
        with open(_KB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # On ignore la clé de métadonnées pour ne garder que les pays.
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except FileNotFoundError:
        logger.warning("Industrial intelligence KB introuvable: %s", _KB_FILE)
        return {}
    except json.JSONDecodeError as exc:  # pragma: no cover - fichier corrompu
        logger.error("Industrial intelligence KB illisible: %s", exc)
        return {}


@lru_cache(maxsize=1)
def _load_projects() -> Dict[str, List[Dict]]:
    """Charge les projets structurants (pour enrichir les capacités futures)."""
    try:
        with open(_PROJECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _project_detail(iso3: str, title: str) -> Optional[Dict]:
    """Retrouve le projet structurant par titre exact pour ce pays."""
    for proj in _load_projects().get(iso3.upper(), []):
        if proj.get("titre") == title:
            return proj
    return None


def has_intelligence(country_iso3: str) -> bool:
    """Vrai si le pays dispose d'une fiche d'intelligence industrielle curée."""
    return country_iso3.upper() in _load_kb()


def get_country_intelligence(country_iso3: str) -> Optional[Dict]:
    """Retourne la fiche brute d'un pays (champions + capacités futures) ou None."""
    return _load_kb().get(country_iso3.upper())


def _hs_matches(product_codes: List[str], hs_code: str) -> Optional[str]:
    """
    Retourne le code catalogue qui matche ``hs_code`` (match par préfixe le plus
    long d'abord : un SH6 exact prime sur un SH4/SH2), ou None.
    """
    code = _normalize_hs(hs_code)
    if not code:
        return None
    best: Optional[str] = None
    for ref in product_codes:
        ref_n = _normalize_hs(ref)
        if not ref_n:
            continue
        # Match bidirectionnel par préfixe : le référentiel SH6 doit pouvoir
        # capter une opportunité donnée en SH6 exact, mais aussi un flux décrit
        # à un niveau plus agrégé (SH4) partageant le même préfixe.
        if code.startswith(ref_n) or ref_n.startswith(code):
            if best is None or len(ref_n) > len(best):
                best = ref_n
    return best


def match_for_hs(country_iso3: str, hs_code: str) -> Dict:
    """
    Cœur du service : pour un (pays, code SH), retourne l'intelligence
    industrielle applicable.

    Structure retournée::

        {
          "available": bool,
          "champion": {... champion opérationnel matché ...} | None,
          "future_capacity": {... capacité future matchée + détail projet ...} | None,
          "signal": "High Growth" | "Established" | None,
        }

    - ``champion`` : capacité industrielle opérationnelle produisant ce SH.
    - ``future_capacity`` : projet structurant à venir portant ce SH
      (signal « High Growth »), enrichi du détail du projet.
    """
    iso3 = country_iso3.upper()
    kb = _load_kb().get(iso3)
    result: Dict = {
        "available": False,
        "champion": None,
        "future_capacity": None,
        "signal": None,
    }
    if not kb:
        return result

    # 1) Champion opérationnel (préfixe SH le plus long gagne).
    best_champion = None
    best_len = -1
    for champ in kb.get("champions", []):
        matched = _hs_matches(champ.get("hs_products", []), hs_code)
        if matched is not None and len(matched) > best_len:
            best_champion = champ
            best_len = len(matched)
    if best_champion is not None:
        result["champion"] = best_champion
        result["available"] = True
        result["signal"] = "Established"

    # 2) Capacité future (projet structurant) — prime sur le signal.
    for fut in kb.get("future_capacity", []):
        if _hs_matches(fut.get("hs_products", []), hs_code) is not None:
            enriched = dict(fut)
            detail = _project_detail(iso3, fut.get("linked_project", ""))
            if detail:
                enriched["project_detail"] = {
                    "titre": detail.get("titre"),
                    "secteur": detail.get("secteur"),
                    "statut": detail.get("statut"),
                    "budget": detail.get("budget"),
                    "echeance": detail.get("echeance"),
                    "impact": detail.get("impact"),
                    "source": detail.get("source"),
                }
            result["future_capacity"] = enriched
            result["available"] = True
            result["signal"] = fut.get("signal", "High Growth")
            break

    return result


def priority_commodities(country_iso3: str) -> List[Dict]:
    """
    Liste des commodités prioritaires d'un pays (extrants de ses champions +
    capacités futures), pour la vue agrégée « Priority Commodities ».
    """
    kb = _load_kb().get(country_iso3.upper())
    if not kb:
        return []
    items: List[Dict] = []
    seen = set()
    for champ in kb.get("champions", []):
        for hs in champ.get("hs_products", []):
            key = _normalize_hs(hs)
            if key and key not in seen:
                seen.add(key)
                items.append(
                    {
                        "hs_code": key,
                        "product": champ.get("output_product") or champ.get("name"),
                        "champion": champ.get("name"),
                        "signal": "Established",
                    }
                )
    for fut in kb.get("future_capacity", []):
        for hs in fut.get("hs_products", []):
            key = _normalize_hs(hs)
            if key and key not in seen:
                seen.add(key)
                items.append(
                    {
                        "hs_code": key,
                        "product": fut.get("product"),
                        "champion": fut.get("linked_project"),
                        "signal": fut.get("signal", "High Growth"),
                    }
                )
    return items
