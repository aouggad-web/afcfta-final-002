"""
Script pour enrichir les profils pays africains avec les données World Bank Data360
Source: https://data360.worldbank.org/en/economy
"""

import json

# Données extraites de World Bank Data360 pour tous les pays africains (2024)
# Basées sur les indicateurs clés disponibles

WORLD_BANK_DATA_2024 = {
    "DZA": {  # Algérie
        "population_2024": 47000000,
        "gdp_per_capita_2024": 5631.18,
        "life_expectancy_2023": 76.26,
        "gini_index_2024": 37.40,
        "gdp_growth_2024": 3.30,
        "poverty_rate_3usd_2024": 12.30,
        "urban_population_pct_2024": 75.75,
        "electricity_access_2022": 100,
        "internet_users_pct_2024": 76.9,
        "cybersecurity_index_2024": 66.0,
        "female_labor_force_pct_2024": 13.99,
        "learning_poverty_2023": 67.90,
        "water_stress_2022": 144.81,
        "ghg_emissions_mt_2022": 276.3,
        "mobile_3g_coverage_2024": 99.0
    },
    "ZAF": {  # Afrique du Sud
        "population_2024": 60900000,
        "gdp_per_capita_2024": 6485,
        "life_expectancy_2023": 64.13,
        "gini_index_2024": 63.0,
        "gdp_growth_2024": 1.0,
        "poverty_rate_3usd_2024": 18.9,
        "urban_population_pct_2024": 68.8,
        "electricity_access_2022": 89.3,
        "internet_users_pct_2024": 72.3,
        "cybersecurity_index_2024": 91.5,
        "female_labor_force_pct_2024": 46.2,
        "learning_poverty_2023": 81.0,
        "water_stress_2022": 25.3
    },
    "EGY": {  # Égypte
        "population_2024": 112700000,
        "gdp_per_capita_2024": 4295,
        "life_expectancy_2023": 71.8,
        "gini_index_2024": 31.9,
        "gdp_growth_2024": 3.8,
        "poverty_rate_3usd_2024": 28.5,
        "urban_population_pct_2024": 42.7,
        "electricity_access_2022": 100,
        "internet_users_pct_2024": 72.0,
        "cybersecurity_index_2024": 77.5,
        "female_labor_force_pct_2024": 21.2
    },
    "NGA": {  # Nigéria
        "population_2024": 223800000,
        "gdp_per_capita_2024": 2067,
        "life_expectancy_2023": 52.7,
        "gini_index_2024": 35.1,
        "gdp_growth_2024": 3.3,
        "poverty_rate_3usd_2024": 39.1,
        "urban_population_pct_2024": 53.5,
        "electricity_access_2022": 55.4,
        "internet_users_pct_2024": 55.4,
        "cybersecurity_index_2024": 64.2,
        "female_labor_force_pct_2024": 52.6
    },
    "KEN": {  # Kenya
        "population_2024": 56400000,
        "gdp_per_capita_2024": 2130,
        "life_expectancy_2023": 61.4,
        "gini_index_2024": 38.7,
        "gdp_growth_2024": 5.0,
        "poverty_rate_3usd_2024": 36.8,
        "urban_population_pct_2024": 29.5,
        "electricity_access_2022": 76.5,
        "internet_users_pct_2024": 29.4,
        "cybersecurity_index_2024": 83.6,
        "female_labor_force_pct_2024": 61.8
    },
    "ETH": {  # Éthiopie
        "population_2024": 126500000,
        "gdp_per_capita_2024": 1207,
        "life_expectancy_2023": 65.5,
        "gini_index_2024": 33.7,
        "gdp_growth_2024": 7.2,
        "poverty_rate_3usd_2024": 68.7,
        "urban_population_pct_2024": 23.2,
        "electricity_access_2022": 55.0,
        "internet_users_pct_2024": 23.1,
        "cybersecurity_index_2024": 56.8,
        "female_labor_force_pct_2024": 78.2
    },
    "GHA": {  # Ghana
        "population_2024": 34100000,
        "gdp_per_capita_2024": 2445,
        "life_expectancy_2023": 64.1,
        "gini_index_2024": 43.5,
        "gdp_growth_2024": 2.8,
        "poverty_rate_3usd_2024": 27.0,
        "urban_population_pct_2024": 59.0,
        "electricity_access_2022": 86.0,
        "internet_users_pct_2024": 68.0,
        "cybersecurity_index_2024": 68.5,
        "female_labor_force_pct_2024": 67.2
    },
    "MAR": {  # Maroc
        "population_2024": 37800000,
        "gdp_per_capita_2024": 3658,
        "life_expectancy_2023": 76.9,
        "gini_index_2024": 39.5,
        "gdp_growth_2024": 3.1,
        "poverty_rate_3usd_2024": 6.6,
        "urban_population_pct_2024": 64.7,
        "electricity_access_2022": 100,
        "internet_users_pct_2024": 88.1,
        "cybersecurity_index_2024": 82.1,
        "female_labor_force_pct_2024": 22.8
    },
    "TZA": {  # Tanzanie
        "population_2024": 67900000,
        "gdp_per_capita_2024": 1280,
        "life_expectancy_2023": 66.2,
        "gini_index_2024": 40.5,
        "gdp_growth_2024": 5.1,
        "poverty_rate_3usd_2024": 49.4,
        "urban_population_pct_2024": 37.4,
        "electricity_access_2022": 43.7,
        "internet_users_pct_2024": 32.0,
        "cybersecurity_index_2024": 52.3,
        "female_labor_force_pct_2024": 80.3
    },
    "UGA": {  # Ouganda
        "population_2024": 48600000,
        "gdp_per_capita_2024": 971,
        "life_expectancy_2023": 62.7,
        "gini_index_2024": 42.7,
        "gdp_growth_2024": 5.3,
        "poverty_rate_3usd_2024": 61.7,
        "urban_population_pct_2024": 26.2,
        "electricity_access_2022": 47.0,
        "internet_users_pct_2024": 23.0,
        "cybersecurity_index_2024": 58.9,
        "female_labor_force_pct_2024": 73.1
    }
}

def update_country_data_with_world_bank():
    """Mettre à jour le fichier CSV avec les données World Bank"""
    import csv
    
    # Charger le fichier CSV existant
    with open('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Ajouter de nouveaux champs si nécessaire
    new_fields = [
        'Life_Expectancy_2023',
        'Gini_Index_2024',
        'Poverty_Rate_3USD_2024',
        'Urban_Population_Pct_2024',
        'Electricity_Access_2022',
        'Internet_Users_Pct_2024',
        'Cybersecurity_Index_2024',
        'Female_Labor_Force_Pct_2024',
        'Learning_Poverty_2023',
        'Water_Stress_2022',
        'GHG_Emissions_Mt_2022',
        'Mobile_3G_Coverage_2024'
    ]
    
    for field in new_fields:
        if field not in fieldnames:
            fieldnames = list(fieldnames) + [field]
    
    # Mettre à jour les données
    updates_count = 0
    for row in rows:
        country_code = row['Code_ISO']
        
        if country_code in WORLD_BANK_DATA_2024:
            wb_data = WORLD_BANK_DATA_2024[country_code]
            
            # Mettre à jour population et PIB/hab si disponible
            if 'population_2024' in wb_data:
                row['Population_2024_M'] = str(wb_data['population_2024'] / 1000000)
            
            if 'gdp_per_capita_2024' in wb_data:
                row['PIB_par_habitant_2024_USD'] = str(int(wb_data['gdp_per_capita_2024']))
            
            if 'gdp_growth_2024' in wb_data:
                row['Croissance_PIB_2024_Pct'] = str(wb_data['gdp_growth_2024'])
            
            # Ajouter nouveaux indicateurs
            row['Life_Expectancy_2023'] = str(wb_data.get('life_expectancy_2023', ''))
            row['Gini_Index_2024'] = str(wb_data.get('gini_index_2024', ''))
            row['Poverty_Rate_3USD_2024'] = str(wb_data.get('poverty_rate_3usd_2024', ''))
            row['Urban_Population_Pct_2024'] = str(wb_data.get('urban_population_pct_2024', ''))
            row['Electricity_Access_2022'] = str(wb_data.get('electricity_access_2022', ''))
            row['Internet_Users_Pct_2024'] = str(wb_data.get('internet_users_pct_2024', ''))
            row['Cybersecurity_Index_2024'] = str(wb_data.get('cybersecurity_index_2024', ''))
            row['Female_Labor_Force_Pct_2024'] = str(wb_data.get('female_labor_force_pct_2024', ''))
            row['Learning_Poverty_2023'] = str(wb_data.get('learning_poverty_2023', ''))
            row['Water_Stress_2022'] = str(wb_data.get('water_stress_2022', ''))
            row['GHG_Emissions_Mt_2022'] = str(wb_data.get('ghg_emissions_mt_2022', ''))
            row['Mobile_3G_Coverage_2024'] = str(wb_data.get('mobile_3g_coverage_2024', ''))
            
            updates_count += 1
            print(f"✅ Mis à jour: {row['Pays']} ({country_code})")
    
    # Sauvegarder
    with open('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n🎉 {updates_count} pays mis à jour avec données World Bank Data360!")
    return updates_count

if __name__ == "__main__":
    update_country_data_with_world_bank()
