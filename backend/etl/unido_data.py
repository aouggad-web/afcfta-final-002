"""
Données UNIDO - Statistiques Industrielles Africaines
======================================================
Sources officielles:
- UNIDO INDSTAT4 Database 2024
- UNIDO International Yearbook of Industrial Statistics 2024
- UNIDO Competitive Industrial Performance Index 2024
- UNIDO Industrial Statistics Database
- African Development Bank Industry Reports

Classification: ISIC Rev.4
Couverture: 54 pays africains
Mise à jour: 2024
"""

from typing import Dict, List, Optional

# =============================================================================
# CLASSIFICATION ISIC REV.4 - SECTEURS MANUFACTURIERS
# =============================================================================

ISIC_SECTORS = {
    "10": "Produits alimentaires",
    "11": "Boissons",
    "12": "Produits du tabac",
    "13": "Textiles",
    "14": "Articles d'habillement",
    "15": "Cuir et articles de cuir",
    "16": "Bois et articles en bois",
    "17": "Papier et articles en papier",
    "18": "Imprimerie et reproduction",
    "19": "Cokéfaction et raffinage",
    "20": "Produits chimiques",
    "21": "Produits pharmaceutiques",
    "22": "Caoutchouc et plastiques",
    "23": "Minéraux non métalliques",
    "24": "Métallurgie de base",
    "25": "Ouvrages en métaux",
    "26": "Produits informatiques et électroniques",
    "27": "Équipements électriques",
    "28": "Machines et équipements",
    "29": "Véhicules automobiles",
    "30": "Autres matériels de transport",
    "31": "Meubles",
    "32": "Autres industries manufacturières",
    "33": "Réparation et installation",
}

# =============================================================================
# DONNÉES INDUSTRIELLES PAR PAYS
# Source: UNIDO INDSTAT4 2024, UNIDO Yearbook 2024, estimations 2024
# =============================================================================

UNIDO_INDUSTRY_DATA = {
    # =========================================================================
    # GRANDES ÉCONOMIES INDUSTRIELLES AFRICAINES
    # =========================================================================
    "ZAF": {
        "country_name": "Afrique du Sud",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 48500,
        "mva_gdp_percent": 12.8,
        "mva_per_capita_usd": 810,
        "industry_employment": 1850000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 18.5, "value_mln_usd": 8973},
            {"isic": "29", "name": "Véhicules automobiles", "share_mva": 14.2, "value_mln_usd": 6887},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 12.1, "value_mln_usd": 5869},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 10.8, "value_mln_usd": 5238},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 8.5, "value_mln_usd": 4123},
        ],
        "growth_rate_2023": 1.2,
        "exports_manuf_mln_usd": 45000,
        "key_products": [
            "Véhicules automobiles",
            "Métaux précieux transformés",
            "Produits chimiques",
            "Machines industrielles",
            "Produits alimentaires transformés"
        ],
        "industrial_zones": 12,
        "source": "UNIDO INDSTAT4 2024, Stats SA, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 49800,
        "mva_per_capita_2015usd": 660,
        "growth_rate_2024_est": 1.5,
        "cip_index_rank": 77,
        "mht_share_mva": 21.2,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 42.0,
        "data_year": 2024
    },
    
    "EGY": {
        "country_name": "Égypte",
        "region": "Afrique du Nord",
        "mva_2023_mln_usd": 42800,
        "mva_gdp_percent": 15.2,
        "mva_per_capita_usd": 398,
        "industry_employment": 2850000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 22.4, "value_mln_usd": 9587},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 14.8, "value_mln_usd": 6334},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 11.2, "value_mln_usd": 4794},
            {"isic": "13", "name": "Textiles", "share_mva": 9.6, "value_mln_usd": 4109},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 8.9, "value_mln_usd": 3809},
        ],
        "growth_rate_2023": 3.8,
        "exports_manuf_mln_usd": 18500,
        "key_products": [
            "Textiles et vêtements",
            "Produits pétroliers raffinés",
            "Engrais chimiques",
            "Ciment et matériaux de construction",
            "Produits alimentaires"
        ],
        "industrial_zones": 18,
        "source": "UNIDO INDSTAT4 2024, CAPMAS, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 44500,
        "mva_per_capita_2015usd": 320,
        "growth_rate_2024_est": 4.2,
        "cip_index_rank": 80,
        "mht_share_mva": 14.5,
        "industry_va_gdp_percent": 32.8,
        "manuf_share_exports": 38.5,
        "data_year": 2024
    },
    
    "NGA": {
        "country_name": "Nigéria",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 38500,
        "mva_gdp_percent": 8.9,
        "mva_per_capita_usd": 175,
        "industry_employment": 4200000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 35.2, "value_mln_usd": 13552},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 18.5, "value_mln_usd": 7123},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 12.4, "value_mln_usd": 4774},
            {"isic": "11", "name": "Boissons", "share_mva": 8.6, "value_mln_usd": 3311},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 5.8, "value_mln_usd": 2233},
        ],
        "growth_rate_2023": 2.1,
        "exports_manuf_mln_usd": 2800,
        "key_products": [
            "Ciment",
            "Produits alimentaires transformés",
            "Produits pétroliers",
            "Boissons",
            "Plastiques"
        ],
        "industrial_zones": 8,
        "dangote_refinery_capacity_bpd": 650000,
        "source": "UNIDO INDSTAT4 2024, NBS Nigeria, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 39500,
        "mva_per_capita_2015usd": 140,
        "growth_rate_2024_est": 2.5,
        "cip_index_rank": 95,
        "mht_share_mva": 6.2,
        "industry_va_gdp_percent": 22.4,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "MAR": {
        "country_name": "Maroc",
        "region": "Afrique du Nord",
        "mva_2023_mln_usd": 32500,
        "mva_gdp_percent": 24.8,
        "mva_per_capita_usd": 870,
        "industry_employment": 1250000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 19.8, "value_mln_usd": 6435},
            {"isic": "29", "name": "Véhicules automobiles", "share_mva": 16.5, "value_mln_usd": 5363},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 12.4, "value_mln_usd": 4030},
            {"isic": "27", "name": "Équipements électriques", "share_mva": 8.9, "value_mln_usd": 2893},
            {"isic": "13", "name": "Textiles", "share_mva": 7.6, "value_mln_usd": 2470},
        ],
        "growth_rate_2023": 3.2,
        "exports_manuf_mln_usd": 28500,
        "key_products": [
            "Véhicules automobiles (Renault, PSA)",
            "Pièces automobiles",
            "Phosphates et engrais",
            "Textiles et vêtements",
            "Composants aéronautiques"
        ],
        "industrial_zones": 15,
        "automotive_units_2023": 500000,
        "source": "UNIDO INDSTAT4 2024, HCP Maroc, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 33800,
        "mva_per_capita_2015usd": 710,
        "growth_rate_2024_est": 3.8,
        "cip_index_rank": 90,
        "mht_share_mva": 26.5,
        "industry_va_gdp_percent": 32.2,
        "manuf_share_exports": 68.5,
        "data_year": 2024
    },
    
    "DZA": {
        "country_name": "Algérie",
        "region": "Afrique du Nord",
        "mva_2023_mln_usd": 18500,
        "mva_gdp_percent": 10.2,
        "mva_per_capita_usd": 410,
        "industry_employment": 1150000,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 28.5, "value_mln_usd": 5273},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 18.2, "value_mln_usd": 3367},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 14.5, "value_mln_usd": 2683},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 9.8, "value_mln_usd": 1813},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 8.2, "value_mln_usd": 1517},
        ],
        "growth_rate_2023": 4.1,
        "exports_manuf_mln_usd": 3200,
        "key_products": [
            "Produits pétroliers raffinés",
            "Engrais",
            "Ciment",
            "Acier",
            "Produits alimentaires"
        ],
        "industrial_zones": 10,
        "source": "UNIDO INDSTAT4 2024, ONS Algérie, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 19200,
        "mva_per_capita_2015usd": 330,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 99,
        "mht_share_mva": 8.5,
        "industry_va_gdp_percent": 38.5,
        "manuf_share_exports": 5.2,
        "data_year": 2024
    },
    
    "TUN": {
        "country_name": "Tunisie",
        "region": "Afrique du Nord",
        "mva_2023_mln_usd": 8500,
        "mva_gdp_percent": 18.5,
        "mva_per_capita_usd": 710,
        "industry_employment": 520000,
        "top_sectors": [
            {"isic": "13", "name": "Textiles", "share_mva": 18.5, "value_mln_usd": 1573},
            {"isic": "14", "name": "Articles d'habillement", "share_mva": 14.2, "value_mln_usd": 1207},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 12.8, "value_mln_usd": 1088},
            {"isic": "27", "name": "Équipements électriques", "share_mva": 11.5, "value_mln_usd": 978},
            {"isic": "26", "name": "Produits électroniques", "share_mva": 8.9, "value_mln_usd": 757},
        ],
        "growth_rate_2023": 1.8,
        "exports_manuf_mln_usd": 12500,
        "key_products": [
            "Textiles et vêtements",
            "Composants électriques",
            "Câblage automobile",
            "Huile d'olive",
            "Pièces mécaniques"
        ],
        "industrial_zones": 12,
        "source": "UNIDO INDSTAT4 2024, INS Tunisie, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 8700,
        "mva_per_capita_2015usd": 575,
        "growth_rate_2024_est": 2.0,
        "cip_index_rank": 103,
        "mht_share_mva": 22.8,
        "industry_va_gdp_percent": 27.5,
        "manuf_share_exports": 72.0,
        "data_year": 2024
    },
    
    "ETH": {
        "country_name": "Éthiopie",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 7800,
        "mva_gdp_percent": 6.2,
        "mva_per_capita_usd": 65,
        "industry_employment": 850000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5, "value_mln_usd": 3003},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2, "value_mln_usd": 1186},
            {"isic": "13", "name": "Textiles", "share_mva": 12.8, "value_mln_usd": 998},
            {"isic": "14", "name": "Articles d'habillement", "share_mva": 8.5, "value_mln_usd": 663},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 7.2, "value_mln_usd": 562},
        ],
        "growth_rate_2023": 5.8,
        "exports_manuf_mln_usd": 850,
        "key_products": [
            "Textiles et vêtements",
            "Cuir et chaussures",
            "Produits alimentaires",
            "Ciment",
            "Boissons"
        ],
        "industrial_zones": 15,
        "industrial_parks": ["Hawassa", "Bole Lemi", "Kilinto", "Mekelle"],
        "source": "UNIDO INDSTAT4 2024, CSA Ethiopia, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 8200,
        "mva_per_capita_2015usd": 52,
        "growth_rate_2024_est": 6.5,
        "cip_index_rank": 120,
        "mht_share_mva": 5.8,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 18.5,
        "data_year": 2024
    },
    
    "KEN": {
        "country_name": "Kenya",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 8200,
        "mva_gdp_percent": 7.8,
        "mva_per_capita_usd": 155,
        "industry_employment": 380000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 32.5, "value_mln_usd": 2665},
            {"isic": "11", "name": "Boissons", "share_mva": 12.8, "value_mln_usd": 1050},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 9.5, "value_mln_usd": 779},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 8.2, "value_mln_usd": 672},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 7.8, "value_mln_usd": 640},
        ],
        "growth_rate_2023": 3.5,
        "exports_manuf_mln_usd": 1200,
        "key_products": [
            "Thé transformé",
            "Produits alimentaires",
            "Ciment",
            "Produits chimiques",
            "Plastiques"
        ],
        "industrial_zones": 8,
        "special_economic_zones": 4,
        "source": "UNIDO INDSTAT4 2024, KNBS Kenya, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 8600,
        "mva_per_capita_2015usd": 125,
        "growth_rate_2024_est": 4.0,
        "cip_index_rank": 108,
        "mht_share_mva": 9.2,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 22.0,
        "data_year": 2024
    },
    
    "CIV": {
        "country_name": "Côte d'Ivoire",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 9800,
        "mva_gdp_percent": 14.2,
        "mva_per_capita_usd": 350,
        "industry_employment": 420000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5, "value_mln_usd": 4165},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 15.8, "value_mln_usd": 1548},
            {"isic": "11", "name": "Boissons", "share_mva": 8.5, "value_mln_usd": 833},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 6.8, "value_mln_usd": 666},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 5.2, "value_mln_usd": 510},
        ],
        "growth_rate_2023": 6.2,
        "exports_manuf_mln_usd": 4500,
        "key_products": [
            "Cacao transformé",
            "Produits pétroliers",
            "Conserves de poisson",
            "Caoutchouc",
            "Huile de palme"
        ],
        "industrial_zones": 6,
        "cocoa_processing_capacity_tonnes": 750000,
        "source": "UNIDO INDSTAT4 2024, INS Côte d'Ivoire, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 10400,
        "mva_per_capita_2015usd": 280,
        "growth_rate_2024_est": 6.8,
        "cip_index_rank": 112,
        "mht_share_mva": 6.5,
        "industry_va_gdp_percent": 25.5,
        "manuf_share_exports": 28.5,
        "data_year": 2024
    },
    
    "GHA": {
        "country_name": "Ghana",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 6800,
        "mva_gdp_percent": 9.8,
        "mva_per_capita_usd": 205,
        "industry_employment": 320000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5, "value_mln_usd": 2618},
            {"isic": "11", "name": "Boissons", "share_mva": 12.2, "value_mln_usd": 830},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 10.5, "value_mln_usd": 714},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 8.8, "value_mln_usd": 598},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 6.5, "value_mln_usd": 442},
        ],
        "growth_rate_2023": 2.8,
        "exports_manuf_mln_usd": 2200,
        "key_products": [
            "Cacao transformé",
            "Aluminium",
            "Produits alimentaires",
            "Produits pétroliers",
            "Ciment"
        ],
        "industrial_zones": 5,
        "source": "UNIDO INDSTAT4 2024, GSS Ghana, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 7000,
        "mva_per_capita_2015usd": 165,
        "growth_rate_2024_est": 3.2,
        "cip_index_rank": 115,
        "mht_share_mva": 8.5,
        "industry_va_gdp_percent": 24.5,
        "manuf_share_exports": 28.0,
        "data_year": 2024
    },
    
    "TZA": {
        "country_name": "Tanzanie",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 5200,
        "mva_gdp_percent": 7.5,
        "mva_per_capita_usd": 82,
        "industry_employment": 280000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.8, "value_mln_usd": 2226},
            {"isic": "11", "name": "Boissons", "share_mva": 14.5, "value_mln_usd": 754},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 12.2, "value_mln_usd": 634},
            {"isic": "13", "name": "Textiles", "share_mva": 6.8, "value_mln_usd": 354},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 5.5, "value_mln_usd": 286},
        ],
        "growth_rate_2023": 5.2,
        "exports_manuf_mln_usd": 1100,
        "key_products": [
            "Ciment",
            "Sucre",
            "Boissons",
            "Textiles",
            "Produits alimentaires"
        ],
        "industrial_zones": 4,
        "source": "UNIDO INDSTAT4 2024, NBS Tanzania, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 5500,
        "mva_per_capita_2015usd": 65,
        "growth_rate_2024_est": 5.5,
        "cip_index_rank": 122,
        "mht_share_mva": 5.2,
        "industry_va_gdp_percent": 25.2,
        "manuf_share_exports": 15.5,
        "data_year": 2024
    },
    
    "SEN": {
        "country_name": "Sénégal",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 4500,
        "mva_gdp_percent": 16.5,
        "mva_per_capita_usd": 255,
        "industry_employment": 180000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5, "value_mln_usd": 1733},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 18.2, "value_mln_usd": 819},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 12.5, "value_mln_usd": 563},
            {"isic": "11", "name": "Boissons", "share_mva": 8.8, "value_mln_usd": 396},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 5.5, "value_mln_usd": 248},
        ],
        "growth_rate_2023": 4.8,
        "exports_manuf_mln_usd": 1800,
        "key_products": [
            "Acide phosphorique",
            "Engrais",
            "Ciment",
            "Conserves de poisson",
            "Produits alimentaires"
        ],
        "industrial_zones": 5,
        "source": "UNIDO INDSTAT4 2024, ANSD Sénégal, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 4800,
        "mva_per_capita_2015usd": 205,
        "growth_rate_2024_est": 5.2,
        "cip_index_rank": 118,
        "mht_share_mva": 7.5,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 25.0,
        "data_year": 2024
    },
    
    "CMR": {
        "country_name": "Cameroun",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 5800,
        "mva_gdp_percent": 13.2,
        "mva_per_capita_usd": 210,
        "industry_employment": 250000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 35.5, "value_mln_usd": 2059},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2, "value_mln_usd": 882},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 12.8, "value_mln_usd": 742},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 8.5, "value_mln_usd": 493},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 7.2, "value_mln_usd": 418},
        ],
        "growth_rate_2023": 3.8,
        "exports_manuf_mln_usd": 1500,
        "key_products": [
            "Aluminium",
            "Produits pétroliers",
            "Bois transformé",
            "Cacao transformé",
            "Ciment"
        ],
        "industrial_zones": 4,
        "alucam_capacity_tonnes": 110000,
        "source": "UNIDO INDSTAT4 2024, INS Cameroun, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 6000,
        "mva_per_capita_2015usd": 170,
        "growth_rate_2024_est": 4.0,
        "cip_index_rank": 114,
        "mht_share_mva": 7.2,
        "industry_va_gdp_percent": 30.5,
        "manuf_share_exports": 18.5,
        "data_year": 2024
    },
    
    "UGA": {
        "country_name": "Ouganda",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 3800,
        "mva_gdp_percent": 8.5,
        "mva_per_capita_usd": 82,
        "industry_employment": 180000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.2, "value_mln_usd": 1718},
            {"isic": "11", "name": "Boissons", "share_mva": 18.5, "value_mln_usd": 703},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 10.2, "value_mln_usd": 388},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 6.8, "value_mln_usd": 258},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 5.5, "value_mln_usd": 209},
        ],
        "growth_rate_2023": 4.5,
        "exports_manuf_mln_usd": 650,
        "key_products": [
            "Sucre",
            "Café transformé",
            "Ciment",
            "Boissons",
            "Savons et détergents"
        ],
        "industrial_zones": 3,
        "source": "UNIDO INDSTAT4 2024, UBOS Uganda, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 4000,
        "mva_per_capita_2015usd": 65,
        "growth_rate_2024_est": 5.0,
        "cip_index_rank": 125,
        "mht_share_mva": 5.5,
        "industry_va_gdp_percent": 25.8,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "AGO": {
        "country_name": "Angola",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 4200,
        "mva_gdp_percent": 5.2,
        "mva_per_capita_usd": 120,
        "industry_employment": 150000,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 35.5, "value_mln_usd": 1491},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 25.2, "value_mln_usd": 1058},
            {"isic": "11", "name": "Boissons", "share_mva": 15.8, "value_mln_usd": 664},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 8.5, "value_mln_usd": 357},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 4.2, "value_mln_usd": 176},
        ],
        "growth_rate_2023": 2.5,
        "exports_manuf_mln_usd": 450,
        "key_products": [
            "Produits pétroliers raffinés",
            "Ciment",
            "Boissons",
            "Matériaux de construction",
            "Produits alimentaires"
        ],
        "industrial_zones": 3,
        "source": "UNIDO INDSTAT4 2024, INE Angola, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 4400,
        "mva_per_capita_2015usd": 97,
        "growth_rate_2024_est": 2.8,
        "cip_index_rank": 128,
        "mht_share_mva": 5.8,
        "industry_va_gdp_percent": 48.5,
        "manuf_share_exports": 3.5,
        "data_year": 2024
    },
    
    "COD": {
        "country_name": "RD Congo",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 3500,
        "mva_gdp_percent": 5.5,
        "mva_per_capita_usd": 35,
        "industry_employment": 120000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.5, "value_mln_usd": 1593},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8, "value_mln_usd": 798},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 12.5, "value_mln_usd": 438},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 5.8, "value_mln_usd": 203},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 4.5, "value_mln_usd": 158},
        ],
        "growth_rate_2023": 6.8,
        "exports_manuf_mln_usd": 280,
        "key_products": [
            "Ciment",
            "Boissons",
            "Farine",
            "Huile de palme",
            "Savons"
        ],
        "industrial_zones": 2,
        "source": "UNIDO INDSTAT4 2024, INS RDC, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 3700,
        "mva_per_capita_2015usd": 28,
        "growth_rate_2024_est": 7.2,
        "cip_index_rank": 135,
        "mht_share_mva": 4.5,
        "industry_va_gdp_percent": 42.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "ZMB": {
        "country_name": "Zambie",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 2800,
        "mva_gdp_percent": 9.2,
        "mva_per_capita_usd": 145,
        "industry_employment": 95000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5, "value_mln_usd": 1078},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 18.2, "value_mln_usd": 510},
            {"isic": "11", "name": "Boissons", "share_mva": 12.5, "value_mln_usd": 350},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 10.8, "value_mln_usd": 302},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 5.2, "value_mln_usd": 146},
        ],
        "growth_rate_2023": 4.2,
        "exports_manuf_mln_usd": 1200,
        "key_products": [
            "Cuivre affiné",
            "Sucre",
            "Ciment",
            "Boissons",
            "Textiles"
        ],
        "industrial_zones": 4,
        "source": "UNIDO INDSTAT4 2024, CSO Zambia, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 2950,
        "mva_per_capita_2015usd": 117,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 126,
        "mht_share_mva": 6.8,
        "industry_va_gdp_percent": 32.5,
        "manuf_share_exports": 28.5,
        "data_year": 2024
    },
    
    "ZWE": {
        "country_name": "Zimbabwe",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 2200,
        "mva_gdp_percent": 10.5,
        "mva_per_capita_usd": 140,
        "industry_employment": 85000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 35.5, "value_mln_usd": 781},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2, "value_mln_usd": 334},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 12.8, "value_mln_usd": 282},
            {"isic": "13", "name": "Textiles", "share_mva": 8.5, "value_mln_usd": 187},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 6.2, "value_mln_usd": 136},
        ],
        "growth_rate_2023": 3.5,
        "exports_manuf_mln_usd": 850,
        "key_products": [
            "Ferrochrome",
            "Sucre",
            "Textiles",
            "Ciment",
            "Produits alimentaires"
        ],
        "industrial_zones": 3,
        "source": "UNIDO INDSTAT4 2024, ZIMSTAT, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 2300,
        "mva_per_capita_2015usd": 113,
        "growth_rate_2024_est": 4.0,
        "cip_index_rank": 129,
        "mht_share_mva": 8.5,
        "industry_va_gdp_percent": 35.5,
        "manuf_share_exports": 22.5,
        "data_year": 2024
    },
    
    # =========================================================================
    # ÉCONOMIES MOYENNES
    # =========================================================================
    "RWA": {
        "country_name": "Rwanda",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 1200,
        "mva_gdp_percent": 10.2,
        "mva_per_capita_usd": 88,
        "industry_employment": 65000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5, "value_mln_usd": 510},
            {"isic": "11", "name": "Boissons", "share_mva": 18.5, "value_mln_usd": 222},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 15.2, "value_mln_usd": 182},
            {"isic": "22", "name": "Caoutchouc et plastiques", "share_mva": 8.5, "value_mln_usd": 102},
        ],
        "growth_rate_2023": 8.5,
        "exports_manuf_mln_usd": 180,
        "key_products": [
            "Ciment",
            "Boissons",
            "Produits alimentaires",
            "Café et thé transformés",
            "Matériaux de construction"
        ],
        "industrial_zones": 3,
        "kigali_sez": True,
        "source": "UNIDO INDSTAT4 2024, NISR Rwanda, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1300,
        "mva_per_capita_2015usd": 72,
        "growth_rate_2024_est": 9.0,
        "cip_index_rank": 130,
        "mht_share_mva": 6.2,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "MUS": {
        "country_name": "Maurice",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 1800,
        "mva_gdp_percent": 12.5,
        "mva_per_capita_usd": 1420,
        "industry_employment": 95000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 28.5, "value_mln_usd": 513},
            {"isic": "14", "name": "Articles d'habillement", "share_mva": 22.8, "value_mln_usd": 410},
            {"isic": "13", "name": "Textiles", "share_mva": 12.5, "value_mln_usd": 225},
            {"isic": "21", "name": "Produits pharmaceutiques", "share_mva": 8.2, "value_mln_usd": 148},
            {"isic": "26", "name": "Produits électroniques", "share_mva": 5.8, "value_mln_usd": 104},
        ],
        "growth_rate_2023": 5.2,
        "exports_manuf_mln_usd": 2200,
        "key_products": [
            "Textiles et vêtements",
            "Sucre raffiné",
            "Produits pharmaceutiques",
            "Bijoux",
            "Équipements électroniques"
        ],
        "industrial_zones": 5,
        "freeport": True,
        "source": "UNIDO INDSTAT4 2024, Statistics Mauritius, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1900,
        "mva_per_capita_2015usd": 1150,
        "growth_rate_2024_est": 5.5,
        "cip_index_rank": 101,
        "mht_share_mva": 18.5,
        "industry_va_gdp_percent": 24.5,
        "manuf_share_exports": 68.5,
        "data_year": 2024
    },
    
    "BWA": {
        "country_name": "Botswana",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 850,
        "mva_gdp_percent": 4.5,
        "mva_per_capita_usd": 340,
        "industry_employment": 35000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 35.5, "value_mln_usd": 302},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8, "value_mln_usd": 194},
            {"isic": "13", "name": "Textiles", "share_mva": 12.5, "value_mln_usd": 106},
            {"isic": "32", "name": "Autres industries (diamants)", "share_mva": 10.2, "value_mln_usd": 87},
        ],
        "growth_rate_2023": 3.2,
        "exports_manuf_mln_usd": 650,
        "key_products": [
            "Diamants taillés",
            "Viande transformée",
            "Textiles",
            "Boissons",
            "Véhicules assemblés"
        ],
        "industrial_zones": 2,
        "diamond_cutting_hub": True,
        "source": "UNIDO INDSTAT4 2024, Statistics Botswana, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 900,
        "mva_per_capita_2015usd": 275,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 127,
        "mht_share_mva": 5.8,
        "industry_va_gdp_percent": 42.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "NAM": {
        "country_name": "Namibie",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 1500,
        "mva_gdp_percent": 11.2,
        "mva_per_capita_usd": 580,
        "industry_employment": 45000,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.2, "value_mln_usd": 678},
            {"isic": "11", "name": "Boissons", "share_mva": 18.5, "value_mln_usd": 278},
            {"isic": "24", "name": "Métallurgie de base", "share_mva": 12.8, "value_mln_usd": 192},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 8.5, "value_mln_usd": 128},
        ],
        "growth_rate_2023": 2.8,
        "exports_manuf_mln_usd": 1800,
        "key_products": [
            "Poisson transformé",
            "Viande",
            "Boissons",
            "Métaux raffinés",
            "Ciment"
        ],
        "industrial_zones": 3,
        "walvis_bay_processing": True,
        "source": "UNIDO INDSTAT4 2024, NSA Namibia, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1600,
        "mva_per_capita_2015usd": 470,
        "growth_rate_2024_est": 3.2,
        "cip_index_rank": 119,
        "mht_share_mva": 7.5,
        "industry_va_gdp_percent": 32.5,
        "manuf_share_exports": 38.5,
        "data_year": 2024
    },
    
    # =========================================================================
    # AUTRES PAYS - DONNÉES ESTIMÉES
    # =========================================================================
    "BEN": {
        "country_name": "Bénin",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 2100,
        "mva_gdp_percent": 11.5,
        "mva_per_capita_usd": 160,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5},
            {"isic": "13", "name": "Textiles (coton)", "share_mva": 25.2},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 12.5},
        ],
        "growth_rate_2023": 5.8,
        "key_products": ["Coton égrené", "Huile de coton", "Ciment", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 2200,
        "mva_per_capita_2015usd": 128,
        "growth_rate_2024_est": 6.2,
        "cip_index_rank": 138,
        "mht_share_mva": 4.8,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 15.5,
        "data_year": 2024
    },
    
    "BFA": {
        "country_name": "Burkina Faso",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 1800,
        "mva_gdp_percent": 9.8,
        "mva_per_capita_usd": 82,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5},
            {"isic": "13", "name": "Textiles (coton)", "share_mva": 22.8},
            {"isic": "24", "name": "Métallurgie (or)", "share_mva": 15.2},
        ],
        "growth_rate_2023": 3.2,
        "key_products": ["Coton égrené", "Or raffiné", "Boissons", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1900,
        "mva_per_capita_2015usd": 66,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 140,
        "mht_share_mva": 4.5,
        "industry_va_gdp_percent": 24.8,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "MLI": {
        "country_name": "Mali",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 2200,
        "mva_gdp_percent": 11.2,
        "mva_per_capita_usd": 100,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.5},
            {"isic": "13", "name": "Textiles (coton)", "share_mva": 28.5},
            {"isic": "24", "name": "Métallurgie (or)", "share_mva": 12.8},
        ],
        "growth_rate_2023": 4.5,
        "key_products": ["Coton égrené", "Or raffiné", "Sucre", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 2300,
        "mva_per_capita_2015usd": 82,
        "growth_rate_2024_est": 5.0,
        "cip_index_rank": 139,
        "mht_share_mva": 4.2,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "NER": {
        "country_name": "Niger",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 850,
        "mva_gdp_percent": 5.8,
        "mva_per_capita_usd": 32,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 52.5},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 18.5},
            {"isic": "11", "name": "Boissons", "share_mva": 12.8},
        ],
        "growth_rate_2023": 5.2,
        "key_products": ["Ciment", "Huile d'arachide", "Farine", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 900,
        "mva_per_capita_2015usd": 26,
        "growth_rate_2024_est": 5.5,
        "cip_index_rank": 148,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "TGO": {
        "country_name": "Togo",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 1100,
        "mva_gdp_percent": 13.5,
        "mva_per_capita_usd": 125,
        "top_sectors": [
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 35.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 28.5},
            {"isic": "20", "name": "Produits chimiques", "share_mva": 15.2},
        ],
        "growth_rate_2023": 5.8,
        "key_products": ["Clinker/Ciment", "Phosphates", "Boissons", "Coton égrené"],
        "industrial_zones": 2,
        "pya_industrial_platform": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1150,
        "mva_per_capita_2015usd": 100,
        "growth_rate_2024_est": 6.2,
        "cip_index_rank": 136,
        "mht_share_mva": 5.2,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 18.5,
        "data_year": 2024
    },
    
    "GIN": {
        "country_name": "Guinée",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 1500,
        "mva_gdp_percent": 8.2,
        "mva_per_capita_usd": 110,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5},
            {"isic": "24", "name": "Métallurgie (alumine)", "share_mva": 25.8},
            {"isic": "11", "name": "Boissons", "share_mva": 12.5},
        ],
        "growth_rate_2023": 4.8,
        "key_products": ["Alumine", "Ciment", "Boissons", "Produits alimentaires"],
        "bauxite_alumina_refinery": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1600,
        "mva_per_capita_2015usd": 88,
        "growth_rate_2024_est": 5.2,
        "cip_index_rank": 141,
        "mht_share_mva": 4.8,
        "industry_va_gdp_percent": 32.5,
        "manuf_share_exports": 15.5,
        "data_year": 2024
    },
    
    "MOZ": {
        "country_name": "Mozambique",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 2500,
        "mva_gdp_percent": 12.8,
        "mva_per_capita_usd": 75,
        "top_sectors": [
            {"isic": "24", "name": "Métallurgie (aluminium)", "share_mva": 32.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 28.5},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2},
        ],
        "growth_rate_2023": 5.5,
        "key_products": ["Aluminium", "Sucre", "Bière", "Ciment", "Gaz naturel liquéfié"],
        "mozal_aluminum_smelter": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 2650,
        "mva_per_capita_2015usd": 60,
        "growth_rate_2024_est": 5.8,
        "cip_index_rank": 134,
        "mht_share_mva": 5.5,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "MDG": {
        "country_name": "Madagascar",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 1800,
        "mva_gdp_percent": 12.5,
        "mva_per_capita_usd": 62,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 38.5},
            {"isic": "14", "name": "Articles d'habillement", "share_mva": 22.8},
            {"isic": "13", "name": "Textiles", "share_mva": 12.5},
        ],
        "growth_rate_2023": 4.2,
        "key_products": ["Textiles", "Vêtements", "Vanille transformée", "Ciment", "Sucre"],
        "zone_franche_active": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1900,
        "mva_per_capita_2015usd": 50,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 137,
        "mht_share_mva": 4.5,
        "industry_va_gdp_percent": 25.5,
        "manuf_share_exports": 18.5,
        "data_year": 2024
    },
    
    "MWI": {
        "country_name": "Malawi",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 1200,
        "mva_gdp_percent": 9.8,
        "mva_per_capita_usd": 58,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.5},
            {"isic": "12", "name": "Produits du tabac", "share_mva": 22.8},
            {"isic": "11", "name": "Boissons", "share_mva": 12.5},
        ],
        "growth_rate_2023": 3.5,
        "key_products": ["Tabac transformé", "Sucre", "Thé", "Boissons", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1250,
        "mva_per_capita_2015usd": 46,
        "growth_rate_2024_est": 3.8,
        "cip_index_rank": 143,
        "mht_share_mva": 4.2,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "BDI": {
        "country_name": "Burundi",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 350,
        "mva_gdp_percent": 8.5,
        "mva_per_capita_usd": 28,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 52.5},
            {"isic": "11", "name": "Boissons", "share_mva": 25.8},
            {"isic": "13", "name": "Textiles", "share_mva": 8.5},
        ],
        "growth_rate_2023": 3.8,
        "key_products": ["Bière", "Café transformé", "Thé", "Sucre", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 365,
        "mva_per_capita_2015usd": 22,
        "growth_rate_2024_est": 4.2,
        "cip_index_rank": 152,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "GAB": {
        "country_name": "Gabon",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 1800,
        "mva_gdp_percent": 8.5,
        "mva_per_capita_usd": 780,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 35.5},
            {"isic": "16", "name": "Bois et articles en bois", "share_mva": 22.8},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 18.5},
        ],
        "growth_rate_2023": 2.8,
        "key_products": ["Produits pétroliers", "Bois transformé", "Manganèse raffiné", "Ciment"],
        "special_economic_zone": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1900,
        "mva_per_capita_2015usd": 635,
        "growth_rate_2024_est": 3.2,
        "cip_index_rank": 124,
        "mht_share_mva": 7.5,
        "industry_va_gdp_percent": 42.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "COG": {
        "country_name": "République du Congo",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 1200,
        "mva_gdp_percent": 8.2,
        "mva_per_capita_usd": 210,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 42.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 22.8},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2},
        ],
        "growth_rate_2023": 3.2,
        "key_products": ["Produits pétroliers", "Sucre", "Bière", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 1250,
        "mva_per_capita_2015usd": 170,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 133,
        "mht_share_mva": 5.8,
        "industry_va_gdp_percent": 52.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "TCD": {
        "country_name": "Tchad",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 650,
        "mva_gdp_percent": 5.2,
        "mva_per_capita_usd": 38,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 45.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 28.5},
            {"isic": "11", "name": "Boissons", "share_mva": 12.8},
        ],
        "growth_rate_2023": 2.5,
        "key_products": ["Produits pétroliers", "Coton égrené", "Sucre", "Boissons"],
        "djermaya_refinery": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 680,
        "mva_per_capita_2015usd": 30,
        "growth_rate_2024_est": 2.8,
        "cip_index_rank": 149,
        "mht_share_mva": 3.8,
        "industry_va_gdp_percent": 35.5,
        "manuf_share_exports": 3.5,
        "data_year": 2024
    },
    
    "CAF": {
        "country_name": "République Centrafricaine",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 180,
        "mva_gdp_percent": 6.5,
        "mva_per_capita_usd": 35,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 55.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
            {"isic": "16", "name": "Bois et articles", "share_mva": 12.5},
        ],
        "growth_rate_2023": 1.5,
        "key_products": ["Boissons", "Bois transformé", "Diamants taillés", "Huile"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 185,
        "mva_per_capita_2015usd": 28,
        "growth_rate_2024_est": 1.8,
        "cip_index_rank": 154,
        "mht_share_mva": 3.2,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "SDN": {
        "country_name": "Soudan",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 4500,
        "mva_gdp_percent": 12.8,
        "mva_per_capita_usd": 98,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5},
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 22.8},
            {"isic": "13", "name": "Textiles", "share_mva": 12.5},
        ],
        "growth_rate_2023": -2.5,
        "key_products": ["Sucre", "Huile végétale", "Produits pétroliers", "Ciment", "Textiles"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 4200,
        "mva_per_capita_2015usd": 79,
        "growth_rate_2024_est": -2.0,
        "cip_index_rank": 144,
        "mht_share_mva": 5.5,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024,
        "note": "Données impactées par le conflit"
    },
    
    "LBY": {
        "country_name": "Libye",
        "region": "Afrique du Nord",
        "mva_2023_mln_usd": 2800,
        "mva_gdp_percent": 5.5,
        "mva_per_capita_usd": 410,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 55.5},
            {"isic": "23", "name": "Minéraux non métalliques", "share_mva": 15.2},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 12.8},
        ],
        "growth_rate_2023": 8.5,
        "key_products": ["Produits pétroliers raffinés", "Acier", "Ciment", "Produits alimentaires"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 3000,
        "mva_per_capita_2015usd": 330,
        "growth_rate_2024_est": 9.0,
        "cip_index_rank": 132,
        "mht_share_mva": 5.5,
        "industry_va_gdp_percent": 48.5,
        "manuf_share_exports": 3.5,
        "data_year": 2024
    },
    
    # Petites économies
    "SYC": {
        "country_name": "Seychelles",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 120,
        "mva_gdp_percent": 6.8,
        "mva_per_capita_usd": 1180,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires (poisson)", "share_mva": 65.5},
            {"isic": "11", "name": "Boissons", "share_mva": 18.5},
        ],
        "key_products": ["Thon en conserve", "Boissons", "Produits de la mer"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 128,
        "mva_per_capita_2015usd": 950,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 116,
        "mht_share_mva": 8.5,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 38.5,
        "data_year": 2024
    },
    
    "CPV": {
        "country_name": "Cap-Vert",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 180,
        "mva_gdp_percent": 8.5,
        "mva_per_capita_usd": 320,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 45.5},
            {"isic": "11", "name": "Boissons", "share_mva": 25.8},
        ],
        "key_products": ["Poisson en conserve", "Boissons", "Rhum", "Chaussures"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 190,
        "mva_per_capita_2015usd": 255,
        "growth_rate_2024_est": 4.2,
        "cip_index_rank": 142,
        "mht_share_mva": 5.2,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 22.5,
        "data_year": 2024
    },
    
    "COM": {
        "country_name": "Comores",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 65,
        "mva_gdp_percent": 5.2,
        "mva_per_capita_usd": 75,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 52.5},
            {"isic": "20", "name": "Produits chimiques (parfums)", "share_mva": 28.5},
        ],
        "key_products": ["Ylang-ylang distillé", "Vanille transformée", "Huiles essentielles"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 68,
        "mva_per_capita_2015usd": 60,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 153,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "DJI": {
        "country_name": "Djibouti",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 150,
        "mva_gdp_percent": 4.2,
        "mva_per_capita_usd": 145,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 48.5},
            {"isic": "11", "name": "Boissons", "share_mva": 25.8},
        ],
        "key_products": ["Eau minérale", "Sel", "Boissons", "Produits alimentaires"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 158,
        "mva_per_capita_2015usd": 115,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 145,
        "mht_share_mva": 4.2,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "ERI": {
        "country_name": "Érythrée",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 280,
        "mva_gdp_percent": 12.5,
        "mva_per_capita_usd": 78,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
            {"isic": "24", "name": "Métallurgie", "share_mva": 15.5},
        ],
        "key_products": ["Bière", "Ciment", "Sel", "Cuir"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 295,
        "mva_per_capita_2015usd": 62,
        "growth_rate_2024_est": 3.8,
        "cip_index_rank": 147,
        "mht_share_mva": 5.5,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "GNQ": {
        "country_name": "Guinée Équatoriale",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 450,
        "mva_gdp_percent": 3.5,
        "mva_per_capita_usd": 310,
        "top_sectors": [
            {"isic": "19", "name": "Raffinage pétrolier", "share_mva": 55.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 22.8},
        ],
        "key_products": ["Méthanol", "LNG", "Produits pétroliers"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 475,
        "mva_per_capita_2015usd": 252,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 131,
        "mht_share_mva": 5.2,
        "industry_va_gdp_percent": 72.5,
        "manuf_share_exports": 3.5,
        "data_year": 2024
    },
    
    "GMB": {
        "country_name": "Gambie",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 120,
        "mva_gdp_percent": 5.8,
        "mva_per_capita_usd": 48,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 52.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
        ],
        "key_products": ["Huile d'arachide", "Poisson transformé", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 128,
        "mva_per_capita_2015usd": 38,
        "growth_rate_2024_est": 5.2,
        "cip_index_rank": 151,
        "mht_share_mva": 3.8,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "GNB": {
        "country_name": "Guinée-Bissau",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 85,
        "mva_gdp_percent": 5.2,
        "mva_per_capita_usd": 42,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 65.5},
            {"isic": "11", "name": "Boissons", "share_mva": 18.5},
        ],
        "key_products": ["Noix de cajou transformées", "Riz", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 88,
        "mva_per_capita_2015usd": 34,
        "growth_rate_2024_est": 4.0,
        "cip_index_rank": 155,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "LBR": {
        "country_name": "Libéria",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 180,
        "mva_gdp_percent": 5.5,
        "mva_per_capita_usd": 35,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 42.5},
            {"isic": "22", "name": "Caoutchouc", "share_mva": 28.5},
            {"isic": "11", "name": "Boissons", "share_mva": 15.2},
        ],
        "key_products": ["Caoutchouc", "Huile de palme", "Boissons", "Ciment"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 190,
        "mva_per_capita_2015usd": 28,
        "growth_rate_2024_est": 4.2,
        "cip_index_rank": 150,
        "mht_share_mva": 3.8,
        "industry_va_gdp_percent": 22.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "LSO": {
        "country_name": "Lesotho",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 380,
        "mva_gdp_percent": 14.5,
        "mva_per_capita_usd": 175,
        "top_sectors": [
            {"isic": "14", "name": "Articles d'habillement", "share_mva": 55.5},
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 22.8},
        ],
        "key_products": ["Vêtements (AGOA)", "Textiles", "Produits alimentaires"],
        "agoa_beneficiary": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 400,
        "mva_per_capita_2015usd": 142,
        "growth_rate_2024_est": 3.8,
        "cip_index_rank": 146,
        "mht_share_mva": 8.5,
        "industry_va_gdp_percent": 32.5,
        "manuf_share_exports": 68.5,
        "data_year": 2024
    },
    
    "MRT": {
        "country_name": "Mauritanie",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 650,
        "mva_gdp_percent": 7.2,
        "mva_per_capita_usd": 140,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires (poisson)", "share_mva": 52.5},
            {"isic": "24", "name": "Métallurgie (fer)", "share_mva": 25.8},
        ],
        "key_products": ["Poisson transformé", "Minerai de fer", "Or raffiné"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 680,
        "mva_per_capita_2015usd": 112,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 144,
        "mht_share_mva": 4.5,
        "industry_va_gdp_percent": 28.5,
        "manuf_share_exports": 12.5,
        "data_year": 2024
    },
    
    "SLE": {
        "country_name": "Sierra Leone",
        "region": "Afrique de l'Ouest",
        "mva_2023_mln_usd": 220,
        "mva_gdp_percent": 5.2,
        "mva_per_capita_usd": 26,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 48.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
        ],
        "key_products": ["Riz transformé", "Boissons", "Poisson transformé"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 230,
        "mva_per_capita_2015usd": 21,
        "growth_rate_2024_est": 4.5,
        "cip_index_rank": 153,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 8.5,
        "data_year": 2024
    },
    
    "SOM": {
        "country_name": "Somalie",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 280,
        "mva_gdp_percent": 3.2,
        "mva_per_capita_usd": 17,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 55.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
        ],
        "key_products": ["Viande transformée", "Poisson", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 290,
        "mva_per_capita_2015usd": 13,
        "growth_rate_2024_est": 4.0,
        "cip_index_rank": 156,
        "mht_share_mva": 3.2,
        "industry_va_gdp_percent": 15.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "SSD": {
        "country_name": "Soudan du Sud",
        "region": "Afrique de l'Est",
        "mva_2023_mln_usd": 120,
        "mva_gdp_percent": 2.5,
        "mva_per_capita_usd": 10,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 58.5},
            {"isic": "11", "name": "Boissons", "share_mva": 25.8},
        ],
        "key_products": ["Boissons", "Produits alimentaires de base"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 125,
        "mva_per_capita_2015usd": 8,
        "growth_rate_2024_est": 2.0,
        "cip_index_rank": 157,
        "mht_share_mva": 3.0,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 3.5,
        "data_year": 2024
    },
    
    "STP": {
        "country_name": "São Tomé-et-Príncipe",
        "region": "Afrique Centrale",
        "mva_2023_mln_usd": 35,
        "mva_gdp_percent": 6.5,
        "mva_per_capita_usd": 155,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires", "share_mva": 62.5},
            {"isic": "11", "name": "Boissons", "share_mva": 22.8},
        ],
        "key_products": ["Cacao transformé", "Huile de palme", "Boissons"],
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 37,
        "mva_per_capita_2015usd": 124,
        "growth_rate_2024_est": 3.8,
        "cip_index_rank": 158,
        "mht_share_mva": 3.5,
        "industry_va_gdp_percent": 18.5,
        "manuf_share_exports": 5.5,
        "data_year": 2024
    },
    
    "SWZ": {
        "country_name": "Eswatini",
        "region": "Afrique Australe",
        "mva_2023_mln_usd": 850,
        "mva_gdp_percent": 18.5,
        "mva_per_capita_usd": 720,
        "top_sectors": [
            {"isic": "10", "name": "Produits alimentaires (sucre)", "share_mva": 42.5},
            {"isic": "11", "name": "Boissons (concentrés)", "share_mva": 25.8},
            {"isic": "17", "name": "Papier et pâte", "share_mva": 12.5},
        ],
        "key_products": ["Sucre", "Concentrés de boissons", "Pâte à papier", "Textiles"],
        "coca_cola_concentrate_plant": True,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024",
        "mva_2024_mln_usd": 900,
        "mva_per_capita_2015usd": 585,
        "growth_rate_2024_est": 3.5,
        "cip_index_rank": 123,
        "mht_share_mva": 9.5,
        "industry_va_gdp_percent": 42.5,
        "manuf_share_exports": 42.5,
        "data_year": 2024
    },
}

# =============================================================================
# FONCTIONS D'ACCÈS
# =============================================================================

def get_unido_country_data(country_iso3: str) -> Dict:
    """Récupère les données UNIDO pour un pays."""
    return UNIDO_INDUSTRY_DATA.get(country_iso3, {})

def get_all_unido_data() -> Dict:
    """Retourne toutes les données UNIDO."""
    return UNIDO_INDUSTRY_DATA

def get_isic_sectors() -> Dict:
    """Retourne la classification ISIC Rev.4."""
    return ISIC_SECTORS

def get_countries_by_mva() -> List[Dict]:
    """Retourne les pays triés par valeur ajoutée manufacturière."""
    countries = []
    for code, data in UNIDO_INDUSTRY_DATA.items():
        if "mva_2024_mln_usd" in data or "mva_2023_mln_usd" in data:
            countries.append({
                "country_iso3": code,
                "country_name": data.get("country_name"),
                "mva_2024_mln_usd": data.get("mva_2024_mln_usd", data.get("mva_2023_mln_usd")),
                "mva_2023_mln_usd": data.get("mva_2023_mln_usd"),
                "mva_gdp_percent": data.get("mva_gdp_percent"),
                "mva_per_capita_usd": data.get("mva_per_capita_usd"),
                "region": data.get("region")
            })
    return sorted(countries, key=lambda x: x.get("mva_2024_mln_usd") or x.get("mva_2023_mln_usd", 0), reverse=True)

def get_sector_analysis(isic_code: str) -> List[Dict]:
    """Analyse d'un secteur ISIC à travers tous les pays."""
    results = []
    for code, data in UNIDO_INDUSTRY_DATA.items():
        top_sectors = data.get("top_sectors", [])
        for sector in top_sectors:
            if sector.get("isic") == isic_code:
                results.append({
                    "country_iso3": code,
                    "country_name": data.get("country_name"),
                    "sector_name": sector.get("name"),
                    "share_mva": sector.get("share_mva"),
                    "value_mln_usd": sector.get("value_mln_usd", 0)
                })
    return sorted(results, key=lambda x: x.get("value_mln_usd", 0), reverse=True)

def get_unido_statistics() -> Dict:
    """Retourne des statistiques globales sur les données UNIDO."""
    total_mva = sum(d.get("mva_2024_mln_usd", d.get("mva_2023_mln_usd", 0)) for d in UNIDO_INDUSTRY_DATA.values())
    
    # Par région
    by_region = {}
    for code, data in UNIDO_INDUSTRY_DATA.items():
        region = data.get("region", "Non classé")
        if region not in by_region:
            by_region[region] = {"count": 0, "total_mva": 0, "countries": []}
        by_region[region]["count"] += 1
        by_region[region]["total_mva"] += data.get("mva_2024_mln_usd", data.get("mva_2023_mln_usd", 0))
        by_region[region]["countries"].append(code)
    
    return {
        "total_countries": len(UNIDO_INDUSTRY_DATA),
        "total_mva_mln_usd": total_mva,
        "total_mva_bln_usd": round(total_mva / 1000, 1),
        "by_region": by_region,
        "isic_sectors_count": len(ISIC_SECTORS),
        "data_year": 2024,
        "source": "UNIDO INDSTAT4 2024, UNIDO Yearbook 2024"
    }
