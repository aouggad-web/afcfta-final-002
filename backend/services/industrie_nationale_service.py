"""
Industrie nationale et marchés d'export d'un pays — module Opportunités
=======================================================================
Sert, pour un pays couvert, deux lectures complémentaires :

* **l'industrie par branche** d'après les comptes de l'office statistique
  national (Algérie : ONS, comptes économiques 2021-2024) — production brute,
  valeur ajoutée, part privée, croissance ;
* **les exportations par produit et la demande mondiale** d'après CEPII BACI
  (via l'API OEC) : où le pays vend, qui achète ce produit dans le monde et en
  Afrique, et quelle part le pays y tient.

Les données viennent de fichiers construits et contrôlés hors ligne
(``scripts/build_dza_industrie.py``, ``scripts/build_dza_commerce_baci.py``) ;
ce service ne calcule que des sommes, des parts et des filtres, sans pondération.

GARDE-FOUS « ZÉRO FABRICATION »
--------------------------------
- Chaque valeur porte sa nature : ``officiel`` (publié), ``calcul_officiel``
  (dérivé exactement de l'officiel : VA 2020, conversions en dollars au taux
  moyen de la Banque mondiale) ou ``estimation``. Une estimation porte
  ``is_estimation: true``, sa méthode, ses indicateurs, ses sources, sa
  fourchette et sa confiance ; elle n'est jamais présentée comme une mesure.
- Un pays non couvert renvoie ``available: False`` — jamais une valeur
  empruntée à un autre pays.
- Les « marchés où le pays est absent » sont un filtre explicite (seuils
  renvoyés dans la réponse) sur des flux réels, pas un score.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

RACINE = Path(__file__).resolve().parent.parent.parent
FICHIERS = {
    "DZA": {
        "industrie": RACINE / "data" / "json" / "dza_industrie.json",
        "commerce": RACINE / "data" / "json" / "dza_commerce_baci.json",
    }
}
DESIGNATIONS = RACINE / "backend" / "data" / "hs6_designations_fr_en.json"

#: Filtre « marché où le pays est absent ou marginal » : seuils explicites.
SEUIL_IMPORT_USD = 1_000_000
SEUIL_PART_PCT = 1.0


@lru_cache(maxsize=8)
def _charger(chemin: str) -> Optional[Dict]:
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        logger.warning("Données nationales illisibles (%s) : %s", chemin, e)
        return None


@lru_cache(maxsize=1)
def _designations() -> Dict:
    donnees = _charger(str(DESIGNATIONS)) or {}
    return donnees.get("libelles", {})


@lru_cache(maxsize=1)
def _noms_pays_fr() -> Dict[str, str]:
    """Noms français par ISO3 : pays africains du référentiel, sinon rien."""
    try:
        from services.real_trade_data_service import AFRICAN_COUNTRIES
    except ImportError:  # pragma: no cover — référentiel indisponible
        return {}
    return {iso: info.get("name_fr", "") for iso, info in AFRICAN_COUNTRIES.items()}


@lru_cache(maxsize=1)
def _traductions_pays() -> Dict[str, str]:
    """Nom anglais → nom français, pour les partenaires hors Afrique connus."""
    try:
        from etl.translations import COUNTRY_TRANSLATIONS
    except ImportError:  # pragma: no cover
        return {}
    return {en: fr for fr, en in COUNTRY_TRANSLATIONS.items()}


def pays_couverts() -> List[str]:
    return sorted(FICHIERS)


def _fichier(iso3: str, cle: str) -> Optional[Dict]:
    chemins = FICHIERS.get((iso3 or "").upper())
    if not chemins:
        return None
    return _charger(str(chemins[cle]))


def _non_couvert(iso3: str, lang: str) -> Dict:
    return {
        "available": False,
        "country_iso3": (iso3 or "").upper(),
        "covered_countries": pays_couverts(),
        "message": (
            "Pays non couvert : aucune série nationale n'est intégrée pour ce pays."
            if lang == "fr"
            else "Country not covered: no national series is integrated for this country."
        ),
    }


def libelle_produit(hs6: str, lang: str = "fr", repli: str = "") -> Dict[str, str]:
    """Libellé SH6 emprunté aux tarifs nationaux collectés, avec sa source.

    Le libellé OEC n'est qu'un repli : il est faux pour certains codes (121292,
    les caroubes, y figure comme « Sugar cane »).
    """
    entree = _designations().get(hs6) or {}
    texte = (entree.get(lang) or entree.get("en") or "").lstrip("- ").strip()
    if texte:
        return {
            "libelle": texte,
            "source": entree.get(f"{lang}_source") or entree.get("en_source", ""),
        }
    return {"libelle": repli, "source": "OEC"}


def _nom_pays(iso3: str, nom_en: str, lang: str) -> str:
    if lang != "fr":
        return nom_en
    return _noms_pays_fr().get(iso3) or _traductions_pays().get(nom_en) or nom_en


def _nature(valeur_annee: Dict) -> Dict:
    nature = valeur_annee.get("nature")
    return {
        "nature": nature,
        "is_estimation": nature == "estimation",
    }


# ---------------------------------------------------------------------------
# Industrie par branche
# ---------------------------------------------------------------------------


def industrie(iso3: str, lang: str = "fr") -> Dict:
    donnees = _fichier(iso3, "industrie")
    if not donnees:
        return _non_couvert(iso3, lang)
    meta = donnees["meta"]
    branches = []
    for b in donnees["branches"]:
        annees = {}
        for an, v in b["annees"].items():
            annees[an] = {**v, **_nature(v)}
        branches.append(
            {
                "code": b["code"],
                "libelle": b["libelle_fr"] if lang == "fr" else b["libelle_en"],
                "branche_ons": b["branche_ons"],
                "citi_rev4": b["citi_rev4"],
                "note_citi": b.get("note_citi", ""),
                "annees": annees,
            }
        )
    total = {an: {**v, **_nature(v)} for an, v in donnees["total"].items()}
    return {
        "available": True,
        "country_iso3": iso3.upper(),
        "titre": meta["titre"],
        "natures": meta["natures"],
        "unites": meta["unites"],
        "perimetre": meta["perimetre"],
        "limites": meta["limites"],
        "methode_2025": meta["methode_2025"],
        "taux_change_dzd_usd": meta["taux_change_dzd_usd"],
        "sources": meta["sources"],
        "total": total,
        "branches": branches,
    }


# ---------------------------------------------------------------------------
# Exportations par produit et demande mondiale (BACI)
# ---------------------------------------------------------------------------


def _meta_commerce(donnees: Dict) -> Dict:
    m = donnees["meta"]
    return {
        "source": m["source"],
        "nature": m["nature"],
        "cubes": m["cubes"],
        "unites": m["unites"],
        "champ": m["champ"],
        "limites": m["limites"],
    }


def _part(numerateur: float, denominateur: float) -> Optional[float]:
    return round(numerateur / denominateur * 100, 1) if denominateur else None


def exportations(
    iso3: str,
    lang: str = "fr",
    region: str = "monde",
    limite: int = 30,
    hors_hydrocarbures: bool = False,
) -> Dict:
    """Produits exportés, du plus important au moins important en 2024.

    ``hors_hydrocarbures`` écarte le chapitre 27 (combustibles minéraux), comme la
    définition « hors hydrocarbures » de l'ONS (CTCI 3)."""
    donnees = _fichier(iso3, "commerce")
    if not donnees:
        return _non_couvert(iso3, lang)
    lignes = []
    for hs6, p in donnees["produits"].items():
        if hors_hydrocarbures and hs6.startswith("27"):
            continue
        v24, t24 = (p["exportations"].get("2024") or [0, None])[:2]
        v21 = (p["exportations"].get("2021") or [0])[0]
        afr24 = p["exportations_afrique"].get("2024", 0)
        dm, da = p["demande_monde"].get("2024", 0), p["demande_afrique"].get("2024", 0)
        cle = afr24 if region == "afrique" else v24
        if not cle:
            continue
        lib = libelle_produit(hs6, lang, p["libelle_en"])
        lignes.append(
            {
                "hs6": hs6,
                "libelle": lib["libelle"],
                "libelle_source": lib["source"],
                "exportations_2024_usd": v24,
                "exportations_2024_t": t24,
                "exportations_2021_usd": v21,
                "exportations_afrique_2024_usd": afr24,
                "part_afrique_2024_pct": _part(afr24, v24),
                "demande_monde_2024_usd": dm,
                "part_monde_2024_pct": _part(v24, dm),
                "demande_afrique_2024_usd": da,
                "part_marche_africain_2024_pct": _part(afr24, da),
            }
        )
    cle_tri = "exportations_afrique_2024_usd" if region == "afrique" else "exportations_2024_usd"
    lignes.sort(key=lambda x: -x[cle_tri])
    return {
        "available": True,
        "country_iso3": iso3.upper(),
        "region": region,
        "hors_hydrocarbures": hors_hydrocarbures,
        "annee": 2024,
        "total_produits": len(lignes),
        "produits": lignes[: max(1, min(limite, 400))],
        **_meta_commerce(donnees),
    }


def fiche_produit(
    iso3: str,
    hs6: str,
    lang: str = "fr",
    seuil_import_usd: float = SEUIL_IMPORT_USD,
    seuil_part_pct: float = SEUIL_PART_PCT,
) -> Dict:
    """Exportations d'un produit, ses destinations et les marchés où le pays est absent."""
    donnees = _fichier(iso3, "commerce")
    if not donnees:
        return _non_couvert(iso3, lang)
    code = "".join(c for c in str(hs6) if c.isdigit())[:6]
    p = donnees["produits"].get(code)
    if not p:
        return {
            "available": False,
            "country_iso3": iso3.upper(),
            "hs6": code,
            "message": (
                "Produit hors champ : exportations inférieures à 0,5 M USD chaque année de 2021 à 2024."
                if lang == "fr"
                else "Product out of scope: exports below USD 0.5 M every year from 2021 to 2024."
            ),
            **_meta_commerce(donnees),
        }

    def importateur(ligne):
        k, nom, v24, v19, part = ligne
        return {
            "iso3": k,
            "pays": _nom_pays(k, nom, lang),
            "importations_2024_usd": v24,
            "importations_2019_usd": v19,
            "evolution_2019_2024_pct": _part(v24 - v19, v19) if v19 else None,
            "part_pays_pct": part,
        }

    monde = [importateur(x) for x in p["importateurs_2024"]]
    afrique = [importateur(x) for x in p["importateurs_afrique_2024"]]

    def absents(liste):
        return [
            m
            for m in liste
            if m["importations_2024_usd"] >= seuil_import_usd
            and (m["part_pays_pct"] or 0) < seuil_part_pct
        ]

    lib = libelle_produit(code, lang, p["libelle_en"])
    return {
        "available": True,
        "country_iso3": iso3.upper(),
        "hs6": code,
        "libelle": lib["libelle"],
        "libelle_source": lib["source"],
        "exportations": [
            {"annee": int(an), "valeur_usd": v[0], "tonnes": v[1]}
            for an, v in sorted(p["exportations"].items())
        ],
        "exportations_afrique": [
            {"annee": int(an), "valeur_usd": v}
            for an, v in sorted(p["exportations_afrique"].items())
        ],
        "destinations_2024": [
            {"iso3": k, "pays": _nom_pays(k, n, lang), "valeur_usd": v, "tonnes": q}
            for k, n, v, q in p["destinations_2024"]
        ],
        "demande_monde": [
            {"annee": int(an), "valeur_usd": v} for an, v in sorted(p["demande_monde"].items())
        ],
        "demande_afrique": [
            {"annee": int(an), "valeur_usd": v} for an, v in sorted(p["demande_afrique"].items())
        ],
        "importateurs_monde_2024": monde,
        "importateurs_afrique_2024": afrique,
        "marches_absents": {
            "critere": {
                "importations_2024_min_usd": seuil_import_usd,
                "part_pays_max_pct": seuil_part_pct,
                "note": (
                    "Pays qui importent le produit au-dessus du seuil et où le pays exportateur pèse moins "
                    "que la part indiquée : un filtre sur des flux réels, pas un score."
                    if lang == "fr"
                    else "Countries importing the product above the threshold where the exporting country "
                    "holds less than the stated share: a filter on real flows, not a score."
                ),
            },
            "monde": absents(monde),
            "afrique": absents(afrique),
        },
        **_meta_commerce(donnees),
    }
