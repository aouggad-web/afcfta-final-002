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


def _parse_growth_pct(value):
    """Parse a growth value (string '3.5%' or float 3.5) into a numeric percent."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace('%', '').replace(',', '.')
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def build_top_10_gdp_2024():
    """
    Build the Top 10 African GDP 2024 ranking from the same `REAL_COUNTRY_DATA`
    used by the country-profile endpoint, ensuring perfect consistency between
    the dashboard table and individual country pages.

    Source: Banque Mondiale (WDI 2024) — current US$.
    """
    rows = []
    for iso3, info in REAL_COUNTRY_DATA.items():
        gdp = info.get('gdp_usd_2024')
        if gdp is None:
            continue
        try:
            gdp_value = float(gdp)
        except (ValueError, TypeError):
            continue
        rows.append({
            "iso3": iso3,
            "country": info.get('name', iso3),
            "gdp_2024_billion": round(gdp_value, 2),
            "growth_2024": _parse_growth_pct(info.get('growth_forecast_2024')),
            "growth_projection_2025": info.get('growth_projection_2025') or '',
            "data_source": info.get('data_source', 'Banque Mondiale (WDI 2024)'),
        })
    rows.sort(key=lambda r: r["gdp_2024_billion"], reverse=True)
    top10 = rows[:10]
    for idx, r in enumerate(top10, start=1):
        r["rank"] = idx
    return top10


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
    Count total verified national tariff positions across all 54 countries.

    Priority order (the highest reflects what the calculator actually serves):
      1. Live tariff_data_service stats (HS6 lines + sub-positions)
      2. Live crawled_data_service stats (authentic positions)
      3. Disk fallback: engine/output/*_canonical.jsonl line count
      4. Last-resort estimate from JSON tariff files
    """
    # 1) Live tariff data service (most comprehensive — combines HS6 + sub-positions)
    try:
        from services.tariff_data_service import tariff_service
        stats = tariff_service.get_stats()
        total = stats.get("total_positions") or (
            (stats.get("total_hs6_lines") or 0)
            + (stats.get("total_sub_positions") or 0)
        )
        if total and total > 0:
            return int(total)
    except Exception:
        pass

    # 2) Crawled data service
    try:
        from services.crawled_data_service import crawled_service
        stats = crawled_service.get_stats()
        total = stats.get("total_positions", 0)
        if total and total > 0:
            return int(total)
    except Exception:
        pass

    # 3) Disk fallback — engine canonical files
    backend_dir = Path(__file__).parent.parent
    engine_dir = backend_dir.parent / "engine" / "output"
    total_positions = 0
    if engine_dir.exists():
        for canonical_file in engine_dir.glob("*_canonical.jsonl"):
            try:
                with open(canonical_file, 'r', encoding='utf-8') as f:
                    total_positions += sum(1 for _ in f)
            except Exception:
                continue

    # 4) Last-resort estimate
    if total_positions == 0:
        data_dir = backend_dir / "data"
        total_positions = len(list(data_dir.glob("*_tariffs.json"))) * 4200

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
