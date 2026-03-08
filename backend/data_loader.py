"""
Data loader for ZLECAf 2024 enhanced commerce and economic data
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).parent.parent

# Load the corrections and enhanced statistics
def load_corrections_data():
    """Load the 2024 corrections JSON with tariffs and enhanced statistics"""
    corrections_path = ROOT_DIR / "zlecaf_corrections_2024.json"
    with open(corrections_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load the complete commerce data
def load_commerce_data():
    """Load the enriched 2024 commerce data for all 54 countries"""
    commerce_path = ROOT_DIR / "ZLECAf_ENRICHI_2024_COMMERCE.csv"
    df = pd.read_csv(commerce_path)
    return df

# Load the complete country economic data
def load_country_economic_data():
    """Load the complete economic data for 54 countries"""
    economic_path = ROOT_DIR / "ZLECAF_54_PAYS_DONNEES_COMPLETES.csv"
    df = pd.read_csv(economic_path)
    return df

# Get country profile from commerce data
def get_country_commerce_profile(country_code: str) -> Optional[Dict]:
    """Get detailed commerce profile for a specific country"""
    df = load_commerce_data()
    
    # Match by Code_ISO
    country_row = df[df['Code_ISO'] == country_code.upper()]
    
    if country_row.empty:
        return None
    
    row = country_row.iloc[0]
    
    # Extract export products
    export_products = []
    for i in range(1, 6):
        col = f'Export_Produit_{i}'
        if col in row and pd.notna(row[col]):
            export_products.append(row[col])
    
    # Extract import products
    import_products = []
    for i in range(1, 6):
        col = f'Import_Produit_{i}'
        if col in row and pd.notna(row[col]):
            import_products.append(row[col])
    
    # Extract trading partners
    export_partners = []
    for i in range(1, 3):
        col = f'Partenaire_Export_{i}'
        if col in row and pd.notna(row[col]):
            export_partners.append(row[col])
    
    import_partners = []
    for i in range(1, 3):
        col = f'Partenaire_Import_{i}'
        if col in row and pd.notna(row[col]):
            import_partners.append(row[col])
    
    # Extract credit ratings
    ratings = {
        'sp': row.get('S_P_Rating_2024', 'NR'),
        'moodys': row.get('Moodys_Rating_2024', 'NR'),
        'fitch': row.get('Fitch_Rating_2024', 'NR'),
        'scope': row.get('Scope_Rating_2024', 'NR'),
        'global_risk': row.get('Risque_Global_2024', 'Non évalué')
    }
    
    # Infrastructure data
    infrastructure = {
        'international_ports': int(row['Ports_Internationaux']) if pd.notna(row.get('Ports_Internationaux')) else 1,
        'domestic_ports': int(row['Ports_Domestiques']) if pd.notna(row.get('Ports_Domestiques')) else 2,
        'international_airports': int(row['Aeroports_Internationaux']) if pd.notna(row.get('Aeroports_Internationaux')) else 1,
        'domestic_airports': int(row['Aeroports_Domestiques']) if pd.notna(row.get('Aeroports_Domestiques')) else 5,
        'railways_km': int(row['Chemins_Fer_KM']) if pd.notna(row.get('Chemins_Fer_KM')) else 0,
        'external_debt_pct_gdp': float(row['Dette_Exterieure_Pct_PIB']) if pd.notna(row.get('Dette_Exterieure_Pct_PIB')) else 60.0,
        'energy_cost_usd_kwh': float(row['Cout_Energie_USD_kWh']) if pd.notna(row.get('Cout_Energie_USD_kWh')) else 0.20
    }
    
    # World Bank Data360 indicators (2024)
    world_bank_data = {
        'life_expectancy_2023': float(row['Life_Expectancy_2023']) if pd.notna(row.get('Life_Expectancy_2023')) else None,
        'gini_index_2024': float(row['Gini_Index_2024']) if pd.notna(row.get('Gini_Index_2024')) else None,
        'poverty_rate_3usd_2024': float(row['Poverty_Rate_3USD_2024']) if pd.notna(row.get('Poverty_Rate_3USD_2024')) else None,
        'urban_population_pct_2024': float(row['Urban_Population_Pct_2024']) if pd.notna(row.get('Urban_Population_Pct_2024')) else None,
        'electricity_access_2022': float(row['Electricity_Access_2022']) if pd.notna(row.get('Electricity_Access_2022')) else None,
        'internet_users_pct_2024': float(row['Internet_Users_Pct_2024']) if pd.notna(row.get('Internet_Users_Pct_2024')) else None,
        'cybersecurity_index_2024': float(row['Cybersecurity_Index_2024']) if pd.notna(row.get('Cybersecurity_Index_2024')) else None,
        'female_labor_force_pct_2024': float(row['Female_Labor_Force_Pct_2024']) if pd.notna(row.get('Female_Labor_Force_Pct_2024')) else None,
        'learning_poverty_2023': float(row['Learning_Poverty_2023']) if pd.notna(row.get('Learning_Poverty_2023')) else None,
        'water_stress_2022': float(row['Water_Stress_2022']) if pd.notna(row.get('Water_Stress_2022')) else None,
        'ghg_emissions_mt_2022': float(row['GHG_Emissions_Mt_2022']) if pd.notna(row.get('GHG_Emissions_Mt_2022')) else None,
        'mobile_3g_coverage_2024': float(row['Mobile_3G_Coverage_2024']) if pd.notna(row.get('Mobile_3G_Coverage_2024')) else None
    }
    
    return {
        'country': row['Pays'],
        'code': row['Code_ISO'],
        'gdp_2024_billion_usd': float(row['PIB_2024_Mds_USD']) if pd.notna(row['PIB_2024_Mds_USD']) else None,
        'population_2024_million': float(row['Population_2024_M']) if pd.notna(row['Population_2024_M']) else None,
        'gdp_per_capita_2024': float(row['PIB_par_habitant_2024_USD']) if pd.notna(row['PIB_par_habitant_2024_USD']) else None,
        'hdi_2024': float(row['IDH_2024']) if pd.notna(row['IDH_2024']) else None,
        'hdi_rank_2024': int(row['IDH_Rang_2024']) if pd.notna(row.get('IDH_Rang_2024')) else None,
        'inflation_2024': float(row['Inflation_2024_Pct']) if pd.notna(row.get('Inflation_2024_Pct')) else None,
        'unemployment_2024': float(row['Chomage_2024_Pct']) if pd.notna(row.get('Chomage_2024_Pct')) else None,
        'growth_rate_2024': float(row['Croissance_PIB_2024_Pct']) if pd.notna(row['Croissance_PIB_2024_Pct']) else None,
        'exports_2024_billion_usd': float(row['Exportations_2024_Mds_USD']) if pd.notna(row['Exportations_2024_Mds_USD']) else None,
        'imports_2024_billion_usd': float(row['Importations_2024_Mds_USD']) if pd.notna(row['Importations_2024_Mds_USD']) else None,
        'trade_balance_2024_billion_usd': float(row['Balance_Commerciale_2024_Mds_USD']) if pd.notna(row['Balance_Commerciale_2024_Mds_USD']) else None,
        # Données de dette publique 2024
        'total_debt_pct_gdp': float(row['Dette_Totale_Pct_PIB']) if pd.notna(row.get('Dette_Totale_Pct_PIB')) else None,
        'external_debt_bn_usd': float(row['Dette_Exterieure_Mds_USD']) if pd.notna(row.get('Dette_Exterieure_Mds_USD')) else None,
        'external_debt_pct_gdp': float(row['Dette_Exterieure_Pct_PIB']) if pd.notna(row.get('Dette_Exterieure_Pct_PIB')) else None,
        'domestic_debt_pct_gdp': float(row['Dette_Interieure_Pct_PIB']) if pd.notna(row.get('Dette_Interieure_Pct_PIB')) else None,
        'export_products': export_products,
        'import_products': import_products,
        'export_partners': export_partners,
        'import_partners': import_partners,
        'ratings': ratings,
        'infrastructure': infrastructure,
        'world_bank_data': world_bank_data,
        'zlecaf_ratified': row.get('ZLECAf_Ratifie', 'Non'),
        'zlecaf_ratification_date': row.get('Date_Ratification_ZLECAf', None),
        'sources': row.get('Sources_Principales', ''),
        'last_updated': row.get('Derniere_MAJ', ''),
        'validation_status': row.get('STATUT_VALIDATION', '')
    }

# Get all countries trade performance data
def get_all_countries_trade_performance() -> List[Dict]:
    """Get trade performance data for all countries"""
    df = load_commerce_data()
    
    countries_data = []
    for _, row in df.iterrows():
        countries_data.append({
            'country': row['Pays'],
            'code': row['Code_ISO'],
            'gdp_2024': float(row['PIB_2024_Mds_USD']) if pd.notna(row['PIB_2024_Mds_USD']) else 0,
            'population_2024': float(row['Population_2024_M']) if pd.notna(row['Population_2024_M']) else 0,
            'gdp_per_capita_2024': float(row['PIB_par_habitant_2024_USD']) if pd.notna(row['PIB_par_habitant_2024_USD']) else 0,
            'exports_2024': float(row['Exportations_2024_Mds_USD']) if pd.notna(row['Exportations_2024_Mds_USD']) else 0,
            'imports_2024': float(row['Importations_2024_Mds_USD']) if pd.notna(row['Importations_2024_Mds_USD']) else 0,
            'trade_balance_2024': float(row['Balance_Commerciale_2024_Mds_USD']) if pd.notna(row['Balance_Commerciale_2024_Mds_USD']) else 0,
            'hdi_2024': float(row['IDH_2024']) if pd.notna(row['IDH_2024']) else 0,
            'hdi_rank_2024': int(row['IDH_Rang_2024']) if pd.notna(row.get('IDH_Rang_2024')) else None,
            'inflation_2024': float(row['Inflation_2024_Pct']) if pd.notna(row.get('Inflation_2024_Pct')) else None,
            'unemployment_2024': float(row['Chomage_2024_Pct']) if pd.notna(row.get('Chomage_2024_Pct')) else None,
            'growth_rate_2024': float(row['Croissance_PIB_2024_Pct']) if pd.notna(row['Croissance_PIB_2024_Pct']) else 0
        })
    
    return countries_data

# Get enhanced statistics from corrections JSON
def get_enhanced_statistics() -> Dict:
    """Get enhanced statistics including projections and trade evolution"""
    corrections = load_corrections_data()
    return corrections.get('enhanced_statistics', {})

# Get tariff corrections
def get_tariff_corrections() -> Dict:
    """Get updated tariff rates for normal and zlecaf"""
    corrections = load_corrections_data()
    return corrections.get('tariff_corrections', {})

# Load customs data
def load_customs_data():
    """Load African customs administrations data"""
    customs_path = ROOT_DIR / "douanes_africaines.json"
    with open(customs_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load infrastructure ranking data
def load_infrastructure_ranking():
    """Load African infrastructure ranking (IPL & AIDI)"""
    ranking_path = ROOT_DIR / "classement_infrastructure_afrique.json"
    with open(ranking_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Get customs info for a country
def get_country_customs_info(country_name: str) -> Optional[Dict]:
    """Get customs administration info for a specific country"""
    customs_data = load_customs_data()
    
    # Match by country name (case-insensitive)
    for entry in customs_data:
        if entry['pays'].lower() == country_name.lower():
            return {
                'administration': entry['administration_douaniere'],
                'adresse': entry.get('adresse', ''),
                'website': entry['site_web'],
                'bureaux_portuaires': entry.get('bureaux_portuaires', ''),
                'bureaux_aeriens': entry.get('bureaux_aeriens', ''),
                'bureaux_terrestres': entry.get('bureaux_terrestres', ''),
            }
    return None

# Get infrastructure ranking for a country
def get_country_infrastructure_ranking(country_name: str) -> Optional[Dict]:
    """Get infrastructure ranking for a specific country"""
    ranking_data = load_infrastructure_ranking()
    
    # Normaliser le nom pour la comparaison
    import unicodedata
    def normalize(s):
        # Enlever les accents et convertir en minuscules
        return unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode('ascii')
    
    search_name = normalize(country_name)
    
    # Match by country name (case-insensitive, accent-insensitive)
    for entry in ranking_data:
        entry_name = normalize(entry['pays'])
        if entry_name == search_name or search_name in entry_name or entry_name in search_name:
            return {
                'africa_rank': entry['rang_afrique'],
                'lpi_infrastructure_score': entry['score_infrastructure_ipl'],
                'lpi_world_rank': entry['rang_mondial_ipl'],
                'aidi_transport_score': entry.get('score_aidi_2024', entry.get('score_transport_aidi', 0))
            }
    return None
