"""
Authentic Tariff Routes
API endpoints for authentic African tariff data with sub-positions,
detailed taxes, fiscal advantages, and administrative formalities
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.authentic_tariff_service import (
    get_available_countries,
    get_tariff_line,
    get_sub_positions,
    get_taxes_detail,
    get_fiscal_advantages,
    get_administrative_formalities,
    calculate_import_taxes,
    search_tariff_lines,
    get_country_summary
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authentic-tariffs", tags=["Authentic Tariffs"])


@router.get("/countries")
async def list_available_countries():
    """
    Liste des pays avec données tarifaires authentiques
    
    Returns:
        Liste des pays et leurs statistiques tarifaires
    """
    countries = get_available_countries()
    return {
        "success": True,
        "total": len(countries),
        "countries": countries,
        "data_format": "enhanced_v2",
        "source": "Official African Customs Tariffs"
    }


@router.get("/country/{country_iso3}/summary")
async def get_tariff_summary(country_iso3: str):
    """
    Résumé des données tarifaires d'un pays
    
    Args:
        country_iso3: Code ISO3 du pays (ex: DZA, ETH)
    
    Returns:
        Statistiques et résumé des tarifs
    """
    summary = get_country_summary(country_iso3.upper())
    
    if not summary:
        raise HTTPException(
            status_code=404, 
            detail=f"No tariff data found for country {country_iso3}"
        )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "summary": summary
    }


@router.get("/country/{country_iso3}/line/{hs_code}")
async def get_tariff_line_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir une ligne tarifaire complète avec sous-positions
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        language: Langue pour les descriptions
    
    Returns:
        Ligne tarifaire complète avec taxes, avantages, formalités
    """
    tariff = get_tariff_line(country_iso3.upper(), hs_code)
    
    if not tariff:
        raise HTTPException(
            status_code=404,
            detail=f"No tariff found for {country_iso3}/{hs_code}"
        )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "tariff_line": tariff
    }


@router.get("/country/{country_iso3}/sub-positions/{hs6}")
async def get_sub_positions_endpoint(
    country_iso3: str,
    hs6: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir toutes les sous-positions nationales pour un code HS6
    
    Args:
        country_iso3: Code ISO3 du pays
        hs6: Code HS6 (6 chiffres)
    
    Returns:
        Liste des sous-positions avec leurs taux DD spécifiques
    """
    sub_positions = get_sub_positions(country_iso3.upper(), hs6[:6])
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs6": hs6[:6],
        "total": len(sub_positions),
        "sub_positions": sub_positions,
        "note_fr": "Les sous-positions nationales peuvent avoir des taux DD différents du code HS6 parent",
        "note_en": "National sub-positions may have different DD rates than the parent HS6 code"
    }


@router.get("/country/{country_iso3}/taxes/{hs_code}")
async def get_taxes_detail_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir le détail des taxes pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Détail de chaque taxe (DD, TVA, PRCT, TCS, etc.)
    """
    taxes = get_taxes_detail(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "taxes": taxes
    }


@router.get("/country/{country_iso3}/advantages/{hs_code}")
async def get_fiscal_advantages_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les avantages fiscaux (dont ZLECAf) pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Liste des avantages fiscaux applicables
    """
    advantages = get_fiscal_advantages(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "advantages": advantages
    }


@router.get("/country/{country_iso3}/formalities/{hs_code}")
async def get_formalities_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les formalités administratives requises pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Liste des documents/formalités requis
    """
    formalities = get_administrative_formalities(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "formalities": formalities
    }


@router.post("/calculate")
async def calculate_taxes_endpoint(
    country_iso3: str = Query(..., description="ISO3 country code"),
    hs_code: str = Query(..., description="HS code (6-12 digits)"),
    cif_value: float = Query(..., description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Calculer les taxes d'importation avec données authentiques
    
    Calcule et compare:
    - Régime NPF (Normal)
    - Régime ZLECAf (avec exonérations)
    - Économies réalisées
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        cif_value: Valeur CIF en USD
        language: Langue pour les descriptions
    
    Returns:
        Calcul détaillé NPF vs ZLECAf avec économies
    """
    result = calculate_import_taxes(
        country_iso3=country_iso3.upper(),
        hs_code=hs_code,
        cif_value=cif_value,
        language=language
    )
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/calculate/{country_iso3}/{hs_code}")
async def calculate_taxes_get_endpoint(
    country_iso3: str,
    hs_code: str,
    value: float = Query(10000, description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Version GET du calculateur (pour tests rapides)
    """
    return await calculate_taxes_endpoint(
        country_iso3=country_iso3,
        hs_code=hs_code,
        cif_value=value,
        language=language
    )


@router.get("/search/{country_iso3}")
async def search_tariffs_endpoint(
    country_iso3: str,
    q: str = Query(..., min_length=2, description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, le=100, description="Max results")
):
    """
    Rechercher dans les lignes tarifaires d'un pays
    
    Args:
        country_iso3: Code ISO3 du pays
        q: Requête de recherche (code HS ou description)
        language: Langue
        limit: Nombre max de résultats
    
    Returns:
        Liste des lignes tarifaires correspondantes
    """
    results = search_tariff_lines(
        country_iso3=country_iso3.upper(),
        query=q,
        language=language,
        limit=limit
    )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "query": q,
        "total": len(results),
        "results": results
    }


def register_routes(api_router):
    """Register authentic tariff routes with the main API router"""
    api_router.include_router(router)
