"""
Statistics routes - Trade statistics, UNCTAD data, trade products
Comprehensive statistics for African trade and ZLECAf analysis
"""
from fastapi import APIRouter, Query
from typing import Optional
import os
from pathlib import Path

from etl.trade_products_data import (
    get_trade_summary,
    get_top_imports_from_world,
    get_top_exports_to_world,
    get_top_intra_african_imports,
    get_top_intra_african_exports,
    get_all_trade_products_data
)
from etl.translations import translate_product, translate_country_list
from etl.unctad_data import (
    get_unctad_port_statistics,
    get_unctad_trade_flows,
    get_unctad_lsci,
    get_all_unctad_data
)
from country_data import REAL_COUNTRY_DATA

# Import cache service
try:
    from services.cache_service import cache_get, cache_set, generate_cache_key
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


def count_authentic_countries():
    """
    Count countries with authentic tariff data by checking:
    1. backend/data/*_tariffs.json files
    2. engine/output/*_canonical.jsonl files
    Returns the count of countries with authentic data
    """
    backend_dir = Path(__file__).parent.parent
    
    # Check data directory for tariff files
    data_dir = backend_dir / "data"
    tariff_files = list(data_dir.glob("*_tariffs.json"))
    
    # Check engine/output for canonical files
    engine_dir = backend_dir.parent / "engine" / "output"
    canonical_files = list(engine_dir.glob("*_canonical.jsonl")) if engine_dir.exists() else []
    
    # Use the maximum count as some countries might only be in one location
    count = max(len(tariff_files), len(canonical_files))
    
    return count


def count_verified_positions():
    """
    Count total verified tariff positions across all countries
    """
    backend_dir = Path(__file__).parent.parent
    engine_dir = backend_dir.parent / "engine" / "output"
    
    total_positions = 0
    if engine_dir.exists():
        for canonical_file in engine_dir.glob("*_canonical.jsonl"):
            try:
                # Count lines in the file (each line is a tariff position)
                with open(canonical_file, 'r', encoding='utf-8') as f:
                    total_positions += sum(1 for _ in f)
            except Exception:
                continue
    
    # If no canonical files, estimate based on data files
    if total_positions == 0:
        data_dir = backend_dir / "data"
        total_positions = len(list(data_dir.glob("*_tariffs.json"))) * 4200  # Rough estimate
    
    return total_positions

def translate_products_list(products: list, language: str = 'fr') -> list:
    """Translate product names and country names in a products list"""
    if language == 'fr':
        return products
    
    translated = []
    for product in products:
        translated_product = product.copy()
        translated_product['product'] = translate_product(product['product'], language)
        if 'top_importers' in product:
            translated_product['top_importers'] = translate_country_list(product['top_importers'], language)
        if 'top_exporters' in product:
            translated_product['top_exporters'] = translate_country_list(product['top_exporters'], language)
        translated.append(translated_product)
    return translated

GDP_HISTORY_TOP10 = {
    "NGA": {"name": "Nigéria",       "series": {2019: 448.1, 2020: 432.3, 2021: 441.5, 2022: 472.6, 2023: 477.0, 2024: 477.0}},
    "EGY": {"name": "Égypte",         "series": {2019: 303.1, 2020: 361.9, 2021: 394.3, 2022: 476.7, 2023: 387.0, 2024: 387.0}},
    "ZAF": {"name": "Afrique du Sud", "series": {2019: 381.3, 2020: 335.4, 2021: 419.0, 2022: 405.7, 2023: 377.8, 2024: 373.0}},
    "DZA": {"name": "Algérie",        "series": {2019: 171.0, 2020: 145.0, 2021: 167.6, 2022: 191.9, 2023: 239.9, 2024: 266.0}},
    "ETH": {"name": "Éthiopie",       "series": {2019: 96.1,  2020: 107.6, 2021: 111.3, 2022: 126.8, 2023: 163.7, 2024: 205.0}},
    "MAR": {"name": "Maroc",          "series": {2019: 119.7, 2020: 114.7, 2021: 132.7, 2022: 130.9, 2023: 141.1, 2024: 142.0}},
    "KEN": {"name": "Kenya",          "series": {2019: 95.5,  2020: 98.8,  2021: 110.3, 2022: 113.4, 2023: 107.4, 2024: 116.0}},
    "AGO": {"name": "Angola",         "series": {2019: 88.8,  2020: 72.4,  2021: 72.4,  2022: 92.3,  2023: 84.9,  2024: 76.0}},
    "TZA": {"name": "Tanzanie",       "series": {2019: 60.8,  2020: 63.2,  2021: 67.9,  2022: 75.5,  2023: 79.2,  2024: 85.0}},
    "GHA": {"name": "Ghana",          "series": {2019: 66.9,  2020: 68.3,  2021: 77.6,  2022: 72.8,  2023: 76.4,  2024: 77.0}},
}


def build_top_10_gdp_2024():
    """Top 10 African economies by GDP 2024 (World Bank WDI)"""
    return [
        {"rank": 1,  "country": "Nigéria",        "iso3": "NGA", "gdp_2024_musd": 477000, "gdp_per_capita": 2248},
        {"rank": 2,  "country": "Égypte",         "iso3": "EGY", "gdp_2024_musd": 387000, "gdp_per_capita": 3443},
        {"rank": 3,  "country": "Afrique du Sud", "iso3": "ZAF", "gdp_2024_musd": 373000, "gdp_per_capita": 6176},
        {"rank": 4,  "country": "Algérie",        "iso3": "DZA", "gdp_2024_musd": 266000, "gdp_per_capita": 5949},
        {"rank": 5,  "country": "Éthiopie",       "iso3": "ETH", "gdp_2024_musd": 205000, "gdp_per_capita": 1634},
        {"rank": 6,  "country": "Kenya",          "iso3": "KEN", "gdp_2024_musd": 116000, "gdp_per_capita": 2146},
        {"rank": 7,  "country": "Tanzanie",       "iso3": "TZA", "gdp_2024_musd": 85000,  "gdp_per_capita": 1329},
        {"rank": 8,  "country": "Ghana",          "iso3": "GHA", "gdp_2024_musd": 77000,  "gdp_per_capita": 2296},
        {"rank": 9,  "country": "Angola",         "iso3": "AGO", "gdp_2024_musd": 76000,  "gdp_per_capita": 2155},
        {"rank": 10, "country": "Maroc",          "iso3": "MAR", "gdp_2024_musd": 142000, "gdp_per_capita": 3758},
    ]


router = APIRouter(prefix="/statistics")


# =============================================================================
# MAIN STATISTICS ENDPOINT - Dashboard Data (CACHED)
# =============================================================================

@router.get("")
async def get_main_statistics():
    """
    Main statistics endpoint for the dashboard
    Returns comprehensive African trade statistics
    CACHED: 1 hour TTL
    """
    # Check cache first
    if CACHE_AVAILABLE:
        cache_key = generate_cache_key("statistics", "main")
        cached = cache_get(cache_key)
        if cached:
            return cached
    
    # Calculate dynamic values
    authentic_countries_count = count_authentic_countries()
    verified_positions_count = count_verified_positions()
    
    result = {
        "overview": {
            "estimated_combined_gdp": 2706000000000,  # $2.706T - PIB combiné Afrique 2024
            "african_countries_members": 54,
            "total_population_millions": 1400,
            "intra_african_trade_share": 15.5,
            "zlecaf_target_2030": 25,
            "authentic_countries": authentic_countries_count,  # Calculated dynamically
            "verified_positions": verified_positions_count  # Calculated dynamically
        },
        "top_exporters_2024": [
            {"name": "Afrique du Sud", "exports_2024": 151330986674, "share_pct": 21.0},
            {"name": "Nigéria", "exports_2024": 63618347665, "share_pct": 8.8},
            {"name": "Maroc", "exports_2024": 63321762480, "share_pct": 8.8},
            {"name": "Égypte", "exports_2024": 53058090760, "share_pct": 7.4},
            {"name": "Algérie", "exports_2024": 48158384830, "share_pct": 6.7},
            {"name": "Angola", "exports_2024": 42571848317, "share_pct": 5.9},
            {"name": "Libye", "exports_2024": 30592249697, "share_pct": 4.2},
            {"name": "RD Congo", "exports_2024": 29599520451, "share_pct": 4.1},
            {"name": "Côte d'Ivoire", "exports_2024": 25584487601, "share_pct": 3.6},
            {"name": "Tunisie", "exports_2024": 23030704970, "share_pct": 3.2}
        ],
        "top_importers_2024": [
            {"name": "Afrique du Sud", "imports_2024": 100888775675, "share_pct": 13.3},
            {"name": "Égypte", "imports_2024": 99521024321, "share_pct": 13.1},
            {"name": "Maroc", "imports_2024": 89173010831, "share_pct": 11.7},
            {"name": "Nigéria", "imports_2024": 50893435322, "share_pct": 6.7},
            {"name": "Algérie", "imports_2024": 43644432751, "share_pct": 5.7},
            {"name": "Tunisie", "imports_2024": 26146791180, "share_pct": 3.4},
            {"name": "Kenya", "imports_2024": 23627120576, "share_pct": 3.1},
            {"name": "Libéria", "imports_2024": 22951268703, "share_pct": 3.0},
            {"name": "Libye", "imports_2024": 20918075548, "share_pct": 2.7},
            {"name": "Tanzanie", "imports_2024": 20411960514, "share_pct": 2.7}
        ],
        "top_10_gdp_2024": build_top_10_gdp_2024(),
        "top_10_gdp_2024_source": "Banque Mondiale (World Development Indicators 2024) — projections 2025: WB Africa Economic Update Jan 2025",
        "trade_evolution": {
            "intra_african_trade_2023": 111.8,  # Milliards USD
            "intra_african_trade_2024": 123.5,  # Milliards USD (estimé +10.5%)
            "growth_rate_2024": 10.5,
            "growth_rate_2023_2024": 10.5,
            "trend": "Croissance soutenue",
            "zlecaf_target_2030": 200,
            "projected_2025": 138.3,
            "projected_2030": 188.0
        },
        "top_5_gdp_trade_comparison": [
            {
                "country": "Afrique du Sud",
                "gdp_2024": 373.0,
                "exports_world": 151.3,
                "exports_intra_african": 28.7,
                "imports_world": 100.9,
                "imports_intra_african": 8.2,
                "intra_african_percentage": 19.0
            },
            {
                "country": "Nigéria",
                "gdp_2024": 477.0,
                "exports_world": 63.6,
                "exports_intra_african": 8.5,
                "imports_world": 50.9,
                "imports_intra_african": 4.1,
                "intra_african_percentage": 13.4
            },
            {
                "country": "Égypte",
                "gdp_2024": 387.0,
                "exports_world": 53.1,
                "exports_intra_african": 6.8,
                "imports_world": 99.5,
                "imports_intra_african": 3.2,
                "intra_african_percentage": 12.8
            },
            {
                "country": "Maroc",
                "gdp_2024": 142.0,
                "exports_world": 63.3,
                "exports_intra_african": 4.9,
                "imports_world": 89.2,
                "imports_intra_african": 2.8,
                "intra_african_percentage": 7.7
            },
            {
                "country": "Algérie",
                "gdp_2024": 224.0,
                "exports_world": 48.2,
                "exports_intra_african": 3.2,
                "imports_world": 43.6,
                "imports_intra_african": 1.8,
                "intra_african_percentage": 6.6
            }
        ],
        "sector_performance": {
            "hydrocarbures": {"share": 32.5, "value_2024": 234.3},
            "minerais_metaux": {"share": 18.7, "value_2024": 134.8},
            "agriculture": {"share": 15.2, "value_2024": 109.5},
            "produits_manufactures": {"share": 12.8, "value_2024": 92.3},
            "automobile_transport": {"share": 8.3, "value_2024": 59.8},
            "chimie_pharmaceutique": {"share": 6.1, "value_2024": 44.0},
            "textile_habillement": {"share": 4.2, "value_2024": 30.3},
            "autres": {"share": 2.2, "value_2024": 15.8}
        },
        "source": "IMF WEO 2024, World Bank, UNCTAD, OEC/BACI, AfCFTA Secretariat",
        "last_updated": "2024-12"
    }
    
    # Cache the result
    if CACHE_AVAILABLE:
        cache_set(cache_key, result, "statistics")
    
    return result

# =============================================================================
# TRADE PRODUCTS ENDPOINTS
# =============================================================================

@router.get("/gdp-history-top10")
async def get_gdp_history_top10():
    """
    Return the historical GDP series (2019–2024) for the Top 10 African economies.
    Source: World Bank — Open Data (NY.GDP.MKTP.CD, current US$ billion).
    """
    series = []
    for iso3, info in GDP_HISTORY_TOP10.items():
        # Order years ascending so Recharts renders left-to-right.
        ordered = sorted(info["series"].items())
        series.append({
            "iso3": iso3,
            "country": info["name"],
            "history": [{"year": y, "gdp_billion": v} for y, v in ordered],
            "gdp_2024_billion": ordered[-1][1] if ordered else None,
        })
    # Sort by 2024 GDP descending so the legend matches the Top 10 ranking.
    series.sort(key=lambda r: r.get("gdp_2024_billion") or 0, reverse=True)

    years = sorted({y for info in GDP_HISTORY_TOP10.values() for y in info["series"]})
    # Wide-format table for charting libraries that prefer one row per year.
    chart_rows = []
    for year in years:
        row = {"year": year}
        for entry in series:
            iso3 = entry["iso3"]
            year_value = GDP_HISTORY_TOP10[iso3]["series"].get(year)
            if year_value is not None:
                row[iso3] = year_value
        chart_rows.append(row)

    return {
        "source": "Banque Mondiale — World Development Indicators (NY.GDP.MKTP.CD), current US$ billion",
        "years": years,
        "countries": [{"iso3": s["iso3"], "country": s["country"], "gdp_2024_billion": s["gdp_2024_billion"]} for s in series],
        "series": series,
        "chart_rows": chart_rows,
    }


@router.get("/trade-products/summary")
async def get_trade_products_summary():
    """Get summary of trade products data"""
    return get_trade_summary()

@router.get("/trade-products/imports-world")
async def get_imports_from_world(lang: str = 'fr'):
    """Get Top 20 products imported by Africa from the world"""
    titles = {
        'fr': "Top 20 Produits Importés par l'Afrique du Monde",
        'en': "Top 20 Products Imported by Africa from the World"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/ITC Trade Map + OEC/BACI 2024",
        "year": 2024,
        "products": translate_products_list(get_top_imports_from_world(), lang)
    }

@router.get("/trade-products/exports-world")
async def get_exports_to_world(lang: str = 'fr'):
    """Get Top 20 products exported by Africa to the world"""
    titles = {
        'fr': "Top 20 Produits Exportés par l'Afrique vers le Monde",
        'en': "Top 20 Products Exported by Africa to the World"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/ITC Trade Map + OEC/BACI 2024",
        "year": 2024,
        "products": translate_products_list(get_top_exports_to_world(), lang)
    }

@router.get("/trade-products/intra-imports")
async def get_intra_imports(lang: str = 'fr'):
    """Get Top 20 products imported in intra-African trade"""
    titles = {
        'fr': "Top 20 Produits Importés en Commerce Intra-Africain",
        'en': "Top 20 Products Imported in Intra-African Trade"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/AfCFTA Secretariat 2024",
        "year": 2024,
        "products": translate_products_list(get_top_intra_african_imports(), lang)
    }

@router.get("/trade-products/intra-exports")
async def get_intra_exports(lang: str = 'fr'):
    """Get Top 20 products exported in intra-African trade"""
    titles = {
        'fr': "Top 20 Produits Exportés en Commerce Intra-Africain",
        'en': "Top 20 Products Exported in Intra-African Trade"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/AfCFTA Secretariat 2024",
        "year": 2024,
        "products": translate_products_list(get_top_intra_african_exports(), lang)
    }

@router.get("/trade-products")
async def get_all_trade_products():
    """Get all trade products data (imports, exports, intra-African)"""
    return get_all_trade_products_data()

# =============================================================================
# UNCTAD DATA ENDPOINTS
# =============================================================================

@router.get("/unctad/ports")
async def get_unctad_ports():
    """
    Get UNCTAD port statistics for African ports
    Source: UNCTAD Review of Maritime Transport 2023
    """
    return get_unctad_port_statistics()

@router.get("/unctad/trade-flows")
async def get_unctad_flows():
    """
    Get UNCTAD trade flow statistics
    Source: UNCTAD Trade Statistics 2023
    """
    return get_unctad_trade_flows()

@router.get("/unctad/lsci")
async def get_unctad_liner_connectivity():
    """
    Get UNCTAD Liner Shipping Connectivity Index for Africa
    Source: UNCTAD 2023
    """
    return get_unctad_lsci()

@router.get("/unctad")
async def get_all_unctad():
    """Get all UNCTAD data (ports, trade flows, LSCI)"""
    return get_all_unctad_data()


# =============================================================================
# TRADE PERFORMANCE ENDPOINTS (Global and Intra-African)
# =============================================================================

@router.get("/trade-performance")
async def get_trade_performance_global():
    """
    Get trade performance data for all African countries (GLOBAL - with all world partners)
    Source: OEC, World Bank, IMF 2024
    """
    return {
        "year": 2024,
        "type": "global",
        "description": "Commerce total avec tous les partenaires mondiaux",
        "countries_global": [
            {"code": "ZA", "country": "Afrique du Sud", "exports_2024": 151.3, "imports_2024": 100.9, "trade_balance_2024": 50.4},
            {"code": "NG", "country": "Nigéria", "exports_2024": 63.6, "imports_2024": 50.9, "trade_balance_2024": 12.7},
            {"code": "MA", "country": "Maroc", "exports_2024": 63.3, "imports_2024": 89.2, "trade_balance_2024": -25.9},
            {"code": "EG", "country": "Égypte", "exports_2024": 53.1, "imports_2024": 99.5, "trade_balance_2024": -46.4},
            {"code": "DZ", "country": "Algérie", "exports_2024": 48.2, "imports_2024": 43.6, "trade_balance_2024": 4.6},
            {"code": "AO", "country": "Angola", "exports_2024": 42.6, "imports_2024": 14.8, "trade_balance_2024": 27.8},
            {"code": "LY", "country": "Libye", "exports_2024": 30.6, "imports_2024": 20.9, "trade_balance_2024": 9.7},
            {"code": "CD", "country": "RD Congo", "exports_2024": 29.6, "imports_2024": 18.2, "trade_balance_2024": 11.4},
            {"code": "CI", "country": "Côte d'Ivoire", "exports_2024": 25.6, "imports_2024": 17.3, "trade_balance_2024": 8.3},
            {"code": "TN", "country": "Tunisie", "exports_2024": 23.0, "imports_2024": 26.1, "trade_balance_2024": -3.1},
            {"code": "KE", "country": "Kenya", "exports_2024": 12.8, "imports_2024": 23.6, "trade_balance_2024": -10.8},
            {"code": "GH", "country": "Ghana", "exports_2024": 18.5, "imports_2024": 16.8, "trade_balance_2024": 1.7},
            {"code": "ET", "country": "Éthiopie", "exports_2024": 4.2, "imports_2024": 15.8, "trade_balance_2024": -11.6}
        ],
        "source": "OEC/BACI, World Bank, IMF WEO 2024"
    }


@router.get("/trade-performance-intra-african")
async def get_trade_performance_intra_african():
    """
    Get INTRA-AFRICAN trade performance data (trade between African countries only)
    Source: OEC, UNCTAD, AfDB 2024
    """
    return {
        "year": 2024,
        "type": "intra_african",
        "description": "Commerce uniquement entre pays africains",
        "total_intra_african_trade_2024": 123.5,
        "intra_african_share_of_total": 16.3,
        "countries_intra_african": [
            {"code": "ZA", "country": "Afrique du Sud", "exports_2024": 28.7, "imports_2024": 8.2, "trade_balance_2024": 20.5, "intra_african_percentage": 19.0},
            {"code": "NG", "country": "Nigéria", "exports_2024": 8.5, "imports_2024": 4.1, "trade_balance_2024": 4.4, "intra_african_percentage": 13.4},
            {"code": "KE", "country": "Kenya", "exports_2024": 8.2, "imports_2024": 3.8, "trade_balance_2024": 4.4, "intra_african_percentage": 64.1},
            {"code": "EG", "country": "Égypte", "exports_2024": 6.8, "imports_2024": 3.2, "trade_balance_2024": 3.6, "intra_african_percentage": 12.8},
            {"code": "CI", "country": "Côte d'Ivoire", "exports_2024": 6.5, "imports_2024": 2.9, "trade_balance_2024": 3.6, "intra_african_percentage": 25.4},
            {"code": "GH", "country": "Ghana", "exports_2024": 5.8, "imports_2024": 3.1, "trade_balance_2024": 2.7, "intra_african_percentage": 31.4},
            {"code": "MA", "country": "Maroc", "exports_2024": 4.9, "imports_2024": 2.8, "trade_balance_2024": 2.1, "intra_african_percentage": 7.7},
            {"code": "TZ", "country": "Tanzanie", "exports_2024": 4.8, "imports_2024": 2.4, "trade_balance_2024": 2.4, "intra_african_percentage": 37.5},
            {"code": "TN", "country": "Tunisie", "exports_2024": 4.2, "imports_2024": 1.8, "trade_balance_2024": 2.4, "intra_african_percentage": 18.3},
            {"code": "SN", "country": "Sénégal", "exports_2024": 3.6, "imports_2024": 2.1, "trade_balance_2024": 1.5, "intra_african_percentage": 42.4},
            {"code": "DZ", "country": "Algérie", "exports_2024": 3.2, "imports_2024": 1.8, "trade_balance_2024": 1.4, "intra_african_percentage": 6.6},
            {"code": "ET", "country": "Éthiopie", "exports_2024": 3.1, "imports_2024": 1.5, "trade_balance_2024": 1.6, "intra_african_percentage": 73.8},
            {"code": "AO", "country": "Angola", "exports_2024": 2.1, "imports_2024": 1.2, "trade_balance_2024": 0.9, "intra_african_percentage": 4.9}
        ],
        "source": "OEC/BACI, UNCTAD, African Development Bank 2024"
    }
