"""
Statistics routes - Trade statistics, UNCTAD data, trade products
Comprehensive statistics for African trade and ZLECAf analysis
"""
from fastapi import APIRouter, Query
from typing import Optional

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
