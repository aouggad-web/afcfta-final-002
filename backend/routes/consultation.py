"""Consultation du tarif, servie par le socle — la même source que POST /calcul.

Une position proposée à l'écran est une position que le calcul sait liquider :
les sous-positions viennent des positions nationales du socle, et de rien
d'autre. L'ancien service fusionnait quatre sources (base PostgreSQL, fichier
ETL, crawl, table de nomenclature), dont des codes que le tarif en vigueur ne
publie plus.
"""

import functools
import json
import os
import re
import unicodedata
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Query

from services import socle
from services.designation import texte_designation
from services.formalites import (
    FORMALITES_AUCUNE_PARTICULIERE,
    FORMALITES_DOCUMENTEES,
    FORMALITES_NON_ETABLIES,
    FORMALITES_POSITION_INTROUVABLE,
    RESERVES_FORMALITES,
    SOURCES_EXHAUSTIVES_FORMALITES,
)

router = APIRouter(prefix="/consultation")

DONNEES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _droit_de_douane(position: dict) -> dict:
    """Le droit de douane tel que le socle le porte : un taux, ou l'expression
    d'un droit spécifique, ou rien (« à compléter »)."""
    dd = next((d for d in position.get("droits") or [] if d.get("code") == "DD"), None) or {}
    specifique = dd.get("specifique") or {}
    return {
        "dd_rate": dd.get("taux"),
        "dd_expression": dd.get("expression_brute") or specifique.get("brut"),
    }


@router.get(
    "/{iso3}/sous-positions/{hs6}",
    summary="Positions nationales publiées sous un SH6, lues au socle",
)
def sous_positions(iso3: str, hs6: str):
    try:
        codes = socle.positions_nationales(iso3, hs6)
        positions = socle.charger(iso3)["positions"]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    lignes = []
    for entree in codes:
        position = positions[entree["code"]]
        designation = position.get("designation")
        ligne = {
            "code": entree["code"],
            "national_code": entree["code"],
            "digits": len(entree["code"]),
            "description_fr": texte_designation(designation, "fr"),
            "description_en": texte_designation(designation, "en"),
            **_droit_de_douane(position),
        }
        if position.get("cle_controle"):
            ligne["cle_controle"] = position["cle_controle"]
        lignes.append(ligne)
    return {
        "success": True,
        "country_iso3": iso3.upper(),
        "hs6": socle.normaliser_code(hs6)[:6],
        "total": len(lignes),
        "sub_positions": lignes,
        "source": "socle",
    }


@functools.lru_cache(maxsize=1)
def _libelles_internationaux():
    """Intitulés des positions SH4 (anglais) et libellés SH6 empruntés (français,
    anglais). Ils servent à TROUVER une ligne que le tarif ne désigne que par
    son dernier niveau (« Other ») ; ils ne remplacent jamais sa désignation."""
    with open(os.path.join(DONNEES, "hs4_headings_en.json"), encoding="utf-8") as f:
        sh4 = json.load(f)
    with open(os.path.join(DONNEES, "hs6_designations_fr_en.json"), encoding="utf-8") as f:
        sh6 = json.load(f)["libelles"]
    return sh4, sh6


def _pli(texte: str) -> str:
    """Le texte sans accents ni casse : « Chaussures » se trouve par « chaussure »."""
    decompose = unicodedata.normalize("NFKD", texte or "")
    return "".join(c for c in decompose if not unicodedata.combining(c)).lower()


#: {ISO3: (positions du socle, [(code, français plié, anglais en minuscules)])},
#: borné comme le cache du socle.
_textes = OrderedDict()


def _textes_cherchables(iso3: str, positions: dict) -> list:
    """Les textes de chaque position, préparés une fois par chargement du socle.

    Le français est plié (sans accents) ; l'anglais garde ses accents, pour que
    « thé » ne trouve pas l'article « the »."""
    cle = iso3.upper()
    deja = _textes.get(cle)
    if deja is not None and deja[0] is positions:
        _textes.move_to_end(cle)
        return deja[1]
    sh4, sh6 = _libelles_internationaux()
    textes = []
    for code in sorted(positions):
        designation = positions[code].get("designation")
        libelle = sh6.get(code[:6]) or {}
        francais = _pli(f'{texte_designation(designation, "fr")} {libelle.get("fr") or ""}')
        anglais = (
            f'{texte_designation(designation, "en")} {libelle.get("en") or ""} {sh4.get(code[:4]) or ""}'
        ).lower()
        textes.append((code, francais, anglais))
    _textes[cle] = (positions, textes)
    while len(_textes) > socle._MAX_PAYS_EN_CACHE:
        _textes.popitem(last=False)
    return textes


@router.get(
    "/{iso3}/recherche",
    summary="Positions du tarif par code ou par mots de la désignation, lues au socle",
)
def recherche(iso3: str, q: str = Query(..., min_length=2), limit: int = Query(25, ge=1, le=100)):
    """Un code (« 0902 », « 0902.10 ») cherche les positions qui commencent par
    lui ; des mots cherchent les positions dont la désignation les contient
    tous. Seul le droit de douane du socle accompagne chaque position : le
    total des droits et taxes est celui de POST /calcul, et de lui seul."""
    try:
        positions = socle.charger(iso3)["positions"]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sh4, _sh6 = _libelles_internationaux()
    if re.fullmatch(r"[\d.\s]*\d[\d.\s]*", q):
        prefixe = re.sub(r"\D", "", q)
        trouves = sorted(code for code in positions if code.startswith(prefixe))
    else:
        # Chaque mot doit commencer un mot de la désignation, et tous dans la
        # même langue : « thé vert » ne trouve ni « the » ni « invertebrates ».
        # Les nombres mêlés aux mots (« 87.03 voiture ») bornent le code.
        mots = re.findall(r"\w+", q.lower())
        prefixe = "".join(mot for mot in mots if mot.isdigit())
        mots = [mot for mot in mots if not mot.isdigit() and len(mot) >= 2]
        # Par langue : (débuts de mot, mots entiers, pluriel en -s/-x admis).
        langues = [
            [(re.compile(rf"\b{re.escape(m)}"), re.compile(rf"\b{re.escape(m)}[sx]?\b")) for m in termes]
            for termes in ([_pli(mot) for mot in mots], mots)
        ]
        classes = []
        for code, *textes in _textes_cherchables(iso3, positions) if mots else ():
            if not code.startswith(prefixe):
                continue
            accords = [
                all(entier.search(texte) for _, entier in motifs)
                for motifs, texte in zip(langues, textes)
                if all(debut.search(texte) for debut, _ in motifs)
            ]
            if accords:
                # En tête, les positions où les mots figurent en entier
                # (« thé » avant « théophylline ») ; par code dans chaque groupe.
                classes.append((not any(accords), code))
        trouves = [code for _, code in sorted(classes)]

    lignes = []
    for code in trouves[:limit]:
        position = positions[code]
        designation = position.get("designation")
        lignes.append({
            "code": code,
            "hs6": code[:6],
            "digits": len(code),
            "description_fr": texte_designation(designation, "fr"),
            "description_en": texte_designation(designation, "en"),
            # L'intitulé de la position SH4 situe une ligne que le tarif ne
            # désigne que par son dernier niveau. Les libellés SH6 empruntés ne
            # sont pas affichés : certains portent le niveau national du tarif
            # qui les a fournis (1006.10 « de semence »).
            "intitule_sh4": sh4.get(code[:4]),
            **_droit_de_douane(position),
        })
    return {
        "success": True,
        "country_iso3": iso3.upper(),
        "q": q,
        "total": len(trouves),
        "results": lignes,
        "source": "socle",
    }


@router.get(
    "/{iso3}/formalites/{code}",
    summary="Formalités administratives de la position, lues au socle",
)
def formalites(iso3: str, code: str):
    """LE STATUT ACCOMPAGNE TOUJOURS LA LISTE. Une liste vide ne dit pas
    pourquoi elle l'est : la source peut n'avoir rien publié (non établies),
    ou dire qu'il n'y a rien à présenter (aucune formalité particulière)."""
    iso3 = iso3.upper()
    try:
        position, provenance = socle.position(iso3, code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError:
        position, provenance = None, {}

    liste = (position or {}).get("formalites") or []
    if position is None:
        statut = FORMALITES_POSITION_INTROUVABLE
    elif liste:
        statut = FORMALITES_DOCUMENTEES
    elif position.get("formalites_aucune") or iso3 in SOURCES_EXHAUSTIVES_FORMALITES:
        statut = FORMALITES_AUCUNE_PARTICULIERE
    else:
        statut = FORMALITES_NON_ETABLIES
    return {
        "success": True,
        "country_iso3": iso3,
        "hs_code": provenance.get("code_demande", code),
        "formalities": liste,
        "statut": statut,
        "reserve": RESERVES_FORMALITES.get(statut),
        "source": "socle",
    }
