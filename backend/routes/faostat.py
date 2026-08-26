"""
FAOSTAT Routes - Real-time agricultural production data from FAO
Updated for 2024 data
"""

import logging
import os
import re
import sys
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from etl.faostat_data import (
    FAOSTAT_AGRICULTURE_DATA,
    get_faostat_country_data,
    get_fisheries_rankings,
)
from production_data import get_agriculture_by_country, get_agriculture_projections
from services.faostat_service import (
    AFRICAN_COUNTRIES,
    KEY_COMMODITIES,
    get_commodity_list,
    get_faostat_statistics,
    get_production_by_country,
    get_production_data,
    get_production_trends,
    get_top_producers,
)

# Nombre max de commodités supplémentaires (bulk FAOSTAT, hors table curée)
# ajoutées à la liste "cultures" d'un pays — évite de noyer le graphique/tableau
# existant pour les pays où le bulk couvre 50-100+ produits.
_MAX_EXTRA_BULK_CROPS = 20

# Alias FR (noms curés FAOSTAT_AGRICULTURE_DATA) -> EN (libellés bulk agri_faostat),
# pour dédupliquer correctement les cultures déjà présentes dans la table curée
# avant de compléter avec le bulk (ex. "Manioc" curé == "Cassava" bulk : sans cet
# alias, le même produit apparaissait deux fois sous deux noms différents).
_CROP_ALIASES_FR_EN = {
    "agrumes": "citrus",
    "ananas": "pineapples",
    "arachide": "groundnuts",
    "banane": "bananas",
    "blé": "wheat",
    "cacao": "cocoa beans",
    "café": "coffee",
    "canne à sucre": "sugarcane",
    "cannelle": "cinnamon",
    "clou de girofle": "cloves",
    "coton": "seed cotton",
    "dattes": "dates",
    "fonio": "fonio",
    "haricot": "beans",
    "huile de palme": "oil palm",
    "hévéa": "rubber",
    "igname": "yam",
    "manioc": "cassava",
    "maïs": "maize (corn)",
    "mil": "millet",
    "niébé": "cowpeas",
    "noix de cajou": "cashew nuts",
    "noix de coco": "coconuts",
    "oignon": "onions",
    "olives": "olives",
    "oranges": "oranges",
    "orge": "barley",
    "plantain": "plantain",
    "pomme de terre": "potatoes",
    "riz": "rice",
    "soja": "soybeans",
    "sorgho": "sorghum",
    "sésame": "sesame",
    "tabac": "tobacco",
    "teff": "teff",
    "thé": "tea",
    "tomate": "tomatoes",
    "tomates": "tomatoes",
    "tournesol": "sunflower seed",
    "vanille": "vanilla",
}

# Le bulk agri_faostat mêle cultures et produits animaux (viande, lait, œufs).
# L'onglet "Cultures" ne doit afficher que des cultures : on exclut les produits
# animaux (dont les gros volumes — lait/viande bovine — consommeraient sinon les
# slots du plafond _MAX_EXTRA_BULK_CROPS). La détection porte sur des MOTS ENTIERS
# pour ne pas rejeter une culture comme "Eggplants" (contient "egg" mais pas le mot
# "eggs") : ex. "Cattle milk", "Chicken meat", "Hen eggs" sont exclus.
_ANIMAL_PRODUCT_WORDS = {"meat", "milk", "egg", "eggs"}

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
    return {"commodities": get_commodity_list(language), "total": len(KEY_COMMODITIES)}


@router.get("/production")
async def get_production(
    country: Optional[str] = Query(default=None, description="ISO3 country code (e.g., MAR)"),
    commodity: Optional[str] = Query(
        default=None, description="FAO commodity code (e.g., 661 for Cocoa)"
    ),
    year: Optional[int] = Query(default=None, description="Year (2021-2024)"),
    language: str = Query(default="fr", description="Language for descriptions"),
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
            country_iso3=country, commodity_code=commodity, year=year, language=language
        )

        return {
            "data": data,
            "total_records": len(data),
            "filters": {"country": country, "commodity": commodity, "year": year},
            "data_source": "FAOSTAT 2024",
        }
    except Exception as e:
        logger.error(f"Error fetching FAOSTAT production data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/production/{country_iso3}")
async def get_country_production(country_iso3: str, language: str = Query(default="fr")):
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
            status_code=404, detail=f"Country {country_iso3} not found in African countries list"
        )

    try:
        data = get_production_by_country(country_iso3.upper(), language)
        return data
    except Exception as e:
        logger.error(f"Error fetching production for {country_iso3}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/country-detail/{country_iso3}")
async def get_country_full_detail(country_iso3: str, language: str = Query(default="fr")):
    """
    Données FAOSTAT complètes pour un pays : cultures, élevage, pêche/aquaculture.
    Source: FAOSTAT_AGRICULTURE_DATA (données enrichies 2023).
    """
    iso3 = country_iso3.upper()
    if iso3 not in AFRICAN_COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Pays {iso3} non trouvé")

    data = get_faostat_country_data(iso3)
    if not data:
        raise HTTPException(status_code=404, detail=f"Pas de données FAOSTAT pour {iso3}")

    # --- Cultures: respecte display_order si défini, sinon trié par volume ---
    production_raw = data.get("production_2023", {})
    display_order = data.get("display_order", [])
    cultures_list = [
        {
            "name": name,
            "value_2023": info.get("value", 0),
            "unit": info.get("unit", "tonnes"),
            "rank_africa": info.get("rank_africa"),
            "area_ha": info.get("area_ha"),
            "yield_kg_ha": info.get("yield_kg_ha"),
        }
        for name, info in production_raw.items()
    ]
    if display_order:
        order_map = {name: i for i, name in enumerate(display_order)}
        cultures_sorted = sorted(
            cultures_list, key=lambda x: (order_map.get(x["name"], 999), -x["value_2023"])
        )
    else:
        cultures_sorted = sorted(cultures_list, key=lambda x: x["value_2023"], reverse=True)

    # --- Cultures supplémentaires (bulk FAOSTAT réel, hors table curée) ---
    # La table curée FAOSTAT_AGRICULTURE_DATA ne couvre que 6-10 produits phares
    # par pays. Le dataset enrichi production_africaine.json (agri_faostat, bulk
    # FAOSTAT 2019-2024) en couvre 30-100+. On complète la liste "cultures" avec
    # les produits bulk absents de la table curée (comparaison insensible à la
    # casse), triés par valeur décroissante et plafonnés pour rester lisible.
    curated_names_lower = {
        _CROP_ALIASES_FR_EN.get(c["name"].strip().lower(), c["name"].strip().lower())
        for c in cultures_sorted
    }
    bulk = get_agriculture_by_country(iso3)
    extra_crops = []
    for commodity, records in bulk.get("data_by_commodity", {}).items():
        commodity_key = commodity.strip().lower()
        if commodity_key in curated_names_lower or not records:
            continue
        if _ANIMAL_PRODUCT_WORDS & set(re.findall(r"[a-z]+", commodity_key)):
            continue  # produit animal — hors onglet "Cultures"
        latest = max(records, key=lambda r: r.get("year") or 0)
        value = latest.get("value")
        if not value:
            continue
        extra_crops.append(
            {
                "name": commodity,
                "value_2023": value,  # valeur bulk de l'année la plus récente (voir "year")
                "year": latest.get("year"),
                "unit": latest.get("unit", "tonnes"),
                "rank_africa": None,
                "area_ha": None,
                "yield_kg_ha": None,
                "is_bulk_faostat": True,
            }
        )
    extra_crops.sort(key=lambda x: x["value_2023"], reverse=True)
    cultures_sorted = cultures_sorted + extra_crops[:_MAX_EXTRA_BULK_CROPS]

    # --- Prévisions OCDE-FAO (agri_projections, horizons 2025/2030) ---
    proj_records = get_agriculture_projections(iso3)
    projections_by_commodity: dict = {}
    for rec in proj_records:
        label = rec.get("commodity_label", "")
        entry = projections_by_commodity.setdefault(
            label,
            {
                "commodity": label,
                "unit": rec.get("unit", "tonnes"),
                "source_institution": rec.get("source_institution"),
                "source_dataset": rec.get("source_dataset"),
                "source_url": rec.get("source_url"),
                "points": [],
            },
        )
        entry["points"].append({"year": rec.get("year"), "value": rec.get("value")})
    projections = list(projections_by_commodity.values())
    for entry in projections:
        entry["points"].sort(key=lambda p: p["year"])

    # --- Évolution temporelle ---
    evolution = data.get("evolution", {})
    evolution_formatted = {}
    for crop, years_list in evolution.items():
        evolution_formatted[crop] = {str(e["year"]): e["value"] for e in years_list}

    # --- Élevage ---
    livestock_raw = data.get("livestock_2023", {})
    elevage = sorted(
        [
            {
                "name": name,
                "value": info.get("value", 0),
                "unit": info.get("unit", "têtes"),
                "rank_africa": info.get("rank_africa"),
            }
            for name, info in livestock_raw.items()
        ],
        key=lambda x: x["value"],
        reverse=True,
    )

    # --- Pêche & Aquaculture ---
    fish_raw = data.get("fisheries_2023", {})
    peche = {
        "capture_tonnes": fish_raw.get("capture", {}).get("value", 0),
        "aquaculture_tonnes": fish_raw.get("aquaculture", {}).get("value", 0),
        "capture_rank_africa": fish_raw.get("capture", {}).get("rank_africa"),
        "aquaculture_rank_africa": fish_raw.get("aquaculture", {}).get("rank_africa"),
    }

    # --- Indicateurs clés ---
    indicators = data.get("key_indicators", {})

    # --- Production animale (lait, viande, laine, oeufs) ---
    livestock_prod_raw = data.get("livestock_production_2023", {})
    livestock_production = {
        name: {"value": info.get("value", 0), "unit": info.get("unit", "tonnes")}
        for name, info in livestock_prod_raw.items()
    }

    # --- Espèces et ports pêche ---
    fish_species = fish_raw.get("species", [])
    fish_ports = fish_raw.get("main_ports", [])
    peche["species"] = fish_species
    peche["main_ports"] = fish_ports

    return {
        "country_iso3": iso3,
        "country_name": data.get("country_name", iso3),
        "region": data.get("region", ""),
        "data_year": data.get("data_year", 2023),
        "source": data.get("source", "FAOSTAT 2023"),
        "main_crops": data.get("main_crops", []),
        "cultures": cultures_sorted,
        "evolution": evolution_formatted,
        "elevage": elevage,
        "livestock_production_2023": livestock_production,
        "peche_aquaculture": peche,
        "key_indicators": indicators,
        "has_livestock": len(elevage) > 0,
        "has_fisheries": (peche["capture_tonnes"] + peche["aquaculture_tonnes"]) > 0,
        "projections": projections,
        "has_projections": len(projections) > 0,
    }


@router.get("/fisheries/rankings")
async def get_fisheries_rankings_route():
    """Classement africain pêche et aquaculture (source: FAO FishStat 2023)."""
    return get_fisheries_rankings()


@router.get("/top-producers/{commodity_code}")
async def get_commodity_top_producers(
    commodity_code: str,
    year: int = Query(default=2023, description="Year"),
    limit: int = Query(default=10, le=54, description="Number of top producers"),
    language: str = Query(default="fr"),
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
            detail=f"Commodity code {commodity_code} not found. Use /api/faostat/commodities to see available codes.",
        )

    try:
        data = get_top_producers(commodity_code, year, limit, language)
        commodity_info = KEY_COMMODITIES[commodity_code]

        return {
            "commodity_code": commodity_code,
            "commodity_name": commodity_info.get(f"name_{language}", commodity_info["name_en"]),
            "year": year,
            "top_producers": data,
            "data_source": "FAOSTAT 2024",
        }
    except Exception as e:
        logger.error(f"Error fetching top producers for {commodity_code}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends/{country_iso3}/{commodity_code}")
async def get_commodity_trends(
    country_iso3: str, commodity_code: str, language: str = Query(default="fr")
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
            status_code=404, detail=f"Country {country_iso3} not found in African countries list"
        )

    if commodity_code not in KEY_COMMODITIES:
        raise HTTPException(status_code=404, detail=f"Commodity code {commodity_code} not found")

    try:
        data = get_production_trends(country_iso3.upper(), commodity_code, language)
        return data
    except Exception as e:
        logger.error(f"Error fetching trends for {country_iso3}/{commodity_code}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/countries")
async def list_african_countries():
    """
    Get list of African countries covered by FAOSTAT data

    Returns:
        List of ISO3 country codes
    """
    return {"countries": AFRICAN_COUNTRIES, "total": len(AFRICAN_COUNTRIES)}


@router.get("/compare")
async def compare_countries(
    countries: str = Query(..., description="Comma-separated ISO3 codes (e.g., MAR,DZA,EGY)"),
    commodity: str = Query(..., description="FAO commodity code"),
    year: int = Query(default=2023),
    language: str = Query(default="fr"),
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
    country_list = [c.strip().upper() for c in countries.split(",")]

    # Validate countries
    invalid = [c for c in country_list if c not in AFRICAN_COUNTRIES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid country codes: {invalid}")

    if commodity not in KEY_COMMODITIES:
        raise HTTPException(status_code=404, detail=f"Commodity code {commodity} not found")

    try:
        results = []
        for iso3 in country_list:
            data = get_production_data(
                country_iso3=iso3, commodity_code=commodity, year=year, language=language
            )
            total_value = sum(r["value"] for r in data)
            results.append(
                {
                    "country_iso3": iso3,
                    "country_name": data[0]["country_name"] if data else iso3,
                    "value": total_value,
                    "unit": data[0]["unit"] if data else "tonnes",
                }
            )

        # Sort and rank
        results.sort(key=lambda x: x["value"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        commodity_info = KEY_COMMODITIES[commodity]

        return {
            "commodity": commodity_info.get(f"name_{language}", commodity_info["name_en"]),
            "year": year,
            "comparison": results,
            "data_source": "FAOSTAT 2024",
        }
    except Exception as e:
        logger.error(f"Error comparing countries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
