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
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Mapping projet structurant -> commodité exportable (SH6).
#
# Les projets structurants (data/json/projets_structurants_afrique.json)
# couvrent déjà les 54 pays. Leur champ ``secteur`` est taxonomisé proprement
# (« Mines - Fer », « Mines - Or », « Pétrole - Raffinage »…), ce qui permet de
# DÉRIVER automatiquement une capacité future exportable pour chaque pays, sans
# curation manuelle. Seuls les projets créant une commodité échangeable sont
# retenus ; les infrastructures pures (ports, rail, barrages, numérique) sont des
# facilitateurs logistiques et ne génèrent pas de flux produit.
# --------------------------------------------------------------------------- #

# Correspondance directe par ``secteur`` (prioritaire, taxonomie fiable).
_SECTOR_COMMODITY: Dict[str, Tuple[List[str], str]] = {
    "mines - fer": (["260111", "260112", "720110"], "Minerai de fer & acier"),
    "mines - or": (["710812", "710813"], "Or"),
    "mines - terres rares": (["280530", "284690"], "Terres rares"),
    "mines - lithium": (["282520", "283691"], "Lithium"),
    "mines - cuivre/cobalt": (["260300", "810520", "740200"], "Cuivre & cobalt"),
    "pétrole - raffinage": (["271000"], "Produits pétroliers raffinés"),
}

# Repli par mots-clés (secteur générique « Mines & Industrie » ou parsing titre).
# Frontières de mots (\b) pour les termes courts afin d'éviter les faux positifs
# (« fer » ne doit pas matcher « ferroviaire » ni « transfert »).
_KEYWORD_COMMODITY: List[Tuple[str, List[str], str]] = [
    (r"phosphate", ["251010", "310310", "310530"], "Phosphates & engrais phosphatés"),
    (
        r"\bfer\b|sidérurg|\bacier\b|\bsteel\b|iron ore",
        ["260111", "260112", "720110"],
        "Minerai de fer & acier",
    ),
    (r"terres rares|rare earth", ["280530", "284690"], "Terres rares"),
    (r"lithium", ["282520", "283691"], "Lithium"),
    (r"cuivre|copper", ["260300", "740200"], "Cuivre"),
    (r"cobalt", ["810520", "282200"], "Cobalt"),
    (r"bauxite|alumini|alumine", ["260600", "760110"], "Bauxite & aluminium"),
    (r"manganèse|manganese", ["260200"], "Manganèse"),
    (r"\bzinc\b", ["260800", "790111"], "Zinc"),
    (r"\bnickel\b", ["750110", "260400"], "Nickel"),
    (r"chromite|\bchrome\b", ["261000"], "Chrome"),
    (r"uranium", ["261210", "284410"], "Uranium"),
    (r"potasse|potash", ["310420"], "Potasse"),
    (r"\bor\b|aurifère|\bgold\b", ["710812", "710813"], "Or"),
    (r"gaz naturel|\bgnl\b|\blng\b|liquéfié", ["271111", "271121"], "Gaz naturel"),
    (r"raffin|refinery", ["271000"], "Produits pétroliers raffinés"),
    (r"hydrogène|hydrogen", ["280410"], "Hydrogène vert"),
    (r"ciment|cement|clinker", ["252310", "252329"], "Ciment & clinker"),
    (r"engrais|fertiliz|urée|ammoniac", ["310210", "281410"], "Engrais azotés"),
    (r"cacao|cocoa", ["180100", "180310"], "Cacao & dérivés"),
    (r"\bcoton\b|cotton", ["520100"], "Coton"),
    (r"\bsucre\b|\bsugar\b", ["170199"], "Sucre"),
]

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


def _commodity_for_project(secteur: str, titre: str) -> Optional[Tuple[List[str], str]]:
    """
    Retourne (hs_products, label) pour un projet structurant s'il crée une
    commodité exportable, sinon None (infrastructure/facilitateur pur).
    """
    key = (secteur or "").strip().lower()
    if key in _SECTOR_COMMODITY:
        return _SECTOR_COMMODITY[key]
    text = f"{secteur} {titre}".lower()
    for pattern, codes, label in _KEYWORD_COMMODITY:
        if re.search(pattern, text):
            return codes, label
    return None


def _derive_future_from_projects(country_iso3: str) -> List[Dict]:
    """
    Dérive des capacités futures exportables depuis les projets structurants
    d'un pays (couvre les 54 pays sans curation manuelle).
    """
    derived: List[Dict] = []
    for proj in _load_projects().get(country_iso3.upper(), []):
        secteur = proj.get("secteur", "") or ""
        titre = proj.get("titre", "")
        if not titre or "test" in (secteur or "").lower() or "test" in titre.lower():
            continue
        mapping = _commodity_for_project(secteur, titre)
        if not mapping:
            continue
        codes, label = mapping
        derived.append(
            {
                "linked_project": titre,
                "hs_products": codes,
                "product": label,
                "signal": "High Growth",
                "impact": proj.get("impact", ""),
                "rationale": (
                    f"Le projet structurant « {titre} » ({secteur}) ouvre une capacité "
                    f"future d'export de {label.lower()}, à capter sur les marchés africains "
                    f"important déjà ce produit sous la ZLECAf."
                ),
                "_derived": True,
            }
        )
    return derived


@lru_cache(maxsize=64)
def _merged_intelligence(country_iso3: str) -> Optional[Dict]:
    """
    Vue fusionnée par pays : champions curés + capacités futures (curées PUIS
    dérivées des projets structurants, dédupliquées par projet). Retourne None
    si le pays n'a ni champion curé ni projet exploitable.
    """
    iso3 = country_iso3.upper()
    kb = _load_kb().get(iso3) or {}
    champions = list(kb.get("champions", []))
    future = list(kb.get("future_capacity", []))
    curated_titles = {f.get("linked_project") for f in future}
    for d in _derive_future_from_projects(iso3):
        if d["linked_project"] not in curated_titles:
            future.append(d)
    if not champions and not future:
        return None
    return {
        "country_name_fr": kb.get("country_name_fr"),
        "curated": bool(kb),
        "champions": champions,
        "future_capacity": future,
    }


def has_intelligence(country_iso3: str) -> bool:
    """
    Vrai si le pays a de l'intelligence exploitable : champions curés OU
    capacités futures dérivées de ses projets structurants.
    """
    return _merged_intelligence(country_iso3) is not None


def is_curated(country_iso3: str) -> bool:
    """Vrai uniquement si le pays a une fiche curée à la main (champions nommés)."""
    return country_iso3.upper() in _load_kb()


def get_country_intelligence(country_iso3: str) -> Optional[Dict]:
    """Fiche fusionnée d'un pays (champions + capacités futures) ou None."""
    return _merged_intelligence(country_iso3)


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
    kb = _merged_intelligence(iso3)
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
        # Signal « High Growth » : toute filière de transformation à valeur
        # ajoutée est une opportunité de croissance sous la ZLECAf (la capacité
        # existe, le débouché régional s'ouvre). La provenance opérationnel vs
        # futur reste portée par ``transformation.status`` / ``is_emerging``.
        result["signal"] = "High Growth"

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
    kb = _merged_intelligence(country_iso3)
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
                        "signal": "High Growth",
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
