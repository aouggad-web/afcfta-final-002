#!/usr/bin/env python3
"""
⛔ DÉPRÉCIÉ — NE PAS UTILISER ⛔
=================================================================
Ce script générait production_africaine.json avec des valeurs ALÉATOIRES
(random.uniform / random.randint) tout en les étiquetant « FAO/USGS/UNIDO ».
Les données produites n'étaient PAS réelles ni vérifiables.

➡️  Remplacé par : backend/scripts/build_production_real.py
    (sources réelles : FAO FAOSTAT, UNIDO INDSTAT4, USGS MCS, EIA/OPEC)

Conservé pour référence historique uniquement. Exécution bloquée.
"""

import sys

print(__doc__)
print("⛔ Script désactivé. Utilisez: python3 backend/scripts/build_production_real.py")
sys.exit(1)

import json
import random

# Profils économiques des pays africains (basés sur données réelles)
COUNTRY_PROFILES = {
    # Grandes économies diversifiées
    "ZAF": {"agri": 2.4, "industry": 25.6, "manuf": 12.1, "main_crops": ["Maize (corn)", "Sugarcane", "Wheat"], "minerals": ["Gold", "Platinum", "Coal"]},
    "NGA": {"agri": 23.8, "industry": 27.4, "manuf": 8.9, "main_crops": ["Cassava", "Yam", "Maize (corn)"], "minerals": ["Crude oil", "Natural gas", "Tin"]},
    "EGY": {"agri": 11.3, "industry": 34.2, "manuf": 16.8, "main_crops": ["Wheat", "Rice", "Maize (corn)"], "minerals": ["Crude oil", "Natural gas", "Phosphate"]},
    
    # Économies émergentes
    "KEN": {"agri": 21.2, "industry": 17.8, "manuf": 7.6, "main_crops": ["Tea", "Maize (corn)", "Coffee"], "minerals": ["Soda ash", "Fluorspar", "Titanium"]},
    "ETH": {"agri": 33.1, "industry": 21.6, "manuf": 5.2, "main_crops": ["Maize (corn)", "Teff", "Coffee"], "minerals": ["Gold", "Tantalum", "Potash"]},
    "GHA": {"agri": 18.3, "industry": 33.8, "manuf": 11.2, "main_crops": ["Cocoa beans", "Cassava", "Maize (corn)"], "minerals": ["Gold", "Bauxite", "Manganese"]},
    "TZA": {"agri": 26.7, "industry": 26.6, "manuf": 8.4, "main_crops": ["Maize (corn)", "Cassava", "Rice"], "minerals": ["Gold", "Diamonds", "Tanzanite"]},
    "CIV": {"agri": 16.8, "industry": 28.4, "manuf": 12.7, "main_crops": ["Cocoa beans", "Cashew nuts", "Rubber"], "minerals": ["Gold", "Diamonds", "Nickel"]},
    "MAR": {"agri": 11.9, "industry": 25.7, "manuf": 15.3, "main_crops": ["Wheat", "Barley", "Citrus fruits"], "minerals": ["Phosphate", "Zinc", "Lead"]},
    "SEN": {"agri": 14.2, "industry": 24.1, "manuf": 13.8, "main_crops": ["Groundnuts", "Millet", "Maize (corn)"], "minerals": ["Gold", "Phosphate", "Zircon"]},
    
    # Économies pétrolières
    "DZA": {"agri": 10.4, "industry": 46.7, "manuf": 5.6, "main_crops": ["Wheat", "Barley", "Potatoes"], "minerals": ["Crude oil", "Natural gas", "Iron ore"]},
    "AGO": {"agri": 8.2, "industry": 51.3, "manuf": 4.8, "main_crops": ["Cassava", "Maize (corn)", "Sweet potatoes"], "minerals": ["Crude oil", "Diamonds", "Iron ore"]},
    "LBY": {"agri": 2.1, "industry": 52.4, "manuf": 3.2, "main_crops": ["Wheat", "Barley", "Dates"], "minerals": ["Crude oil", "Natural gas", "Gypsum"]},
    "GAB": {"agri": 3.7, "industry": 48.9, "manuf": 6.1, "main_crops": ["Cassava", "Plantain", "Sugarcane"], "minerals": ["Crude oil", "Manganese", "Gold"]},
    "GNQ": {"agri": 2.3, "industry": 68.7, "manuf": 1.8, "main_crops": ["Cassava", "Sweet potatoes", "Cocoa beans"], "minerals": ["Crude oil", "Natural gas", "Gold"]},
    "COG": {"agri": 7.8, "industry": 56.2, "manuf": 7.3, "main_crops": ["Cassava", "Sugarcane", "Plantain"], "minerals": ["Crude oil", "Copper", "Gold"]},
    
    # Économies minières
    "COD": {"agri": 19.7, "industry": 43.6, "manuf": 8.9, "main_crops": ["Cassava", "Maize (corn)", "Plantain"], "minerals": ["Copper", "Cobalt", "Diamonds"]},
    "ZMB": {"agri": 7.5, "industry": 41.2, "manuf": 7.8, "main_crops": ["Maize (corn)", "Cassava", "Sweet potatoes"], "minerals": ["Copper", "Cobalt", "Gold"]},
    "BWA": {"agri": 1.8, "industry": 27.5, "manuf": 4.2, "main_crops": ["Sorghum", "Maize (corn)", "Millet"], "minerals": ["Diamonds", "Copper", "Nickel"]},
    "NAM": {"agri": 6.2, "industry": 31.4, "manuf": 9.7, "main_crops": ["Millet", "Maize (corn)", "Wheat"], "minerals": ["Diamonds", "Uranium", "Gold"]},
    "ZWE": {"agri": 11.9, "industry": 28.7, "manuf": 10.1, "main_crops": ["Maize (corn)", "Tobacco", "Wheat"], "minerals": ["Platinum", "Gold", "Diamonds"]},
    
    # Économies agricoles
    "MLI": {"agri": 38.5, "industry": 19.1, "manuf": 6.2, "main_crops": ["Millet", "Sorghum", "Rice"], "minerals": ["Gold", "Phosphate", "Salt"]},
    "BFA": {"agri": 26.3, "industry": 26.4, "manuf": 8.1, "main_crops": ["Millet", "Sorghum", "Maize (corn)"], "minerals": ["Gold", "Zinc", "Manganese"]},
    "UGA": {"agri": 24.1, "industry": 21.3, "manuf": 8.7, "main_crops": ["Coffee", "Tea", "Maize (corn)"], "minerals": ["Gold", "Copper", "Cobalt"]},
    "RWA": {"agri": 28.3, "industry": 18.2, "manuf": 6.4, "main_crops": ["Tea", "Coffee", "Cassava"], "minerals": ["Tin", "Tantalum", "Tungsten"]},
    "BDI": {"agri": 39.1, "industry": 13.8, "manuf": 5.3, "main_crops": ["Coffee", "Tea", "Maize (corn)"], "minerals": ["Gold", "Nickel", "Cobalt"]},
    "MWI": {"agri": 28.6, "industry": 15.4, "manuf": 6.8, "main_crops": ["Maize (corn)", "Tobacco", "Tea"], "minerals": ["Uranium", "Coal", "Bauxite"]},
    "TCD": {"agri": 42.7, "industry": 14.7, "manuf": 3.1, "main_crops": ["Millet", "Sorghum", "Groundnuts"], "minerals": ["Crude oil", "Gold", "Uranium"]},
    "NER": {"agri": 39.9, "industry": 19.5, "manuf": 5.7, "main_crops": ["Millet", "Sorghum", "Cowpeas"], "minerals": ["Uranium", "Gold", "Coal"]},
    "CAF": {"agri": 43.2, "industry": 14.9, "manuf": 5.1, "main_crops": ["Cassava", "Groundnuts", "Maize (corn)"], "minerals": ["Diamonds", "Gold", "Uranium"]},
    
    # Économies diversifiées moyennes
    "TUN": {"agri": 9.8, "industry": 26.2, "manuf": 14.9, "main_crops": ["Wheat", "Barley", "Olives"], "minerals": ["Phosphate", "Crude oil", "Natural gas"]},
    "CMR": {"agri": 16.7, "industry": 26.5, "manuf": 14.1, "main_crops": ["Cassava", "Maize (corn)", "Plantain"], "minerals": ["Crude oil", "Bauxite", "Iron ore"]},
    "MOZ": {"agri": 23.9, "industry": 21.5, "manuf": 9.3, "main_crops": ["Cassava", "Maize (corn)", "Rice"], "minerals": ["Coal", "Natural gas", "Titanium"]},
    "SDN": {"agri": 30.5, "industry": 24.1, "manuf": 7.2, "main_crops": ["Sorghum", "Millet", "Wheat"], "minerals": ["Gold", "Crude oil", "Chromite"]},
    "MDG": {"agri": 24.2, "industry": 19.7, "manuf": 11.6, "main_crops": ["Rice", "Cassava", "Sugarcane"], "minerals": ["Nickel", "Cobalt", "Ilmenite"]},
    
    # Petites économies
    "BEN": {"agri": 26.1, "industry": 22.4, "manuf": 8.9, "main_crops": ["Cassava", "Yam", "Maize (corn)"], "minerals": ["Gold", "Limestone", "Marble"]},
    "TGO": {"agri": 19.8, "industry": 21.9, "manuf": 7.4, "main_crops": ["Cassava", "Yam", "Maize (corn)"], "minerals": ["Phosphate", "Limestone", "Marble"]},
    "SLE": {"agri": 60.7, "industry": 6.5, "manuf": 2.1, "main_crops": ["Rice", "Cassava", "Oil palm"], "minerals": ["Diamonds", "Rutile", "Bauxite"]},
    "LBR": {"agri": 34.0, "industry": 13.8, "manuf": 3.7, "main_crops": ["Cassava", "Rice", "Rubber"], "minerals": ["Iron ore", "Gold", "Diamonds"]},
    "GIN": {"agri": 19.8, "industry": 32.1, "manuf": 5.3, "main_crops": ["Rice", "Cassava", "Maize (corn)"], "minerals": ["Bauxite", "Gold", "Diamonds"]},
    "GNB": {"agri": 45.8, "industry": 13.1, "manuf": 8.2, "main_crops": ["Rice", "Cashew nuts", "Groundnuts"], "minerals": ["Bauxite", "Phosphate", "Gold"]},
    "MRT": {"agri": 25.3, "industry": 29.3, "manuf": 8.7, "main_crops": ["Millet", "Sorghum", "Dates"], "minerals": ["Iron ore", "Gold", "Copper"]},
    "GMB": {"agri": 20.4, "industry": 14.2, "manuf": 5.8, "main_crops": ["Groundnuts", "Millet", "Sorghum"], "minerals": ["Zircon", "Ilmenite", "Rutile"]},
    "LSO": {"agri": 5.8, "industry": 32.4, "manuf": 11.2, "main_crops": ["Maize (corn)", "Wheat", "Sorghum"], "minerals": ["Diamonds", "Water (export)", "Wool"]},
    "SWZ": {"agri": 6.5, "industry": 44.9, "manuf": 37.1, "main_crops": ["Sugarcane", "Maize (corn)", "Citrus fruits"], "minerals": ["Coal", "Diamonds", "Gold"]},
    "DJI": {"agri": 2.4, "industry": 16.6, "manuf": 3.1, "main_crops": ["Vegetables", "Fruits", "Livestock"], "minerals": ["Salt", "Perlite", "Limestone"]},
    "ERI": {"agri": 11.7, "industry": 22.6, "manuf": 5.4, "main_crops": ["Sorghum", "Millet", "Barley"], "minerals": ["Gold", "Copper", "Zinc"]},
    "SOM": {"agri": 60.2, "industry": 7.4, "manuf": 2.9, "main_crops": ["Sorghum", "Maize (corn)", "Sesame"], "minerals": ["Uranium", "Iron ore", "Tin"]},
    "SSD": {"agri": 15.2, "industry": 54.3, "manuf": 4.1, "main_crops": ["Sorghum", "Maize (corn)", "Cassava"], "minerals": ["Crude oil", "Gold", "Diamonds"]},
    
    # Îles et petites économies insulaires
    "MUS": {"agri": 3.4, "industry": 20.1, "manuf": 13.7, "main_crops": ["Sugarcane", "Tea", "Vegetables"], "minerals": ["Salt", "Basalt", "Limestone"]},
    "SYC": {"agri": 2.1, "industry": 13.4, "manuf": 6.2, "main_crops": ["Coconuts", "Cinnamon", "Vanilla"], "minerals": ["Granite", "Guano", "Salt"]},
    "CPV": {"agri": 8.9, "industry": 19.3, "manuf": 5.1, "main_crops": ["Maize (corn)", "Beans", "Sweet potatoes"], "minerals": ["Salt", "Pozzolana", "Limestone"]},
    "STP": {"agri": 11.8, "industry": 14.7, "manuf": 4.3, "main_crops": ["Cocoa beans", "Coconuts", "Coffee"], "minerals": ["None significant", "Basalt", "Limestone"]},
    "COM": {"agri": 32.4, "industry": 11.8, "manuf": 4.2, "main_crops": ["Vanilla", "Cloves", "Ylang-ylang"], "minerals": ["None significant", "Pumice", "Basalt"]},
}

def generate_value_added_data(country_code, country_name, profile):
    """Générer des données de valeur ajoutée macro pour un pays"""
    records = []
    base_year = 2021
    
    # Agriculture
    for year in range(2021, 2025):
        variation = random.uniform(-0.3, 0.5)  # Variation annuelle réaliste
        value = profile['agri'] * (1 + variation * (year - base_year) / 10)
        records.append({
            "country_name": country_name,
            "country_iso3": country_code,
            "year": year,
            "sector_isic_section": "A",
            "sector_detail": "Agriculture, forestry and fishing",
            "indicator_code": "NV.AGR.TOTL.ZS",
            "indicator_label": "Agriculture, value added (% of GDP)",
            "value": round(value, 1),
            "unit": "percent",
            "currency": None,
            "price_base_year": None,
            "source_institution": "World Bank",
            "source_dataset": "World Development Indicators",
            "source_url": "https://data.worldbank.org/indicator/NV.AGR.TOTL.ZS",
            "wb_indicator_code": "NV.AGR.TOTL.ZS"
        })
    
    # Industry
    for year in range(2021, 2025):
        variation = random.uniform(-0.2, 0.4)
        value = profile['industry'] * (1 + variation * (year - base_year) / 10)
        records.append({
            "country_name": country_name,
            "country_iso3": country_code,
            "year": year,
            "sector_isic_section": "B-F",
            "sector_detail": "Industry (including construction)",
            "indicator_code": "NV.IND.TOTL.ZS",
            "indicator_label": "Industry, value added (% of GDP)",
            "value": round(value, 1),
            "unit": "percent",
            "currency": None,
            "price_base_year": None,
            "source_institution": "World Bank",
            "source_dataset": "World Development Indicators",
            "source_url": "https://data.worldbank.org/indicator/NV.IND.TOTL.ZS",
            "wb_indicator_code": "NV.IND.TOTL.ZS"
        })
    
    # Manufacturing
    for year in range(2021, 2025):
        variation = random.uniform(-0.2, 0.3)
        value = profile['manuf'] * (1 + variation * (year - base_year) / 10)
        records.append({
            "country_name": country_name,
            "country_iso3": country_code,
            "year": year,
            "sector_isic_section": "C",
            "sector_detail": "Manufacturing",
            "indicator_code": "NV.IND.MANF.ZS",
            "indicator_label": "Manufacturing, value added (% of GDP)",
            "value": round(value, 1),
            "unit": "percent",
            "currency": None,
            "price_base_year": None,
            "source_institution": "World Bank",
            "source_dataset": "World Development Indicators",
            "source_url": "https://data.worldbank.org/indicator/NV.IND.MANF.ZS",
            "wb_indicator_code": "NV.IND.MANF.ZS"
        })
    
    return records

def generate_agriculture_data(country_code, country_name, profile):
    """Générer des données agricoles pour un pays"""
    records = []
    
    # Échelle de production basée sur la taille économique du pays
    production_scales = {
        'large': 15000000,  # Grandes économies agricoles
        'medium': 5000000,   # Économies moyennes
        'small': 1000000     # Petites économies
    }
    
    # Déterminer l'échelle
    if profile['agri'] > 25 or country_code in ['NGA', 'EGY', 'ZAF', 'ETH', 'TZA']:
        scale = production_scales['large']
    elif profile['agri'] > 15:
        scale = production_scales['medium']
    else:
        scale = production_scales['small']
    
    for crop in profile['main_crops']:
        base_production = scale * random.uniform(0.5, 1.5)
        for year in range(2021, 2025):
            variation = random.uniform(0.9, 1.15)  # Variation climatique
            value = int(base_production * variation * (1 + (year - 2021) * 0.02))
            
            records.append({
                "country_name": country_name,
                "country_iso3": country_code,
                "year": year,
                "sector_isic_section": "A",
                "sector_detail": "Crops",
                "indicator_code": "QCL_PROD",
                "indicator_label": "Production",
                "value": value,
                "unit": "tonnes",
                "currency": None,
                "price_base_year": None,
                "source_institution": "FAO",
                "source_dataset": "FAOSTAT - Production",
                "source_url": "https://www.fao.org/faostat/",
                "faostat_domain": "QCL",
                "commodity_code": str(random.randint(1, 999)).zfill(4),
                "commodity_label": crop,
                "element_code": "5510",
                "element_label": "Production"
            })
    
    return records

def generate_manufacturing_data(country_code, country_name, profile):
    """Générer des données manufacturières pour un pays"""
    records = []
    
    # Échelle basée sur le PIB manufacturier
    if profile['manuf'] > 12 or country_code in ['ZAF', 'EGY', 'MAR', 'TUN']:
        base_value = 30000000000  # 30 milliards USD
    elif profile['manuf'] > 7:
        base_value = 10000000000  # 10 milliards USD
    else:
        base_value = 2000000000   # 2 milliards USD
    
    # Secteurs manufacturiers principaux
    sectors = [
        {"code": "10", "label": "Manufacture of food products"},
        {"code": "24", "label": "Manufacture of basic metals"},
    ]
    
    for sector in sectors:
        for year in range(2021, 2025):
            variation = random.uniform(0.95, 1.08)
            value = int(base_value * variation * (1 + (year - 2021) * 0.03))
            
            records.append({
                "country_name": country_name,
                "country_iso3": country_code,
                "year": year,
                "sector_isic_section": "C",
                "sector_detail": sector['label'],
                "indicator_code": "INDSTAT_VA",
                "indicator_label": "Value added",
                "value": value,
                "unit": "USD",
                "currency": "USD",
                "price_base_year": "2015",
                "source_institution": "UNIDO",
                "source_dataset": "INDSTAT4",
                "source_url": "https://stat.unido.org/",
                "unido_dataset": "INDSTAT4",
                "isic_revision": "4",
                "isic_code": sector['code'],
                "isic_label": sector['label']
            })
    
    return records

def generate_mining_data(country_code, country_name, profile):
    """Générer des données minières pour un pays"""
    records = []
    
    # Échelle de production basée sur les ressources minières (en tonnes)
    mining_scales = {
        'major': 500000,      # Grands producteurs (500k tonnes)
        'medium': 150000,     # Producteurs moyens (150k tonnes)
        'small': 30000        # Petits producteurs (30k tonnes)
    }
    
    # Déterminer l'échelle selon l'importance minière du pays
    if country_code in ['ZAF', 'GHA', 'TZA', 'MLI', 'COD', 'ZMB', 'BWA', 'NGA', 'DZA', 'AGO']:
        scale = mining_scales['major']
    elif len(profile['minerals']) > 2:
        scale = mining_scales['medium']
    else:
        scale = mining_scales['small']
    
    for mineral in profile['minerals'][:2]:  # Limiter à 2 minéraux principaux
        base_production = scale * random.uniform(0.7, 1.3)
        for year in range(2021, 2025):
            variation = random.uniform(0.95, 1.10)
            value = int(base_production * variation * (1 + (year - 2021) * 0.015))
            
            records.append({
                "country_name": country_name,
                "country_iso3": country_code,
                "year": year,
                "sector_isic_section": "B",
                "sector_detail": "Mining and quarrying",
                "indicator_code": "USGS_PROD",
                "indicator_label": "Mine production",
                "value": value,
                "unit": "tonnes",
                "currency": None,
                "price_base_year": None,
                "source_institution": "USGS",
                "source_dataset": "Mineral Commodity Summaries 2023",
                "source_url": "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
                "commodity_code": mineral[:2].upper() if len(mineral) > 2 else "XX",
                "commodity_label": mineral,
                "usgs_table_name": f"Table 1 - {mineral} mine production"
            })
    
    return records

# Générer toutes les données
print("🚀 Génération des données de production pour tous les pays africains...")

all_value_added = []
all_agriculture = []
all_manufacturing = []
all_mining = []

for country_code, profile in COUNTRY_PROFILES.items():
    # Trouver le nom du pays
    country_name = None
    for c in [
        {"code": "DZA", "name": "Algérie"}, {"code": "AGO", "name": "Angola"}, {"code": "BEN", "name": "Bénin"},
        {"code": "BWA", "name": "Botswana"}, {"code": "BFA", "name": "Burkina Faso"}, {"code": "BDI", "name": "Burundi"},
        {"code": "CMR", "name": "Cameroun"}, {"code": "CPV", "name": "Cap-Vert"}, {"code": "CAF", "name": "République Centrafricaine"},
        {"code": "TCD", "name": "Tchad"}, {"code": "COM", "name": "Comores"}, {"code": "COG", "name": "République du Congo"},
        {"code": "COD", "name": "RD Congo"}, {"code": "CIV", "name": "Côte d'Ivoire"}, {"code": "DJI", "name": "Djibouti"},
        {"code": "EGY", "name": "Égypte"}, {"code": "GNQ", "name": "Guinée Équatoriale"}, {"code": "ERI", "name": "Érythrée"},
        {"code": "SWZ", "name": "Eswatini"}, {"code": "ETH", "name": "Éthiopie"}, {"code": "GAB", "name": "Gabon"},
        {"code": "GMB", "name": "Gambie"}, {"code": "GHA", "name": "Ghana"}, {"code": "GIN", "name": "Guinée"},
        {"code": "GNB", "name": "Guinée-Bissau"}, {"code": "KEN", "name": "Kenya"}, {"code": "LSO", "name": "Lesotho"},
        {"code": "LBR", "name": "Libéria"}, {"code": "LBY", "name": "Libye"}, {"code": "MDG", "name": "Madagascar"},
        {"code": "MWI", "name": "Malawi"}, {"code": "MLI", "name": "Mali"}, {"code": "MRT", "name": "Mauritanie"},
        {"code": "MUS", "name": "Maurice"}, {"code": "MAR", "name": "Maroc"}, {"code": "MOZ", "name": "Mozambique"},
        {"code": "NAM", "name": "Namibie"}, {"code": "NER", "name": "Niger"}, {"code": "NGA", "name": "Nigéria"},
        {"code": "RWA", "name": "Rwanda"}, {"code": "STP", "name": "São Tomé"}, {"code": "SEN", "name": "Sénégal"},
        {"code": "SYC", "name": "Seychelles"}, {"code": "SLE", "name": "Sierra Leone"}, {"code": "SOM", "name": "Somalie"},
        {"code": "ZAF", "name": "Afrique du Sud"}, {"code": "SSD", "name": "Soudan du Sud"}, {"code": "SDN", "name": "Soudan"},
        {"code": "TZA", "name": "Tanzanie"}, {"code": "TGO", "name": "Togo"}, {"code": "TUN", "name": "Tunisie"},
        {"code": "UGA", "name": "Ouganda"}, {"code": "ZMB", "name": "Zambie"}, {"code": "ZWE", "name": "Zimbabwe"}
    ]:
        if c['code'] == country_code:
            country_name = c['name']
            break
    
    if not country_name:
        country_name = country_code
    
    print(f"   Génération données pour {country_name} ({country_code})...")
    
    all_value_added.extend(generate_value_added_data(country_code, country_name, profile))
    all_agriculture.extend(generate_agriculture_data(country_code, country_name, profile))
    all_manufacturing.extend(generate_manufacturing_data(country_code, country_name, profile))
    all_mining.extend(generate_mining_data(country_code, country_name, profile))

# Créer la structure finale
output_data = {
    "countries": list(COUNTRY_PROFILES.keys()),
    "value_added_macro": all_value_added,
    "agri_faostat": all_agriculture,
    "manufacturing_unido": all_manufacturing,
    "mining_usgs": all_mining
}

# Sauvegarder
with open('/app/production_africaine.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ Données générées avec succès!")
print(f"   📊 {len(COUNTRY_PROFILES)} pays")
print(f"   📈 {len(all_value_added)} enregistrements macro")
print(f"   🌾 {len(all_agriculture)} enregistrements agricoles")
print(f"   🏭 {len(all_manufacturing)} enregistrements manufacturiers")
print(f"   ⛏️ {len(all_mining)} enregistrements miniers")
print(f"   📁 Total: {len(all_value_added) + len(all_agriculture) + len(all_manufacturing) + len(all_mining)} enregistrements")
