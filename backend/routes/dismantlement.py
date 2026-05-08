"""
dismantlement.py
Endpoint: schéma de démantèlement tarifaire ZLECAf officiel
GET /api/dismantlement/{country}/{hs6}?npf_rate=X&category=A
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from etl.afcfta_schedule import get_dismantlement_schedule, LDC_COUNTRIES, CAT_A, CAT_B, CAT_C, CAT_D

router = APIRouter(prefix="/dismantlement", tags=["ZLECAf Dismantlement Schedule"])


@router.get("/{country_iso3}/{hs6}")
async def dismantlement_schedule(
    country_iso3: str,
    hs6: str,
    npf_rate: float = Query(..., ge=0.0, le=100.0, description="Taux NPF (droit normal) en %"),
    category: Optional[str] = Query(None, pattern="^[ABCD]$",
                                    description="Catégorie ZLECAf (A/B/C/D). Auto-détectée si absent."),
    language: str = Query("fr", pattern="^(fr|en)$"),
):
    """
    Retourne le calendrier officiel de démantèlement tarifaire ZLECAf
    pour un pays et un code HS6 donné.

    Le schéma suit l'Annexe 1 du Protocole sur le Commerce des Marchandises
    (Union Africaine, 2018), en vigueur depuis le 1er janvier 2021.

    - Catégorie A (90% des lignes): 5 ans non-PMA / 10 ans PMA
    - Catégorie B (7% — sensibles): 10 ans non-PMA / 13 ans PMA
    - Catégorie C (3% — exclus): aucune réduction
    - Catégorie D (déjà à 0%): consolidé immédiatement
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
    )

    # Adapter les labels selon la langue
    label_key = f"category_label_{language}"
    result["category_label"] = result.get(label_key, result.get("category_label_fr"))

    return result


@router.get("/summary/{country_iso3}")
async def country_dismantlement_summary(country_iso3: str):
    """
    Résumé du statut ZLECAf d'un pays:
    - PMA ou non-PMA
    - Durées de libéralisation par catégorie
    - Année actuelle d'implémentation
    """
    from etl.afcfta_schedule import (
        CURRENT_IMPLEMENTATION_YEAR, CURRENT_YEAR,
        AFCFTA_EIF_YEAR, REDUCTION_YEARS
    )

    country = country_iso3.strip().upper()
    is_ldc = country in LDC_COUNTRIES
    group = "ldc" if is_ldc else "non_ldc"
    years = REDUCTION_YEARS[group]

    return {
        "country_iso3": country,
        "is_ldc": is_ldc,
        "status_label": "PMA (Pays Moins Avancé)" if is_ldc else "Non-PMA",
        "eif_year": AFCFTA_EIF_YEAR,
        "current_calendar_year": CURRENT_YEAR,
        "current_implementation_year": CURRENT_IMPLEMENTATION_YEAR,
        "liberalization_schedule": {
            "category_a": {
                "description_fr": "Libéralisation normale (90% des lignes)",
                "duration_years": years[CAT_A],
                "target_year": AFCFTA_EIF_YEAR + years[CAT_A] - 1,
                "status": "complété" if CURRENT_IMPLEMENTATION_YEAR >= years[CAT_A] else "en cours",
            },
            "category_b": {
                "description_fr": "Produits sensibles (7% des lignes)",
                "duration_years": years[CAT_B],
                "target_year": AFCFTA_EIF_YEAR + years[CAT_B] - 1,
                "status": "complété" if CURRENT_IMPLEMENTATION_YEAR >= years[CAT_B] else "en cours",
            },
            "category_c": {
                "description_fr": "Produits exclus (3% des lignes)",
                "duration_years": None,
                "target_year": None,
                "status": "exclus",
            },
        },
    }
