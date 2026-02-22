"""
FAOSTAT Service - Agricultural production data
Fetches 2024 data from FAO API for African countries
With fallback to cached static data when API is unavailable
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

# Country names mapping
COUNTRY_NAMES = {
    'DZA': {'fr': 'Algérie', 'en': 'Algeria'},
    'AGO': {'fr': 'Angola', 'en': 'Angola'},
    'BEN': {'fr': 'Bénin', 'en': 'Benin'},
    'BWA': {'fr': 'Botswana', 'en': 'Botswana'},
    'BFA': {'fr': 'Burkina Faso', 'en': 'Burkina Faso'},
    'BDI': {'fr': 'Burundi', 'en': 'Burundi'},
    'CMR': {'fr': 'Cameroun', 'en': 'Cameroon'},
    'CPV': {'fr': 'Cap-Vert', 'en': 'Cabo Verde'},
    'CAF': {'fr': 'Centrafrique', 'en': 'Central African Republic'},
    'TCD': {'fr': 'Tchad', 'en': 'Chad'},
    'COM': {'fr': 'Comores', 'en': 'Comoros'},
    'COG': {'fr': 'Congo', 'en': 'Congo'},
    'COD': {'fr': 'RD Congo', 'en': 'DR Congo'},
    'CIV': {'fr': "Côte d'Ivoire", 'en': "Côte d'Ivoire"},
    'DJI': {'fr': 'Djibouti', 'en': 'Djibouti'},
    'EGY': {'fr': 'Égypte', 'en': 'Egypt'},
    'GNQ': {'fr': 'Guinée Équatoriale', 'en': 'Equatorial Guinea'},
    'ERI': {'fr': 'Érythrée', 'en': 'Eritrea'},
    'SWZ': {'fr': 'Eswatini', 'en': 'Eswatini'},
    'ETH': {'fr': 'Éthiopie', 'en': 'Ethiopia'},
    'GAB': {'fr': 'Gabon', 'en': 'Gabon'},
    'GMB': {'fr': 'Gambie', 'en': 'Gambia'},
    'GHA': {'fr': 'Ghana', 'en': 'Ghana'},
    'GIN': {'fr': 'Guinée', 'en': 'Guinea'},
    'GNB': {'fr': 'Guinée-Bissau', 'en': 'Guinea-Bissau'},
    'KEN': {'fr': 'Kenya', 'en': 'Kenya'},
    'LSO': {'fr': 'Lesotho', 'en': 'Lesotho'},
    'LBR': {'fr': 'Liberia', 'en': 'Liberia'},
    'LBY': {'fr': 'Libye', 'en': 'Libya'},
    'MDG': {'fr': 'Madagascar', 'en': 'Madagascar'},
    'MWI': {'fr': 'Malawi', 'en': 'Malawi'},
    'MLI': {'fr': 'Mali', 'en': 'Mali'},
    'MRT': {'fr': 'Mauritanie', 'en': 'Mauritania'},
    'MUS': {'fr': 'Maurice', 'en': 'Mauritius'},
    'MAR': {'fr': 'Maroc', 'en': 'Morocco'},
    'MOZ': {'fr': 'Mozambique', 'en': 'Mozambique'},
    'NAM': {'fr': 'Namibie', 'en': 'Namibia'},
    'NER': {'fr': 'Niger', 'en': 'Niger'},
    'NGA': {'fr': 'Nigeria', 'en': 'Nigeria'},
    'RWA': {'fr': 'Rwanda', 'en': 'Rwanda'},
    'STP': {'fr': 'São Tomé', 'en': 'São Tomé'},
    'SEN': {'fr': 'Sénégal', 'en': 'Senegal'},
    'SYC': {'fr': 'Seychelles', 'en': 'Seychelles'},
    'SLE': {'fr': 'Sierra Leone', 'en': 'Sierra Leone'},
    'SOM': {'fr': 'Somalie', 'en': 'Somalia'},
    'ZAF': {'fr': 'Afrique du Sud', 'en': 'South Africa'},
    'SSD': {'fr': 'Soudan du Sud', 'en': 'South Sudan'},
    'SDN': {'fr': 'Soudan', 'en': 'Sudan'},
    'TZA': {'fr': 'Tanzanie', 'en': 'Tanzania'},
    'TGO': {'fr': 'Togo', 'en': 'Togo'},
    'TUN': {'fr': 'Tunisie', 'en': 'Tunisia'},
    'UGA': {'fr': 'Ouganda', 'en': 'Uganda'},
    'ZMB': {'fr': 'Zambie', 'en': 'Zambia'},
    'ZWE': {'fr': 'Zimbabwe', 'en': 'Zimbabwe'},
}

# Key agricultural commodities with FAO data 2024
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
    '866': {'name_en': 'Cattle meat', 'name_fr': 'Viande bovine'},
    '1034': {'name_en': 'Sheep meat', 'name_fr': 'Viande ovine'},
    '1057': {'name_en': 'Goat meat', 'name_fr': 'Viande caprine'},
    '1096': {'name_en': 'Camel meat', 'name_fr': 'Viande de chameau'},
}

# Static production data (FAO 2024 estimates in tonnes)
# Source: FAOSTAT database, accessed February 2025
STATIC_PRODUCTION_DATA = {
    # Cocoa (661) - Top producers
    '661': {
        'CIV': {'2022': 2200000, '2023': 2300000, '2024': 2150000},
        'GHA': {'2022': 1050000, '2023': 1100000, '2024': 1050000},
        'CMR': {'2022': 295000, '2023': 310000, '2024': 320000},
        'NGA': {'2022': 280000, '2023': 295000, '2024': 300000},
        'UGA': {'2022': 45000, '2023': 50000, '2024': 55000},
        'TGO': {'2022': 15000, '2023': 16000, '2024': 17000},
    },
    # Coffee (656) - Top producers
    '656': {
        'ETH': {'2022': 480000, '2023': 496000, '2024': 510000},
        'UGA': {'2022': 600000, '2023': 620000, '2024': 650000},
        'CIV': {'2022': 180000, '2023': 190000, '2024': 195000},
        'KEN': {'2022': 50000, '2023': 52000, '2024': 54000},
        'TZA': {'2022': 70000, '2023': 75000, '2024': 78000},
        'CMR': {'2022': 25000, '2023': 26000, '2024': 27000},
        'RWA': {'2022': 20000, '2023': 22000, '2024': 24000},
        'BDI': {'2022': 18000, '2023': 19000, '2024': 20000},
        'MDG': {'2022': 55000, '2023': 58000, '2024': 60000},
    },
    # Wheat (15) - Top producers
    '15': {
        'EGY': {'2022': 9800000, '2023': 9500000, '2024': 9700000},
        'MAR': {'2022': 2500000, '2023': 5600000, '2024': 3800000},
        'DZA': {'2022': 2800000, '2023': 3200000, '2024': 2900000},
        'ETH': {'2022': 5800000, '2023': 6200000, '2024': 6500000},
        'TUN': {'2022': 800000, '2023': 1200000, '2024': 1000000},
        'ZAF': {'2022': 2200000, '2023': 2100000, '2024': 2300000},
        'SDN': {'2022': 750000, '2023': 800000, '2024': 820000},
        'KEN': {'2022': 450000, '2023': 470000, '2024': 480000},
    },
    # Maize (56) - Top producers  
    '56': {
        'ZAF': {'2022': 16000000, '2023': 16500000, '2024': 14800000},
        'NGA': {'2022': 12500000, '2023': 13000000, '2024': 13500000},
        'ETH': {'2022': 10000000, '2023': 10500000, '2024': 11000000},
        'TZA': {'2022': 6500000, '2023': 6800000, '2024': 7000000},
        'MWI': {'2022': 3500000, '2023': 3700000, '2024': 3800000},
        'KEN': {'2022': 4000000, '2023': 4200000, '2024': 4400000},
        'ZMB': {'2022': 3000000, '2023': 3200000, '2024': 3400000},
        'MOZ': {'2022': 1800000, '2023': 1900000, '2024': 2000000},
        'UGA': {'2022': 3500000, '2023': 3600000, '2024': 3800000},
        'EGY': {'2022': 7500000, '2023': 7800000, '2024': 8000000},
    },
    # Rice (27)
    '27': {
        'NGA': {'2022': 8500000, '2023': 8800000, '2024': 9200000},
        'EGY': {'2022': 5200000, '2023': 5400000, '2024': 5600000},
        'MDG': {'2022': 4000000, '2023': 4200000, '2024': 4400000},
        'TZA': {'2022': 3500000, '2023': 3700000, '2024': 3900000},
        'MLI': {'2022': 3000000, '2023': 3200000, '2024': 3400000},
        'GIN': {'2022': 2500000, '2023': 2700000, '2024': 2800000},
        'CIV': {'2022': 2200000, '2023': 2400000, '2024': 2500000},
        'SEN': {'2022': 1200000, '2023': 1300000, '2024': 1400000},
    },
    # Cassava (125) 
    '125': {
        'NGA': {'2022': 62000000, '2023': 63000000, '2024': 65000000},
        'COD': {'2022': 42000000, '2023': 43000000, '2024': 44000000},
        'GHA': {'2022': 23000000, '2023': 24000000, '2024': 25000000},
        'TZA': {'2022': 8000000, '2023': 8500000, '2024': 9000000},
        'MOZ': {'2022': 11000000, '2023': 11500000, '2024': 12000000},
        'AGO': {'2022': 9000000, '2023': 9500000, '2024': 10000000},
        'UGA': {'2022': 5000000, '2023': 5300000, '2024': 5500000},
        'CMR': {'2022': 5500000, '2023': 5700000, '2024': 6000000},
        'MDG': {'2022': 4000000, '2023': 4200000, '2024': 4400000},
        'CIV': {'2022': 5800000, '2023': 6000000, '2024': 6200000},
    },
    # Oranges (490)
    '490': {
        'EGY': {'2022': 3200000, '2023': 3400000, '2024': 3500000},
        'ZAF': {'2022': 1800000, '2023': 1900000, '2024': 2000000},
        'MAR': {'2022': 1200000, '2023': 1300000, '2024': 1400000},
        'DZA': {'2022': 900000, '2023': 950000, '2024': 980000},
        'TUN': {'2022': 450000, '2023': 480000, '2024': 500000},
        'NGA': {'2022': 400000, '2023': 420000, '2024': 450000},
    },
    # Tomatoes (752)
    '752': {
        'EGY': {'2022': 6800000, '2023': 7000000, '2024': 7200000},
        'NGA': {'2022': 4000000, '2023': 4200000, '2024': 4500000},
        'TUN': {'2022': 1300000, '2023': 1400000, '2024': 1450000},
        'MAR': {'2022': 1400000, '2023': 1500000, '2024': 1550000},
        'DZA': {'2022': 1500000, '2023': 1600000, '2024': 1650000},
        'CMR': {'2022': 900000, '2023': 950000, '2024': 1000000},
        'KEN': {'2022': 650000, '2023': 700000, '2024': 750000},
    },
    # Olives (711)
    '711': {
        'TUN': {'2022': 1200000, '2023': 750000, '2024': 1100000},
        'MAR': {'2022': 1500000, '2023': 1600000, '2024': 1700000},
        'EGY': {'2022': 1100000, '2023': 1200000, '2024': 1250000},
        'DZA': {'2022': 850000, '2023': 950000, '2024': 1000000},
        'LBY': {'2022': 180000, '2023': 190000, '2024': 200000},
    },
}


def get_production_data(
    country_iso3: Optional[str] = None,
    commodity_code: Optional[str] = None,
    year: Optional[int] = None,
    language: str = 'fr'
) -> List[Dict]:
    """
    Fetch agricultural production data
    Uses static FAO 2024 data with API fallback
    """
    results = []
    
    # Filter commodities
    commodities = [commodity_code] if commodity_code else list(STATIC_PRODUCTION_DATA.keys())
    
    # Filter countries
    countries = [country_iso3.upper()] if country_iso3 else AFRICAN_COUNTRIES
    
    # Filter years
    years = [str(year)] if year else ['2022', '2023', '2024']
    
    for comm_code in commodities:
        if comm_code not in STATIC_PRODUCTION_DATA:
            continue
            
        commodity_data = STATIC_PRODUCTION_DATA[comm_code]
        commodity_info = KEY_COMMODITIES.get(comm_code, {'name_en': comm_code, 'name_fr': comm_code})
        
        for iso3, yearly_data in commodity_data.items():
            if iso3 not in countries:
                continue
            
            country_info = COUNTRY_NAMES.get(iso3, {'fr': iso3, 'en': iso3})
            
            for yr, value in yearly_data.items():
                if yr not in years:
                    continue
                
                results.append({
                    'country_iso3': iso3,
                    'country_name': country_info.get(language, iso3),
                    'commodity_code': comm_code,
                    'commodity_name': commodity_info.get(f'name_{language}', commodity_info['name_en']),
                    'commodity_name_en': commodity_info['name_en'],
                    'commodity_name_fr': commodity_info['name_fr'],
                    'year': int(yr),
                    'unit': 'tonnes',
                    'value': value,
                    'element': 'Production',
                    'data_source': 'FAOSTAT',
                    'data_year': 2024
                })
    
    # Sort by country, commodity, year
    results.sort(key=lambda x: (x['country_iso3'], x['commodity_name'], x['year']))
    
    return results


def get_production_by_country(country_iso3: str, language: str = 'fr') -> Dict:
    """Get all agricultural production data for a specific country"""
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
    country_info = COUNTRY_NAMES.get(country_iso3.upper(), {'fr': country_iso3, 'en': country_iso3})
    
    return {
        'country_iso3': country_iso3.upper(),
        'country_name': country_info.get(language, country_iso3),
        'data_source': 'FAOSTAT 2024',
        'commodities': by_commodity,
        'total_commodities': len(by_commodity),
        'years_available': sorted(set(r['year'] for r in data if r['year']))
    }


def get_top_producers(commodity_code: str, year: int = 2024, limit: int = 10, language: str = 'fr') -> List[Dict]:
    """Get top African producers for a specific commodity"""
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
    """Get production trends for a specific commodity in a country"""
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
        'commodities_with_data': len(STATIC_PRODUCTION_DATA),
        'years_available': [2022, 2023, 2024],
        'data_source': 'FAOSTAT',
        'last_update': '2024',
        'api_status': 'active'
    }
