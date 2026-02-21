"""
FAOSTAT Service - Real-time agricultural production data
Fetches 2024 data from FAO API for African countries
"""
import faostat
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# Cache for FAOSTAT data
_fao_cache: Dict[str, Any] = {}
_cache_expiry: Dict[str, datetime] = {}
CACHE_DURATION = timedelta(hours=6)  # Cache for 6 hours

# African countries ISO3 codes
AFRICAN_COUNTRIES = [
    'DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CMR', 'CPV', 'CAF', 'TCD',
    'COM', 'COG', 'COD', 'CIV', 'DJI', 'EGY', 'GNQ', 'ERI', 'SWZ', 'ETH',
    'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO', 'LBR', 'LBY', 'MDG',
    'MWI', 'MLI', 'MRT', 'MUS', 'MAR', 'MOZ', 'NAM', 'NER', 'NGA', 'RWA',
    'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF', 'SSD', 'SDN', 'TZA', 'TGO',
    'TUN', 'UGA', 'ZMB', 'ZWE'
]

# FAO country codes mapping (ISO3 -> FAO Area Code)
ISO3_TO_FAO = {
    'DZA': 4, 'AGO': 7, 'BEN': 53, 'BWA': 20, 'BFA': 233, 'BDI': 29,
    'CMR': 32, 'CPV': 35, 'CAF': 37, 'TCD': 39, 'COM': 45, 'COG': 46,
    'COD': 250, 'CIV': 107, 'DJI': 72, 'EGY': 59, 'GNQ': 61, 'ERI': 178,
    'SWZ': 209, 'ETH': 238, 'GAB': 74, 'GMB': 75, 'GHA': 81, 'GIN': 90,
    'GNB': 175, 'KEN': 114, 'LSO': 122, 'LBR': 123, 'LBY': 124, 'MDG': 129,
    'MWI': 130, 'MLI': 133, 'MRT': 136, 'MUS': 137, 'MAR': 143, 'MOZ': 144,
    'NAM': 147, 'NER': 158, 'NGA': 159, 'RWA': 184, 'STP': 193, 'SEN': 195,
    'SYC': 196, 'SLE': 197, 'SOM': 201, 'ZAF': 202, 'SSD': 277, 'SDN': 276,
    'TZA': 215, 'TGO': 217, 'TUN': 222, 'UGA': 226, 'ZMB': 251, 'ZWE': 181
}

# Key agricultural commodities
KEY_COMMODITIES = {
    '15': {'name_en': 'Wheat', 'name_fr': 'Blé'},
    '27': {'name_en': 'Rice', 'name_fr': 'Riz'},
    '56': {'name_en': 'Maize', 'name_fr': 'Maïs'},
    '44': {'name_en': 'Barley', 'name_fr': 'Orge'},
    '71': {'name_en': 'Millet', 'name_fr': 'Mil'},
    '83': {'name_en': 'Sorghum', 'name_fr': 'Sorgho'},
    '116': {'name_en': 'Potatoes', 'name_fr': 'Pommes de terre'},
    '125': {'name_en': 'Cassava', 'name_fr': 'Manioc'},
    '135': {'name_en': 'Yams', 'name_fr': 'Ignames'},
    '156': {'name_en': 'Sugar cane', 'name_fr': 'Canne à sucre'},
    '176': {'name_en': 'Soybeans', 'name_fr': 'Soja'},
    '236': {'name_en': 'Groundnuts', 'name_fr': 'Arachides'},
    '267': {'name_en': 'Sunflower seed', 'name_fr': 'Tournesol'},
    '270': {'name_en': 'Sesame seed', 'name_fr': 'Sésame'},
    '328': {'name_en': 'Seed cotton', 'name_fr': 'Coton'},
    '486': {'name_en': 'Bananas', 'name_fr': 'Bananes'},
    '490': {'name_en': 'Oranges', 'name_fr': 'Oranges'},
    '515': {'name_en': 'Apples', 'name_fr': 'Pommes'},
    '526': {'name_en': 'Grapes', 'name_fr': 'Raisins'},
    '572': {'name_en': 'Mangoes', 'name_fr': 'Mangues'},
    '577': {'name_en': 'Pineapples', 'name_fr': 'Ananas'},
    '656': {'name_en': 'Coffee', 'name_fr': 'Café'},
    '661': {'name_en': 'Cocoa beans', 'name_fr': 'Cacao'},
    '667': {'name_en': 'Tea', 'name_fr': 'Thé'},
    '689': {'name_en': 'Chillies and peppers', 'name_fr': 'Piments'},
    '711': {'name_en': 'Olives', 'name_fr': 'Olives'},
    '752': {'name_en': 'Tomatoes', 'name_fr': 'Tomates'},
    '773': {'name_en': 'Onions', 'name_fr': 'Oignons'},
    '826': {'name_en': 'Tobacco', 'name_fr': 'Tabac'},
    '866': {'name_en': 'Cattle', 'name_fr': 'Bovins'},
    '1034': {'name_en': 'Sheep', 'name_fr': 'Ovins'},
    '1057': {'name_en': 'Goats', 'name_fr': 'Caprins'},
    '1096': {'name_en': 'Camels', 'name_fr': 'Chameaux'},
}

def _get_cache_key(func_name: str, **kwargs) -> str:
    """Generate cache key"""
    return f"{func_name}_{json.dumps(kwargs, sort_keys=True)}"

def _is_cache_valid(key: str) -> bool:
    """Check if cache is still valid"""
    if key not in _cache_expiry:
        return False
    return datetime.now() < _cache_expiry[key]

def _set_cache(key: str, data: Any):
    """Set cache with expiry"""
    _fao_cache[key] = data
    _cache_expiry[key] = datetime.now() + CACHE_DURATION

def _get_cache(key: str) -> Optional[Any]:
    """Get from cache if valid"""
    if _is_cache_valid(key):
        return _fao_cache.get(key)
    return None


def get_fao_areas() -> Dict[str, int]:
    """Get FAO area codes for all countries"""
    cache_key = _get_cache_key("areas")
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        areas = faostat.get_areas('QCL')
        _set_cache(cache_key, areas)
        return areas
    except Exception as e:
        logger.error(f"Error fetching FAO areas: {e}")
        return {}


def get_fao_items() -> Dict[str, str]:
    """Get FAO item codes (commodities)"""
    cache_key = _get_cache_key("items")
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        items = faostat.get_items('QCL')
        _set_cache(cache_key, items)
        return items
    except Exception as e:
        logger.error(f"Error fetching FAO items: {e}")
        return {}


def get_production_data(
    country_iso3: Optional[str] = None,
    commodity_code: Optional[str] = None,
    year: Optional[int] = None,
    language: str = 'fr'
) -> List[Dict]:
    """
    Fetch agricultural production data from FAOSTAT
    
    Args:
        country_iso3: ISO3 country code (e.g., 'MAR')
        commodity_code: FAO commodity code (e.g., '661' for Cocoa)
        year: Year (default: latest available, up to 2024)
        language: Language for descriptions ('fr' or 'en')
    
    Returns:
        List of production records
    """
    cache_key = _get_cache_key("production", country=country_iso3, commodity=commodity_code, year=year)
    cached = _get_cache(cache_key)
    if cached:
        logger.info(f"Cache hit for production data: {cache_key}")
        return cached
    
    try:
        # Build query parameters
        params = {
            'elements': [5510],  # Production Quantity
        }
        
        # Filter by country
        if country_iso3:
            fao_code = ISO3_TO_FAO.get(country_iso3)
            if fao_code:
                params['areas'] = [fao_code]
        else:
            # All African countries
            params['areas'] = [ISO3_TO_FAO[c] for c in AFRICAN_COUNTRIES if c in ISO3_TO_FAO]
        
        # Filter by commodity
        if commodity_code:
            params['items'] = [commodity_code]
        else:
            # Key commodities
            params['items'] = list(KEY_COMMODITIES.keys())
        
        # Filter by year
        if year:
            params['years'] = [year]
        else:
            # Get last 4 years
            params['years'] = [2021, 2022, 2023, 2024]
        
        # Fetch data
        logger.info(f"Fetching FAOSTAT data with params: {params}")
        raw_data = faostat.get_data('QCL', pars=params)
        
        # Transform to structured format
        results = []
        fao_to_iso3 = {v: k for k, v in ISO3_TO_FAO.items()}
        
        for record in raw_data:
            # record format: (dataset, area_code, area, element_code, element, item_code, item, year_code, year, unit, value, flag)
            if len(record) >= 11:
                area_code = record[1]
                iso3 = fao_to_iso3.get(int(area_code) if area_code else 0, 'UNK')
                item_code = str(record[5])
                commodity_info = KEY_COMMODITIES.get(item_code, {'name_en': record[6], 'name_fr': record[6]})
                
                results.append({
                    'country_iso3': iso3,
                    'country_name': record[2],
                    'commodity_code': item_code,
                    'commodity_name': commodity_info.get(f'name_{language}', record[6]),
                    'commodity_name_en': commodity_info.get('name_en', record[6]),
                    'commodity_name_fr': commodity_info.get('name_fr', record[6]),
                    'year': int(record[8]) if record[8] else None,
                    'unit': record[9],
                    'value': float(record[10]) if record[10] else 0,
                    'element': record[4],
                    'data_source': 'FAOSTAT',
                    'data_year': 2024
                })
        
        # Sort by country, commodity, year
        results.sort(key=lambda x: (x['country_iso3'], x['commodity_name'], x['year'] or 0))
        
        _set_cache(cache_key, results)
        logger.info(f"Fetched {len(results)} production records from FAOSTAT")
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching FAOSTAT data: {e}")
        return []


def get_production_by_country(country_iso3: str, language: str = 'fr') -> Dict:
    """
    Get all agricultural production data for a specific country
    
    Args:
        country_iso3: ISO3 country code
        language: Language for descriptions
    
    Returns:
        Dictionary with production data organized by commodity
    """
    data = get_production_data(country_iso3=country_iso3, language=language)
    
    # Organize by commodity
    by_commodity = {}
    for record in data:
        commodity = record['commodity_name']
        if commodity not in by_commodity:
            by_commodity[commodity] = {
                'commodity_code': record['commodity_code'],
                'commodity_name_fr': record['commodity_name_fr'],
                'commodity_name_en': record['commodity_name_en'],
                'unit': record['unit'],
                'years': {}
            }
        by_commodity[commodity]['years'][record['year']] = record['value']
    
    # Get country name
    country_name = data[0]['country_name'] if data else country_iso3
    
    return {
        'country_iso3': country_iso3,
        'country_name': country_name,
        'data_source': 'FAOSTAT 2024',
        'commodities': by_commodity,
        'total_commodities': len(by_commodity),
        'years_available': sorted(set(r['year'] for r in data if r['year']))
    }


def get_top_producers(commodity_code: str, year: int = 2023, limit: int = 10, language: str = 'fr') -> List[Dict]:
    """
    Get top African producers for a specific commodity
    
    Args:
        commodity_code: FAO commodity code
        year: Year
        limit: Number of top producers
        language: Language for descriptions
    
    Returns:
        List of top producing countries
    """
    data = get_production_data(commodity_code=commodity_code, year=year, language=language)
    
    # Aggregate by country
    by_country = {}
    for record in data:
        iso3 = record['country_iso3']
        if iso3 not in by_country:
            by_country[iso3] = {
                'country_iso3': iso3,
                'country_name': record['country_name'],
                'commodity': record['commodity_name'],
                'value': 0,
                'unit': record['unit']
            }
        by_country[iso3]['value'] += record['value']
    
    # Sort by value descending
    sorted_countries = sorted(by_country.values(), key=lambda x: x['value'], reverse=True)
    
    # Add rank
    for i, country in enumerate(sorted_countries[:limit], 1):
        country['rank'] = i
    
    return sorted_countries[:limit]


def get_production_trends(country_iso3: str, commodity_code: str, language: str = 'fr') -> Dict:
    """
    Get production trends for a specific commodity in a country
    
    Args:
        country_iso3: ISO3 country code
        commodity_code: FAO commodity code
        language: Language
    
    Returns:
        Dictionary with trend data
    """
    data = get_production_data(country_iso3=country_iso3, commodity_code=commodity_code, language=language)
    
    # Sort by year
    data.sort(key=lambda x: x['year'] or 0)
    
    if not data:
        return {
            'country_iso3': country_iso3,
            'commodity_code': commodity_code,
            'trend': 'no_data',
            'data': []
        }
    
    # Calculate trend
    years_data = [(r['year'], r['value']) for r in data if r['year'] and r['value']]
    
    if len(years_data) >= 2:
        first_value = years_data[0][1]
        last_value = years_data[-1][1]
        change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
        
        if change_pct > 5:
            trend = 'increasing'
        elif change_pct < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'insufficient_data'
        change_pct = 0
    
    return {
        'country_iso3': country_iso3,
        'commodity': data[0]['commodity_name'] if data else commodity_code,
        'trend': trend,
        'change_percent': round(change_pct, 1),
        'data': [{'year': r['year'], 'value': r['value'], 'unit': r['unit']} for r in data],
        'data_source': 'FAOSTAT 2024'
    }


def get_commodity_list(language: str = 'fr') -> List[Dict]:
    """Get list of key commodities with translations"""
    return [
        {
            'code': code,
            'name': info.get(f'name_{language}', info['name_en']),
            'name_fr': info['name_fr'],
            'name_en': info['name_en']
        }
        for code, info in KEY_COMMODITIES.items()
    ]


def get_faostat_statistics() -> Dict:
    """Get statistics about available FAOSTAT data"""
    return {
        'total_african_countries': len(AFRICAN_COUNTRIES),
        'total_commodities_tracked': len(KEY_COMMODITIES),
        'years_available': [2021, 2022, 2023, 2024],
        'data_source': 'FAOSTAT',
        'last_update': '2024',
        'api_status': 'active'
    }
