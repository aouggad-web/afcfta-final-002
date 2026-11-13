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
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services import socle
from services.calcul import _est_moyenne_statistique, calculer, droits_a_la_date
from services.designation import texte_designation
from services.formalites import (
    FORMALITES_AUCUNE_PARTICULIERE,
    FORMALITES_DOCUMENTEES,
    FORMALITES_NON_ETABLIES,
    FORMALITES_POSITION_INTROUVABLE,
    RESERVES_FORMALITES,
    SOURCES_EXHAUSTIVES_FORMALITES,
)
from services.preference import taux_preferentiels

router = APIRouter(prefix="/consultation")
#: La fiche d'une position (droits, taxes, restrictions) est le module de
#: consultation « reglementation » de la décision d'accès du 09/11/2026 : connexion,
#: puis 5 recherches par mois en formule Découverte (routes/__init__.py). Elle a son
#: propre routeur, comme la couverture du calcul : la garde ne doit pas peser sur
#: les routes que le calculateur partage (sous-positions, recherche, formalités),
#: dont l'usage est déjà compté au calcul.
router_reglementation = APIRouter(prefix="/consultation")

DONNEES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _taux_publie(droit: dict) -> dict:
    """Le taux d'un droit tel que le socle le porte : un taux, ou l'expression
    d'un droit spécifique, ou rien (« à compléter »)."""
    specifique = droit.get("specifique") or {}
    # « 40% or 240c/kg », « 40% + US$0.50/L » : le pourcentage n'est qu'une
    # composante. Le servir comme LE taux afficherait 40 % là où la part
    # spécifique peut l'emporter ; c'est l'expression entière qui se lit.
    deux_composantes = droit.get("taux") is not None and bool(droit.get("specifique"))
    return {
        "taux": None if deux_composantes else droit.get("taux"),
        "expression": droit.get("expression_brute") or specifique.get("brut"),
    }


def _restriction(restriction: dict) -> dict:
    """Une restriction sous une forme unique. La source l'écrit de deux façons
    (Égypte : ``kind`` / ``text_verbatim`` ; Libye : ``type`` / ``verbatim`` /
    ``libelle_fr`` / ``portee``) : lue sous une seule, l'autre devenait une carte
    vide, et une interdiction d'importation ne se voyait pas. Le texte reste celui
    de la source ; seule la forme est unifiée."""
    return {
        "type": restriction.get("type") or restriction.get("kind"),
        "libelle": restriction.get("libelle_fr"),
        "texte": restriction.get("text_verbatim") or restriction.get("verbatim"),
        "portee": restriction.get("portee"),
        "source": restriction.get("source"),
    }


def _droit_de_douane(position: dict) -> dict:
    """Le droit de douane tel que le socle le porte."""
    dd = next((d for d in droits_a_la_date(position.get("droits") or []) if d.get("code") == "DD"), None) or {}
    publie = _taux_publie(dd)
    return {"dd_rate": publie["taux"], "dd_expression": publie["expression"]}


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


def _preference(position: dict, provenance: dict, destination: str, code: str, origine: str):
    """La préférence qu'une origine ouvre sur cette position : un bloc qui dit le
    régime et, quand il est refusé, pourquoi, et ce que chaque ligne devient.

    Le taux de chaque ligne est celui que POST /calcul liquiderait : la table
    ``{code: taux}`` du moteur passe par ``calculer`` lui-même, qui applique la
    règle du plancher (aucun importateur n'invoque un régime plus cher que le
    NPF : KEN vers DZA, la table donne 26,25 % pour un NPF de 5 %, et c'est 5 %
    qui est retenu). Les réécrire ici donnerait deux règles qui divergeraient.
    Aucune valeur en douane : seuls les taux sont lus, jamais un montant."""
    if origine == destination:
        return {"origine": origine, "applique": False, "statut": "MEME_PAYS", "regime": None,
                "libelle_bloc": None, "note": None, "perimetre": None}, {}
    pref = taux_preferentiels(position, destination, origine, code)
    lignes = {}
    if pref.get("taux"):
        resultat = calculer(
            position, 0, taux_preferentiels=pref["taux"],
            devise_position=provenance.get("devise_nationale"), couverture=provenance.get("couverture"),
        )
        for ligne in resultat["preference"]["lignes"]:
            if ligne.get("regime_applique") and ligne["code"] not in lignes:
                lignes[ligne["code"]] = {
                    "regime": ligne["regime_applique"],
                    "taux": ligne.get("taux_pct"),
                    "taux_ecarte": (ligne.get("plancher_npf") or {}).get("taux_preferentiel_ecarte_pct"),
                }
    bloc = {
        "origine": origine,
        "applique": bool(pref.get("applique")),
        "statut": pref.get("statut"),
        "regime": pref.get("regime"),
        "libelle_bloc": pref.get("libelle_bloc"),
        "note": pref.get("note"),
        "perimetre": pref.get("perimetre") or None,
    }
    return bloc, lignes


@router_reglementation.get(
    "/{iso3}/position/{code}",
    summary="Droits, taxes et restrictions publiés pour une position, lus au socle",
)
def fiche_position(
    iso3: str,
    code: str,
    origine: Optional[str] = Query(
        None,
        pattern="^[A-Za-z]{3}$",
        description="Pays d'origine (ISO-3), facultatif : ajoute la préférence qu'il ouvre (ZLECAf, union douanière, zone arabe).",
    ),
):
    """Ce que le tarif publie pour la position, ligne à ligne, sans rien calculer.

    Ni total : le total des droits et taxes est celui de POST /calcul. Sans
    ``origine``, ni taux préférentiel, qui en dépend ; avec elle, ``preference`` dit
    le régime que l'origine ouvre et chaque ligne porte le taux qu'il lui donne.
    Les mesures temporaires (gazettes EAC) et le choix d'un
    usage restent au calcul : ``usages`` nomme les régimes qui en dépendent.
    Un taux que la source ne porte pas reste ``null`` — jamais un zéro — et
    ``couverture`` dit quelles familles la source ne publie pas pour ce pays,
    pour qu'une liste incomplète ne se lise pas comme complète. Une ligne dont
    le taux est une moyenne statistique (WITS/TRAINS) le dit (``base_statistique``),
    comme le calcul : ce n'est pas le droit applicable à une marchandise.
    """
    try:
        position, provenance = socle.position(iso3, code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        # Même réponse que POST /calcul : un SH6 qui porte plusieurs positions
        # nationales n'en désigne aucune, et le choix revient à l'opérateur.
        normalise = socle.normaliser_code(code)
        sous = socle.positions_nationales(iso3, normalise) if len(normalise) == 6 else []
        if sous:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "POSITION_NATIONALE_REQUISE",
                    "message": (
                        f"{iso3.upper()}/{normalise} : {len(sous)} positions nationales "
                        "sous ce SH6 — choisir la position."
                    ),
                    "positions": sous,
                },
            ) from exc
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc

    designation = position.get("designation")
    couverture = provenance.get("couverture") or {}
    niveau = provenance["niveau"]
    preference, preferentiels = (
        _preference(position, provenance, provenance["iso3"], code, origine.upper()) if origine else (None, {})
    )
    # Le code de la ligne servie. À défaut de position nationale à ce code, c'est
    # la ligne du SH6 qui répond : annoncer le code saisi ferait lire, sous
    # « code national », une position que le tarif ne publie pas.
    code_servi = provenance["code_demande"] if niveau == "national" else provenance["code_demande"][:6]
    return {
        "success": True,
        "country_iso3": provenance["iso3"],
        "code": code_servi,
        "niveau": niveau,
        "hs6": position.get("hs6"),
        "chapitre": position.get("chapitre"),
        "unite": position.get("unite"),
        "description_fr": texte_designation(designation, "fr"),
        "description_en": texte_designation(designation, "en"),
        "description_ar": texte_designation(designation, "ar"),
        "droits": [
            {
                "code": droit.get("code"),
                "libelle": droit.get("libelle"),
                "famille": droit.get("famille"),
                **_taux_publie(droit),
                "assiette": droit.get("assiette"),
                "note": droit.get("note"),
                "source": droit.get("source"),
                "base_statistique": _est_moyenne_statistique(droit.get("source")),
                # Mesure de défense commerciale (antidumping, sauvegarde) : le taux
                # existe mais dépend de l'origine, du producteur ou du produit. Servi
                # sans taux, il se lirait « la source n'en publie pas ».
                "conditionnel": bool(droit.get("defense_commerciale")),
                # Ce que l'origine change à cette ligne ; None quand elle n'y change rien.
                "preference": preferentiels.get(droit.get("code")),
            }
            for droit in position.get("droits") or []
        ],
        "restrictions": [_restriction(r) for r in position.get("restrictions") or []],
        # Les régimes que l'usage déclaré peut substituer (Égypte : taxe de Table
        # à la place de la TVA, par exemple). Les lignes ci-dessus sont celles du
        # régime courant ; le calcul applique l'usage choisi.
        "preference": preference,
        "usages": [
            {"code": usage.get("code"), "libelle": usage.get("libelle"), "texte": usage.get("texte")}
            for usage in position.get("usages") or []
        ],
        "couverture": {
            "etat": couverture.get("etat"),
            "motif": couverture.get("motif"),
            "tva": couverture.get("tva"),
        },
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


#: Mots-outils qui disent la langue d'un tarif publié en texte simple.
_MOTS_OUTILS = {
    "fr": {"de", "des", "du", "la", "le", "les", "et", "pour", "autres"},
    "en": {"the", "of", "and", "or", "for", "with", "other"},
}

#: {ISO3: (positions du socle, langue du texte publié, {langue: [(code, texte plié)]})},
#: borné comme le cache du socle.
_textes = OrderedDict()


def _langue_publiee(positions: dict) -> str:
    """La langue des désignations publiées en texte simple, sans indication de
    langue : celle dont les mots-outils dominent dans le tarif."""
    compte = {"fr": 0, "en": 0}
    for position in positions.values():
        designation = position.get("designation")
        if isinstance(designation, str):
            for mot in re.findall(r"\w+", designation.lower()):
                for langue, outils in _MOTS_OUTILS.items():
                    compte[langue] += mot in outils
    return "en" if compte["en"] > compte["fr"] else "fr"


def _textes_cherchables(iso3: str, positions: dict):
    """La langue du texte publié et, par langue, le texte plié de chaque
    position, préparés une fois par chargement du socle.

    Un texte n'est cherché que dans sa langue : la désignation dans cette
    langue (ou le texte publié s'il l'est), le libellé SH6 emprunté dans cette
    langue et, en anglais, l'intitulé SH4."""
    cle = iso3.upper()
    deja = _textes.get(cle)
    if deja is not None and deja[0] is positions:
        _textes.move_to_end(cle)
        return deja[1], deja[2]
    sh4, sh6 = _libelles_internationaux()
    publiee = _langue_publiee(positions)
    textes = {"fr": [], "en": []}
    for code in sorted(positions):
        designation = positions[code].get("designation")
        libelle = sh6.get(code[:6]) or {}
        for langue in textes:
            if isinstance(designation, dict):
                propre = designation.get(langue) or ""
            else:
                propre = designation if langue == publiee and isinstance(designation, str) else ""
            intitule = (sh4.get(code[:4]) or "") if langue == "en" else ""
            textes[langue].append((code, _pli(f"{propre} {libelle.get(langue) or ''} {intitule}")))
    _textes[cle] = (positions, publiee, textes)
    while len(_textes) > socle._MAX_PAYS_EN_CACHE:
        _textes.popitem(last=False)
    return publiee, textes


@router.get(
    "/{iso3}/recherche",
    summary="Positions du tarif par code ou par mots de la désignation, lues au socle",
)
def recherche(
    iso3: str,
    # Borné (constat E2) : une désignation nationale collée tient (jusqu'à
    # ~1 200 caractères au Maroc ; au-delà, seules quelques notes de chapitre
    # recopiées dans la désignation, à Madagascar et en Zambie).
    q: str = Query(..., min_length=2, max_length=2000),
    limit: int = Query(25, ge=1, le=100),
    langue: str = Query("fr", pattern="^(fr|en)$"),
):
    """Un code (« 0902 », « 0902.10 ») cherche les positions qui commencent par
    lui ; des mots cherchent les positions dont la désignation les contient
    tous, dans la langue de l'interface (``langue``). Seul le droit de douane du socle accompagne chaque position : le
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
        # Chaque mot doit commencer un mot du texte dans la langue demandée,
        # sans accents ni casse. Les nombres mêlés aux mots (« 87.03 voiture »)
        # bornent le code.
        mots = re.findall(r"\w+", _pli(q))
        prefixe = "".join(mot for mot in mots if mot.isdigit())
        # Un mot répété ne coûte qu'une fois (tous les mots sont exigés).
        mots = list(dict.fromkeys(mot for mot in mots if not mot.isdigit() and len(mot) >= 2))
        # (début de mot, mot entier — pluriel en -s/-x admis) pour chaque mot.
        motifs = [(re.compile(rf"\b{re.escape(m)}"), re.compile(rf"\b{re.escape(m)}[sx]?\b")) for m in mots]
        classes = []
        for code, texte in _textes_cherchables(iso3, positions)[1][langue] if mots else ():
            if code.startswith(prefixe) and all(debut.search(texte) for debut, _ in motifs):
                # En tête, les positions où les mots figurent en entier
                # (« thé » avant « théophylline ») ; par code dans chaque groupe.
                classes.append((not all(entier.search(texte) for _, entier in motifs), code))
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
        "langue": langue,
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
        # Contrôles à l'exportation publiés pour la position (Afrique du Sud) ;
        # liste vide quand aucun n'est collecté, sans statut propre.
        "formalities_export": (position or {}).get("formalites_export") or [],
        "statut": statut,
        "reserve": RESERVES_FORMALITES.get(statut),
        "source": "socle",
    }
