"""
Production routes - FAOSTAT, UNIDO, USGS, World Bank data
Covers all 4 dimensions: Macro, Agriculture, Manufacturing, Mining
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from production_data import (
    get_value_added,
    get_value_added_by_country,
    get_agriculture_production,
    get_agriculture_by_country,
    get_manufacturing_production,
    get_manufacturing_by_country,
    get_mining_production,
    get_mining_by_country as get_mining_by_country_data,
    get_production_statistics,
    get_country_production_overview
)

try:
    from etl.unido_data import UNIDO_INDUSTRY_DATA
except ImportError:
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from etl.unido_data import UNIDO_INDUSTRY_DATA
    except ImportError:
        UNIDO_INDUSTRY_DATA = {}

router = APIRouter(prefix="/production")

@router.get("/statistics")
async def get_production_stats():
    """
    Get global production statistics for all African countries
    Returns overview of data coverage across 4 dimensions
    """
    return get_production_statistics()

@router.get("/macro")
async def get_macro_value_added(
    country_iso3: Optional[str] = None,
    year: Optional[int] = None,
    sector: Optional[str] = None
):
    """
    Get macro-level value added data (World Bank/IMF)
    
    Query parameters:
    - country_iso3: ISO3 country code (e.g., 'ZAF')
    - year: Year (2021-2024)
    - sector: ISIC section ('A', 'B-F', 'C')
    """
    return get_value_added(country_iso3=country_iso3, year=year, sector=sector)

@router.get("/macro/{country_iso3}")
async def get_macro_by_country(country_iso3: str):
    """
    Get all macro value added series for a specific country
    Organized by sector with time series
    """
    return get_value_added_by_country(country_iso3)

@router.get("/agriculture")
async def get_agri_production(
    country_iso3: Optional[str] = None,
    year: Optional[int] = None,
    commodity: Optional[str] = None
):
    """
    Get agricultural production data (FAOSTAT)
    
    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - commodity: Commodity name or code (e.g., 'Maize', '0015')
    """
    return get_agriculture_production(country_iso3=country_iso3, year=year, commodity=commodity)

@router.get("/agriculture/{country_iso3}")
async def get_agri_by_country(country_iso3: str):
    """
    Get all agricultural production for a specific country
    Organized by commodity with time series
    """
    return get_agriculture_by_country(country_iso3)

@router.get("/manufacturing")
async def get_manuf_production(
    country_iso3: Optional[str] = None,
    year: Optional[int] = None,
    isic_code: Optional[str] = None
):
    """
    Get manufacturing production data (UNIDO)
    
    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - isic_code: ISIC Rev.4 code (e.g., '10', '11')
    """
    return get_manufacturing_production(country_iso3=country_iso3, year=year, isic_code=isic_code)

@router.get("/manufacturing/{country_iso3}")
async def get_manuf_by_country(country_iso3: str):
    """
    Get all manufacturing production for a specific country
    Organized by ISIC sector with time series
    """
    return get_manufacturing_by_country(country_iso3)

@router.get("/mining")
async def get_mining_prod(
    country_iso3: Optional[str] = None,
    year: Optional[int] = None,
    commodity: Optional[str] = None
):
    """
    Get mining production data (USGS)
    
    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - commodity: Mineral name or code (e.g., 'Gold', 'AU')
    """
    return get_mining_production(country_iso3=country_iso3, year=year, commodity=commodity)

@router.get("/mining/{country_iso3}")
async def get_mining_by_country(country_iso3: str):
    """
    Get all mining production for a specific country
    Organized by commodity with time series
    """
    return get_mining_by_country_data(country_iso3)

@router.get("/overview/{country_iso3}")
async def get_country_production_full_overview(country_iso3: str):
    """
    Get complete production overview for a country
    Includes all 4 dimensions: macro, agriculture, manufacturing, mining
    """
    return get_country_production_overview(country_iso3)

# =============================================================================
# UNIDO INDSTAT4 - Routes spécifiques UNIDO
# Source: UNIDO INDUSTRY_DATA (54 pays africains)
# =============================================================================

@router.get("/unido/statistics")
async def get_unido_statistics():
    """
    Statistiques globales UNIDO - Valeur Ajoutée Manufacturière africaine
    Retourne: MVA total, nb pays, top secteurs, etc.
    """
    if not UNIDO_INDUSTRY_DATA:
        return {"error": "UNIDO data not available", "total_countries": 0}

    total_mva = sum(d.get("mva_2023_mln_usd", 0) for d in UNIDO_INDUSTRY_DATA.values())
    total_employment = sum(d.get("industry_employment", 0) for d in UNIDO_INDUSTRY_DATA.values())
    total_exports = sum(d.get("exports_manuf_mln_usd", 0) for d in UNIDO_INDUSTRY_DATA.values())

    return {
        "total_countries": len(UNIDO_INDUSTRY_DATA),
        "total_mva_mln_usd": round(total_mva, 1),
        "total_mva_bln_usd": round(total_mva / 1000, 1),
        "total_employment": total_employment,
        "total_exports_manuf_mln_usd": round(total_exports, 1),
        "source": "UNIDO INDSTAT4 2024 — International Yearbook of Industrial Statistics",
        "data_year": 2023,
        "coverage": "54 pays membres AfCFTA",
        "classification": "ISIC Rev.4"
    }

@router.get("/unido/ranking")
async def get_unido_ranking():
    """
    Classement africain par Valeur Ajoutée Manufacturière (MVA 2023)
    """
    if not UNIDO_INDUSTRY_DATA:
        return {"ranking": []}

    ranking = []
    for iso3, data in UNIDO_INDUSTRY_DATA.items():
        ranking.append({
            "country_iso3": iso3,
            "country_name": data.get("country_name", iso3),
            "region": data.get("region", ""),
            "mva_2023_mln_usd": data.get("mva_2023_mln_usd", 0),
            "mva_gdp_percent": data.get("mva_gdp_percent", 0),
            "mva_per_capita_usd": data.get("mva_per_capita_usd", 0),
            "growth_rate_2023": data.get("growth_rate_2023", 0),
            "cip_index_rank": data.get("cip_index_rank"),
        })

    ranking.sort(key=lambda x: x["mva_2023_mln_usd"], reverse=True)

    return {
        "ranking": ranking,
        "total": len(ranking),
        "source": "UNIDO INDSTAT4 2024",
        "data_year": 2023
    }

@router.get("/unido/{country_iso3}")
async def get_unido_country_data(country_iso3: str):
    """
    Données UNIDO complètes pour un pays africain
    - MVA, secteurs ISIC, emplois, exportations, produits clés
    """
    iso3_upper = country_iso3.upper()

    if iso3_upper not in UNIDO_INDUSTRY_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune donnée UNIDO disponible pour {iso3_upper}. Pays couverts: {len(UNIDO_INDUSTRY_DATA)}"
        )

    data = UNIDO_INDUSTRY_DATA[iso3_upper].copy()
    data["country_iso3"] = iso3_upper
    return data
