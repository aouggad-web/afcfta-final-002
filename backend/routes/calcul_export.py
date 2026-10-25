"""
Droits et taxes à l'EXPORTATION — `POST /calcul/export`.

Un autre impôt sur une autre opération : ce n'est pas un second calcul de
l'importation. Les droits de sortie sont lus au socle (`droits_export` des
positions nationales, voir `build_socle.droits_export_du_fichier`) et liquidés
par le même moteur que `POST /calcul`, avec les mêmes refus : une assiette non
collectée, un taux sans unité ou une quantité manquante rendent la ligne
indisponible et la nomment, jamais un zéro.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import socle
from services.calcul import calculer

AUCUN_DROIT = "AUCUN_DROIT_PUBLIE"

router = APIRouter()
router_couverture = APIRouter()


class DemandeExport(BaseModel):
    pays: str = Field(..., description="Pays d'exportation (ISO3)")
    code_sh: str = Field(..., description="Position nationale du tarif du pays d'exportation")
    valeur: float = Field(..., ge=0, description="Valeur en douane à l'exportation")
    devise: Optional[str] = Field(
        default=None,
        description=(
            "Devise (ISO 4217) de `valeur`. Un droit spécifique publié dans la devise nationale "
            "exige alors `taux_de_change`."
        ),
    )
    quantite: Optional[float] = Field(
        default=None, ge=0, description="Quantité, dans l'unité que nomme le droit spécifique"
    )
    taux_de_change: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Unités de `devise` pour UNE unité de la monnaie du tarif (comme pour `POST /calcul`) : "
            "valeur en USD, droit en dinars → environ 0,32, pas 3,1."
        ),
    )


def _pays_export():
    """Pays dont le socle porte des droits de sortie, et combien de positions."""
    return {
        iso: entree["compteurs"]["positions_export"]
        for iso, entree in socle.manifeste().get("pays", {}).items()
        if entree.get("compteurs", {}).get("positions_export")
    }


@router.post("/calcul/export", summary="Liquider les droits et taxes d'une exportation")
def calcul_export(demande: DemandeExport):
    pays = demande.pays.upper()
    try:
        couverts = _pays_export()
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if pays not in couverts:
        raise HTTPException(
            status_code=404,
            detail=f"{pays} : aucun droit à l'exportation collecté au socle.",
        )
    try:
        position, provenance = socle.position(pays, demande.code_sh)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        code = socle.normaliser_code(demande.code_sh)
        sous = socle.positions_nationales(pays, code) if len(code) == 6 else []
        if sous:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "POSITION_NATIONALE_REQUISE",
                    "message": f"{pays}/{code} : {len(sous)} positions nationales sous ce SH6 — choisir la position.",
                    "positions": sous,
                },
            ) from exc
        raise HTTPException(status_code=404, detail=str(exc).strip('"')) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    droits = position.get("droits_export") or []
    resultat = calculer(
        {**position, "droits": droits},
        demande.valeur,
        quantite=demande.quantite,
        taux_de_change=demande.taux_de_change,
        devise_position=provenance.get("devise_nationale"),
        devise_cif=demande.devise,
    )
    export = resultat["npf"]
    # Valeur et droits de sortie ne s'additionnent pas en un « total à payer ».
    export.pop("total_a_payer", None)
    if not droits:
        # Le tarif collecté ne porte aucun droit de sortie pour la position.
        # Ce que le tarif ne publie pas (redevances hors tarif) n'y est pas.
        export["etat"] = AUCUN_DROIT
    return {
        "pays": pays,
        "position": resultat["position"],
        "valeur": demande.valeur,
        "droits_export_publies": bool(droits),
        "export": export,
        "provenance": provenance,
    }


@router_couverture.get("/calcul/export/pays", summary="Pays dont le socle porte des droits de sortie")
def pays_export():
    try:
        return {"pays": _pays_export()}
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
