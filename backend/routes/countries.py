"""
Countries routes - Country profiles, lists and economic data
54 African countries members of the AfCFTA
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import json
import unicodedata
from pathlib import Path

from country_data import get_country_data, REAL_COUNTRY_DATA
from constants import AFRICAN_COUNTRIES
from data_loader import (
    get_country_commerce_profile,
    get_country_customs_info,
)
from projects_data import get_country_ongoing_projects
from models import CountryInfo, CountryEconomicProfile
from translations import translate_country_name, translate_region
from gold_reserves_data import GOLD_RESERVES_GAI_DATA

router = APIRouter()

@router.get("/countries")
async def get_countries(lang: str = "fr"):
    """Récupérer la liste des pays membres de la ZLECAf avec traduction
    
    Retourne ISO3 comme code principal, ISO2 conservé pour compatibilité (drapeaux)
    """
    countries = []
    for country in AFRICAN_COUNTRIES:
        translated_country = {
            "code": country["iso3"],
            "iso2": country["code"],
            "iso3": country["iso3"],
            "name": translate_country_name(country["code"], lang),
            "region": translate_region(country["region"], lang),
            "wb_code": country.get("wb_code", country["iso3"]),
            "population": country["population"]
        }
        countries.append(CountryInfo(**translated_country))
    return countries

@router.get("/country-profile/{country_code}")
async def get_country_profile(country_code: str) -> CountryEconomicProfile:
    """Récupérer le profil économique complet d'un pays avec données réelles et commerce 2024
    
    Accepte les codes ISO2 (ex: DZ) ou ISO3 (ex: DZA)
    """
    code_upper = country_code.upper()
    
    # Chercher par ISO3 d'abord, puis ISO2 (rétrocompatibilité)
    country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == code_upper), None)
    if not country:
        country = next((c for c in AFRICAN_COUNTRIES if c['code'] == code_upper), None)
    
    if not country:
        raise HTTPException(status_code=404, detail="Pays non trouvé dans la ZLECAf")
    
    # Utiliser ISO3 pour toutes les requêtes de données
    iso3_code = country['iso3']
    
    # Récupérer les données de commerce enrichies 2024
    commerce_data = get_country_commerce_profile(iso3_code)
    
    # Récupérer les données réelles du pays (fallback)
    real_data = get_country_data(iso3_code)
    
    # Helper function for name normalization
    def normalize_name(s):
        s = s.replace('\u2019', "'").replace('\u2018', "'")
        normalized = unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode('ascii')
        return normalized
    
    # Construire le profil avec données commerce 2024 en priorité
    if commerce_data:
        profile = CountryEconomicProfile(
            country_code=iso3_code,
            country_name=commerce_data['country'],
            population=int(commerce_data['population_2024_million'] * 1000000) if commerce_data['population_2024_million'] else country['population'],
            region=country['region']
        )
        
        # Données économiques 2024
        profile.gdp_usd = commerce_data['gdp_2024_billion_usd'] * 1000000000 if commerce_data['gdp_2024_billion_usd'] else None
        profile.gdp_per_capita = commerce_data['gdp_per_capita_2024']
        profile.inflation_rate = commerce_data.get('inflation_2024')
        profile.unemployment_rate = commerce_data.get('unemployment_2024')
        profile.hdi = commerce_data.get('hdi_2024')
        profile.hdi_rank = commerce_data.get('hdi_rank_2024')
        profile.population_millions = commerce_data.get('population_2024_million')
        
        # Projections enrichies avec données commerce
        profile.projections = {
            "gdp_growth_forecast_2024": f"{commerce_data['growth_rate_2024']}%" if commerce_data['growth_rate_2024'] else '3.0%',
            "gdp_growth_projection_2025": real_data.get('growth_projection_2025', '3.2%'),
            "gdp_growth_projection_2026": real_data.get('growth_projection_2026', '3.5%'),
            "development_index": commerce_data['hdi_2024'] if commerce_data['hdi_2024'] else 0.500,
            "africa_rank": real_data.get('africa_rank', 25),
            "key_sectors": [f"{sector['name']} ({sector['pib_share']}% PIB): {sector['description']}" 
                           for sector in real_data.get('key_sectors', [])],
            "zlecaf_potential_level": real_data.get('zlecaf_potential', {}).get('level', 'Modéré'),
            "zlecaf_potential_description": real_data.get('zlecaf_potential', {}).get('description', ''),
            "zlecaf_opportunities": real_data.get('zlecaf_potential', {}).get('key_opportunities', []),
            "main_exports": commerce_data['export_products'],
            "main_imports": commerce_data['import_products'],
            "export_partners": commerce_data['export_partners'],
            "import_partners": commerce_data['import_partners'],
            "exports_2024_billion_usd": commerce_data['exports_2024_billion_usd'],
            "imports_2024_billion_usd": commerce_data['imports_2024_billion_usd'],
            "trade_balance_2024_billion_usd": commerce_data['trade_balance_2024_billion_usd'],
            "zlecaf_ratified": commerce_data['zlecaf_ratified'],
            "zlecaf_ratification_date": commerce_data['zlecaf_ratification_date'],
            "investment_climate_score": "B+",
            "infrastructure_index": 6.7,
            "business_environment_rank": real_data.get('africa_rank', 25),
            "international_ports": commerce_data.get('infrastructure', {}).get('international_ports', 2),
            "domestic_ports": commerce_data.get('infrastructure', {}).get('domestic_ports', 5),
            "international_airports": commerce_data.get('infrastructure', {}).get('international_airports', 2),
            "domestic_airports": commerce_data.get('infrastructure', {}).get('domestic_airports', 10),
            "railways_km": commerce_data.get('infrastructure', {}).get('railways_km', 0),
            "external_debt_gdp_pct": commerce_data.get('infrastructure', {}).get('external_debt_pct_gdp', 60.0),
            "energy_cost_kwh": commerce_data.get('infrastructure', {}).get('energy_cost_usd_kwh', 0.20)
        }
        
        # World Bank Data360 indicators
        wb_data = commerce_data.get('world_bank_data', {})
        if wb_data:
            for key, value in wb_data.items():
                if value is not None:
                    profile.projections[key] = value
        
        # Gold reserves data
        gold_data = GOLD_RESERVES_GAI_DATA['gold_reserves'].get(country['iso3'], {})
        if gold_data:
            profile.projections['gold_reserves_tonnes'] = gold_data.get('tonnes', 0.0)
            profile.projections['gold_reserves_rank_africa'] = gold_data.get('rank_africa')
            profile.projections['gold_reserves_rank_global'] = gold_data.get('rank_global')
        
        # Global Attractiveness Index 2025
        gai_data = GOLD_RESERVES_GAI_DATA['global_attractiveness_index_2025'].get(country['iso3'], {})
        if gai_data:
            profile.projections['gai_2025_score'] = gai_data.get('score')
            profile.projections['gai_2025_rank_africa'] = gai_data.get('rank_africa')
            profile.projections['gai_2025_rank_global'] = gai_data.get('rank_global')
            profile.projections['gai_2025_rating'] = gai_data.get('rating')
            profile.projections['gai_2025_trend'] = gai_data.get('trend')
        
        # Notations de risque 2024
        profile.risk_ratings = commerce_data['ratings']
        
        # Customs information
        customs_info = get_country_customs_info(commerce_data['country'])
        profile.customs = customs_info if customs_info else {}
        
        # Infrastructure ranking
        country_search_name = commerce_data['country']
        infra_ranking = None
        
        try:
            infra_path = Path(__file__).parent.parent.parent / 'classement_infrastructure_afrique.json'
            with open(infra_path, 'r') as f:
                infra_data = json.load(f)
            
            search_name = normalize_name(country_search_name)
            
            for entry in infra_data:
                entry_name = normalize_name(entry['pays'])
                if entry_name == search_name or search_name in entry_name or entry_name in search_name:
                    infra_ranking = {
                        'africa_rank': entry['rang_afrique'],
                        'lpi_infrastructure_score': entry['score_infrastructure_ipl'],
                        'lpi_world_rank': entry['rang_mondial_ipl'],
                        'aidi_transport_score': entry.get('score_aidi_2024', entry.get('score_transport_aidi', 0))
                    }
                    break
        except Exception as e:
            logging.error(f"Erreur chargement infrastructure: {e}")
        
        # Projets structurants
        profile.ongoing_projects = get_country_ongoing_projects(iso3_code)
        profile.infrastructure_ranking = infra_ranking if infra_ranking else {}
    else:
        # Fallback to old data
        profile = CountryEconomicProfile(
            country_code=country['code'],
            country_name=country['name'],
            population=real_data.get('population_2024', country['population']),
            region=country['region']
        )
        
        profile.gdp_usd = real_data.get('gdp_usd_2024')
        profile.gdp_per_capita = real_data.get('gdp_per_capita_2024')
        profile.inflation_rate = None
        
        profile.projections = {
            "gdp_growth_forecast_2024": real_data.get('growth_forecast_2024', '3.0%'),
            "gdp_growth_projection_2025": real_data.get('growth_projection_2025', '3.2%'),
            "gdp_growth_projection_2026": real_data.get('growth_projection_2026', '3.5%'),
            "development_index": real_data.get('development_index', 0.500),
            "africa_rank": real_data.get('africa_rank', 25),
        }
        
        profile.risk_ratings = {}
        profile.customs = {}
        profile.ongoing_projects = get_country_ongoing_projects(iso3_code)
        profile.infrastructure_ranking = {}
    
    return profile
