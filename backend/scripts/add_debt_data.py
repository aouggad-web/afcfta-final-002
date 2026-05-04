#!/usr/bin/env python3
"""
Script pour ajouter les données de dette publique (intérieure + extérieure) au CSV
Sources: FMI, Banque Mondiale, Trading Economics (données 2024)
"""
import pandas as pd

# Données de dette 2024 (sources: FMI Fiscal Monitor, Banque Mondiale, Trading Economics)
DEBT_DATA_2024 = {
    # Format: dette_totale_pct_pib, dette_exterieure_mds_usd, dette_exterieure_pct_pib, dette_interieure_pct_pib
    # Afrique du Nord
    "DZA": {"total_debt_pct": 46.2, "external_debt_bn": 4.8, "external_debt_pct": 1.8, "domestic_debt_pct": 44.4},
    "EGY": {"total_debt_pct": 82.9, "external_debt_bn": 155.0, "external_debt_pct": 44.9, "domestic_debt_pct": 38.0},
    "LBY": {"total_debt_pct": 35.0, "external_debt_bn": 3.4, "external_debt_pct": 8.0, "domestic_debt_pct": 27.0},
    "MAR": {"total_debt_pct": 70.0, "external_debt_bn": 64.8, "external_debt_pct": 42.6, "domestic_debt_pct": 27.4},
    "TUN": {"total_debt_pct": 80.2, "external_debt_bn": 38.5, "external_debt_pct": 80.0, "domestic_debt_pct": 0.2},
    "ESH": {"total_debt_pct": None, "external_debt_bn": None, "external_debt_pct": None, "domestic_debt_pct": None},
    
    # Afrique de l'Ouest - CEDEAO
    "BEN": {"total_debt_pct": 54.1, "external_debt_bn": 5.2, "external_debt_pct": 28.6, "domestic_debt_pct": 25.5},
    "BFA": {"total_debt_pct": 58.1, "external_debt_bn": 4.9, "external_debt_pct": 26.0, "domestic_debt_pct": 32.1},
    "CPV": {"total_debt_pct": 112.5, "external_debt_bn": 2.1, "external_debt_pct": 85.0, "domestic_debt_pct": 27.5},
    "CIV": {"total_debt_pct": 57.5, "external_debt_bn": 26.8, "external_debt_pct": 35.6, "domestic_debt_pct": 21.9},
    "GMB": {"total_debt_pct": 83.5, "external_debt_bn": 1.0, "external_debt_pct": 45.0, "domestic_debt_pct": 38.5},
    "GHA": {"total_debt_pct": 83.5, "external_debt_bn": 28.5, "external_debt_pct": 38.7, "domestic_debt_pct": 44.8},
    "GIN": {"total_debt_pct": 37.3, "external_debt_bn": 3.8, "external_debt_pct": 22.0, "domestic_debt_pct": 15.3},
    "GNB": {"total_debt_pct": 70.5, "external_debt_bn": 0.8, "external_debt_pct": 48.0, "domestic_debt_pct": 22.5},
    "LBR": {"total_debt_pct": 54.8, "external_debt_bn": 1.8, "external_debt_pct": 44.0, "domestic_debt_pct": 10.8},
    "MLI": {"total_debt_pct": 52.4, "external_debt_bn": 5.1, "external_debt_pct": 28.0, "domestic_debt_pct": 24.4},
    "MRT": {"total_debt_pct": 47.0, "external_debt_bn": 5.2, "external_debt_pct": 42.0, "domestic_debt_pct": 5.0},
    "NER": {"total_debt_pct": 51.2, "external_debt_bn": 4.8, "external_debt_pct": 32.0, "domestic_debt_pct": 19.2},
    "NGA": {"total_debt_pct": 42.0, "external_debt_bn": 43.0, "external_debt_pct": 9.7, "domestic_debt_pct": 32.3},
    "SEN": {"total_debt_pct": 77.8, "external_debt_bn": 18.5, "external_debt_pct": 62.0, "domestic_debt_pct": 15.8},
    "SLE": {"total_debt_pct": 71.6, "external_debt_bn": 2.2, "external_debt_pct": 53.0, "domestic_debt_pct": 18.6},
    "TGO": {"total_debt_pct": 67.0, "external_debt_bn": 2.5, "external_debt_pct": 30.0, "domestic_debt_pct": 37.0},
    
    # Afrique Centrale - CEMAC
    "CMR": {"total_debt_pct": 45.3, "external_debt_bn": 13.2, "external_debt_pct": 28.0, "domestic_debt_pct": 17.3},
    "CAF": {"total_debt_pct": 48.1, "external_debt_bn": 1.0, "external_debt_pct": 38.0, "domestic_debt_pct": 10.1},
    "TCD": {"total_debt_pct": 42.0, "external_debt_bn": 3.2, "external_debt_pct": 27.0, "domestic_debt_pct": 15.0},
    "COG": {"total_debt_pct": 90.0, "external_debt_bn": 6.5, "external_debt_pct": 52.0, "domestic_debt_pct": 38.0},
    "COD": {"total_debt_pct": 21.0, "external_debt_bn": 7.8, "external_debt_pct": 13.0, "domestic_debt_pct": 8.0},
    "GNQ": {"total_debt_pct": 45.0, "external_debt_bn": 2.8, "external_debt_pct": 22.0, "domestic_debt_pct": 23.0},
    "GAB": {"total_debt_pct": 65.2, "external_debt_bn": 7.8, "external_debt_pct": 40.0, "domestic_debt_pct": 25.2},
    "STP": {"total_debt_pct": 71.0, "external_debt_bn": 0.4, "external_debt_pct": 68.0, "domestic_debt_pct": 3.0},
    
    # Afrique de l'Est
    "BDI": {"total_debt_pct": 66.2, "external_debt_bn": 0.7, "external_debt_pct": 22.0, "domestic_debt_pct": 44.2},
    "COM": {"total_debt_pct": 35.0, "external_debt_bn": 0.2, "external_debt_pct": 18.0, "domestic_debt_pct": 17.0},
    "DJI": {"total_debt_pct": 41.0, "external_debt_bn": 1.5, "external_debt_pct": 38.0, "domestic_debt_pct": 3.0},
    "ERI": {"total_debt_pct": 164.7, "external_debt_bn": 0.6, "external_debt_pct": 18.0, "domestic_debt_pct": 146.7},
    "ETH": {"total_debt_pct": 38.5, "external_debt_bn": 28.0, "external_debt_pct": 22.0, "domestic_debt_pct": 16.5},
    "KEN": {"total_debt_pct": 70.3, "external_debt_bn": 38.4, "external_debt_pct": 34.0, "domestic_debt_pct": 36.3},
    "MDG": {"total_debt_pct": 52.8, "external_debt_bn": 4.8, "external_debt_pct": 32.0, "domestic_debt_pct": 20.8},
    "MWI": {"total_debt_pct": 72.0, "external_debt_bn": 2.8, "external_debt_pct": 30.0, "domestic_debt_pct": 42.0},
    "MUS": {"total_debt_pct": 78.3, "external_debt_bn": 7.5, "external_debt_pct": 52.0, "domestic_debt_pct": 26.3},
    "RWA": {"total_debt_pct": 74.0, "external_debt_bn": 6.5, "external_debt_pct": 52.0, "domestic_debt_pct": 22.0},
    "SYC": {"total_debt_pct": 63.0, "external_debt_bn": 0.9, "external_debt_pct": 54.0, "domestic_debt_pct": 9.0},
    "SOM": {"total_debt_pct": 42.0, "external_debt_bn": 4.8, "external_debt_pct": 40.0, "domestic_debt_pct": 2.0},
    "SSD": {"total_debt_pct": 58.0, "external_debt_bn": 2.2, "external_debt_pct": 45.0, "domestic_debt_pct": 13.0},
    "SDN": {"total_debt_pct": 256.0, "external_debt_bn": 58.0, "external_debt_pct": 180.0, "domestic_debt_pct": 76.0},
    "TZA": {"total_debt_pct": 42.3, "external_debt_bn": 26.5, "external_debt_pct": 35.0, "domestic_debt_pct": 7.3},
    "UGA": {"total_debt_pct": 48.4, "external_debt_bn": 14.2, "external_debt_pct": 30.0, "domestic_debt_pct": 18.4},
    
    # Afrique Australe
    "AGO": {"total_debt_pct": 84.9, "external_debt_bn": 52.0, "external_debt_pct": 46.0, "domestic_debt_pct": 38.9},
    "BWA": {"total_debt_pct": 22.0, "external_debt_bn": 2.8, "external_debt_pct": 14.0, "domestic_debt_pct": 8.0},
    "SWZ": {"total_debt_pct": 43.0, "external_debt_bn": 0.8, "external_debt_pct": 15.0, "domestic_debt_pct": 28.0},
    "LSO": {"total_debt_pct": 52.0, "external_debt_bn": 1.0, "external_debt_pct": 38.0, "domestic_debt_pct": 14.0},
    "MOZ": {"total_debt_pct": 100.0, "external_debt_bn": 15.2, "external_debt_pct": 85.0, "domestic_debt_pct": 15.0},
    "NAM": {"total_debt_pct": 70.1, "external_debt_bn": 5.2, "external_debt_pct": 38.0, "domestic_debt_pct": 32.1},
    "ZAF": {"total_debt_pct": 76.9, "external_debt_bn": 164.0, "external_debt_pct": 42.0, "domestic_debt_pct": 34.9},
    "ZMB": {"total_debt_pct": 79.8, "external_debt_bn": 14.2, "external_debt_pct": 52.0, "domestic_debt_pct": 27.8},
    "ZWE": {"total_debt_pct": 98.0, "external_debt_bn": 14.0, "external_debt_pct": 75.0, "domestic_debt_pct": 23.0},
}

def update_csv_with_debt_data():
    csv_path = '/app/ZLECAf_ENRICHI_2024_COMMERCE.csv'
    
    # Charger le CSV
    df = pd.read_csv(csv_path)
    
    # Ajouter les nouvelles colonnes si elles n'existent pas
    new_cols = ['Dette_Totale_Pct_PIB', 'Dette_Exterieure_Mds_USD', 'Dette_Exterieure_Pct_PIB', 'Dette_Interieure_Pct_PIB']
    for col in new_cols:
        if col not in df.columns:
            df[col] = None
    
    # Mettre à jour les données
    updates = 0
    for idx, row in df.iterrows():
        code = row['Code_ISO']
        if code in DEBT_DATA_2024:
            data = DEBT_DATA_2024[code]
            df.at[idx, 'Dette_Totale_Pct_PIB'] = data['total_debt_pct']
            df.at[idx, 'Dette_Exterieure_Mds_USD'] = data['external_debt_bn']
            df.at[idx, 'Dette_Exterieure_Pct_PIB'] = data['external_debt_pct']
            df.at[idx, 'Dette_Interieure_Pct_PIB'] = data['domestic_debt_pct']
            
            updates += 1
            print(f"✅ {code}: Dette totale={data['total_debt_pct']}% PIB, Ext={data['external_debt_bn']}B$, Int={data['domestic_debt_pct']}% PIB")
    
    # Sauvegarder
    df.to_csv(csv_path, index=False)
    print(f"\n✅ {updates} pays mis à jour avec données de dette 2024")
    
    return df

if __name__ == "__main__":
    update_csv_with_debt_data()
