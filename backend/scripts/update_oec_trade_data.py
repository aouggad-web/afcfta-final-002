#!/usr/bin/env python3
"""
Script pour mettre à jour les données commerciales 2024 avec les vraies données OEC
"""
import asyncio
import sys
import os
import pandas as pd

# Ajouter le chemin backend pour importer les services
sys.path.insert(0, '/app/backend')

from services.oec_trade_service import oec_service, AFRICAN_COUNTRIES_OEC

async def fetch_all_trade_data():
    """Récupérer les données commerciales OEC pour tous les pays africains"""
    results = {}
    
    print("Récupération des données OEC pour tous les pays africains...")
    print("=" * 60)
    
    for iso3, info in AFRICAN_COUNTRIES_OEC.items():
        try:
            # Récupérer les exports
            exports_data = await oec_service.get_exports_by_product(iso3, 2024, limit=1)
            exports_value = exports_data.get('total_value', 0) / 1e9  # En milliards
            
            # Récupérer les imports
            imports_data = await oec_service.get_imports_by_product(iso3, 2024, limit=1)
            imports_value = imports_data.get('total_value', 0) / 1e9  # En milliards
            
            results[iso3] = {
                'exports_2024': round(exports_value, 2),
                'imports_2024': round(imports_value, 2),
                'balance_2024': round(exports_value - imports_value, 2)
            }
            
            print(f"{iso3}: Exports=${exports_value:.2f}B, Imports=${imports_value:.2f}B")
            
        except Exception as e:
            print(f"Erreur pour {iso3}: {e}")
            results[iso3] = {'exports_2024': 0, 'imports_2024': 0, 'balance_2024': 0}
    
    return results

def update_csv_with_oec_data(oec_data):
    """Mettre à jour le fichier CSV avec les données OEC"""
    csv_path = '/app/ZLECAf_ENRICHI_2024_COMMERCE.csv'
    
    # Charger le CSV existant
    df = pd.read_csv(csv_path)
    
    print("\n" + "=" * 60)
    print("Mise à jour du fichier CSV...")
    print("=" * 60)
    
    # Mapping des codes ISO2 vers ISO3
    iso2_to_iso3 = {
        'ZAF': 'ZAF', 'DZA': 'DZA', 'AGO': 'AGO', 'BWA': 'BWA', 'BFA': 'BFA',
        'BDI': 'BDI', 'CMR': 'CMR', 'CPV': 'CPV', 'COM': 'COM', 'COG': 'COG',
        'COD': 'COD', 'BEN': 'BEN', 'DJI': 'DJI', 'EGY': 'EGY', 'GNQ': 'GNQ',
        'ERI': 'ERI', 'SWZ': 'SWZ', 'ETH': 'ETH', 'GAB': 'GAB', 'GMB': 'GMB',
        'GHA': 'GHA', 'GIN': 'GIN', 'GNB': 'GNB', 'CIV': 'CIV', 'KEN': 'KEN',
        'LSO': 'LSO', 'LBR': 'LBR', 'LBY': 'LBY', 'MDG': 'MDG', 'MWI': 'MWI',
        'MLI': 'MLI', 'MRT': 'MRT', 'MUS': 'MUS', 'MAR': 'MAR', 'MOZ': 'MOZ',
        'NAM': 'NAM', 'NER': 'NER', 'NGA': 'NGA', 'RWA': 'RWA', 'STP': 'STP',
        'SEN': 'SEN', 'SYC': 'SYC', 'SLE': 'SLE', 'SOM': 'SOM', 'SDN': 'SDN',
        'SSD': 'SSD', 'TZA': 'TZA', 'TGO': 'TGO', 'TUN': 'TUN', 'UGA': 'UGA',
        'CAF': 'CAF', 'TCD': 'TCD', 'ZMB': 'ZMB', 'ZWE': 'ZWE'
    }
    
    updates_made = 0
    for idx, row in df.iterrows():
        code = row['Code_ISO']
        iso3 = iso2_to_iso3.get(code, code)
        
        if iso3 in oec_data:
            old_exports = row['Exportations_2024_Mds_USD']
            old_imports = row['Importations_2024_Mds_USD']
            
            new_exports = oec_data[iso3]['exports_2024']
            new_imports = oec_data[iso3]['imports_2024']
            new_balance = oec_data[iso3]['balance_2024']
            
            # Mettre à jour les valeurs
            df.at[idx, 'Exportations_2024_Mds_USD'] = new_exports
            df.at[idx, 'Importations_2024_Mds_USD'] = new_imports
            df.at[idx, 'Balance_Commerciale_2024_Mds_USD'] = new_balance
            
            if old_exports != new_exports or old_imports != new_imports:
                print(f"{code}: Exports {old_exports}B → {new_exports}B, Imports {old_imports}B → {new_imports}B")
                updates_made += 1
    
    # Sauvegarder le CSV mis à jour
    df.to_csv(csv_path, index=False)
    print(f"\n✅ {updates_made} pays mis à jour dans le fichier CSV")
    
    return df

async def main():
    # Récupérer les données OEC
    oec_data = await fetch_all_trade_data()
    
    # Mettre à jour le CSV
    update_csv_with_oec_data(oec_data)
    
    print("\n✅ Mise à jour terminée!")

if __name__ == "__main__":
    asyncio.run(main())
