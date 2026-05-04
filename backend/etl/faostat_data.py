"""
Données FAOSTAT Enrichies - Production Agricole Africaine
==========================================================
Sources officielles:
- FAO FAOSTAT Production Domain (2020-2023)
- FAO Statistical Yearbook 2023/2024
- World Bank WDI Agricultural Indicators

Couverture: 54 pays africains
Mise à jour: Décembre 2024
"""

import json
from typing import Dict, List, Optional

# =============================================================================
# DONNÉES DE PRODUCTION AGRICOLE PAR PAYS ET PRODUIT
# Source: FAOSTAT Production Domain + estimations 2024
# =============================================================================

FAOSTAT_AGRICULTURE_DATA = {
    # =========================================================================
    # AFRIQUE DU NORD
    # =========================================================================
    "DZA": {
        "country_name": "Algérie",
        "region": "Afrique du Nord",
        "main_crops": ["Blé", "Orge", "Pomme de terre", "Oranges", "Dattes", "Olives", "Tomates"],
        "display_order": ["Blé", "Orge", "Pomme de terre", "Oranges", "Dattes", "Olives", "Tomates"],
        "production_2023": {
            "Blé": {"value": 3500000, "unit": "tonnes", "rank_africa": 4, "area_ha": 1800000, "yield_kg_ha": 1944},
            "Orge": {"value": 2100000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1200000, "yield_kg_ha": 1750},
            "Pomme de terre": {"value": 5200000, "unit": "tonnes", "rank_africa": 2, "area_ha": 170000, "yield_kg_ha": 30588},
            "Oranges": {"value": 950000, "unit": "tonnes", "rank_africa": 4, "area_ha": 62000, "yield_kg_ha": 15322},
            "Dattes": {"value": 1200000, "unit": "tonnes", "rank_africa": 1, "area_ha": 170000, "yield_kg_ha": 7059},
            "Olives": {"value": 850000, "unit": "tonnes", "rank_africa": 3, "area_ha": 500000, "yield_kg_ha": 1700},
            "Tomates": {"value": 1400000, "unit": "tonnes", "rank_africa": 4, "area_ha": 45000, "yield_kg_ha": 31111},
        },
        "evolution": {
            "Blé": [{"year": 2020, "value": 2500000}, {"year": 2021, "value": 2800000}, {"year": 2022, "value": 3200000}, {"year": 2023, "value": 3500000}],
            "Orge": [{"year": 2020, "value": 1800000}, {"year": 2021, "value": 1950000}, {"year": 2022, "value": 2050000}, {"year": 2023, "value": 2100000}],
            "Pomme de terre": [{"year": 2020, "value": 4600000}, {"year": 2021, "value": 4800000}, {"year": 2022, "value": 5000000}, {"year": 2023, "value": 5200000}],
            "Dattes": [{"year": 2020, "value": 1050000}, {"year": 2021, "value": 1100000}, {"year": 2022, "value": 1150000}, {"year": 2023, "value": 1200000}],
        },
        "livestock_2023": {
            "Ovins": {"value": 30000000, "unit": "têtes", "rank_africa": 2},
            "Caprins": {"value": 5000000, "unit": "têtes", "rank_africa": 8},
            "Bovins": {"value": 2000000, "unit": "têtes", "rank_africa": 15},
            "Camelins": {"value": 340000, "unit": "têtes", "rank_africa": 5},
            "Volailles": {"value": 200000000, "unit": "têtes", "rank_africa": 7},
        },
        "livestock_production_2023": {
            "Viande ovine": {"value": 285000, "unit": "tonnes"},
            "Lait": {"value": 3800000, "unit": "tonnes"},
            "Laine": {"value": 75000, "unit": "tonnes"},
            "Oeufs": {"value": 320000, "unit": "tonnes"},
        },
        "fisheries_2023": {
            "capture": {"value": 95000, "unit": "tonnes", "rank_africa": 11},
            "aquaculture": {"value": 5500, "unit": "tonnes", "rank_africa": 14},
            "species": ["Anchois", "Sardine", "Thon", "Merlu", "Crevettes"],
            "main_ports": ["Oran", "Alger", "Annaba", "Béjaïa", "Skikda"],
        },
        "key_indicators": {
            "agri_gdp_percent": 12.5,
            "agri_employment_percent": 10.8,
            "food_import_value_mln_usd": 9500,
            "arable_land_ha": 7500000,
            "irrigated_land_ha": 1200000,
        },
        "source": "FAOSTAT 2023, Ministère de l'Agriculture Algérie (MADR)",
        "data_year": 2023
    },
    
    "EGY": {
        "country_name": "Égypte",
        "region": "Afrique du Nord",
        "main_crops": ["Blé", "Maïs", "Riz", "Canne à sucre", "Agrumes", "Tomate"],
        "production_2023": {
            "Blé": {"value": 9500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 1400000, "yield_kg_ha": 6786},
            "Maïs": {"value": 7800000, "unit": "tonnes", "rank_africa": 3, "area_ha": 1000000, "yield_kg_ha": 7800},
            "Riz": {"value": 4200000, "unit": "tonnes", "rank_africa": 1, "area_ha": 450000, "yield_kg_ha": 9333},
            "Canne à sucre": {"value": 16000000, "unit": "tonnes", "rank_africa": 2, "area_ha": 200000, "yield_kg_ha": 80000},
            "Agrumes": {"value": 5500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 220000, "yield_kg_ha": 25000},
            "Tomate": {"value": 6500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 180000, "yield_kg_ha": 36111},
        },
        "evolution": {
            "Blé": [{"year": 2020, "value": 9000000}, {"year": 2021, "value": 9100000}, {"year": 2022, "value": 9300000}, {"year": 2023, "value": 9500000}],
            "Riz": [{"year": 2020, "value": 3800000}, {"year": 2021, "value": 3900000}, {"year": 2022, "value": 4100000}, {"year": 2023, "value": 4200000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 5200000, "unit": "têtes", "rank_africa": 6},
            "Ovins": {"value": 5500000, "unit": "têtes", "rank_africa": 10},
            "Volailles": {"value": 220000000, "unit": "têtes", "rank_africa": 3},
        },
        "fisheries_2023": {
            "capture": {"value": 380000, "unit": "tonnes"},
            "aquaculture": {"value": 1600000, "unit": "tonnes", "rank_africa": 1},
        },
        "key_indicators": {
            "agri_gdp_percent": 11.8,
            "agri_employment_percent": 24.0,
            "food_import_value_mln_usd": 18500,
            "arable_land_ha": 3700000,
            "irrigated_land_ha": 3600000,
        },
        "source": "FAOSTAT 2023, CAPMAS Egypt",
        "data_year": 2023
    },
    
    "LBY": {
        "country_name": "Libye",
        "region": "Afrique du Nord",
        "main_crops": ["Blé", "Orge", "Olives", "Tomate", "Pomme de terre"],
        "production_2023": {
            "Blé": {"value": 180000, "unit": "tonnes", "rank_africa": 15, "area_ha": 200000, "yield_kg_ha": 900},
            "Orge": {"value": 95000, "unit": "tonnes", "rank_africa": 10, "area_ha": 150000, "yield_kg_ha": 633},
            "Olives": {"value": 180000, "unit": "tonnes", "rank_africa": 8, "area_ha": 150000, "yield_kg_ha": 1200},
            "Tomate": {"value": 220000, "unit": "tonnes", "rank_africa": 15, "area_ha": 8000, "yield_kg_ha": 27500},
        },
        "evolution": {
            "Blé": [{"year": 2020, "value": 170000}, {"year": 2021, "value": 175000}, {"year": 2022, "value": 178000}, {"year": 2023, "value": 180000}],
        },
        "livestock_2023": {
            "Ovins": {"value": 4500000, "unit": "têtes", "rank_africa": 12},
            "Caprins": {"value": 2100000, "unit": "têtes", "rank_africa": 15},
        },
        "fisheries_2023": {
            "capture": {"value": 35000, "unit": "tonnes"},
            "aquaculture": {"value": 2000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 1.3,
            "agri_employment_percent": 17.0,
            "food_import_value_mln_usd": 3200,
            "arable_land_ha": 1750000,
        },
        "source": "FAOSTAT 2023, estimation",
        "data_year": 2023
    },
    
    "MAR": {
        "country_name": "Maroc",
        "region": "Afrique du Nord",
        "main_crops": ["Blé", "Orge", "Olives", "Agrumes", "Tomate", "Légumes"],
        "production_2023": {
            "Blé": {"value": 5500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 2800000, "yield_kg_ha": 1964},
            "Orge": {"value": 2800000, "unit": "tonnes", "rank_africa": 1, "area_ha": 2000000, "yield_kg_ha": 1400},
            "Olives": {"value": 2100000, "unit": "tonnes", "rank_africa": 1, "area_ha": 1100000, "yield_kg_ha": 1909},
            "Agrumes": {"value": 2600000, "unit": "tonnes", "rank_africa": 2, "area_ha": 130000, "yield_kg_ha": 20000},
            "Tomate": {"value": 1500000, "unit": "tonnes", "rank_africa": 3, "area_ha": 50000, "yield_kg_ha": 30000},
        },
        "evolution": {
            "Blé": [{"year": 2020, "value": 7000000}, {"year": 2021, "value": 7500000}, {"year": 2022, "value": 3400000, "note": "Sécheresse"}, {"year": 2023, "value": 5500000}],
            "Olives": [{"year": 2020, "value": 1600000}, {"year": 2021, "value": 1900000}, {"year": 2022, "value": 1500000}, {"year": 2023, "value": 2100000}],
        },
        "livestock_2023": {
            "Ovins": {"value": 22000000, "unit": "têtes", "rank_africa": 4},
            "Caprins": {"value": 6500000, "unit": "têtes", "rank_africa": 6},
            "Bovins": {"value": 3500000, "unit": "têtes", "rank_africa": 11},
        },
        "fisheries_2023": {
            "capture": {"value": 1500000, "unit": "tonnes", "rank_africa": 1},
            "aquaculture": {"value": 2500, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 11.2,
            "agri_employment_percent": 32.0,
            "food_import_value_mln_usd": 7200,
            "arable_land_ha": 8700000,
            "irrigated_land_ha": 1600000,
        },
        "source": "FAOSTAT 2023, Ministère de l'Agriculture Maroc",
        "data_year": 2023
    },
    
    "TUN": {
        "country_name": "Tunisie",
        "region": "Afrique du Nord",
        "main_crops": ["Olives", "Blé", "Orge", "Dattes", "Agrumes", "Tomate"],
        "production_2023": {
            "Olives": {"value": 1500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1800000, "yield_kg_ha": 833},
            "Blé": {"value": 1200000, "unit": "tonnes", "rank_africa": 7, "area_ha": 800000, "yield_kg_ha": 1500},
            "Dattes": {"value": 350000, "unit": "tonnes", "rank_africa": 3, "area_ha": 50000, "yield_kg_ha": 7000},
            "Agrumes": {"value": 450000, "unit": "tonnes", "rank_africa": 6, "area_ha": 30000, "yield_kg_ha": 15000},
        },
        "evolution": {
            "Olives": [{"year": 2020, "value": 1200000}, {"year": 2021, "value": 1800000}, {"year": 2022, "value": 1100000}, {"year": 2023, "value": 1500000}],
        },
        "livestock_2023": {
            "Ovins": {"value": 7000000, "unit": "têtes", "rank_africa": 8},
            "Caprins": {"value": 1500000, "unit": "têtes", "rank_africa": 18},
        },
        "fisheries_2023": {
            "capture": {"value": 120000, "unit": "tonnes"},
            "aquaculture": {"value": 22000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 10.5,
            "agri_employment_percent": 14.0,
            "olive_oil_export_mln_usd": 800,
        },
        "source": "FAOSTAT 2023, INS Tunisie",
        "data_year": 2023
    },
    
    # =========================================================================
    # AFRIQUE DE L'OUEST
    # =========================================================================
    "NGA": {
        "country_name": "Nigéria",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Manioc", "Igname", "Maïs", "Sorgho", "Riz", "Arachide"],
        "production_2023": {
            "Manioc": {"value": 63000000, "unit": "tonnes", "rank_africa": 1, "area_ha": 8500000, "yield_kg_ha": 7412},
            "Igname": {"value": 52000000, "unit": "tonnes", "rank_africa": 1, "area_ha": 6500000, "yield_kg_ha": 8000},
            "Maïs": {"value": 12500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 6800000, "yield_kg_ha": 1838},
            "Sorgho": {"value": 7200000, "unit": "tonnes", "rank_africa": 1, "area_ha": 5000000, "yield_kg_ha": 1440},
            "Riz": {"value": 5200000, "unit": "tonnes", "rank_africa": 3, "area_ha": 3800000, "yield_kg_ha": 1368},
            "Arachide": {"value": 3800000, "unit": "tonnes", "rank_africa": 1, "area_ha": 3200000, "yield_kg_ha": 1188},
        },
        "evolution": {
            "Manioc": [{"year": 2020, "value": 60000000}, {"year": 2021, "value": 61000000}, {"year": 2022, "value": 62000000}, {"year": 2023, "value": 63000000}],
            "Maïs": [{"year": 2020, "value": 11000000}, {"year": 2021, "value": 11500000}, {"year": 2022, "value": 12000000}, {"year": 2023, "value": 12500000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 21000000, "unit": "têtes", "rank_africa": 2},
            "Caprins": {"value": 82000000, "unit": "têtes", "rank_africa": 1},
            "Ovins": {"value": 45000000, "unit": "têtes", "rank_africa": 1},
            "Volailles": {"value": 250000000, "unit": "têtes", "rank_africa": 2},
        },
        "fisheries_2023": {
            "capture": {"value": 780000, "unit": "tonnes"},
            "aquaculture": {"value": 380000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 24.1,
            "agri_employment_percent": 35.0,
            "food_import_value_mln_usd": 11000,
            "arable_land_ha": 34000000,
        },
        "source": "FAOSTAT 2023, NBS Nigeria",
        "data_year": 2023
    },
    
    "GHA": {
        "country_name": "Ghana",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Cacao", "Manioc", "Maïs", "Plantain", "Igname", "Riz"],
        "production_2023": {
            "Cacao": {"value": 700000, "unit": "tonnes", "rank_africa": 2, "rank_world": 2, "area_ha": 1900000, "yield_kg_ha": 368},
            "Manioc": {"value": 23000000, "unit": "tonnes", "rank_africa": 3, "area_ha": 1100000, "yield_kg_ha": 20909},
            "Maïs": {"value": 3500000, "unit": "tonnes", "rank_africa": 7, "area_ha": 1200000, "yield_kg_ha": 2917},
            "Plantain": {"value": 4500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 400000, "yield_kg_ha": 11250},
            "Igname": {"value": 8500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 500000, "yield_kg_ha": 17000},
        },
        "evolution": {
            "Cacao": [{"year": 2020, "value": 1050000}, {"year": 2021, "value": 1000000}, {"year": 2022, "value": 800000}, {"year": 2023, "value": 700000, "note": "Baisse production"}],
        },
        "livestock_2023": {
            "Bovins": {"value": 1800000, "unit": "têtes", "rank_africa": 18},
            "Caprins": {"value": 7500000, "unit": "têtes", "rank_africa": 5},
            "Ovins": {"value": 5000000, "unit": "têtes", "rank_africa": 11},
        },
        "fisheries_2023": {
            "capture": {"value": 380000, "unit": "tonnes"},
            "aquaculture": {"value": 78000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 20.5,
            "agri_employment_percent": 38.0,
            "cacao_export_value_mln_usd": 2800,
        },
        "source": "FAOSTAT 2023, COCOBOD Ghana",
        "data_year": 2023
    },
    
    "CIV": {
        "country_name": "Côte d'Ivoire",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Cacao", "Café", "Hévéa", "Noix de cajou", "Palmier à huile", "Banane"],
        "production_2023": {
            "Cacao": {"value": 2200000, "unit": "tonnes", "rank_africa": 1, "rank_world": 1, "area_ha": 4500000, "yield_kg_ha": 489},
            "Noix de cajou": {"value": 1100000, "unit": "tonnes", "rank_africa": 1, "area_ha": 2500000, "yield_kg_ha": 440},
            "Hévéa": {"value": 1200000, "unit": "tonnes", "rank_africa": 1, "area_ha": 750000, "yield_kg_ha": 1600},
            "Huile de palme": {"value": 550000, "unit": "tonnes", "rank_africa": 3, "area_ha": 350000, "yield_kg_ha": 1571},
            "Café": {"value": 120000, "unit": "tonnes", "rank_africa": 3, "area_ha": 500000, "yield_kg_ha": 240},
        },
        "evolution": {
            "Cacao": [{"year": 2020, "value": 2100000}, {"year": 2021, "value": 2150000}, {"year": 2022, "value": 2100000}, {"year": 2023, "value": 2200000}],
            "Noix de cajou": [{"year": 2020, "value": 800000}, {"year": 2021, "value": 900000}, {"year": 2022, "value": 1000000}, {"year": 2023, "value": 1100000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 1700000, "unit": "têtes", "rank_africa": 19},
            "Ovins": {"value": 2100000, "unit": "têtes", "rank_africa": 15},
        },
        "fisheries_2023": {
            "capture": {"value": 85000, "unit": "tonnes"},
            "aquaculture": {"value": 5000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 21.0,
            "agri_employment_percent": 46.0,
            "cacao_export_value_mln_usd": 5200,
            "cashew_export_value_mln_usd": 1800,
        },
        "source": "FAOSTAT 2023, Conseil Café-Cacao",
        "data_year": 2023
    },
    
    "SEN": {
        "country_name": "Sénégal",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Arachide", "Mil", "Riz", "Maïs", "Sorgho", "Coton"],
        "production_2023": {
            "Arachide": {"value": 1800000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1200000, "yield_kg_ha": 1500},
            "Mil": {"value": 1200000, "unit": "tonnes", "rank_africa": 3, "area_ha": 1000000, "yield_kg_ha": 1200},
            "Riz": {"value": 1300000, "unit": "tonnes", "rank_africa": 5, "area_ha": 350000, "yield_kg_ha": 3714},
        },
        "evolution": {
            "Arachide": [{"year": 2020, "value": 1500000}, {"year": 2021, "value": 1600000}, {"year": 2022, "value": 1700000}, {"year": 2023, "value": 1800000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 3600000, "unit": "têtes", "rank_africa": 10},
            "Ovins": {"value": 6500000, "unit": "têtes", "rank_africa": 9},
            "Caprins": {"value": 5800000, "unit": "têtes", "rank_africa": 7},
        },
        "fisheries_2023": {
            "capture": {"value": 450000, "unit": "tonnes", "rank_africa": 4},
            "aquaculture": {"value": 2000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 16.8,
            "agri_employment_percent": 32.0,
            "groundnut_export_value_mln_usd": 450,
        },
        "source": "FAOSTAT 2023, ANSD Sénégal",
        "data_year": 2023
    },
    
    "MLI": {
        "country_name": "Mali",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Coton", "Riz", "Mil", "Sorgho", "Maïs", "Arachide"],
        "production_2023": {
            "Coton": {"value": 700000, "unit": "tonnes", "rank_africa": 1, "area_ha": 800000, "yield_kg_ha": 875},
            "Riz": {"value": 3200000, "unit": "tonnes", "rank_africa": 4, "area_ha": 900000, "yield_kg_ha": 3556},
            "Mil": {"value": 2000000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1600000, "yield_kg_ha": 1250},
            "Sorgho": {"value": 1500000, "unit": "tonnes", "rank_africa": 5, "area_ha": 1000000, "yield_kg_ha": 1500},
        },
        "evolution": {
            "Coton": [{"year": 2020, "value": 600000}, {"year": 2021, "value": 650000}, {"year": 2022, "value": 680000}, {"year": 2023, "value": 700000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 11000000, "unit": "têtes", "rank_africa": 5},
            "Ovins": {"value": 16000000, "unit": "têtes", "rank_africa": 6},
            "Caprins": {"value": 23000000, "unit": "têtes", "rank_africa": 3},
        },
        "fisheries_2023": {
            "capture": {"value": 100000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 38.0,
            "agri_employment_percent": 62.0,
            "cotton_export_value_mln_usd": 600,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "BFA": {
        "country_name": "Burkina Faso",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Coton", "Sorgho", "Mil", "Maïs", "Riz", "Sésame"],
        "production_2023": {
            "Coton": {"value": 450000, "unit": "tonnes", "rank_africa": 3, "area_ha": 600000, "yield_kg_ha": 750},
            "Sorgho": {"value": 1800000, "unit": "tonnes", "rank_africa": 4, "area_ha": 1400000, "yield_kg_ha": 1286},
            "Mil": {"value": 1300000, "unit": "tonnes", "rank_africa": 4, "area_ha": 1200000, "yield_kg_ha": 1083},
            "Maïs": {"value": 1600000, "unit": "tonnes", "rank_africa": 10, "area_ha": 900000, "yield_kg_ha": 1778},
        },
        "evolution": {
            "Coton": [{"year": 2020, "value": 400000}, {"year": 2021, "value": 420000}, {"year": 2022, "value": 440000}, {"year": 2023, "value": 450000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 9500000, "unit": "têtes", "rank_africa": 7},
            "Ovins": {"value": 10000000, "unit": "têtes", "rank_africa": 7},
            "Caprins": {"value": 15000000, "unit": "têtes", "rank_africa": 4},
        },
        "key_indicators": {
            "agri_gdp_percent": 25.0,
            "agri_employment_percent": 80.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "NER": {
        "country_name": "Niger",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Mil", "Sorgho", "Niébé", "Arachide", "Oignon"],
        "production_2023": {
            "Mil": {"value": 4200000, "unit": "tonnes", "rank_africa": 1, "area_ha": 8000000, "yield_kg_ha": 525},
            "Niébé": {"value": 2500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 5500000, "yield_kg_ha": 455},
            "Sorgho": {"value": 1400000, "unit": "tonnes", "rank_africa": 6, "area_ha": 2500000, "yield_kg_ha": 560},
            "Oignon": {"value": 750000, "unit": "tonnes", "rank_africa": 2, "area_ha": 35000, "yield_kg_ha": 21429},
        },
        "evolution": {
            "Mil": [{"year": 2020, "value": 3800000}, {"year": 2021, "value": 4000000}, {"year": 2022, "value": 4100000}, {"year": 2023, "value": 4200000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 14000000, "unit": "têtes", "rank_africa": 4},
            "Ovins": {"value": 11000000, "unit": "têtes", "rank_africa": 6},
            "Caprins": {"value": 16000000, "unit": "têtes", "rank_africa": 5},
        },
        "key_indicators": {
            "agri_gdp_percent": 42.0,
            "agri_employment_percent": 85.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "BEN": {
        "country_name": "Bénin",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Coton", "Maïs", "Manioc", "Igname", "Ananas"],
        "production_2023": {
            "Coton": {"value": 550000, "unit": "tonnes", "rank_africa": 2, "area_ha": 650000, "yield_kg_ha": 846},
            "Maïs": {"value": 1500000, "unit": "tonnes", "rank_africa": 11, "area_ha": 900000, "yield_kg_ha": 1667},
            "Manioc": {"value": 5000000, "unit": "tonnes", "rank_africa": 6, "area_ha": 400000, "yield_kg_ha": 12500},
            "Ananas": {"value": 350000, "unit": "tonnes", "rank_africa": 4, "area_ha": 6000, "yield_kg_ha": 58333},
        },
        "evolution": {
            "Coton": [{"year": 2020, "value": 450000}, {"year": 2021, "value": 500000}, {"year": 2022, "value": 520000}, {"year": 2023, "value": 550000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 2400000, "unit": "têtes"},
            "Ovins": {"value": 950000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 28.0,
            "agri_employment_percent": 40.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "TGO": {
        "country_name": "Togo",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Maïs", "Manioc", "Igname", "Sorgho", "Coton"],
        "production_2023": {
            "Maïs": {"value": 950000, "unit": "tonnes", "area_ha": 650000, "yield_kg_ha": 1462},
            "Manioc": {"value": 1200000, "unit": "tonnes", "area_ha": 180000, "yield_kg_ha": 6667},
            "Igname": {"value": 850000, "unit": "tonnes", "area_ha": 80000, "yield_kg_ha": 10625},
            "Coton": {"value": 150000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 750},
        },
        "livestock_2023": {
            "Bovins": {"value": 380000, "unit": "têtes"},
            "Ovins": {"value": 2500000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 21.0,
            "agri_employment_percent": 38.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "GIN": {
        "country_name": "Guinée",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Riz", "Manioc", "Maïs", "Fonio", "Palmier à huile"],
        "production_2023": {
            "Riz": {"value": 2800000, "unit": "tonnes", "rank_africa": 6, "area_ha": 1900000, "yield_kg_ha": 1474},
            "Manioc": {"value": 3500000, "unit": "tonnes", "area_ha": 300000, "yield_kg_ha": 11667},
            "Maïs": {"value": 800000, "unit": "tonnes", "area_ha": 500000, "yield_kg_ha": 1600},
            "Fonio": {"value": 550000, "unit": "tonnes", "rank_africa": 1, "area_ha": 500000, "yield_kg_ha": 1100},
        },
        "livestock_2023": {
            "Bovins": {"value": 6500000, "unit": "têtes"},
            "Ovins": {"value": 2000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 180000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 25.0,
            "agri_employment_percent": 52.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "SLE": {
        "country_name": "Sierra Leone",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Riz", "Manioc", "Palmier à huile", "Cacao", "Café"],
        "production_2023": {
            "Riz": {"value": 1200000, "unit": "tonnes", "area_ha": 700000, "yield_kg_ha": 1714},
            "Manioc": {"value": 4500000, "unit": "tonnes", "area_ha": 300000, "yield_kg_ha": 15000},
            "Cacao": {"value": 18000, "unit": "tonnes", "area_ha": 60000, "yield_kg_ha": 300},
        },
        "livestock_2023": {
            "Bovins": {"value": 550000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 200000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 55.0,
            "agri_employment_percent": 61.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "LBR": {
        "country_name": "Libéria",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Riz", "Manioc", "Hévéa", "Cacao", "Palmier à huile"],
        "production_2023": {
            "Riz": {"value": 300000, "unit": "tonnes", "area_ha": 280000, "yield_kg_ha": 1071},
            "Manioc": {"value": 650000, "unit": "tonnes", "area_ha": 90000, "yield_kg_ha": 7222},
            "Hévéa": {"value": 65000, "unit": "tonnes", "area_ha": 120000, "yield_kg_ha": 542},
        },
        "key_indicators": {
            "agri_gdp_percent": 34.0,
            "agri_employment_percent": 44.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "GNB": {
        "country_name": "Guinée-Bissau",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Noix de cajou", "Riz", "Arachide", "Palmier à huile"],
        "production_2023": {
            "Noix de cajou": {"value": 200000, "unit": "tonnes", "rank_africa": 4, "area_ha": 300000, "yield_kg_ha": 667},
            "Riz": {"value": 190000, "unit": "tonnes", "area_ha": 100000, "yield_kg_ha": 1900},
        },
        "key_indicators": {
            "agri_gdp_percent": 50.0,
            "agri_employment_percent": 68.0,
            "cashew_export_percent": 90,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "GMB": {
        "country_name": "Gambie",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Arachide", "Mil", "Sorgho", "Riz", "Maïs"],
        "production_2023": {
            "Arachide": {"value": 180000, "unit": "tonnes", "area_ha": 120000, "yield_kg_ha": 1500},
            "Mil": {"value": 120000, "unit": "tonnes", "area_ha": 100000, "yield_kg_ha": 1200},
            "Riz": {"value": 55000, "unit": "tonnes", "area_ha": 40000, "yield_kg_ha": 1375},
        },
        "fisheries_2023": {
            "capture": {"value": 55000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 20.0,
            "agri_employment_percent": 75.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "CPV": {
        "country_name": "Cap-Vert",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Maïs", "Banane", "Canne à sucre", "Légumes"],
        "production_2023": {
            "Maïs": {"value": 8000, "unit": "tonnes", "area_ha": 8000, "yield_kg_ha": 1000},
            "Banane": {"value": 7500, "unit": "tonnes", "area_ha": 2000, "yield_kg_ha": 3750},
            "Canne à sucre": {"value": 25000, "unit": "tonnes", "area_ha": 800, "yield_kg_ha": 31250},
        },
        "fisheries_2023": {
            "capture": {"value": 35000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 5.0,
            "agri_employment_percent": 10.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "MRT": {
        "country_name": "Mauritanie",
        "region": "Afrique de l'Ouest",
        "main_crops": ["Riz", "Mil", "Sorgho", "Dattes"],
        "production_2023": {
            "Riz": {"value": 320000, "unit": "tonnes", "area_ha": 45000, "yield_kg_ha": 7111},
            "Mil": {"value": 25000, "unit": "tonnes", "area_ha": 20000, "yield_kg_ha": 1250},
            "Dattes": {"value": 95000, "unit": "tonnes", "area_ha": 20000, "yield_kg_ha": 4750},
        },
        "livestock_2023": {
            "Bovins": {"value": 1900000, "unit": "têtes"},
            "Ovins": {"value": 11000000, "unit": "têtes"},
            "Caprins": {"value": 7500000, "unit": "têtes"},
            "Camelins": {"value": 1500000, "unit": "têtes", "rank_africa": 3},
        },
        "fisheries_2023": {
            "capture": {"value": 900000, "unit": "tonnes", "rank_africa": 2},
        },
        "key_indicators": {
            "agri_gdp_percent": 22.0,
            "agri_employment_percent": 50.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    # =========================================================================
    # AFRIQUE CENTRALE
    # =========================================================================
    "CMR": {
        "country_name": "Cameroun",
        "region": "Afrique Centrale",
        "main_crops": ["Cacao", "Café", "Banane", "Manioc", "Maïs", "Huile de palme"],
        "production_2023": {
            "Cacao": {"value": 290000, "unit": "tonnes", "rank_africa": 4, "area_ha": 600000, "yield_kg_ha": 483},
            "Banane": {"value": 1500000, "unit": "tonnes", "rank_africa": 5, "area_ha": 100000, "yield_kg_ha": 15000},
            "Manioc": {"value": 6000000, "unit": "tonnes", "rank_africa": 5, "area_ha": 300000, "yield_kg_ha": 20000},
            "Huile de palme": {"value": 380000, "unit": "tonnes", "rank_africa": 4, "area_ha": 200000, "yield_kg_ha": 1900},
            "Café": {"value": 35000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 175},
        },
        "evolution": {
            "Cacao": [{"year": 2020, "value": 270000}, {"year": 2021, "value": 280000}, {"year": 2022, "value": 285000}, {"year": 2023, "value": 290000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 6500000, "unit": "têtes"},
            "Ovins": {"value": 4000000, "unit": "têtes"},
            "Caprins": {"value": 6500000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 280000, "unit": "tonnes"},
            "aquaculture": {"value": 2500, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 16.7,
            "agri_employment_percent": 45.0,
        },
        "source": "FAOSTAT 2023, INS Cameroun",
        "data_year": 2023
    },
    
    "COD": {
        "country_name": "RD Congo",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Maïs", "Plantain", "Riz", "Huile de palme", "Café"],
        "production_2023": {
            "Manioc": {"value": 45000000, "unit": "tonnes", "rank_africa": 2, "area_ha": 4000000, "yield_kg_ha": 11250},
            "Maïs": {"value": 2500000, "unit": "tonnes", "area_ha": 2200000, "yield_kg_ha": 1136},
            "Plantain": {"value": 5000000, "unit": "tonnes", "rank_africa": 1, "area_ha": 500000, "yield_kg_ha": 10000},
            "Huile de palme": {"value": 230000, "unit": "tonnes", "area_ha": 180000, "yield_kg_ha": 1278},
        },
        "evolution": {
            "Manioc": [{"year": 2020, "value": 42000000}, {"year": 2021, "value": 43000000}, {"year": 2022, "value": 44000000}, {"year": 2023, "value": 45000000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 1000000, "unit": "têtes"},
            "Caprins": {"value": 4500000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 240000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 19.0,
            "agri_employment_percent": 65.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "COG": {
        "country_name": "République du Congo",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Banane", "Canne à sucre", "Huile de palme"],
        "production_2023": {
            "Manioc": {"value": 1500000, "unit": "tonnes", "area_ha": 130000, "yield_kg_ha": 11538},
            "Banane": {"value": 120000, "unit": "tonnes", "area_ha": 15000, "yield_kg_ha": 8000},
            "Canne à sucre": {"value": 650000, "unit": "tonnes", "area_ha": 10000, "yield_kg_ha": 65000},
        },
        "livestock_2023": {
            "Bovins": {"value": 350000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 4.5,
            "agri_employment_percent": 35.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "GAB": {
        "country_name": "Gabon",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Plantain", "Huile de palme", "Canne à sucre"],
        "production_2023": {
            "Manioc": {"value": 330000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 6600},
            "Plantain": {"value": 280000, "unit": "tonnes", "area_ha": 35000, "yield_kg_ha": 8000},
            "Huile de palme": {"value": 35000, "unit": "tonnes", "area_ha": 15000, "yield_kg_ha": 2333},
        },
        "key_indicators": {
            "agri_gdp_percent": 3.5,
            "agri_employment_percent": 20.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "GNQ": {
        "country_name": "Guinée Équatoriale",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Cacao", "Café", "Banane"],
        "production_2023": {
            "Manioc": {"value": 50000, "unit": "tonnes", "area_ha": 8000, "yield_kg_ha": 6250},
            "Cacao": {"value": 5500, "unit": "tonnes", "area_ha": 20000, "yield_kg_ha": 275},
        },
        "key_indicators": {
            "agri_gdp_percent": 2.0,
            "agri_employment_percent": 4.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "CAF": {
        "country_name": "République Centrafricaine",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Arachide", "Maïs", "Sorgho", "Café"],
        "production_2023": {
            "Manioc": {"value": 4800000, "unit": "tonnes", "area_ha": 500000, "yield_kg_ha": 9600},
            "Arachide": {"value": 250000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 1250},
            "Maïs": {"value": 200000, "unit": "tonnes", "area_ha": 150000, "yield_kg_ha": 1333},
        },
        "key_indicators": {
            "agri_gdp_percent": 40.0,
            "agri_employment_percent": 75.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "TCD": {
        "country_name": "Tchad",
        "region": "Afrique Centrale",
        "main_crops": ["Sorgho", "Mil", "Arachide", "Coton", "Riz"],
        "production_2023": {
            "Sorgho": {"value": 2200000, "unit": "tonnes", "rank_africa": 3, "area_ha": 2500000, "yield_kg_ha": 880},
            "Mil": {"value": 900000, "unit": "tonnes", "area_ha": 1500000, "yield_kg_ha": 600},
            "Arachide": {"value": 600000, "unit": "tonnes", "area_ha": 500000, "yield_kg_ha": 1200},
            "Coton": {"value": 180000, "unit": "tonnes", "area_ha": 350000, "yield_kg_ha": 514},
        },
        "livestock_2023": {
            "Bovins": {"value": 8000000, "unit": "têtes", "rank_africa": 8},
            "Ovins": {"value": 3500000, "unit": "têtes"},
            "Caprins": {"value": 8000000, "unit": "têtes"},
            "Camelins": {"value": 1800000, "unit": "têtes", "rank_africa": 2},
        },
        "fisheries_2023": {
            "capture": {"value": 120000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 45.0,
            "agri_employment_percent": 80.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "AGO": {
        "country_name": "Angola",
        "region": "Afrique Centrale",
        "main_crops": ["Manioc", "Maïs", "Banane", "Patate douce", "Café"],
        "production_2023": {
            "Manioc": {"value": 11500000, "unit": "tonnes", "rank_africa": 4, "area_ha": 1200000, "yield_kg_ha": 9583},
            "Maïs": {"value": 2300000, "unit": "tonnes", "area_ha": 1500000, "yield_kg_ha": 1533},
            "Banane": {"value": 4500000, "unit": "tonnes", "area_ha": 150000, "yield_kg_ha": 30000},
            "Café": {"value": 15000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 300},
        },
        "evolution": {
            "Manioc": [{"year": 2020, "value": 10000000}, {"year": 2021, "value": 10500000}, {"year": 2022, "value": 11000000}, {"year": 2023, "value": 11500000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 5500000, "unit": "têtes"},
            "Caprins": {"value": 4000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 450000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 8.0,
            "agri_employment_percent": 52.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "STP": {
        "country_name": "São Tomé-et-Príncipe",
        "region": "Afrique Centrale",
        "main_crops": ["Cacao", "Coprah", "Banane", "Huile de palme"],
        "production_2023": {
            "Cacao": {"value": 3500, "unit": "tonnes", "area_ha": 8000, "yield_kg_ha": 438},
            "Banane": {"value": 3000, "unit": "tonnes", "area_ha": 600, "yield_kg_ha": 5000},
        },
        "fisheries_2023": {
            "capture": {"value": 8500, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 11.0,
            "agri_employment_percent": 25.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    # =========================================================================
    # AFRIQUE DE L'EST
    # =========================================================================
    "ETH": {
        "country_name": "Éthiopie",
        "region": "Afrique de l'Est",
        "main_crops": ["Café", "Teff", "Maïs", "Blé", "Sorgho", "Orge"],
        "production_2023": {
            "Café": {"value": 500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 700000, "yield_kg_ha": 714},
            "Teff": {"value": 5800000, "unit": "tonnes", "rank_africa": 1, "area_ha": 3200000, "yield_kg_ha": 1813},
            "Maïs": {"value": 11000000, "unit": "tonnes", "rank_africa": 4, "area_ha": 2600000, "yield_kg_ha": 4231},
            "Blé": {"value": 5500000, "unit": "tonnes", "rank_africa": 3, "area_ha": 1900000, "yield_kg_ha": 2895},
            "Sorgho": {"value": 5000000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1800000, "yield_kg_ha": 2778},
        },
        "evolution": {
            "Café": [{"year": 2020, "value": 450000}, {"year": 2021, "value": 480000}, {"year": 2022, "value": 490000}, {"year": 2023, "value": 500000}],
            "Maïs": [{"year": 2020, "value": 10000000}, {"year": 2021, "value": 10500000}, {"year": 2022, "value": 10800000}, {"year": 2023, "value": 11000000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 72000000, "unit": "têtes", "rank_africa": 1},
            "Ovins": {"value": 42000000, "unit": "têtes", "rank_africa": 3},
            "Caprins": {"value": 55000000, "unit": "têtes", "rank_africa": 2},
        },
        "fisheries_2023": {
            "capture": {"value": 60000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 35.5,
            "agri_employment_percent": 66.0,
            "coffee_export_value_mln_usd": 1400,
            "arable_land_ha": 16000000,
        },
        "source": "FAOSTAT 2023, CSA Ethiopia",
        "data_year": 2023
    },
    
    "KEN": {
        "country_name": "Kenya",
        "region": "Afrique de l'Est",
        "main_crops": ["Thé", "Café", "Maïs", "Fleurs coupées", "Légumes", "Fruits"],
        "production_2023": {
            "Thé": {"value": 540000, "unit": "tonnes", "rank_africa": 1, "rank_world": 3, "area_ha": 270000, "yield_kg_ha": 2000},
            "Café": {"value": 45000, "unit": "tonnes", "rank_africa": 4, "area_ha": 120000, "yield_kg_ha": 375},
            "Maïs": {"value": 4200000, "unit": "tonnes", "rank_africa": 6, "area_ha": 2200000, "yield_kg_ha": 1909},
            "Fleurs coupées": {"value": 200000, "unit": "tonnes", "rank_africa": 1, "rank_world": 4, "area_ha": 8000, "yield_kg_ha": 25000},
        },
        "evolution": {
            "Thé": [{"year": 2020, "value": 480000}, {"year": 2021, "value": 500000}, {"year": 2022, "value": 520000}, {"year": 2023, "value": 540000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 18000000, "unit": "têtes"},
            "Ovins": {"value": 17000000, "unit": "têtes"},
            "Caprins": {"value": 28000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 150000, "unit": "tonnes"},
            "aquaculture": {"value": 25000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 22.4,
            "agri_employment_percent": 54.0,
            "tea_export_value_mln_usd": 1400,
            "flower_export_value_mln_usd": 1000,
        },
        "source": "FAOSTAT 2023, KNBS Kenya",
        "data_year": 2023
    },
    
    "TZA": {
        "country_name": "Tanzanie",
        "region": "Afrique de l'Est",
        "main_crops": ["Manioc", "Maïs", "Riz", "Banane", "Coton", "Noix de cajou"],
        "production_2023": {
            "Manioc": {"value": 9500000, "unit": "tonnes", "rank_africa": 5, "area_ha": 1000000, "yield_kg_ha": 9500},
            "Maïs": {"value": 6800000, "unit": "tonnes", "rank_africa": 5, "area_ha": 5000000, "yield_kg_ha": 1360},
            "Riz": {"value": 3500000, "unit": "tonnes", "rank_africa": 4, "area_ha": 1200000, "yield_kg_ha": 2917},
            "Banane": {"value": 4000000, "unit": "tonnes", "rank_africa": 3, "area_ha": 500000, "yield_kg_ha": 8000},
            "Noix de cajou": {"value": 280000, "unit": "tonnes", "rank_africa": 3, "area_ha": 400000, "yield_kg_ha": 700},
        },
        "livestock_2023": {
            "Bovins": {"value": 32000000, "unit": "têtes", "rank_africa": 3},
            "Caprins": {"value": 18000000, "unit": "têtes"},
            "Ovins": {"value": 5000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 400000, "unit": "tonnes"},
            "aquaculture": {"value": 20000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 26.5,
            "agri_employment_percent": 65.0,
        },
        "source": "FAOSTAT 2023, NBS Tanzania",
        "data_year": 2023
    },
    
    "UGA": {
        "country_name": "Ouganda",
        "region": "Afrique de l'Est",
        "main_crops": ["Café", "Banane", "Manioc", "Maïs", "Thé", "Sucre"],
        "production_2023": {
            "Café": {"value": 650000, "unit": "tonnes", "rank_africa": 2, "area_ha": 500000, "yield_kg_ha": 1300},
            "Banane": {"value": 10500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 850000, "yield_kg_ha": 12353},
            "Manioc": {"value": 3000000, "unit": "tonnes", "rank_africa": 7, "area_ha": 350000, "yield_kg_ha": 8571},
            "Maïs": {"value": 3200000, "unit": "tonnes", "area_ha": 1200000, "yield_kg_ha": 2667},
        },
        "evolution": {
            "Café": [{"year": 2020, "value": 500000}, {"year": 2021, "value": 550000}, {"year": 2022, "value": 600000}, {"year": 2023, "value": 650000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 15000000, "unit": "têtes"},
            "Caprins": {"value": 16000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 550000, "unit": "tonnes", "rank_africa": 3},
            "aquaculture": {"value": 130000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 24.1,
            "agri_employment_percent": 68.0,
            "coffee_export_value_mln_usd": 900,
        },
        "source": "FAOSTAT 2023, UBOS Uganda",
        "data_year": 2023
    },
    
    "RWA": {
        "country_name": "Rwanda",
        "region": "Afrique de l'Est",
        "main_crops": ["Café", "Thé", "Banane", "Haricot", "Manioc", "Maïs"],
        "production_2023": {
            "Café": {"value": 25000, "unit": "tonnes", "area_ha": 45000, "yield_kg_ha": 556},
            "Thé": {"value": 35000, "unit": "tonnes", "area_ha": 25000, "yield_kg_ha": 1400},
            "Banane": {"value": 3500000, "unit": "tonnes", "area_ha": 250000, "yield_kg_ha": 14000},
            "Haricot": {"value": 450000, "unit": "tonnes", "area_ha": 400000, "yield_kg_ha": 1125},
        },
        "livestock_2023": {
            "Bovins": {"value": 1400000, "unit": "têtes"},
            "Caprins": {"value": 2800000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 30000, "unit": "tonnes"},
            "aquaculture": {"value": 35000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 25.0,
            "agri_employment_percent": 62.0,
        },
        "source": "FAOSTAT 2023, NISR Rwanda",
        "data_year": 2023
    },
    
    "BDI": {
        "country_name": "Burundi",
        "region": "Afrique de l'Est",
        "main_crops": ["Café", "Thé", "Banane", "Manioc", "Haricot"],
        "production_2023": {
            "Café": {"value": 18000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 360},
            "Thé": {"value": 12000, "unit": "tonnes", "area_ha": 12000, "yield_kg_ha": 1000},
            "Banane": {"value": 2000000, "unit": "tonnes", "area_ha": 250000, "yield_kg_ha": 8000},
            "Manioc": {"value": 2500000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 12500},
        },
        "livestock_2023": {
            "Bovins": {"value": 650000, "unit": "têtes"},
            "Caprins": {"value": 3000000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 40.0,
            "agri_employment_percent": 90.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "MDG": {
        "country_name": "Madagascar",
        "region": "Afrique de l'Est",
        "main_crops": ["Riz", "Manioc", "Vanille", "Clou de girofle", "Cacao"],
        "production_2023": {
            "Riz": {"value": 4200000, "unit": "tonnes", "rank_africa": 2, "area_ha": 1300000, "yield_kg_ha": 3231},
            "Manioc": {"value": 4500000, "unit": "tonnes", "area_ha": 400000, "yield_kg_ha": 11250},
            "Vanille": {"value": 2500, "unit": "tonnes", "rank_world": 1, "area_ha": 30000, "yield_kg_ha": 83},
            "Clou de girofle": {"value": 22000, "unit": "tonnes", "rank_world": 3, "area_ha": 40000, "yield_kg_ha": 550},
        },
        "evolution": {
            "Vanille": [{"year": 2020, "value": 2000}, {"year": 2021, "value": 2200}, {"year": 2022, "value": 2400}, {"year": 2023, "value": 2500}],
        },
        "livestock_2023": {
            "Bovins": {"value": 10000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 150000, "unit": "tonnes"},
            "aquaculture": {"value": 15000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 24.0,
            "agri_employment_percent": 76.0,
            "vanilla_export_value_mln_usd": 600,
        },
        "source": "FAOSTAT 2023, INSTAT Madagascar",
        "data_year": 2023
    },
    
    "MOZ": {
        "country_name": "Mozambique",
        "region": "Afrique de l'Est",
        "main_crops": ["Manioc", "Maïs", "Noix de cajou", "Canne à sucre", "Coton"],
        "production_2023": {
            "Manioc": {"value": 14500000, "unit": "tonnes", "rank_africa": 3, "area_ha": 1500000, "yield_kg_ha": 9667},
            "Maïs": {"value": 2200000, "unit": "tonnes", "area_ha": 2000000, "yield_kg_ha": 1100},
            "Noix de cajou": {"value": 150000, "unit": "tonnes", "area_ha": 250000, "yield_kg_ha": 600},
            "Canne à sucre": {"value": 3200000, "unit": "tonnes", "area_ha": 45000, "yield_kg_ha": 71111},
        },
        "livestock_2023": {
            "Bovins": {"value": 1500000, "unit": "têtes"},
            "Caprins": {"value": 5000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 350000, "unit": "tonnes"},
            "aquaculture": {"value": 3000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 25.0,
            "agri_employment_percent": 70.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "MWI": {
        "country_name": "Malawi",
        "region": "Afrique de l'Est",
        "main_crops": ["Tabac", "Maïs", "Thé", "Sucre", "Manioc"],
        "production_2023": {
            "Tabac": {"value": 120000, "unit": "tonnes", "rank_africa": 2, "area_ha": 100000, "yield_kg_ha": 1200},
            "Maïs": {"value": 4500000, "unit": "tonnes", "area_ha": 1800000, "yield_kg_ha": 2500},
            "Thé": {"value": 50000, "unit": "tonnes", "rank_africa": 3, "area_ha": 20000, "yield_kg_ha": 2500},
            "Manioc": {"value": 6000000, "unit": "tonnes", "area_ha": 400000, "yield_kg_ha": 15000},
        },
        "livestock_2023": {
            "Bovins": {"value": 1200000, "unit": "têtes"},
            "Caprins": {"value": 8000000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 200000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 22.0,
            "agri_employment_percent": 76.0,
            "tobacco_export_value_mln_usd": 400,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "SDN": {
        "country_name": "Soudan",
        "region": "Afrique de l'Est",
        "main_crops": ["Sorgho", "Mil", "Sésame", "Arachide", "Gomme arabique"],
        "production_2023": {
            "Sorgho": {"value": 4500000, "unit": "tonnes", "rank_africa": 2, "area_ha": 6000000, "yield_kg_ha": 750},
            "Mil": {"value": 1200000, "unit": "tonnes", "area_ha": 2000000, "yield_kg_ha": 600},
            "Sésame": {"value": 950000, "unit": "tonnes", "rank_africa": 1, "area_ha": 2500000, "yield_kg_ha": 380},
            "Gomme arabique": {"value": 90000, "unit": "tonnes", "rank_world": 1},
        },
        "livestock_2023": {
            "Bovins": {"value": 32000000, "unit": "têtes", "rank_africa": 4},
            "Ovins": {"value": 40000000, "unit": "têtes", "rank_africa": 2},
            "Caprins": {"value": 32000000, "unit": "têtes"},
            "Camelins": {"value": 4800000, "unit": "têtes", "rank_africa": 1},
        },
        "key_indicators": {
            "agri_gdp_percent": 30.0,
            "agri_employment_percent": 40.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "SSD": {
        "country_name": "Soudan du Sud",
        "region": "Afrique de l'Est",
        "main_crops": ["Sorgho", "Maïs", "Manioc", "Arachide"],
        "production_2023": {
            "Sorgho": {"value": 800000, "unit": "tonnes", "area_ha": 700000, "yield_kg_ha": 1143},
            "Maïs": {"value": 150000, "unit": "tonnes", "area_ha": 100000, "yield_kg_ha": 1500},
        },
        "livestock_2023": {
            "Bovins": {"value": 12000000, "unit": "têtes"},
            "Ovins": {"value": 13000000, "unit": "têtes"},
            "Caprins": {"value": 14000000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 10.0,
            "agri_employment_percent": 75.0,
        },
        "source": "FAOSTAT 2023, estimation",
        "data_year": 2023
    },
    
    "ERI": {
        "country_name": "Érythrée",
        "region": "Afrique de l'Est",
        "main_crops": ["Sorgho", "Mil", "Orge", "Blé"],
        "production_2023": {
            "Sorgho": {"value": 180000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 900},
            "Mil": {"value": 50000, "unit": "tonnes", "area_ha": 60000, "yield_kg_ha": 833},
        },
        "livestock_2023": {
            "Bovins": {"value": 2000000, "unit": "têtes"},
            "Ovins": {"value": 2500000, "unit": "têtes"},
            "Caprins": {"value": 4000000, "unit": "têtes"},
            "Camelins": {"value": 350000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 5000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 12.0,
            "agri_employment_percent": 60.0,
        },
        "source": "FAOSTAT 2023, estimation",
        "data_year": 2023
    },
    
    "DJI": {
        "country_name": "Djibouti",
        "region": "Afrique de l'Est",
        "main_crops": ["Fruits", "Légumes"],
        "production_2023": {
            "Légumes": {"value": 25000, "unit": "tonnes", "area_ha": 3000, "yield_kg_ha": 8333},
        },
        "livestock_2023": {
            "Caprins": {"value": 500000, "unit": "têtes"},
            "Ovins": {"value": 400000, "unit": "têtes"},
            "Camelins": {"value": 70000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 2500, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 1.5,
            "agri_employment_percent": 5.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "SOM": {
        "country_name": "Somalie",
        "region": "Afrique de l'Est",
        "main_crops": ["Sorgho", "Maïs", "Banane", "Sésame"],
        "production_2023": {
            "Sorgho": {"value": 400000, "unit": "tonnes", "area_ha": 500000, "yield_kg_ha": 800},
            "Maïs": {"value": 350000, "unit": "tonnes", "area_ha": 300000, "yield_kg_ha": 1167},
            "Banane": {"value": 120000, "unit": "tonnes", "area_ha": 15000, "yield_kg_ha": 8000},
        },
        "livestock_2023": {
            "Camelins": {"value": 7000000, "unit": "têtes", "rank_world": 1},
            "Caprins": {"value": 25000000, "unit": "têtes"},
            "Ovins": {"value": 20000000, "unit": "têtes"},
            "Bovins": {"value": 5500000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 30000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 65.0,
            "agri_employment_percent": 71.0,
            "livestock_export_significant": True,
        },
        "source": "FAOSTAT 2023, estimation",
        "data_year": 2023
    },
    
    "COM": {
        "country_name": "Comores",
        "region": "Afrique de l'Est",
        "main_crops": ["Vanille", "Ylang-ylang", "Clou de girofle", "Banane", "Manioc"],
        "production_2023": {
            "Vanille": {"value": 80, "unit": "tonnes", "rank_world": 3, "area_ha": 500, "yield_kg_ha": 160},
            "Ylang-ylang": {"value": 50, "unit": "tonnes", "rank_world": 1},
            "Banane": {"value": 70000, "unit": "tonnes", "area_ha": 10000, "yield_kg_ha": 7000},
            "Manioc": {"value": 95000, "unit": "tonnes", "area_ha": 15000, "yield_kg_ha": 6333},
        },
        "fisheries_2023": {
            "capture": {"value": 18000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 35.0,
            "agri_employment_percent": 80.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "MUS": {
        "country_name": "Maurice",
        "region": "Afrique de l'Est",
        "main_crops": ["Canne à sucre", "Thé", "Légumes"],
        "production_2023": {
            "Canne à sucre": {"value": 3200000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 64000},
            "Thé": {"value": 8000, "unit": "tonnes", "area_ha": 650, "yield_kg_ha": 12308},
        },
        "fisheries_2023": {
            "capture": {"value": 5000, "unit": "tonnes"},
            "aquaculture": {"value": 2000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 3.5,
            "agri_employment_percent": 6.0,
        },
        "source": "FAOSTAT 2023, Statistics Mauritius",
        "data_year": 2023
    },
    
    "SYC": {
        "country_name": "Seychelles",
        "region": "Afrique de l'Est",
        "main_crops": ["Noix de coco", "Banane", "Cannelle"],
        "production_2023": {
            "Noix de coco": {"value": 2500, "unit": "tonnes", "area_ha": 3000, "yield_kg_ha": 833},
            "Cannelle": {"value": 200, "unit": "tonnes"},
        },
        "fisheries_2023": {
            "capture": {"value": 95000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 2.0,
            "agri_employment_percent": 2.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    # =========================================================================
    # AFRIQUE AUSTRALE
    # =========================================================================
    "ZAF": {
        "country_name": "Afrique du Sud",
        "region": "Afrique Australe",
        "main_crops": ["Maïs", "Canne à sucre", "Blé", "Soja", "Tournesol", "Agrumes"],
        "production_2023": {
            "Maïs": {"value": 16500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 2800000, "yield_kg_ha": 5893},
            "Canne à sucre": {"value": 18500000, "unit": "tonnes", "rank_africa": 1, "area_ha": 340000, "yield_kg_ha": 54412},
            "Blé": {"value": 2100000, "unit": "tonnes", "rank_africa": 5, "area_ha": 510000, "yield_kg_ha": 4118},
            "Soja": {"value": 2800000, "unit": "tonnes", "rank_africa": 1, "area_ha": 950000, "yield_kg_ha": 2947},
            "Tournesol": {"value": 900000, "unit": "tonnes", "rank_africa": 1, "area_ha": 550000, "yield_kg_ha": 1636},
            "Agrumes": {"value": 3200000, "unit": "tonnes", "rank_africa": 3, "area_ha": 80000, "yield_kg_ha": 40000},
        },
        "evolution": {
            "Maïs": [{"year": 2020, "value": 15300000}, {"year": 2021, "value": 16400000}, {"year": 2022, "value": 15700000}, {"year": 2023, "value": 16500000}],
            "Blé": [{"year": 2020, "value": 1800000}, {"year": 2021, "value": 2100000}, {"year": 2022, "value": 2400000}, {"year": 2023, "value": 2100000}],
        },
        "livestock_2023": {
            "Bovins": {"value": 12500000, "unit": "têtes", "rank_africa": 5},
            "Ovins": {"value": 21000000, "unit": "têtes", "rank_africa": 5},
            "Volailles": {"value": 300000000, "unit": "têtes", "rank_africa": 1},
        },
        "fisheries_2023": {
            "capture": {"value": 550000, "unit": "tonnes"},
            "aquaculture": {"value": 8000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 2.5,
            "agri_employment_percent": 5.0,
            "agri_export_value_mln_usd": 12500,
            "arable_land_ha": 12500000,
            "irrigated_land_ha": 1600000,
        },
        "source": "FAOSTAT 2023, DAFF South Africa",
        "data_year": 2023
    },
    
    "ZMB": {
        "country_name": "Zambie",
        "region": "Afrique Australe",
        "main_crops": ["Maïs", "Manioc", "Soja", "Blé", "Coton"],
        "production_2023": {
            "Maïs": {"value": 3500000, "unit": "tonnes", "area_ha": 1600000, "yield_kg_ha": 2188},
            "Manioc": {"value": 1200000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 6000},
            "Soja": {"value": 450000, "unit": "tonnes", "area_ha": 250000, "yield_kg_ha": 1800},
            "Coton": {"value": 100000, "unit": "tonnes", "area_ha": 200000, "yield_kg_ha": 500},
        },
        "livestock_2023": {
            "Bovins": {"value": 3800000, "unit": "têtes"},
            "Caprins": {"value": 3500000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 90000, "unit": "tonnes"},
            "aquaculture": {"value": 35000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 3.0,
            "agri_employment_percent": 50.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "ZWE": {
        "country_name": "Zimbabwe",
        "region": "Afrique Australe",
        "main_crops": ["Tabac", "Maïs", "Coton", "Soja", "Blé"],
        "production_2023": {
            "Tabac": {"value": 290000, "unit": "tonnes", "rank_africa": 1, "area_ha": 140000, "yield_kg_ha": 2071},
            "Maïs": {"value": 2800000, "unit": "tonnes", "area_ha": 1400000, "yield_kg_ha": 2000},
            "Coton": {"value": 100000, "unit": "tonnes", "area_ha": 300000, "yield_kg_ha": 333},
            "Soja": {"value": 150000, "unit": "tonnes", "area_ha": 80000, "yield_kg_ha": 1875},
        },
        "livestock_2023": {
            "Bovins": {"value": 5500000, "unit": "têtes"},
            "Caprins": {"value": 4000000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 12.0,
            "agri_employment_percent": 67.0,
            "tobacco_export_value_mln_usd": 900,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "BWA": {
        "country_name": "Botswana",
        "region": "Afrique Australe",
        "main_crops": ["Sorgho", "Maïs", "Mil"],
        "production_2023": {
            "Sorgho": {"value": 45000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 900},
            "Maïs": {"value": 20000, "unit": "tonnes", "area_ha": 30000, "yield_kg_ha": 667},
        },
        "livestock_2023": {
            "Bovins": {"value": 1800000, "unit": "têtes"},
            "Caprins": {"value": 1600000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 2.0,
            "agri_employment_percent": 20.0,
            "beef_export_significant": True,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "NAM": {
        "country_name": "Namibie",
        "region": "Afrique Australe",
        "main_crops": ["Mil", "Maïs", "Sorgho", "Blé"],
        "production_2023": {
            "Mil": {"value": 60000, "unit": "tonnes", "area_ha": 250000, "yield_kg_ha": 240},
            "Maïs": {"value": 80000, "unit": "tonnes", "area_ha": 50000, "yield_kg_ha": 1600},
        },
        "livestock_2023": {
            "Bovins": {"value": 2500000, "unit": "têtes"},
            "Ovins": {"value": 2000000, "unit": "têtes"},
            "Caprins": {"value": 1800000, "unit": "têtes"},
        },
        "fisheries_2023": {
            "capture": {"value": 550000, "unit": "tonnes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 5.0,
            "agri_employment_percent": 25.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "LSO": {
        "country_name": "Lesotho",
        "region": "Afrique Australe",
        "main_crops": ["Maïs", "Sorgho", "Blé", "Haricot"],
        "production_2023": {
            "Maïs": {"value": 80000, "unit": "tonnes", "area_ha": 100000, "yield_kg_ha": 800},
            "Sorgho": {"value": 25000, "unit": "tonnes", "area_ha": 30000, "yield_kg_ha": 833},
            "Blé": {"value": 15000, "unit": "tonnes", "area_ha": 15000, "yield_kg_ha": 1000},
        },
        "livestock_2023": {
            "Bovins": {"value": 600000, "unit": "têtes"},
            "Ovins": {"value": 1200000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 5.0,
            "agri_employment_percent": 40.0,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
    
    "SWZ": {
        "country_name": "Eswatini",
        "region": "Afrique Australe",
        "main_crops": ["Canne à sucre", "Maïs", "Agrumes"],
        "production_2023": {
            "Canne à sucre": {"value": 5500000, "unit": "tonnes", "area_ha": 55000, "yield_kg_ha": 100000},
            "Maïs": {"value": 90000, "unit": "tonnes", "area_ha": 80000, "yield_kg_ha": 1125},
        },
        "livestock_2023": {
            "Bovins": {"value": 600000, "unit": "têtes"},
            "Caprins": {"value": 400000, "unit": "têtes"},
        },
        "key_indicators": {
            "agri_gdp_percent": 6.5,
            "agri_employment_percent": 15.0,
            "sugar_export_significant": True,
        },
        "source": "FAOSTAT 2023",
        "data_year": 2023
    },
}

# =============================================================================
# CLASSEMENTS AFRICAINS PAR PRODUIT
# =============================================================================

AFRICA_TOP_PRODUCERS = {
    "Cacao": [
        {"rank": 1, "country": "CIV", "name": "Côte d'Ivoire", "production_tonnes": 2200000, "share_africa": 44},
        {"rank": 2, "country": "GHA", "name": "Ghana", "production_tonnes": 700000, "share_africa": 14},
        {"rank": 3, "country": "CMR", "name": "Cameroun", "production_tonnes": 290000, "share_africa": 6},
        {"rank": 4, "country": "NGA", "name": "Nigéria", "production_tonnes": 280000, "share_africa": 5.6},
    ],
    "Café": [
        {"rank": 1, "country": "ETH", "name": "Éthiopie", "production_tonnes": 500000, "share_africa": 35},
        {"rank": 2, "country": "UGA", "name": "Ouganda", "production_tonnes": 650000, "share_africa": 45},
        {"rank": 3, "country": "CIV", "name": "Côte d'Ivoire", "production_tonnes": 120000, "share_africa": 8},
        {"rank": 4, "country": "KEN", "name": "Kenya", "production_tonnes": 45000, "share_africa": 3},
    ],
    "Maïs": [
        {"rank": 1, "country": "ZAF", "name": "Afrique du Sud", "production_tonnes": 16500000, "share_africa": 21},
        {"rank": 2, "country": "NGA", "name": "Nigéria", "production_tonnes": 12500000, "share_africa": 16},
        {"rank": 3, "country": "EGY", "name": "Égypte", "production_tonnes": 7800000, "share_africa": 10},
        {"rank": 4, "country": "ETH", "name": "Éthiopie", "production_tonnes": 11000000, "share_africa": 14},
        {"rank": 5, "country": "TZA", "name": "Tanzanie", "production_tonnes": 6800000, "share_africa": 9},
    ],
    "Blé": [
        {"rank": 1, "country": "EGY", "name": "Égypte", "production_tonnes": 9500000, "share_africa": 45},
        {"rank": 2, "country": "MAR", "name": "Maroc", "production_tonnes": 5500000, "share_africa": 26},
        {"rank": 3, "country": "ETH", "name": "Éthiopie", "production_tonnes": 5500000, "share_africa": 14},
        {"rank": 4, "country": "DZA", "name": "Algérie", "production_tonnes": 3500000, "share_africa": 9},
    ],
    "Manioc": [
        {"rank": 1, "country": "NGA", "name": "Nigéria", "production_tonnes": 63000000, "share_africa": 35},
        {"rank": 2, "country": "COD", "name": "RD Congo", "production_tonnes": 45000000, "share_africa": 25},
        {"rank": 3, "country": "MOZ", "name": "Mozambique", "production_tonnes": 14500000, "share_africa": 8},
        {"rank": 4, "country": "AGO", "name": "Angola", "production_tonnes": 11500000, "share_africa": 6},
        {"rank": 5, "country": "GHA", "name": "Ghana", "production_tonnes": 23000000, "share_africa": 13},
    ],
    "Thé": [
        {"rank": 1, "country": "KEN", "name": "Kenya", "production_tonnes": 540000, "share_africa": 60},
        {"rank": 2, "country": "UGA", "name": "Ouganda", "production_tonnes": 75000, "share_africa": 8},
        {"rank": 3, "country": "MWI", "name": "Malawi", "production_tonnes": 50000, "share_africa": 6},
        {"rank": 4, "country": "TZA", "name": "Tanzanie", "production_tonnes": 40000, "share_africa": 4},
    ],
    "Riz": [
        {"rank": 1, "country": "EGY", "name": "Égypte", "production_tonnes": 4200000, "share_africa": 18},
        {"rank": 2, "country": "MDG", "name": "Madagascar", "production_tonnes": 4200000, "share_africa": 18},
        {"rank": 3, "country": "NGA", "name": "Nigéria", "production_tonnes": 5200000, "share_africa": 22},
        {"rank": 4, "country": "MLI", "name": "Mali", "production_tonnes": 3200000, "share_africa": 14},
        {"rank": 5, "country": "TZA", "name": "Tanzanie", "production_tonnes": 3500000, "share_africa": 15},
    ],
    "Coton": [
        {"rank": 1, "country": "MLI", "name": "Mali", "production_tonnes": 700000, "share_africa": 26},
        {"rank": 2, "country": "BEN", "name": "Bénin", "production_tonnes": 550000, "share_africa": 20},
        {"rank": 3, "country": "BFA", "name": "Burkina Faso", "production_tonnes": 450000, "share_africa": 17},
        {"rank": 4, "country": "CIV", "name": "Côte d'Ivoire", "production_tonnes": 350000, "share_africa": 13},
    ],
    "Arachide": [
        {"rank": 1, "country": "NGA", "name": "Nigéria", "production_tonnes": 3800000, "share_africa": 38},
        {"rank": 2, "country": "SEN", "name": "Sénégal", "production_tonnes": 1800000, "share_africa": 18},
        {"rank": 3, "country": "SDN", "name": "Soudan", "production_tonnes": 1500000, "share_africa": 15},
    ],
    "Noix de cajou": [
        {"rank": 1, "country": "CIV", "name": "Côte d'Ivoire", "production_tonnes": 1100000, "share_africa": 55},
        {"rank": 2, "country": "TZA", "name": "Tanzanie", "production_tonnes": 280000, "share_africa": 14},
        {"rank": 3, "country": "GNB", "name": "Guinée-Bissau", "production_tonnes": 200000, "share_africa": 10},
        {"rank": 4, "country": "MOZ", "name": "Mozambique", "production_tonnes": 150000, "share_africa": 7.5},
    ],
}

# =============================================================================
# DONNÉES PÊCHE ET AQUACULTURE
# =============================================================================

FISHERIES_TOP_PRODUCERS = {
    "capture": [
        {"rank": 1, "country": "MAR", "name": "Maroc", "production_tonnes": 1500000},
        {"rank": 2, "country": "MRT", "name": "Mauritanie", "production_tonnes": 900000},
        {"rank": 3, "country": "NGA", "name": "Nigéria", "production_tonnes": 780000},
        {"rank": 4, "country": "ZAF", "name": "Afrique du Sud", "production_tonnes": 550000},
        {"rank": 5, "country": "NAM", "name": "Namibie", "production_tonnes": 550000},
    ],
    "aquaculture": [
        {"rank": 1, "country": "EGY", "name": "Égypte", "production_tonnes": 1600000},
        {"rank": 2, "country": "NGA", "name": "Nigéria", "production_tonnes": 380000},
        {"rank": 3, "country": "UGA", "name": "Ouganda", "production_tonnes": 130000},
        {"rank": 4, "country": "GHA", "name": "Ghana", "production_tonnes": 78000},
    ],
}

# =============================================================================
# FONCTIONS D'ACCÈS
# =============================================================================

def get_faostat_country_data(country_iso3: str) -> Dict:
    """Récupère les données FAOSTAT pour un pays."""
    return FAOSTAT_AGRICULTURE_DATA.get(country_iso3, {})

def get_africa_top_producers(commodity: str) -> List[Dict]:
    """Récupère le classement des top producteurs africains pour un produit."""
    return AFRICA_TOP_PRODUCERS.get(commodity, [])

def get_all_commodities() -> List[str]:
    """Retourne la liste de tous les produits disponibles."""
    commodities = set()
    for country_data in FAOSTAT_AGRICULTURE_DATA.values():
        if "main_crops" in country_data:
            commodities.update(country_data["main_crops"])
    return sorted(list(commodities))

def get_countries_with_data() -> List[str]:
    """Retourne la liste des pays avec données FAOSTAT."""
    return list(FAOSTAT_AGRICULTURE_DATA.keys())

def get_all_faostat_data() -> Dict:
    """Retourne toutes les données FAOSTAT."""
    return FAOSTAT_AGRICULTURE_DATA

def get_fisheries_rankings() -> Dict:
    """Retourne les classements pêche et aquaculture."""
    return FISHERIES_TOP_PRODUCERS

def get_faostat_statistics() -> Dict:
    """Retourne des statistiques globales sur les données FAOSTAT."""
    total_countries = len(FAOSTAT_AGRICULTURE_DATA)
    
    # Compter les produits uniques
    all_crops = set()
    for country_data in FAOSTAT_AGRICULTURE_DATA.values():
        if "main_crops" in country_data:
            all_crops.update(country_data["main_crops"])
    
    # Régions
    regions = {}
    for code, data in FAOSTAT_AGRICULTURE_DATA.items():
        region = data.get("region", "Non classé")
        if region not in regions:
            regions[region] = []
        regions[region].append(code)
    
    return {
        "total_countries": total_countries,
        "total_commodities": len(all_crops),
        "commodities_list": sorted(list(all_crops)),
        "regions": {k: len(v) for k, v in regions.items()},
        "countries_by_region": regions,
        "data_year": 2023,
        "source": "FAOSTAT 2023"
    }
