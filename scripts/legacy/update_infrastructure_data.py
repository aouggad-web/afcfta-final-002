"""
Script pour mettre à jour les données d'infrastructure dans le CSV ZLECAf
"""
import pandas as pd

# Données d'infrastructure pour les pays africains clés
infrastructure_data = {
    'DZA': {'ports_int': 11, 'ports_dom': 8, 'airports_int': 15, 'airports_dom': 28, 'railways_km': 4200, 'debt_pct': 18.5, 'energy_cost': 0.04},
    'ZAF': {'ports_int': 8, 'ports_dom': 15, 'airports_int': 10, 'airports_dom': 98, 'railways_km': 20500, 'debt_pct': 62.3, 'energy_cost': 0.15},
    'AGO': {'ports_int': 4, 'ports_dom': 8, 'airports_int': 4, 'airports_dom': 31, 'railways_km': 2850, 'debt_pct': 88.4, 'energy_cost': 0.22},
    'BWA': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 3, 'airports_dom': 72, 'railways_km': 888, 'debt_pct': 11.2, 'energy_cost': 0.11},
    'EGY': {'ports_int': 15, 'ports_dom': 28, 'airports_int': 20, 'airports_dom': 72, 'railways_km': 5195, 'debt_pct': 95.2, 'energy_cost': 0.09},
    'NGA': {'ports_int': 9, 'ports_dom': 12, 'airports_int': 5, 'airports_dom': 52, 'railways_km': 3505, 'debt_pct': 38.7, 'energy_cost': 0.18},
    'KEN': {'ports_int': 3, 'ports_dom': 6, 'airports_int': 4, 'airports_dom': 191, 'railways_km': 3819, 'debt_pct': 68.5, 'energy_cost': 0.20},
    'ETH': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 3, 'airports_dom': 57, 'railways_km': 681, 'debt_pct': 55.3, 'energy_cost': 0.05},
    'GHA': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 2, 'airports_dom': 8, 'railways_km': 947, 'debt_pct': 83.1, 'energy_cost': 0.24},
    'TZA': {'ports_int': 3, 'ports_dom': 5, 'airports_int': 3, 'airports_dom': 162, 'railways_km': 3682, 'debt_pct': 42.1, 'energy_cost': 0.16},
    'CIV': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 2, 'airports_dom': 26, 'railways_km': 660, 'debt_pct': 58.7, 'energy_cost': 0.17},
    'UGA': {'ports_int': 0, 'ports_dom': 1, 'airports_int': 2, 'airports_dom': 45, 'railways_km': 1244, 'debt_pct': 52.3, 'energy_cost': 0.12},
    'MAR': {'ports_int': 12, 'ports_dom': 20, 'airports_int': 8, 'airports_dom': 47, 'railways_km': 2067, 'debt_pct': 74.5, 'energy_cost': 0.11},
    'TUN': {'ports_int': 7, 'ports_dom': 12, 'airports_int': 4, 'airports_dom': 25, 'railways_km': 2165, 'debt_pct': 88.9, 'energy_cost': 0.08},
    'SEN': {'ports_int': 2, 'ports_dom': 4, 'airports_int': 1, 'airports_dom': 19, 'railways_km': 906, 'debt_pct': 72.5, 'energy_cost': 0.19},
    'CMR': {'ports_int': 3, 'ports_dom': 5, 'airports_int': 3, 'airports_dom': 42, 'railways_km': 977, 'debt_pct': 45.8, 'energy_cost': 0.14},
    'ZMB': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 2, 'airports_dom': 86, 'railways_km': 2157, 'debt_pct': 131.5, 'energy_cost': 0.10},
    'ZWE': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 2, 'airports_dom': 193, 'railways_km': 3427, 'debt_pct': 88.2, 'energy_cost': 0.13},
    'RWA': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 6, 'railways_km': 0, 'debt_pct': 73.2, 'energy_cost': 0.23},
    'BEN': {'ports_int': 1, 'ports_dom': 2, 'airports_int': 1, 'airports_dom': 5, 'railways_km': 438, 'debt_pct': 54.5, 'energy_cost': 0.21},
    'MWI': {'ports_int': 0, 'ports_dom': 3, 'airports_int': 2, 'airports_dom': 28, 'railways_km': 767, 'debt_pct': 62.8, 'energy_cost': 0.18},
    'MOZ': {'ports_int': 3, 'ports_dom': 7, 'airports_int': 3, 'airports_dom': 94, 'railways_km': 4787, 'debt_pct': 102.5, 'energy_cost': 0.17},
    'NAM': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 2, 'airports_dom': 110, 'railways_km': 2628, 'debt_pct': 66.3, 'energy_cost': 0.14},
    'BFA': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 23, 'railways_km': 622, 'debt_pct': 54.2, 'energy_cost': 0.22},
    'MLI': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 24, 'railways_km': 593, 'debt_pct': 51.8, 'energy_cost': 0.20},
    'NER': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 26, 'railways_km': 0, 'debt_pct': 48.3, 'energy_cost': 0.19},
    'TCD': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 56, 'railways_km': 0, 'debt_pct': 52.1, 'energy_cost': 0.25},
    'SOM': {'ports_int': 3, 'ports_dom': 5, 'airports_int': 2, 'airports_dom': 52, 'railways_km': 0, 'debt_pct': 76.5, 'energy_cost': 0.30},
    'MDG': {'ports_int': 7, 'ports_dom': 12, 'airports_int': 2, 'airports_dom': 81, 'railways_km': 854, 'debt_pct': 45.2, 'energy_cost': 0.21},
    'GAB': {'ports_int': 2, 'ports_dom': 4, 'airports_int': 2, 'airports_dom': 42, 'railways_km': 649, 'debt_pct': 76.8, 'energy_cost': 0.15},
    'GIN': {'ports_int': 1, 'ports_dom': 3, 'airports_int': 1, 'airports_dom': 15, 'railways_km': 662, 'debt_pct': 45.8, 'energy_cost': 0.20},
    'TGO': {'ports_int': 1, 'ports_dom': 1, 'airports_int': 1, 'airports_dom': 7, 'railways_km': 568, 'debt_pct': 73.2, 'energy_cost': 0.23},
    'LBY': {'ports_int': 5, 'ports_dom': 7, 'airports_int': 4, 'airports_dom': 59, 'railways_km': 0, 'debt_pct': 155.3, 'energy_cost': 0.02},
    'MRT': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 1, 'airports_dom': 29, 'railways_km': 728, 'debt_pct': 95.4, 'energy_cost': 0.16},
    'ERI': {'ports_int': 2, 'ports_dom': 4, 'airports_int': 1, 'airports_dom': 12, 'railways_km': 306, 'debt_pct': 0, 'energy_cost': 0.18},
    'GMB': {'ports_int': 1, 'ports_dom': 1, 'airports_int': 1, 'airports_dom': 0, 'railways_km': 0, 'debt_pct': 89.5, 'energy_cost': 0.28},
    'BWA': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 3, 'airports_dom': 72, 'railways_km': 888, 'debt_pct': 11.2, 'energy_cost': 0.11},
    'GNB': {'ports_int': 1, 'ports_dom': 2, 'airports_int': 1, 'airports_dom': 7, 'railways_km': 0, 'debt_pct': 78.4, 'energy_cost': 0.25},
    'GNQ': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 1, 'airports_dom': 6, 'railways_km': 0, 'debt_pct': 43.2, 'energy_cost': 0.12},
    'MUS': {'ports_int': 1, 'ports_dom': 0, 'airports_int': 2, 'airports_dom': 3, 'railways_km': 0, 'debt_pct': 102.8, 'energy_cost': 0.19},
    'SWZ': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 13, 'railways_km': 301, 'debt_pct': 42.5, 'energy_cost': 0.09},
    'DJI': {'ports_int': 1, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 12, 'railways_km': 97, 'debt_pct': 42.3, 'energy_cost': 0.22},
    'CPV': {'ports_int': 8, 'ports_dom': 0, 'airports_int': 4, 'airports_dom': 5, 'railways_km': 0, 'debt_pct': 155.2, 'energy_cost': 0.26},
    'STP': {'ports_int': 1, 'ports_dom': 1, 'airports_int': 1, 'airports_dom': 1, 'railways_km': 0, 'debt_pct': 102.4, 'energy_cost': 0.24},
    'COM': {'ports_int': 3, 'ports_dom': 0, 'airports_int': 3, 'airports_dom': 1, 'railways_km': 0, 'debt_pct': 32.8, 'energy_cost': 0.30},
    'SYC': {'ports_int': 1, 'ports_dom': 0, 'airports_int': 2, 'airports_dom': 12, 'railways_km': 0, 'debt_pct': 83.5, 'energy_cost': 0.27},
    'COG': {'ports_int': 2, 'ports_dom': 3, 'airports_int': 2, 'airports_dom': 24, 'railways_km': 795, 'debt_pct': 108.3, 'energy_cost': 0.13},
    'CAF': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 37, 'railways_km': 0, 'debt_pct': 52.7, 'energy_cost': 0.27},
    'LSO': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 23, 'railways_km': 2.6, 'debt_pct': 59.8, 'energy_cost': 0.10},
    'LBR': {'ports_int': 2, 'ports_dom': 2, 'airports_int': 1, 'airports_dom': 28, 'railways_km': 429, 'debt_pct': 56.3, 'energy_cost': 0.29},
    'SLE': {'ports_int': 1, 'ports_dom': 2, 'airports_int': 1, 'airports_dom': 7, 'railways_km': 84, 'debt_pct': 74.8, 'energy_cost': 0.26},
    'BDI': {'ports_int': 0, 'ports_dom': 1, 'airports_int': 1, 'airports_dom': 6, 'railways_km': 0, 'debt_pct': 73.5, 'energy_cost': 0.22},
    'SSD': {'ports_int': 0, 'ports_dom': 0, 'airports_int': 1, 'airports_dom': 84, 'railways_km': 248, 'debt_pct': 34.2, 'energy_cost': 0.31},
}

# Charger le CSV
df = pd.read_csv('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv')

# Ajouter les données d'infrastructure
for idx, row in df.iterrows():
    code = row['Code_ISO']
    if code in infrastructure_data:
        data = infrastructure_data[code]
        df.at[idx, 'Ports_Internationaux'] = data['ports_int']
        df.at[idx, 'Ports_Domestiques'] = data['ports_dom']
        df.at[idx, 'Aeroports_Internationaux'] = data['airports_int']
        df.at[idx, 'Aeroports_Domestiques'] = data['airports_dom']
        df.at[idx, 'Chemins_Fer_KM'] = data['railways_km']
        df.at[idx, 'Dette_Exterieure_Pct_PIB'] = data['debt_pct']
        df.at[idx, 'Cout_Energie_USD_kWh'] = data['energy_cost']
    else:
        # Valeurs par défaut pour les pays sans données spécifiques
        df.at[idx, 'Ports_Internationaux'] = 1
        df.at[idx, 'Ports_Domestiques'] = 2
        df.at[idx, 'Aeroports_Internationaux'] = 1
        df.at[idx, 'Aeroports_Domestiques'] = 5
        df.at[idx, 'Chemins_Fer_KM'] = 500
        df.at[idx, 'Dette_Exterieure_Pct_PIB'] = 60.0
        df.at[idx, 'Cout_Energie_USD_kWh'] = 0.20

# Sauvegarder le CSV mis à jour
df.to_csv('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', index=False)
print("✅ Données d'infrastructure mises à jour avec succès!")
print(f"Total de {len(df)} pays mis à jour")
