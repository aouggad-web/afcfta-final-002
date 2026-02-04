"""
Gemini AI Trade Analysis Routes
API endpoints for AI-powered trade analysis using Google Gemini
NOW WITH REDIS CACHING for optimized performance
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.gemini_trade_service import gemini_trade_service
from services.real_trade_data_service import AFRICAN_COUNTRIES, has_trade_data
from services.redis_cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Trade Analysis"])

# Countries without trade data (occupied territories, etc.)
NO_DATA_COUNTRIES = {
    "ESH": "RASD (Sahara Occidental)",
    "RASD": "RASD (Sahara Occidental)",
    "Sahara": "RASD (Sahara Occidental)",
    "Western Sahara": "RASD (Sahara Occidental)",
    "Sahara Occidental": "RASD (Sahara Occidental)"
}


def check_country_has_data(country_name: str) -> tuple:
    """
    Check if a country has trade data available
    Returns (has_data, country_info) tuple
    """
    name_lower = country_name.lower().strip()
    
    # Check direct match in NO_DATA_COUNTRIES
    for key, value in NO_DATA_COUNTRIES.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return False, {
                "name": value,
                "iso3": "ESH",
                "reason": "Territoire occupé - aucune statistique commerciale disponible dans les bases de données internationales (OEC, COMTRADE, WITS)"
            }
    
    # Check by ISO3
    for iso3, info in AFRICAN_COUNTRIES.items():
        if info.get("name_fr", "").lower() == name_lower or info.get("name_en", "").lower() == name_lower:
            if not info.get("has_trade_data", True):
                return False, {
                    "name": info.get("name_fr", country_name),
                    "iso3": iso3,
                    "reason": info.get("note", "Données non disponibles")
                }
    
    return True, None


@router.get("/opportunities/{country_name}")
async def get_ai_trade_opportunities(
    country_name: str,
    mode: str = Query(default="export", description="Analysis mode: export, import, or industrial"),
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-analyzed trade opportunities for a country
    
    Uses Google Gemini to analyze trade opportunities based on official data sources.
    
    Args:
        country_name: Name of the African country (e.g., "Algeria", "Nigeria", "Kenya")
        mode: Analysis mode
            - export: Find export opportunities
            - import: Find import substitution opportunities  
            - industrial: Analyze value chain transformation opportunities
        lang: Language for the response
    
    Returns:
        AI-generated trade opportunities with sources and reliability indicators
    """
    valid_modes = ["export", "import", "industrial"]
    if mode not in valid_modes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode. Must be one of: {valid_modes}"
        )
    
    # Check if country has trade data
    has_data, no_data_info = check_country_has_data(country_name)
    if not has_data:
        return {
            "country": no_data_info["name"],
            "iso3": no_data_info["iso3"],
            "mode": mode,
            "no_data": True,
            "message": f"Aucune donnée commerciale disponible pour {no_data_info['name']}",
            "reason": no_data_info["reason"],
            "note": "Ce pays est membre de l'Union Africaine et signataire de la ZLECAf, mais n'a pas de statistiques commerciales disponibles dans les bases de données internationales.",
            "opportunities": [],
            "summary": {
                "total_opportunities": 0,
                "total_potential_value": 0,
                "status": "NO_DATA_AVAILABLE"
            },
            "sources": ["OEC", "UN COMTRADE", "WITS - Aucune donnée trouvée"]
        }
    
    try:
        result = await gemini_trade_service.analyze_trade_opportunities(
            country_name=country_name,
            mode=mode,
            lang=lang
        )
        
        if "error" in result and not result.get("opportunities"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI trade analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{country_name}")
async def get_ai_country_profile(
    country_name: str,
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-generated comprehensive economic profile for a country
    
    Includes:
    - Economic indicators (GDP, inflation, unemployment, debt)
    - Development indices (HDI, GAI)
    - Trade summary with top partners and products
    - AfCFTA potential and opportunities
    
    Args:
        country_name: Name of the African country
        lang: Language for the response
    
    Returns:
        Comprehensive country profile with economic and trade data
    """
    try:
        result = await gemini_trade_service.get_country_economic_profile(
            country_name=country_name,
            lang=lang
        )
        
        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating country profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{hs_code}")
async def get_ai_product_analysis(
    hs_code: str,
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-analyzed trade flows for a specific product (HS code)
    
    Provides:
    - Product information and classification
    - African trade flows summary
    - Top African exporters and importers
    - Production capacities
    - Substitution opportunities
    
    Args:
        hs_code: HS code (4 or 6 digits)
        lang: Language for the response
    
    Returns:
        Comprehensive product trade analysis for Africa
    """
    # Validate HS code format
    if not hs_code.isdigit() or len(hs_code) not in [2, 4, 6]:
        raise HTTPException(
            status_code=400,
            detail="HS code must be 2, 4, or 6 digits"
        )
    
    try:
        result = await gemini_trade_service.analyze_product_by_hs_code(
            hs_code=hs_code,
            lang=lang
        )
        
        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance/{country_name}")
async def get_ai_trade_balance(
    country_name: str,
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-analyzed trade balance history for a country
    
    Returns trade balance data (exports, imports, balance) for 2020-2024
    with trend analysis and outlook.
    
    Args:
        country_name: Name of the African country
        lang: Language for the response
    
    Returns:
        Trade balance history with analysis
    """
    try:
        result = await gemini_trade_service.get_trade_balance_analysis(
            country_name=country_name,
            lang=lang
        )
        
        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_ai_service_health():
    """
    Check if the AI service is properly configured and operational
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    has_key = bool(os.environ.get("EMERGENT_LLM_KEY"))
    
    return {
        "status": "operational" if has_key else "not_configured",
        "api_key_configured": has_key,
        "model": "gemini-2.0-flash",
        "provider": "Google Gemini via Emergent LLM"
    }


@router.get("/summary")
async def get_ai_trade_summary(
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-generated comprehensive African trade summary
    
    Used for the "Vue d'ensemble" (Overview) tab.
    Returns aggregate statistics across all African countries.
    
    Args:
        lang: Language for the response
    
    Returns:
        Trade summary with top countries, sectors, and growth metrics
    """
    try:
        result = await gemini_trade_service.get_trade_summary(lang=lang)
        
        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating trade summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/value-chains")
async def get_ai_value_chains(
    sector: str = Query(default=None, description="Specific sector to analyze (coffee, cocoa, cotton, petroleum, minerals, automotive)"),
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-analyzed African value chains
    
    Used for the "Chaînes de Valeur" (Value Chains) tab.
    Analyzes production, transformation, and export opportunities.
    
    Args:
        sector: Optional specific sector (coffee, cocoa, cotton, petroleum, minerals, automotive)
        lang: Language for the response
    
    Returns:
        Value chains analysis with stages, top producers, and AfCFTA opportunities
    """
    valid_sectors = ["coffee", "cocoa", "cotton", "petroleum", "minerals", "automotive", None]
    if sector and sector not in valid_sectors:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector. Must be one of: {[s for s in valid_sectors if s]}"
        )
    
    try:
        result = await gemini_trade_service.get_value_chains_analysis(
            sector=sector,
            lang=lang
        )
        
        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating value chains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def register_routes(app_router):
    """Register AI analysis routes with the main API router"""
    app_router.include_router(router)
