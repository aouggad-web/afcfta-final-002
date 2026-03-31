
import csv
import json
from backend.server import AFRICAN_COUNTRIES
from update_all_african_countries_worldbank import WORLD_BANK_COMPLETE_2024

MISSING_ISOS = {'SSD', 'LBY', 'ERI', 'SDN', 'LBR', 'MDG', 'BEN', 'SOM'}

def add_missing_countries():
    # Load existing fieldnames
    with open('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    # Prepare new rows
    new_rows = []
    
    for country in AFRICAN_COUNTRIES:
        if country['iso3'] in MISSING_ISOS:
            print(f"Preparing data for {country['name']} ({country['iso3']})...")
            
            # Basic info from server.py
            row = {
                'Pays': country['name'],
                'Code_ISO': country['iso3'],
                'Region': country['region'],
                'Population_2024_M': str(country['population'] / 1000000),
                'ZLECAf_Ratifie': "Non", # Default, check later
                'Sources_Principales': "World Bank Data360, AfDB",
                'STATUT_VALIDATION': "Estimé",
                'Derniere_MAJ': "2025-01-01",
                'Annee_Reference_Donnees': "2024"
            }
            
            # Data from World Bank Dictionary
            wb_data = WORLD_BANK_COMPLETE_2024.get(country['iso3'], {})
            
            if 'gdp_per_capita_2024' in wb_data:
                row['PIB_par_habitant_2024_USD'] = str(wb_data['gdp_per_capita_2024'])
                # Estimate GDP total from Pop * Capita
                gdp_total = (country['population'] * wb_data['gdp_per_capita_2024']) / 1000000000
                row['PIB_2024_Mds_USD'] = f"{gdp_total:.1f}"
            
            # Fill other WB fields
            mapping = {
                'Life_Expectancy_2023': 'life_expectancy_2023',
                'Gini_Index_2024': 'gini_index_2024',
                'Poverty_Rate_3USD_2024': 'poverty_rate_3usd_2024',
                'Urban_Population_Pct_2024': 'urban_population_pct_2024',
                'Electricity_Access_2022': 'electricity_access_2022',
                'Internet_Users_Pct_2024': 'internet_users_pct_2024',
                'Cybersecurity_Index_2024': 'cybersecurity_index_2024',
                'Female_Labor_Force_Pct_2024': 'female_labor_force_pct_2024'
            }
            
            for csv_col, wb_key in mapping.items():
                if wb_key in wb_data:
                    row[csv_col] = str(wb_data[wb_key])
            
            # Ensure all CSV fields exist (fill empty with empty string)
            for field in fieldnames:
                if field not in row:
                    row[field] = ""
            
            new_rows.append(row)

    # Combine and Save
    all_rows = existing_rows + new_rows
    
    with open('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
        
    print(f"✅ Added {len(new_rows)} missing countries to CSV.")
    print("Libye (LBY) check:", next((r for r in new_rows if r['Code_ISO'] == 'LBY'), "Not Found"))

if __name__ == "__main__":
    add_missing_countries()
