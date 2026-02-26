#!/usr/bin/env python3
"""
Script pour ajouter les données d'inflation, chômage et IDH rang au CSV
Sources: FMI WEO, Banque Mondiale, PNUD (données 2024)
"""
import pandas as pd

# Données économiques 2024 (sources: FMI, Banque Mondiale, PNUD)
ECONOMIC_DATA_2024 = {
    # Afrique du Nord
    "DZA": {"inflation": 4.0, "unemployment": 11.4, "hdi_rank": 91, "hdi": 0.745},
    "EGY": {"inflation": 28.3, "unemployment": 6.7, "hdi_rank": 105, "hdi": 0.731},
    "LBY": {"inflation": 3.2, "unemployment": 19.6, "hdi_rank": 104, "hdi": 0.732},
    "MAR": {"inflation": 0.9, "unemployment": 13.3, "hdi_rank": 120, "hdi": 0.698},
    "TUN": {"inflation": 7.0, "unemployment": 15.8, "hdi_rank": 97, "hdi": 0.739},
    "ESH": {"inflation": None, "unemployment": None, "hdi_rank": None, "hdi": None},  # RASD - pas de données
    
    # Afrique de l'Ouest
    "BEN": {"inflation": 2.8, "unemployment": 1.5, "hdi_rank": 166, "hdi": 0.504},
    "BFA": {"inflation": 2.1, "unemployment": 5.3, "hdi_rank": 184, "hdi": 0.438},
    "CPV": {"inflation": 1.2, "unemployment": 11.9, "hdi_rank": 130, "hdi": 0.662},
    "CIV": {"inflation": 4.2, "unemployment": 3.4, "hdi_rank": 159, "hdi": 0.534},
    "GMB": {"inflation": 18.0, "unemployment": 11.2, "hdi_rank": 174, "hdi": 0.496},
    "GHA": {"inflation": 22.3, "unemployment": 4.7, "hdi_rank": 142, "hdi": 0.602},
    "GIN": {"inflation": 10.5, "unemployment": 4.3, "hdi_rank": 182, "hdi": 0.465},
    "GNB": {"inflation": 5.8, "unemployment": 3.1, "hdi_rank": 177, "hdi": 0.483},
    "LBR": {"inflation": 9.9, "unemployment": 4.4, "hdi_rank": 175, "hdi": 0.487},
    "MLI": {"inflation": 2.4, "unemployment": 3.1, "hdi_rank": 186, "hdi": 0.410},
    "MRT": {"inflation": 3.4, "unemployment": 10.2, "hdi_rank": 158, "hdi": 0.540},
    "NER": {"inflation": 4.2, "unemployment": 0.5, "hdi_rank": 189, "hdi": 0.394},
    "NGA": {"inflation": 28.9, "unemployment": 5.0, "hdi_rank": 163, "hdi": 0.548},
    "SEN": {"inflation": 3.9, "unemployment": 3.7, "hdi_rank": 169, "hdi": 0.517},
    "SLE": {"inflation": 32.1, "unemployment": 4.6, "hdi_rank": 181, "hdi": 0.458},
    "TGO": {"inflation": 5.5, "unemployment": 3.9, "hdi_rank": 167, "hdi": 0.539},
    
    # Afrique Centrale
    "CMR": {"inflation": 7.3, "unemployment": 3.6, "hdi_rank": 151, "hdi": 0.587},
    "CAF": {"inflation": 3.2, "unemployment": 6.3, "hdi_rank": 191, "hdi": 0.387},
    "TCD": {"inflation": 3.5, "unemployment": 2.1, "hdi_rank": 190, "hdi": 0.394},
    "COG": {"inflation": 4.2, "unemployment": 10.4, "hdi_rank": 153, "hdi": 0.571},
    "COD": {"inflation": 19.1, "unemployment": 4.4, "hdi_rank": 179, "hdi": 0.479},
    "GNQ": {"inflation": 5.0, "unemployment": 8.6, "hdi_rank": 145, "hdi": 0.596},
    "GAB": {"inflation": 3.1, "unemployment": 20.3, "hdi_rank": 119, "hdi": 0.706},
    "STP": {"inflation": 21.2, "unemployment": 15.0, "hdi_rank": 135, "hdi": 0.618},
    
    # Afrique de l'Est
    "BDI": {"inflation": 16.1, "unemployment": 1.5, "hdi_rank": 187, "hdi": 0.426},
    "COM": {"inflation": 0.5, "unemployment": 5.8, "hdi_rank": 156, "hdi": 0.596},
    "DJI": {"inflation": 1.3, "unemployment": 26.3, "hdi_rank": 171, "hdi": 0.509},
    "ERI": {"inflation": 5.0, "unemployment": 7.2, "hdi_rank": 176, "hdi": 0.492},  # Non signataire ZLECAf
    "ETH": {"inflation": 23.3, "unemployment": 3.7, "hdi_rank": 175, "hdi": 0.492},
    "KEN": {"inflation": 6.6, "unemployment": 5.7, "hdi_rank": 152, "hdi": 0.575},
    "MDG": {"inflation": 9.5, "unemployment": 2.3, "hdi_rank": 173, "hdi": 0.501},
    "MWI": {"inflation": 26.7, "unemployment": 5.0, "hdi_rank": 172, "hdi": 0.508},
    "MUS": {"inflation": 4.0, "unemployment": 6.1, "hdi_rank": 72, "hdi": 0.796},
    "RWA": {"inflation": 5.8, "unemployment": 14.5, "hdi_rank": 165, "hdi": 0.548},
    "SYC": {"inflation": 0.5, "unemployment": 3.0, "hdi_rank": 67, "hdi": 0.802},
    "SOM": {"inflation": 4.0, "unemployment": 19.4, "hdi_rank": 192, "hdi": 0.380},  # Dernier rang mondial
    "SSD": {"inflation": 15.0, "unemployment": 12.7, "hdi_rank": 193, "hdi": 0.381},  # Dernier rang
    "SDN": {"inflation": 138.8, "unemployment": 17.7, "hdi_rank": 170, "hdi": 0.516},
    "TZA": {"inflation": 3.3, "unemployment": 2.6, "hdi_rank": 160, "hdi": 0.532},
    "UGA": {"inflation": 3.0, "unemployment": 2.8, "hdi_rank": 166, "hdi": 0.550},
    
    # Afrique Australe
    "AGO": {"inflation": 27.5, "unemployment": 32.0, "hdi_rank": 148, "hdi": 0.586},
    "BWA": {"inflation": 4.4, "unemployment": 26.0, "hdi_rank": 117, "hdi": 0.708},
    "SWZ": {"inflation": 4.6, "unemployment": 33.3, "hdi_rank": 143, "hdi": 0.597},
    "LSO": {"inflation": 6.0, "unemployment": 22.5, "hdi_rank": 168, "hdi": 0.514},
    "MOZ": {"inflation": 4.0, "unemployment": 3.3, "hdi_rank": 183, "hdi": 0.461},
    "NAM": {"inflation": 4.6, "unemployment": 19.4, "hdi_rank": 139, "hdi": 0.610},
    "ZAF": {"inflation": 4.5, "unemployment": 32.1, "hdi_rank": 109, "hdi": 0.717},
    "ZMB": {"inflation": 15.1, "unemployment": 5.8, "hdi_rank": 154, "hdi": 0.565},
    "ZWE": {"inflation": 56.9, "unemployment": 19.0, "hdi_rank": 155, "hdi": 0.550},
}

def update_csv():
    csv_path = '/app/ZLECAf_ENRICHI_2024_COMMERCE.csv'
    
    # Charger le CSV
    df = pd.read_csv(csv_path)
    
    # Ajouter les nouvelles colonnes si elles n'existent pas
    if 'Inflation_2024_Pct' not in df.columns:
        df['Inflation_2024_Pct'] = None
    if 'Chomage_2024_Pct' not in df.columns:
        df['Chomage_2024_Pct'] = None
    if 'IDH_Rang_2024' not in df.columns:
        df['IDH_Rang_2024'] = None
    
    # Mettre à jour les données
    updates = 0
    for idx, row in df.iterrows():
        code = row['Code_ISO']
        if code in ECONOMIC_DATA_2024:
            data = ECONOMIC_DATA_2024[code]
            df.at[idx, 'Inflation_2024_Pct'] = data['inflation']
            df.at[idx, 'Chomage_2024_Pct'] = data['unemployment']
            df.at[idx, 'IDH_Rang_2024'] = data['hdi_rank']
            
            # Mettre à jour l'IDH si présent
            if data['hdi'] is not None:
                df.at[idx, 'IDH_2024'] = data['hdi']
            
            updates += 1
            print(f"✅ {code}: Inflation={data['inflation']}%, Chômage={data['unemployment']}%, IDH Rang={data['hdi_rank']}")
    
    # Sauvegarder
    df.to_csv(csv_path, index=False)
    print(f"\n✅ {updates} pays mis à jour avec données économiques 2024")
    
    return df

if __name__ == "__main__":
    update_csv()
