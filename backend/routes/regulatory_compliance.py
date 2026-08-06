"""API routes for source-bound import formalities and mandated providers."""

from fastapi import APIRouter, HTTPException
from services.regulatory_compliance_service import (
    get_country_regulatory_compliance,
    get_supported_regulatory_countries,
)

router = APIRouter(prefix="/regulatory-compliance", tags=["Regulatory Compliance"])


@router.get("/countries")
async def list_regulatory_compliance_countries():
    """List countries with a source-bound regulatory-compliance dataset."""

    countries = get_supported_regulatory_countries()
    return {"success": True, "total": len(countries), "countries": countries}


@router.get("/country/{country_iso3}")
async def get_regulatory_compliance_endpoint(country_iso3: str):
    """Return import formalities and government-mandated execution actors."""

    compliance = get_country_regulatory_compliance(country_iso3)
    if compliance is None:
        raise HTTPException(
            status_code=404,
            detail=f"No regulatory-compliance registry found for country {country_iso3.upper()}",
        )
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "regulatory_compliance": compliance,
    }
