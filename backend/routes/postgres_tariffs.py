"""
API Routes pour les tarifs avec PostgreSQL
Remplace les anciennes routes basées sur les fichiers JSONL
"""

import logging

from entitlement_guard import require_calculations_quota
from fastapi import APIRouter, Depends, HTTPException, Query
from routes.authentic_tariffs import calculate_taxes_endpoint
from services.authentic_tariff_service import (
    get_administrative_formalities,
    get_available_countries,
    get_country_summary,
)
from services.authentic_tariff_service import get_sub_positions as get_facade_sub_positions
from services.authentic_tariff_service import (
    get_tariff_line,
    get_taxes_detail,
    search_tariff_lines,
)

from engine.schemas.legal_override import RemissionEligibility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/postgres-tariffs", tags=["PostgreSQL Tariffs"])


@router.get("/countries")
async def get_countries():
    """Liste des pays via la facade tarifaire (PostgreSQL-first)."""
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
    """Informations sur un pays via la facade tarifaire."""
    try:
        country = get_country_summary(iso3)
        if not country:
            raise HTTPException(status_code=404, detail=f"Country {iso3} not found")
        return {"success": True, "country": country}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting country {iso3}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country/{iso3}/sub-positions/{hs6}")
async def get_sub_positions(iso3: str, hs6: str, language: str = Query("fr", pattern="^(fr|en)$")):
    """Sous-positions nationales via la facade tarifaire."""
    try:
        positions = get_facade_sub_positions(iso3, hs6, language=language)
        return {
            "success": True,
            "country_iso3": iso3.upper(),
            "hs6": hs6,
            "total": len(positions),
            "sub_positions": positions,
            "note": "Data from PostgreSQL - Real national tariff descriptions",
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
        return {"success": True, "commodity": details}
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
    language: str = Query("fr", pattern="^(fr|en)$"),
):
    """Recherche de marchandises par description"""
    try:
        results = search_tariff_lines(iso3, q, limit=limit, language=language)
        return {
            "success": True,
            "query": q,
            "country_iso3": iso3.upper(),
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error searching {iso3} for '{q}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate", dependencies=[Depends(require_calculations_quota())])
async def calculate_tariffs(
    country_iso3: str = Query(..., pattern="^[A-Za-z]{3}$", description="Country ISO3 code"),
    hs6: str = Query(..., description="HS code or exact national position (6-12 digits)"),
    value: float = Query(1000, gt=0, allow_inf_nan=False, description="Goods value"),
):
    """Compatibility URL using the same calculation boundary as authentic tariffs."""
    try:
        # Keep the legacy query names while sharing doctrine, selection errors,
        # legal layers and provenance. Dependency injection is enforced above;
        # a direct Python call does not execute the target route's dependencies.
        return await calculate_taxes_endpoint(
            country_iso3=country_iso3.upper(),
            hs_code=hs6,
            cif_value=value,
            language="fr",
            origin=None,
            calculation_date=None,
            remission_eligibility=RemissionEligibility.ELIGIBILITY_UNKNOWN,
            authorization_reference=None,
            authorization_valid_from=None,
            authorization_valid_to=None,
            authorization_hs_codes=None,
            authorization_goods=None,
            beneficiary=None,
            import_purpose=None,
            quantity=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating tariffs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/regulatory/{iso3}/{hs6}")
async def get_regulatory_details(iso3: str, hs6: str):
    """Détails réglementaires via la facade tarifaire."""
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
            "message": "Tariff facade active (PostgreSQL-first with ETL fallback)",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
