"""
dismantlement.py
Endpoint: schéma de démantèlement tarifaire ZLECAf officiel
GET /api/dismantlement/{country_iso3}/{hs6}?npf_rate=X&category=A
"""

from typing import Optional

from etl.afcfta_national_offers import check_conformity
from etl.afcfta_schedule import (
    CAT_A,
    CAT_B,
    CAT_C,
    CAT_D,
    LDC_COUNTRIES,
    compute_impact_projection,
    get_dismantlement_schedule,
)
from etl.country_tariffs_complete import get_tariff_rate_for_country
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


@router.get("/impact/{country_iso3}/{hs6}")
async def dismantlement_impact(
    country_iso3: str,
    hs6: str,
    trade_value: float = Query(..., gt=0, description="Valeur annuelle échangée, en USD"),
    npf_rate: Optional[float] = Query(
        None,
        ge=0.0,
        le=100.0,
        description="Taux NPF en %. Auto-détecté depuis les données tarifaires si absent.",
    ),
    category: Optional[str] = Query(
        None, pattern="^[ABCD]$", description="Catégorie ZLECAf (A/B/C/D). Auto-détectée si absent."
    ),
    language: str = Query("fr", pattern="^(fr|en)$"),
):
    """
    Simulateur d'impact ZLECAf: projette l'économie de droits de douane
    année par année (et cumulée) pour un flux commercial donné, en suivant
    le calendrier officiel de démantèlement tarifaire.

    Exemple: exporter 1 000 000 USD de produit `hs6` vers `country_iso3`,
    combien d'économie de droits chaque année jusqu'à la pleine libéralisation ?
    """
    country = country_iso3.strip().upper()
    if len(country) != 3:
        raise HTTPException(400, detail="country_iso3 doit être un code ISO3 à 3 lettres")

    # Code HS6 strict: exactement 6 chiffres (l'UI envoie toujours 6). On ne
    # complète pas par des zéros à gauche pour éviter d'accepter un code tronqué
    # (ex: "123" → "000123") qui pointerait vers un mauvais produit.
    code = hs6.strip()
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(400, detail="hs6 doit être un code à 6 chiffres")

    # Taux NPF: fourni par l'appelant, sinon auto-détecté depuis les données tarifaires.
    npf_auto_detected = npf_rate is None
    npf_source = "fourni par l'utilisateur"
    rate = npf_rate
    if rate is None:
        rate_decimal, npf_source = get_tariff_rate_for_country(country, code)
        rate = round(rate_decimal * 100.0, 2)

    schedule_info = get_dismantlement_schedule(country, code, rate, category)
    projection = compute_impact_projection(
        npf_rate=rate,
        category=schedule_info["category"],
        is_ldc=schedule_info["is_ldc"],
        trade_value=trade_value,
    )

    total_saving = projection[-1]["cumulative_saving"] if projection else 0.0
    full_year = next(
        (
            r["calendar_year"]
            for r in projection
            if r["zlecaf_rate"] == 0.0 and schedule_info["category"] != CAT_C
        ),
        None,
    )
    # Économie actuelle dérivée directement du taux ZLECAf en vigueur, robuste
    # aux catégories dont la projection ne couvre pas l'année courante (ex: D).
    current_rate_now = schedule_info["current_zlecaf_rate"]
    annual_saving_now = round(trade_value * (rate - current_rate_now) / 100.0, 2)

    label_key = f"category_label_{language}"
    return {
        "country_iso3": country,
        "hs6": code,
        "trade_value": trade_value,
        "npf_rate": rate,
        "npf_rate_source": npf_source,
        "npf_auto_detected": npf_auto_detected,
        "category": schedule_info["category"],
        "category_label": schedule_info.get(label_key, schedule_info.get("category_label_fr")),
        "is_ldc": schedule_info["is_ldc"],
        "current_implementation_year": schedule_info["current_implementation_year"],
        "current_zlecaf_rate": current_rate_now,
        "annual_saving_now": annual_saving_now,
        "full_liberalization_year": full_year,
        "total_saving_over_schedule": total_saving,
        "projection": projection,
    }


@router.get("/summary/{country_iso3}")
async def country_dismantlement_summary(country_iso3: str):
    """
    Résumé du statut ZLECAf d'un pays:
    - PMA ou non-PMA
    - Durées de libéralisation par catégorie
    - Année actuelle d'implémentation
    """
    from etl.afcfta_schedule import (
        AFCFTA_EIF_YEAR,
        CURRENT_IMPLEMENTATION_YEAR,
        CURRENT_YEAR,
        REDUCTION_YEARS,
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
