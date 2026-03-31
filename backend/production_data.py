"""
Production Africaine - Gestion des données de production (Agriculture, Industrie, Mines)
Charge et expose les données de production pour 2021-2024
"""

import json
import os
from typing import List, Dict, Optional

# Chemin du fichier JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'json', 'production_africaine.json')

# Cache global
_production_data = None

def load_production_data():
    """Charge les données de production depuis le fichier JSON"""
    global _production_data
    if _production_data is None:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                _production_data = json.load(f)
            print(f"✅ Loaded production data from {DATA_FILE}")
            print(f"   - Value added macro: {len(_production_data.get('value_added_macro', []))} records")
            print(f"   - Agriculture FAOSTAT: {len(_production_data.get('agri_faostat', []))} records")
            print(f"   - Manufacturing UNIDO: {len(_production_data.get('manufacturing_unido', []))} records")
            print(f"   - Mining USGS: {len(_production_data.get('mining_usgs', []))} records")
        except FileNotFoundError:
            print(f"❌ File not found: {DATA_FILE}")
            _production_data = {
                "value_added_macro": [],
                "agri_faostat": [],
                "manufacturing_unido": [],
                "mining_usgs": []
            }
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            _production_data = {
                "value_added_macro": [],
                "agri_faostat": [],
                "manufacturing_unido": [],
                "mining_usgs": []
            }
    return _production_data

# ==========================================
# VALUE ADDED MACRO (WDI/WEO)
# ==========================================

def get_value_added(country_iso3: Optional[str] = None, 
                    year: Optional[int] = None,
                    sector: Optional[str] = None) -> List[Dict]:
    """
    Récupère les données de valeur ajoutée macro
    
    Args:
        country_iso3: Code ISO3 du pays (ex: 'ZAF')
        year: Année (2021-2024)
        sector: Section ISIC (A, B-F, C)
    """
    data = load_production_data()
    records = data.get('value_added_macro', [])
    
    if country_iso3:
        records = [r for r in records if r.get('country_iso3') == country_iso3]
    
    if year:
        records = [r for r in records if r.get('year') == year]
    
    if sector:
        records = [r for r in records if r.get('sector_isic_section') == sector]
    
    return records

def get_value_added_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les séries de valeur ajoutée pour un pays"""
    records = get_value_added(country_iso3=country_iso3)
    
    # Organiser par secteur
    by_sector = {}
    for record in records:
        sector = record.get('sector_detail', 'Unknown')
        if sector not in by_sector:
            by_sector[sector] = []
        by_sector[sector].append(record)
    
    return {
        'country_iso3': country_iso3,
        'country_name': records[0].get('country_name') if records else None,
        'data_by_sector': by_sector,
        'total_records': len(records)
    }

# ==========================================
# AGRICULTURE FAOSTAT
# ==========================================

def get_agriculture_production(country_iso3: Optional[str] = None,
                               year: Optional[int] = None,
                               commodity: Optional[str] = None) -> List[Dict]:
    """
    Récupère les données de production agricole
    
    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        commodity: Nom ou code du produit (ex: 'Maize', '0015')
    """
    data = load_production_data()
    records = data.get('agri_faostat', [])
    
    if country_iso3:
        records = [r for r in records if r.get('country_iso3') == country_iso3]
    
    if year:
        records = [r for r in records if r.get('year') == year]
    
    if commodity:
        records = [r for r in records 
                  if commodity.lower() in r.get('commodity_label', '').lower() 
                  or commodity == r.get('commodity_code')]
    
    return records

def get_agriculture_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions agricoles pour un pays"""
    records = get_agriculture_production(country_iso3=country_iso3)
    
    # Organiser par produit
    by_commodity = {}
    for record in records:
        commodity = record.get('commodity_label', 'Unknown')
        if commodity not in by_commodity:
            by_commodity[commodity] = []
        by_commodity[commodity].append(record)
    
    return {
        'country_iso3': country_iso3,
        'country_name': records[0].get('country_name') if records else None,
        'data_by_commodity': by_commodity,
        'total_records': len(records)
    }

# ==========================================
# MANUFACTURING UNIDO
# ==========================================

def get_manufacturing_production(country_iso3: Optional[str] = None,
                                year: Optional[int] = None,
                                isic_code: Optional[str] = None) -> List[Dict]:
    """
    Récupère les données de production manufacturière
    
    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        isic_code: Code ISIC Rev.4 (ex: '10', '11', '13')
    """
    data = load_production_data()
    records = data.get('manufacturing_unido', [])
    
    if country_iso3:
        records = [r for r in records if r.get('country_iso3') == country_iso3]
    
    if year:
        records = [r for r in records if r.get('year') == year]
    
    if isic_code:
        records = [r for r in records if r.get('isic_code') == isic_code]
    
    return records

def get_manufacturing_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions manufacturières pour un pays"""
    records = get_manufacturing_production(country_iso3=country_iso3)
    
    # Organiser par secteur ISIC
    by_isic = {}
    for record in records:
        isic = f"{record.get('isic_code')} - {record.get('isic_label', 'Unknown')}"
        if isic not in by_isic:
            by_isic[isic] = []
        by_isic[isic].append(record)
    
    return {
        'country_iso3': country_iso3,
        'country_name': records[0].get('country_name') if records else None,
        'data_by_isic': by_isic,
        'total_records': len(records)
    }

# ==========================================
# MINING USGS
# ==========================================

def get_mining_production(country_iso3: Optional[str] = None,
                         year: Optional[int] = None,
                         commodity: Optional[str] = None) -> List[Dict]:
    """
    Récupère les données de production minière
    
    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        commodity: Nom ou code du minerai (ex: 'Gold', 'AU')
    """
    data = load_production_data()
    records = data.get('mining_usgs', [])
    
    if country_iso3:
        records = [r for r in records if r.get('country_iso3') == country_iso3]
    
    if year:
        records = [r for r in records if r.get('year') == year]
    
    if commodity:
        records = [r for r in records 
                  if commodity.lower() in r.get('commodity_label', '').lower()
                  or commodity.upper() == r.get('commodity_code')]
    
    return records

def get_mining_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions minières pour un pays"""
    records = get_mining_production(country_iso3=country_iso3)
    
    # Organiser par minerai
    by_commodity = {}
    for record in records:
        commodity = record.get('commodity_label', 'Unknown')
        if commodity not in by_commodity:
            by_commodity[commodity] = []
        by_commodity[commodity].append(record)
    
    return {
        'country_iso3': country_iso3,
        'country_name': records[0].get('country_name') if records else None,
        'data_by_commodity': by_commodity,
        'total_records': len(records)
    }

# ==========================================
# STATISTICS & OVERVIEW
# ==========================================

def get_production_statistics() -> Dict:
    """Calcule des statistiques globales sur les données de production"""
    data = load_production_data()
    
    # Compter les pays uniques dans chaque dimension
    countries_va = set(r.get('country_iso3') for r in data.get('value_added_macro', []))
    countries_agri = set(r.get('country_iso3') for r in data.get('agri_faostat', []))
    countries_manuf = set(r.get('country_iso3') for r in data.get('manufacturing_unido', []))
    countries_mining = set(r.get('country_iso3') for r in data.get('mining_usgs', []))
    
    all_countries = countries_va | countries_agri | countries_manuf | countries_mining
    
    # Années couvertes
    years_va = set(r.get('year') for r in data.get('value_added_macro', []))
    years_agri = set(r.get('year') for r in data.get('agri_faostat', []))
    years_manuf = set(r.get('year') for r in data.get('manufacturing_unido', []))
    years_mining = set(r.get('year') for r in data.get('mining_usgs', []))
    
    all_years = sorted(years_va | years_agri | years_manuf | years_mining)
    
    return {
        'total_countries': len(all_countries),
        'countries_list': sorted(list(all_countries)),
        'years_covered': all_years,
        'dimensions': {
            'value_added_macro': {
                'total_records': len(data.get('value_added_macro', [])),
                'countries': len(countries_va),
                'years': sorted(list(years_va))
            },
            'agriculture_faostat': {
                'total_records': len(data.get('agri_faostat', [])),
                'countries': len(countries_agri),
                'years': sorted(list(years_agri))
            },
            'manufacturing_unido': {
                'total_records': len(data.get('manufacturing_unido', [])),
                'countries': len(countries_manuf),
                'years': sorted(list(years_manuf))
            },
            'mining_usgs': {
                'total_records': len(data.get('mining_usgs', [])),
                'countries': len(countries_mining),
                'years': sorted(list(years_mining))
            }
        }
    }

def get_country_production_overview(country_iso3: str) -> Dict:
    """Vue d'ensemble complète de la production pour un pays"""
    return {
        'country_iso3': country_iso3,
        'value_added': get_value_added_by_country(country_iso3),
        'agriculture': get_agriculture_by_country(country_iso3),
        'manufacturing': get_manufacturing_by_country(country_iso3),
        'mining': get_mining_by_country(country_iso3)
    }

# Initialize data on module import
load_production_data()
