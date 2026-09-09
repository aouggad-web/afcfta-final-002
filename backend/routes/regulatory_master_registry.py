"""API routes for the 54-country regulatory-compliance master registry."""

from fastapi import APIRouter, HTTPException
from services.regulatory_master_registry_service import (
    get_all_regulatory_countries,
    get_published_regulatory_countries,
    get_regulatory_country_entry,
    get_regulatory_registry,
)

router = APIRouter(prefix="/regulatory-master-registry")


@router.get("/countries")
def list_regulatory_master_registry_countries():
    """List all 54 African ISO3 codes tracked by the master registry, plus the
    subset currently published with a source-bound dataset."""

    all_countries = get_all_regulatory_countries()
    published = get_published_regulatory_countries()
    return {
        "success": True,
        "total": len(all_countries),
        "countries": all_countries,
        "published_total": len(published),
        "published_countries": published,
    }


@router.get("/registry")
def get_regulatory_master_registry_endpoint():
    """Return the full 54-country master registry (coverage-status dimensions,
    dataset/source paths, notes) — never numeric rates or fees."""

    registry = get_regulatory_registry()
    return {"success": True, "registry": registry}


@router.get("/country/{country_iso3}")
def get_regulatory_master_registry_country_endpoint(country_iso3: str):
    """Return the master-registry coverage entry for a single African country."""

    entry = get_regulatory_country_entry(country_iso3)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"{country_iso3.upper()} is not a tracked African ISO3 code in the regulatory master registry",
        )
    return {"success": True, "country_iso3": country_iso3.upper(), "entry": entry}
