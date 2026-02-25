"""
OEC Trade Service routes
Observatory of Economic Complexity integration
MISE À JOUR 2025: Données 2024 maintenant disponibles
"""
from fastapi import APIRouter, HTTPException, Query

from services.oec_trade_service import (
    oec_service,
    get_african_countries_list,
    AFRICAN_COUNTRIES_OEC,
    DEFAULT_YEAR,
    get_country_name_to_iso3_mapping
)

router = APIRouter(prefix="/oec")

@router.get("/countries")
async def get_oec_african_countries(
    language: str = Query("fr", description="Langue (fr/en)")
):
    """Liste des pays africains disponibles pour les statistiques OEC"""
    return {
        "success": True,
        "total": len(AFRICAN_COUNTRIES_OEC),
        "countries": get_african_countries_list(language),
        "source": "OEC/BACI",
        "latest_year": DEFAULT_YEAR
    }

@router.get("/countries/name-to-iso3")
async def get_oec_country_name_mapping():
    """
    Mapping inversé des noms de pays (name_en) vers codes ISO3.
    Utile pour convertir les noms de pays retournés par l'API OEC en codes ISO3
    pour afficher les drapeaux dans le frontend.
    """
    return {
        "success": True,
        "mapping": get_country_name_to_iso3_mapping(),
        "source": "OEC/BACI"
    }

@router.get("/years")
async def get_oec_available_years():
    """Années disponibles dans les données OEC"""
    years = await oec_service.get_available_years()
    return {"success": True, "years": years, "source": "OEC/BACI", "default_year": DEFAULT_YEAR}

@router.get("/exports/{country_iso3}")
async def get_oec_country_exports(
    country_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    hs_level: str = Query("HS4"),
    limit: int = Query(50)
):
    """Exportations d'un pays africain par produit HS"""
    result = await oec_service.get_exports_by_product(country_iso3, year, hs_level, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/imports/{country_iso3}")
async def get_oec_country_imports(
    country_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    hs_level: str = Query("HS4"),
    limit: int = Query(50)
):
    """Importations d'un pays africain par produit HS"""
    result = await oec_service.get_imports_by_product(country_iso3, year, hs_level, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/product/{hs_code}")
async def get_oec_product_trade(
    hs_code: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    trade_flow: str = Query("exports"),
    limit: int = Query(50)
):
    """Statistiques commerciales mondiales pour un code HS"""
    result = await oec_service.get_trade_by_hs_code(hs_code, year, trade_flow, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/product/{hs_code}/africa")
async def get_oec_african_exporters(
    hs_code: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    limit: int = Query(20)
):
    """Top exportateurs africains pour un produit HS"""
    result = await oec_service.get_top_african_exporters(hs_code, year, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/bilateral/{exporter_iso3}/{importer_iso3}")
async def get_oec_bilateral_trade(
    exporter_iso3: str,
    importer_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    year: int = Query(2024),
    hs_level: str = Query("HS4"),
    limit: int = Query(50)
):
    """Commerce bilatéral entre deux pays africains"""
    result = await oec_service.get_bilateral_trade(exporter_iso3, importer_iso3, year, hs_level, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
