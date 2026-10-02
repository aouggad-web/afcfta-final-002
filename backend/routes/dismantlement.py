"""
dismantlement.py
Endpoint: schéma de démantèlement tarifaire ZLECAf officiel
GET /api/dismantlement/{country_iso3}/{hs6}?npf_rate=X&category=A
"""

from typing import Optional

from etl.afcfta_national_offers import check_conformity
from etl.afcfta_schedule import CAT_D, get_dismantlement_schedule
from fastapi import APIRouter, HTTPException, Query
from services.preference_profile_service import get_preference_profile

router = APIRouter(prefix="/dismantlement", tags=["ZLECAf Dismantlement Schedule"])


@router.get("/national-offer-conformity/{country_iso3}")
async def national_offer_conformity(country_iso3: str):
    """
    Vérifie la conformité d'une offre tarifaire nationale ZLECAf (niveau 2)
    au canevas générique (niveau 1, ~90/7/3 — Annexe 1, Article 4).

    Ne rejette ni n'accepte silencieusement une offre : un écart au-delà de
    la tolérance est remonté comme constat à revoir, l'offre officielle
    reste applicable dans tous les cas.
    """
    country = country_iso3.strip().upper()
    if len(country) != 3:
        raise HTTPException(400, detail="country_iso3 doit être un code ISO3 à 3 lettres")
    return check_conformity(country)


@router.get("/preference-profile/{country_iso3}")
async def preference_profile(country_iso3: str):
    """
    Profil de marge préférentielle ZLECAf d'un pays, agrégé depuis son fichier
    tarifaire national: marge moyenne NPF−ZLECAf, part des lignes bénéficiant
    d'une préférence, ventilation par sensibilité et secteurs à plus forte marge.
    """
    country = country_iso3.strip().upper()
    if len(country) != 3:
        raise HTTPException(400, detail="country_iso3 doit être un code ISO3 à 3 lettres")
    result = get_preference_profile(country)
    if "error" in result:
        raise HTTPException(404, detail=result["error"])
    return result


@router.get("/{country_iso3}/{hs6}")
async def dismantlement_schedule(
    country_iso3: str,
    hs6: str,
    npf_rate: float = Query(..., ge=0.0, le=100.0, description="Taux NPF (droit normal) en %"),
    category: Optional[str] = Query(
        None, pattern="^[ABCD]$", description="Catégorie ZLECAf (A/B/C/D). Auto-détectée si absent."
    ),
    hs_code: Optional[str] = Query(
        None,
        description="Code HS à la précision de l'offre tarifaire nationale "
        "(ex: 10 chiffres pour l'Algérie). Sans lui, une offre nationale "
        "publiée à une précision supérieure au SH6 ne peut pas être "
        "appliquée — le canevas générique ZLECAf s'applique.",
    ),
    language: str = Query("fr", pattern="^(fr|en)$"),
):
    """
    Retourne le calendrier de démantèlement tarifaire ZLECAf pour un pays et
    un code HS6 donné.

    Démantèlement à deux niveaux :

    - Niveau 1, canevas générique (Annexe 1 du Protocole sur le Commerce des
      Marchandises, UA 2018, en vigueur depuis le 1er janvier 2021) : parts
      indicatives ~90/7/3 en catégories A/B/C au niveau du chapitre SH2.
      Catégorie A : 5 ans non-PMA / 10 ans PMA. Catégorie B (sensibles) :
      10 ans non-PMA / 13 ans PMA. Catégorie C (exclus) : aucune réduction.
      Catégorie D (déjà à 0%) : consolidé immédiatement.
    - Niveau 2, offre tarifaire nationale officielle : quand le pays en
      dispose (fournir alors ``hs_code`` à la précision publiée), elle
      prime sur le canevas pour la classification de cette ligne.
      ``classification_source`` indique laquelle des deux réponses.
    """
    country = country_iso3.strip().upper()
    if len(country) != 3:
        raise HTTPException(400, detail="country_iso3 doit être un code ISO3 à 3 lettres")

    code = hs6.strip().zfill(6)
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(400, detail="hs6 doit être un code à 6 chiffres")

    result = get_dismantlement_schedule(
        country_iso3=country,
        hs6=code,
        npf_rate=npf_rate,
        category=category,
        hs_code_precise=hs_code,
    )

    # Adapter les labels selon la langue
    label_key = f"category_label_{language}"
    result["category_label"] = result.get(label_key, result.get("category_label_fr"))

    return result
