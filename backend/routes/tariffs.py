"""
Tariffs routes - routes de consultation conservées jusqu'au lot O2-0b :
/hs6-tariffs/code/{hs6} et /tariffs/sub-positions/{cc}/{hs6} (appelées par
CalculatorTab.jsx), /tariffs/detailed-countries. Les autres routes de ce
module, sans appelant, servaient des taux de chapitre ou de repli non sourcés
et ont été retirées (lot O2-0).
"""

from typing import Optional

from etl.country_hs6_detailed import (
    COUNTRY_HS6_DETAILED,
    get_all_sub_positions,
    get_tariff_summary,
    has_varying_rates,
)
from etl.country_tariffs_complete import ISO2_TO_ISO3
from etl.hs6_tariffs import get_hs6_tariff, get_hs6_tariff_rates
from etl.hs_codes_data import get_hs6_code, get_hs_chapters
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# =============================================================================
# HS6 TARIFFS ENDPOINTS
# =============================================================================


@router.get("/hs6-tariffs/code/{hs6_code}")
async def get_hs6_tariff_endpoint(hs6_code: str, language: str = Query("fr")):
    """
    Obtenir les tarifs détaillés pour un code SH6 spécifique
    Inclut taux NPF, taux ZLECAf, et économies potentielles
    """
    tariff = get_hs6_tariff(hs6_code)
    if not tariff:
        hs_info = get_hs6_code(hs6_code, language)
        if hs_info:
            return {
                "code": hs6_code,
                "has_specific_tariff": False,
                "hs_info": hs_info,
                "message": "Pas de tarif SH6 spécifique - utiliser le taux par chapitre",
            }
        raise HTTPException(status_code=404, detail=f"Code SH6 {hs6_code} non trouvé")

    desc_key = f"description_{language}"
    return {
        "code": hs6_code,
        "has_specific_tariff": True,
        "description": tariff.get(desc_key, tariff.get("description_fr")),
        "normal_rate": tariff["normal"],
        "normal_rate_pct": f"{tariff['normal'] * 100:.1f}%",
        "zlecaf_rate": tariff["zlecaf"],
        "zlecaf_rate_pct": f"{tariff['zlecaf'] * 100:.1f}%",
        "savings_pct": (
            round((tariff["normal"] - tariff["zlecaf"]) / tariff["normal"] * 100, 1)
            if tariff["normal"] > 0
            else 0
        ),
        "chapter": hs6_code[:2],
        "chapter_name": get_hs_chapters().get(hs6_code[:2], {}).get(language, ""),
    }


# =============================================================================
# DETAILED TARIFFS WITH SUB-POSITIONS ENDPOINTS
# =============================================================================


@router.get("/tariffs/sub-positions/{country_code}/{hs6_code}")
async def get_all_sub_positions_endpoint(country_code: str, hs6_code: str):
    """Obtenir toutes les sous-positions nationales pour un code SH6"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()

    sub_positions = get_all_sub_positions(iso3, hs6_code)
    has_varying = has_varying_rates(iso3, hs6_code)
    summary = get_tariff_summary(iso3, hs6_code)

    return {
        "country_code": iso3,
        "hs6_code": hs6_code,
        "has_sub_positions": len(sub_positions) > 0,
        "has_varying_rates": has_varying,
        "summary": summary,
        "sub_positions": sub_positions,
    }


@router.get("/tariffs/detailed-countries")
async def get_detailed_countries_list():
    """Liste des pays avec tarifs détaillés (sous-positions nationales) disponibles"""
    return {
        "countries": list(COUNTRY_HS6_DETAILED.keys()),
        "count": len(COUNTRY_HS6_DETAILED),
        "description": "Pays avec sous-positions nationales (8-12 chiffres) disponibles",
    }
