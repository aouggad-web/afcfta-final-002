"""
Route unique de calcul — chantier L3.

Un point d'entrée, `POST /calcul`, entre la donnée du crawler et le montant
affiché. Il enchaîne quatre gestes et aucun autre : résoudre la position au
socle, établir le périmètre de la préférence, liquider, répondre en disant d'où
vient chaque chiffre.

Ce que cette route ne fait pas, délibérément : aucun repli silencieux vers une
autre source, aucun taux dérivé du NPF par un coefficient, aucune position
voisine servie à la place de celle qui manque. Une indisponibilité est une
réponse, pas une panne à masquer.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import socle
from services.calcul import calculer
from services.preference import taux_preferentiels

logger = logging.getLogger(__name__)
router = APIRouter()


class DemandeCalcul(BaseModel):
    destination: str = Field(..., description="Pays d'importation (ISO-3)")
    origine: Optional[str] = Field(None, description="Pays d'origine (ISO-3)")
    code_sh: str = Field(..., description="Code SH6 ou position nationale")
    valeur_cif: float = Field(..., ge=0, description="Valeur en douane")
    quantite: Optional[float] = Field(
        None, ge=0, description="Requise par les droits spécifiques (poids, litres, unités)"
    )
    taux_de_change: Optional[float] = Field(
        None,
        gt=0,
        description="Requis par les assiettes plafonnées ou spécifiques en devise étrangère",
    )
    devise_cif: Optional[str] = Field(
        None,
        description=(
            "Devise (ISO 4217) de `valeur_cif`. Omise, elle est supposée être "
            "celle du tarif national. Un droit spécifique publié dans une "
            "autre devise que `devise_cif` exige `taux_de_change`, faute de "
            "quoi il reste indisponible plutôt que mélangé à la valeur CIF."
        ),
    )


@router.post("/calcul", summary="Liquider les droits et taxes d'une importation")
def calcul(demande: DemandeCalcul):
    # Route synchrone à dessein : le chargement du socle hache et charge
    # jusqu'à 60 Mo de JSON par pays manqué en cache. FastAPI exécute une
    # route `def` classique dans son bassin de fils ; la déclarer `async def`
    # bloquerait la boucle d'événements — et toutes les requêtes concurrentes
    # du même worker — le temps de ce calcul.
    try:
        position, provenance = socle.position(demande.destination, demande.code_sh)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip('"')) from exc
    except socle.SocleIndisponible as exc:
        # Un socle absent ou périmé ne se contourne pas par une autre source :
        # il rend le service indisponible, et le dit.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    preference = {"applique": False, "statut": "ORIGINE_NON_FOURNIE", "taux": {}}
    if demande.origine:
        preference = taux_preferentiels(
            position, demande.destination, demande.origine, demande.code_sh
        )

    resultat = calculer(
        position,
        demande.valeur_cif,
        quantite=demande.quantite,
        taux_de_change=demande.taux_de_change,
        taux_preferentiels=preference.get("taux") or None,
        devise_position=provenance.get("devise_nationale"),
        devise_cif=demande.devise_cif,
        couverture=provenance.get("couverture"),
    )
    resultat["provenance"] = provenance
    resultat["preference_zlecaf"] = {k: v for k, v in preference.items() if k != "taux"}
    return resultat


@router.get("/calcul/pays", summary="Pays servis par le socle, et leur couverture")
def pays():
    try:
        servis = socle.pays_servis()
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    manifeste = socle.manifeste()
    return {
        "socle_version": manifeste.get("socle_version"),
        "construit_le": manifeste.get("construit_le"),
        "totaux": manifeste.get("totaux"),
        "pays": servis,
    }
