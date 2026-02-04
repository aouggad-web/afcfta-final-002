"""
Trade Substitution Analysis Routes
API endpoints for analyzing intra-African trade substitution opportunities
Uses REAL data from OEC API
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

# Import real services only (OEC data)
from services.real_substitution_service import real_substitution_service
from services.real_trade_data_service import AFRICAN_COUNTRIES, get_country_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/substitution", tags=["Trade Substitution Analysis"])


@router.get("/countries")
async def get_available_countries(
    lang: str = Query(default="fr", description="Language for country names (fr/en)")
):
    """
    Get list of available African countries for analysis
    """
    countries = []
    for iso3, info in AFRICAN_COUNTRIES.items():
        countries.append({
            "iso3": iso3,
            "name": info.get(f"name_{lang}", info.get("name_en", iso3)),
            "oec_id": info.get("oec", "")
        })
    
    countries.sort(key=lambda x: x["name"])
    
    return {
        "total": len(countries),
        "countries": countries
    }


@router.get("/opportunities/import/{country_iso3}")
async def get_import_substitution_opportunities(
    country_iso3: str,
    year: int = Query(default=2022, description="Year for trade data"),
    min_value: int = Query(default=5000000, description="Minimum import value to consider (USD)"),
    lang: str = Query(default="fr", description="Language for names (fr/en)"),
    use_real_data: bool = Query(default=True, description="Use real OEC data (always true)")
):
    """
    Find import substitution opportunities for a specific African country
    
    This endpoint identifies products that the country currently imports 
    from outside Africa that could be sourced from other AfCFTA countries.
    
    Uses REAL data from OEC (Observatory of Economic Complexity) API.
    """
    try:
        result = await real_substitution_service.find_import_substitution_opportunities(
            country_iso3, year=year, min_value=min_value, lang=lang
        )
        
        # Handle "no_data" response (e.g., RASD - occupied territory)
        if result.get("no_data"):
            return result
        
        if result.get("error") and not result.get("opportunities"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding substitution opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities/export/{country_iso3}")
async def get_export_opportunities(
    country_iso3: str,
    year: int = Query(default=2022, description="Year for trade data"),
    min_market_size: int = Query(default=5000000, description="Minimum market size to consider (USD)"),
    lang: str = Query(default="fr", description="Language for names (fr/en)"),
    use_real_data: bool = Query(default=True, description="Use real OEC data (always true)")
):
    """
    Find export opportunities for a specific African country
    
    This endpoint identifies products that the country produces and could export
    to other AfCFTA countries that currently import from outside Africa.
    
    Uses REAL data from OEC (Observatory of Economic Complexity) API.
    """
    try:
        result = await real_substitution_service.find_export_opportunities(
            country_iso3, year=year, min_market_size=min_market_size, lang=lang
        )
        
        # Handle "no_data" response (e.g., RASD - occupied territory)
        if result.get("no_data"):
            return result
        
        if result.get("error") and not result.get("opportunities"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding export opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def register_routes(app_router):
    """Register substitution routes with the main API router"""
    app_router.include_router(router)
