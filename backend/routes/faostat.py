"""
FAOSTAT Routes - Real-time agricultural production data from FAO
Updated for 2024 data
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from ..services.faostat_service import (
    get_production_data,
    get_production_by_country,
    get_top_producers,
    get_production_trends,
    get_commodity_list,
    get_faostat_statistics,
    AFRICAN_COUNTRIES,
    KEY_COMMODITIES
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/faostat")


@router.get("/statistics")
async def faostat_stats():
    """
    Get FAOSTAT service statistics
    
    Returns information about available data, countries, and commodities
    """
    return get_faostat_statistics()


@router.get("/commodities")
async def list_commodities(language: str = Query(default="fr")):
    """
    Get list of tracked agricultural commodities
    
    Args:
        language: Language for names ('fr' or 'en')
    
    Returns:
        List of commodities with codes and names
    """
    return {
        'commodities': get_commodity_list(language),
        'total': len(KEY_COMMODITIES)
    }


@router.get("/production")
async def get_production(
    country: Optional[str] = Query(default=None, description="ISO3 country code (e.g., MAR)"),
    commodity: Optional[str] = Query(default=None, description="FAO commodity code (e.g., 661 for Cocoa)"),
    year: Optional[int] = Query(default=None, description="Year (2021-2024)"),
    language: str = Query(default="fr", description="Language for descriptions")
):
    """
    Get agricultural production data from FAOSTAT
    
    Fetches real-time data from FAO API with caching.
    
    Args:
        country: ISO3 country code (optional, filters by country)
        commodity: FAO commodity code (optional, filters by commodity)
        year: Year (optional, default: all available years)
        language: Language for commodity names ('fr' or 'en')
    
    Returns:
        List of production records with country, commodity, year, and value
    """
    try:
        data = get_production_data(
            country_iso3=country,
            commodity_code=commodity,
            year=year,
            language=language
        )
        
        return {
            'data': data,
            'total_records': len(data),
            'filters': {
                'country': country,
                'commodity': commodity,
                'year': year
            },
            'data_source': 'FAOSTAT 2024'
        }
    except Exception as e:
        logger.error(f"Error fetching FAOSTAT production data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/production/{country_iso3}")
async def get_country_production(
    country_iso3: str,
    language: str = Query(default="fr")
):
    """
    Get all agricultural production data for a specific country
    
    Args:
        country_iso3: ISO3 country code (e.g., MAR, DZA, NGA)
        language: Language for descriptions
    
    Returns:
        Production data organized by commodity with yearly values
    """
    if country_iso3.upper() not in AFRICAN_COUNTRIES:
        raise HTTPException(
            status_code=404, 
            detail=f"Country {country_iso3} not found in African countries list"
        )
    
    try:
        data = get_production_by_country(country_iso3.upper(), language)
        return data
    except Exception as e:
        logger.error(f"Error fetching production for {country_iso3}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-producers/{commodity_code}")
async def get_commodity_top_producers(
    commodity_code: str,
    year: int = Query(default=2023, description="Year"),
    limit: int = Query(default=10, le=54, description="Number of top producers"),
    language: str = Query(default="fr")
):
    """
    Get top African producers for a specific commodity
    
    Args:
        commodity_code: FAO commodity code (e.g., 661 for Cocoa, 656 for Coffee)
        year: Year (default: 2023)
        limit: Number of top producers to return (max: 54)
        language: Language for descriptions
    
    Returns:
        Ranked list of top producing countries
    """
    if commodity_code not in KEY_COMMODITIES:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity code {commodity_code} not found. Use /api/faostat/commodities to see available codes."
        )
    
    try:
        data = get_top_producers(commodity_code, year, limit, language)
        commodity_info = KEY_COMMODITIES[commodity_code]
        
        return {
            'commodity_code': commodity_code,
            'commodity_name': commodity_info.get(f'name_{language}', commodity_info['name_en']),
            'year': year,
            'top_producers': data,
            'data_source': 'FAOSTAT 2024'
        }
    except Exception as e:
        logger.error(f"Error fetching top producers for {commodity_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{country_iso3}/{commodity_code}")
async def get_commodity_trends(
    country_iso3: str,
    commodity_code: str,
    language: str = Query(default="fr")
):
    """
    Get production trends for a specific commodity in a country
    
    Args:
        country_iso3: ISO3 country code
        commodity_code: FAO commodity code
        language: Language for descriptions
    
    Returns:
        Trend analysis with yearly data and change percentage
    """
    if country_iso3.upper() not in AFRICAN_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_iso3} not found in African countries list"
        )
    
    if commodity_code not in KEY_COMMODITIES:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity code {commodity_code} not found"
        )
    
    try:
        data = get_production_trends(country_iso3.upper(), commodity_code, language)
        return data
    except Exception as e:
        logger.error(f"Error fetching trends for {country_iso3}/{commodity_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def list_african_countries():
    """
    Get list of African countries covered by FAOSTAT data
    
    Returns:
        List of ISO3 country codes
    """
    return {
        'countries': AFRICAN_COUNTRIES,
        'total': len(AFRICAN_COUNTRIES)
    }


@router.get("/compare")
async def compare_countries(
    countries: str = Query(..., description="Comma-separated ISO3 codes (e.g., MAR,DZA,EGY)"),
    commodity: str = Query(..., description="FAO commodity code"),
    year: int = Query(default=2023),
    language: str = Query(default="fr")
):
    """
    Compare production of a commodity across multiple countries
    
    Args:
        countries: Comma-separated ISO3 country codes
        commodity: FAO commodity code
        year: Year to compare
        language: Language for descriptions
    
    Returns:
        Comparison data with rankings
    """
    country_list = [c.strip().upper() for c in countries.split(',')]
    
    # Validate countries
    invalid = [c for c in country_list if c not in AFRICAN_COUNTRIES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid country codes: {invalid}"
        )
    
    if commodity not in KEY_COMMODITIES:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity code {commodity} not found"
        )
    
    try:
        results = []
        for iso3 in country_list:
            data = get_production_data(
                country_iso3=iso3,
                commodity_code=commodity,
                year=year,
                language=language
            )
            total_value = sum(r['value'] for r in data)
            results.append({
                'country_iso3': iso3,
                'country_name': data[0]['country_name'] if data else iso3,
                'value': total_value,
                'unit': data[0]['unit'] if data else 'tonnes'
            })
        
        # Sort and rank
        results.sort(key=lambda x: x['value'], reverse=True)
        for i, r in enumerate(results, 1):
            r['rank'] = i
        
        commodity_info = KEY_COMMODITIES[commodity]
        
        return {
            'commodity': commodity_info.get(f'name_{language}', commodity_info['name_en']),
            'year': year,
            'comparison': results,
            'data_source': 'FAOSTAT 2024'
        }
    except Exception as e:
        logger.error(f"Error comparing countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
