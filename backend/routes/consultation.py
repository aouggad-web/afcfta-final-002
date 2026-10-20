"""Consultation du tarif, servie par le socle — la même source que POST /calcul.

Une position proposée à l'écran est une position que le calcul sait liquider :
les sous-positions viennent des positions nationales du socle, et de rien
d'autre. L'ancien service fusionnait quatre sources (base PostgreSQL, fichier
ETL, crawl, table de nomenclature), dont des codes que le tarif en vigueur ne
publie plus.
"""

from fastapi import APIRouter, HTTPException

from services import socle
from services.designation import texte_designation

router = APIRouter(prefix="/consultation")


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
