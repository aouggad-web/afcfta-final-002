"""
OEC Trade Service routes
Observatory of Economic Complexity integration
MISE À JOUR 2025: Données 2024 maintenant disponibles
"""

from fastapi import APIRouter, HTTPException, Query
from services.oec_trade_service import (
    AFRICAN_COUNTRIES_OEC,
    DEFAULT_YEAR,
    get_african_countries_list,
    get_country_name_to_iso3_mapping,
    oec_service,
)
from services.trade_series_orchestrator import get_trade_series_resilient

router = APIRouter(prefix="/oec")


@router.get("/countries")
async def get_oec_african_countries(
    language: str = Query("fr", description="Langue (fr/en)"),
    lang: str = Query(None, description="Alias de 'language' (fr/en)"),
):
    """Liste des pays africains disponibles pour les statistiques OEC"""
    lang_code = lang or language
    return {
        "success": True,
        "total": len(AFRICAN_COUNTRIES_OEC),
        "countries": get_african_countries_list(lang_code),
        "source": "OEC/BACI",
        "latest_year": DEFAULT_YEAR,
    }


@router.get("/countries/name-to-iso3")
async def get_oec_country_name_mapping():
    """
    Mapping inversé des noms de pays (name_en) vers codes ISO3.
    Utile pour convertir les noms de pays retournés par l'API OEC en codes ISO3
    pour afficher les drapeaux dans le frontend.
    """
    return {"success": True, "mapping": get_country_name_to_iso3_mapping(), "source": "OEC/BACI"}


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
    limit: int = Query(50),
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
    limit: int = Query(50),
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
    limit: int = Query(50),
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
    limit: int = Query(20),
):
    """Top exportateurs africains pour un produit HS"""
    result = await oec_service.get_top_african_exporters(hs_code, year, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/country/{country_iso3}/hs6/{hs_code}/history")
async def get_country_hs6_history(
    country_iso3: str,
    hs_code: str,
    years: int = Query(5, ge=2, le=10, description="Nombre d'années (2 à 10)"),
    end_year: int = Query(
        DEFAULT_YEAR, description="Dernière année (par défaut: dernière disponible)"
    ),
    level: str = Query(None, description="Niveau SH: hs2 | hs4 | hs6 (auto si non fourni)"),
):
    """
    Historique commercial (exports + imports) d'un pays africain pour un code SH
    (chapitre SH2, position SH4 ou sous-position SH6) sur les N dernières années.
    """
    result = await oec_service.get_country_hs6_history(
        country_iso3=country_iso3,
        hs_code=hs_code,
        n_years=years,
        end_year=end_year,
        level=level,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/country/{country_iso3}/trade-series")
async def get_oec_country_trade_series(
    country_iso3: str,
    start_year: int = Query(2018, ge=2018, le=DEFAULT_YEAR, description="Première année"),
    end_year: int = Query(DEFAULT_YEAR, ge=2018, le=DEFAULT_YEAR, description="Dernière année"),
):
    """
    Série temporelle du commerce total d'un pays (exports/imports/balance par
    année, sur la plage `start_year`..`end_year`).

    Résilient: essaie OEC d'abord, puis les sources de secours configurées
    (Comtrade opt-in), et dégrade proprement si aucune source n'a de données —
    pour ne pas tomber en rade si OEC est indisponible/rate-limité. La réponse
    indique `source_used` et `sources_tried`.
    """
    return await get_trade_series_resilient(
        country_iso3=country_iso3,
        start_year=start_year,
        end_year=end_year,
    )


@router.get("/bilateral/{exporter_iso3}/{importer_iso3}")
async def get_oec_bilateral_trade(
    exporter_iso3: str,
    importer_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    hs_level: str = Query("HS4"),
    limit: int = Query(50),
):
    """Commerce bilatéral entre deux pays africains"""
    result = await oec_service.get_bilateral_trade(
        exporter_iso3, importer_iso3, year, hs_level, limit
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/rca/{country_iso3}")
async def get_oec_rca(
    country_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    hs_level: str = Query("HS4", description="Niveau SH: HS2, HS4 ou HS6"),
    limit: int = Query(30, description="Nombre de produits à retourner"),
):
    """
    Avantage comparatif révélé (RCA, indice de Balassa) d'un pays africain,
    par produit, au niveau SH2, SH4 ou SH6. RCA > 1 ⇒ avantage révélé.
    """
    result = await oec_service.get_revealed_comparative_advantage(
        country_iso3, year, hs_level=hs_level, limit=limit
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/complementarity/{exporter_iso3}/{importer_iso3}")
async def get_oec_trade_complementarity(
    exporter_iso3: str,
    importer_iso3: str,
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)"),
    hs_level: str = Query("HS4", description="Niveau SH: HS2, HS4 ou HS6"),
    limit: int = Query(20, description="Nombre d'opportunités à retourner"),
):
    """
    Indice de complémentarité commerciale (TCI) entre un exportateur et un
    importateur africains, par niveau SH (HS2/HS4/HS6). Renvoie aussi les
    produits où l'offre de l'exportateur recoupe la demande de l'importateur.
    """
    result = await oec_service.get_trade_complementarity(
        exporter_iso3, importer_iso3, year, hs_level=hs_level, limit=limit
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/africa/totals")
async def get_oec_africa_totals(
    year: int = Query(DEFAULT_YEAR, description="Année (2024 par défaut)")
):
    """
    Récupère les totaux d'exportations et d'importations pour toute l'Afrique.
    Ces données sont utilisées pour les statistiques globales de la ZLECAf.
    """
    result = await oec_service.get_africa_totals(year)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
