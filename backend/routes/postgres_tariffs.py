"""
API Routes pour les tarifs avec PostgreSQL
Remplace les anciennes routes basées sur les fichiers JSONL
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from services.authentic_tariff_service import (
    get_available_countries,
    get_country_summary,
    get_sub_positions as get_facade_sub_positions,
    get_tariff_line,
    search_tariff_lines,
    calculate_import_taxes,
    get_taxes_detail,
    get_administrative_formalities,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/postgres-tariffs", tags=["PostgreSQL Tariffs"])

@router.get("/countries")
async def get_countries():
    """Liste des pays via le facade tarifaire (PostgreSQL-first)."""
    try:
        countries = get_available_countries()
        return {
            "success": True,
            "total": len(countries),
            "countries": countries,
            "source": "tariff_facade_postgres_first",
        }
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country/{iso3}")
async def get_country_info(iso3: str):
    """Informations sur un pays via le facade tarifaire."""
    try:
        country = get_country_summary(iso3)
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country/{iso3}/sub-positions/{hs6}")
async def get_sub_positions(
    iso3: str, 
    hs6: str, 
    language: str = Query("fr", pattern="^(fr|en)$")
):
    """Sous-positions nationales via le facade tarifaire."""
    try:
        positions = get_facade_sub_positions(iso3, hs6)
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country/{iso3}/commodity/{code}")
async def get_commodity_details(iso3: str, code: str):
    """Détails complets d'une marchandise"""
    try:
        details = get_tariff_line(iso3, code)
        if not details:
            raise HTTPException(status_code=404, detail=f"Commodity {code} not found")
        return {
            "success": True,
            "commodity": details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity {iso3}/{code}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country/{iso3}/search")
async def search_commodities(
    iso3: str,
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    language: str = Query("fr", pattern="^(fr|en)$")
):
    """Recherche de marchandises par description"""
    try:
        results = search_tariff_lines(iso3, q, language=language, limit=limit)
        return {
            "success": True,
            "query": q,
            "country_iso3": iso3.upper(),
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching {iso3} for '{q}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate")
async def calculate_tariffs(
    country_iso3: str = Query(..., description="Country ISO3 code"),
    hs6: str = Query(..., description="HS6 code"),
    value: float = Query(1000, ge=0, description="Goods value")
):
    """Calculer les tarifs pour un code HS6"""
    try:
        result = calculate_import_taxes(country_iso3, hs6, value)
        return result
    except Exception as e:
        logger.error(f"Error calculating tariffs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/regulatory/{iso3}/{hs6}")
async def get_regulatory_details(iso3: str, hs6: str):
    """Détails réglementaires via le facade tarifaire."""
    try:
        return {
            "success": True,
            "country_iso3": iso3.upper(),
            "hs6": hs6,
            "taxes": get_taxes_detail(iso3, hs6),
            "requirements": get_administrative_formalities(iso3, hs6),
            "source": "tariff_facade_postgres_first",
        }
    except Exception as e:
        logger.error(f"Error getting regulatory details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def postgres_health():
    """Vérifier la disponibilité du facade tarifaire PostgreSQL-first."""
    try:
        countries = get_available_countries()
        return {
            "status": "healthy",
            "countries_loaded": len(countries),
            "message": "Tariff facade active (PostgreSQL-first with ETL fallback)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
