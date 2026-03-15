"""
API Routes pour les tarifs avec PostgreSQL
Remplace les anciennes routes basées sur les fichiers JSONL
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/postgres-tariffs", tags=["PostgreSQL Tariffs"])

# Lazy import to avoid startup issues if PostgreSQL not ready
_service = None

def get_service():
    global _service
    if _service is None:
        try:
            from services.postgres_tariff_service import get_postgres_tariff_service
            _service = get_postgres_tariff_service()
        except Exception as e:
            logger.warning(f"PostgreSQL service not available: {e}")
            return None
    return _service


@router.get("/countries")
async def get_countries():
    """Liste des pays avec données PostgreSQL"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        countries = service.get_countries()
        return {
            "success": True,
            "total": len(countries),
            "countries": countries
        }
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{iso3}")
async def get_country_info(iso3: str):
    """Informations sur un pays"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        country = service.get_country_info(iso3)
        if not country:
            raise HTTPException(status_code=404, detail=f"Country {iso3} not found")
        
        return {
            "success": True,
            "country": country
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting country {iso3}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{iso3}/sub-positions/{hs6}")
async def get_sub_positions(
    iso3: str, 
    hs6: str, 
    language: str = Query("fr", regex="^(fr|en)$")
):
    """Sous-positions nationales pour un code HS6"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        positions = service.get_sub_positions(iso3, hs6, language)
        return {
            "success": True,
            "country_iso3": iso3.upper(),
            "hs6": hs6,
            "total": len(positions),
            "sub_positions": positions,
            "note": "Data from PostgreSQL - Real national tariff descriptions"
        }
    except Exception as e:
        logger.error(f"Error getting sub-positions for {iso3}/{hs6}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{iso3}/commodity/{code}")
async def get_commodity_details(iso3: str, code: str):
    """Détails complets d'une marchandise"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        details = service.get_commodity_details(iso3, code)
        if not details:
            raise HTTPException(status_code=404, detail=f"Commodity {code} not found")
        
        return {
            "success": True,
            **details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity {iso3}/{code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{iso3}/search")
async def search_commodities(
    iso3: str,
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    language: str = Query("fr", regex="^(fr|en)$")
):
    """Recherche de marchandises par description"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        results = service.search_commodities(iso3, q, limit, language)
        return {
            "success": True,
            "query": q,
            "country_iso3": iso3.upper(),
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching {iso3} for '{q}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_tariffs(
    country_iso3: str = Query(..., description="Country ISO3 code"),
    hs6: str = Query(..., description="HS6 code"),
    value: float = Query(1000, ge=0, description="Goods value")
):
    """Calculer les tarifs pour un code HS6"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        result = service.calculate_tariffs(country_iso3, hs6, value)
        return result
    except Exception as e:
        logger.error(f"Error calculating tariffs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulatory/{iso3}/{hs6}")
async def get_regulatory_details(iso3: str, hs6: str):
    """Détails réglementaires pour un code HS6"""
    service = get_service()
    if not service:
        raise HTTPException(status_code=503, detail="PostgreSQL service not available")
    
    try:
        details = service.get_regulatory_details(iso3, hs6)
        return details
    except Exception as e:
        logger.error(f"Error getting regulatory details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def postgres_health():
    """Vérifier la santé de PostgreSQL"""
    service = get_service()
    if not service:
        return {
            "status": "unavailable",
            "message": "PostgreSQL service not initialized"
        }
    
    try:
        countries = service.get_countries()
        return {
            "status": "healthy",
            "countries_loaded": len(countries),
            "message": "PostgreSQL connection active"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
