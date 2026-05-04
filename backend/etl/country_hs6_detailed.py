"""
Tarifs douaniers avec SOUS-POSITIONS NATIONALES (8-12 chiffres)
Structure professionnelle avec taux spécifiques par sous-position

Format:
{
    "hs6_code": {
        "default_dd": taux_par_defaut,
        "description_fr": "...",
        "description_en": "...",
        "sub_positions": {
            "code_8_10_12": {
                "dd": taux_specifique,
                "description_fr": "...",
                "description_en": "..."
            }
        }
    }
}

Sources: Tarifs Intégrés Nationaux (TIN), SYDONIA, Administrations douanières
Dernière mise à jour: Janvier 2025
"""

from typing import Dict, Optional, Tuple, List

# =============================================================================
# NIGERIA (NGA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Nigeria Customs Service - Tarif Intégré
# =============================================================================

NGA_HS6_DETAILED = {
    # VÉHICULES - Différences neufs/occasion
    "870321": {
        "default_dd": 0.35,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870322": {
        "default_dd": 0.35,
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "sub_positions": {
            "8703221000": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc neuves", "description_en": "New cars 1000-1500cc"},
            "8703229000": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc occasion", "description_en": "Used cars 1000-1500cc"},
        }
    },
    "870323": {
        "default_dd": 0.35,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703231100": {"dd": 0.35, "description_fr": "Berlines neuves 1500-2000cc", "description_en": "New sedans 1500-2000cc"},
            "8703231200": {"dd": 0.35, "description_fr": "SUV neufs 1500-3000cc", "description_en": "New SUVs 1500-3000cc"},
            "8703239000": {"dd": 0.70, "description_fr": "Voitures 1500-3000cc occasion >10 ans", "description_en": "Used cars >10 years 1500-3000cc"},
            "8703239100": {"dd": 0.50, "description_fr": "Voitures 1500-3000cc occasion 5-10 ans", "description_en": "Used cars 5-10 years 1500-3000cc"},
            "8703239200": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc occasion <5 ans", "description_en": "Used cars <5 years 1500-3000cc"},
        }
    },
    "870324": {
        "default_dd": 0.35,
        "description_fr": "Voitures >3000cc",
        "description_en": "Cars >3000cc",
        "sub_positions": {
            "8703241000": {"dd": 0.35, "description_fr": "Voitures >3000cc neuves", "description_en": "New cars >3000cc"},
            "8703249000": {"dd": 0.70, "description_fr": "Voitures >3000cc occasion", "description_en": "Used cars >3000cc"},
        }
    },
    
    # RIZ - Différents niveaux de transformation
    "100610": {
        "default_dd": 0.10,
        "description_fr": "Riz paddy (non décortiqué)",
        "description_en": "Rice in the husk (paddy)",
        "sub_positions": {
            "1006101000": {"dd": 0.05, "description_fr": "Riz paddy pour semence", "description_en": "Paddy rice for sowing"},
            "1006109000": {"dd": 0.10, "description_fr": "Autre riz paddy", "description_en": "Other paddy rice"},
        }
    },
    "100620": {
        "default_dd": 0.50,
        "description_fr": "Riz décortiqué (cargo)",
        "description_en": "Husked (brown) rice",
        "sub_positions": {
            "1006201000": {"dd": 0.30, "description_fr": "Riz cargo long grain", "description_en": "Long grain brown rice"},
            "1006209000": {"dd": 0.50, "description_fr": "Autre riz décortiqué", "description_en": "Other husked rice"},
        }
    },
    "100630": {
        "default_dd": 0.60,
        "description_fr": "Riz semi-blanchi ou blanchi",
        "description_en": "Semi-milled or wholly milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.50, "description_fr": "Riz semi-blanchi", "description_en": "Semi-milled rice"},
            "1006302000": {"dd": 0.60, "description_fr": "Riz blanchi non étuvé", "description_en": "Wholly milled rice, not parboiled"},
            "1006303000": {"dd": 0.60, "description_fr": "Riz blanchi étuvé", "description_en": "Parboiled wholly milled rice"},
            "1006309100": {"dd": 0.70, "description_fr": "Riz parfumé (Basmati, Jasmin)", "description_en": "Perfumed rice (Basmati, Jasmine)"},
            "1006309900": {"dd": 0.60, "description_fr": "Autre riz blanchi", "description_en": "Other wholly milled rice"},
        }
    },
    "100640": {
        "default_dd": 0.10,
        "description_fr": "Brisures de riz",
        "description_en": "Broken rice",
        "sub_positions": {
            "1006401000": {"dd": 0.05, "description_fr": "Brisures pour industrie brassicole", "description_en": "Broken rice for brewing"},
            "1006409000": {"dd": 0.10, "description_fr": "Autres brisures de riz", "description_en": "Other broken rice"},
        }
    },
    
    # TEXTILES - Par composition
    "610910": {
        "default_dd": 0.35,
        "description_fr": "T-shirts en coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109100010": {"dd": 0.35, "description_fr": "T-shirts 100% coton", "description_en": "100% cotton T-shirts"},
            "6109100020": {"dd": 0.35, "description_fr": "T-shirts coton mélangé >50%", "description_en": "Cotton blend T-shirts >50%"},
            "6109100030": {"dd": 0.20, "description_fr": "T-shirts coton pour enfants", "description_en": "Children's cotton T-shirts"},
        }
    },
    "620342": {
        "default_dd": 0.35,
        "description_fr": "Pantalons hommes coton",
        "description_en": "Men's cotton trousers",
        "sub_positions": {
            "6203420010": {"dd": 0.35, "description_fr": "Jeans hommes 100% coton", "description_en": "Men's 100% cotton jeans"},
            "6203420020": {"dd": 0.35, "description_fr": "Pantalons chinos hommes coton", "description_en": "Men's cotton chinos"},
            "6203420030": {"dd": 0.20, "description_fr": "Pantalons travail coton", "description_en": "Cotton work trousers"},
        }
    },
    
    # CIMENT - Par type
    "252321": {
        "default_dd": 0.35,
        "description_fr": "Ciment Portland ordinaire",
        "description_en": "Ordinary Portland cement",
        "sub_positions": {
            "2523210010": {"dd": 0.35, "description_fr": "Ciment Portland 32.5", "description_en": "Portland cement 32.5"},
            "2523210020": {"dd": 0.35, "description_fr": "Ciment Portland 42.5", "description_en": "Portland cement 42.5"},
            "2523210030": {"dd": 0.35, "description_fr": "Ciment Portland 52.5", "description_en": "Portland cement 52.5"},
            "2523210090": {"dd": 0.35, "description_fr": "Autre ciment Portland", "description_en": "Other Portland cement"},
        }
    },
    
    # SUCRE - Différents types
    "170114": {
        "default_dd": 0.20,
        "description_fr": "Sucre de canne brut",
        "description_en": "Raw cane sugar",
        "sub_positions": {
            "1701141000": {"dd": 0.10, "description_fr": "Sucre brut pour raffinage", "description_en": "Raw sugar for refining"},
            "1701149000": {"dd": 0.20, "description_fr": "Autre sucre brut", "description_en": "Other raw sugar"},
        }
    },
    "170199": {
        "default_dd": 0.20,
        "description_fr": "Sucre raffiné",
        "description_en": "Refined sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.20, "description_fr": "Sucre blanc cristallisé", "description_en": "White crystallized sugar"},
            "1701992000": {"dd": 0.25, "description_fr": "Sucre en morceaux", "description_en": "Sugar cubes"},
            "1701993000": {"dd": 0.20, "description_fr": "Sucre en poudre", "description_en": "Powdered sugar"},
        }
    },
    
    # HUILES VÉGÉTALES
    "151110": {
        "default_dd": 0.35,
        "description_fr": "Huile de palme brute",
        "description_en": "Crude palm oil",
        "sub_positions": {
            "1511100010": {"dd": 0.20, "description_fr": "Huile de palme brute pour industrie", "description_en": "Crude palm oil for industry"},
            "1511100090": {"dd": 0.35, "description_fr": "Autre huile de palme brute", "description_en": "Other crude palm oil"},
        }
    },
    
    # MACHINES ET ÉQUIPEMENTS
    "847130": {
        "default_dd": 0.05,
        "description_fr": "Ordinateurs portables",
        "description_en": "Laptop computers",
        "sub_positions": {
            "8471300010": {"dd": 0.00, "description_fr": "Ordinateurs portables éducation", "description_en": "Educational laptops"},
            "8471300020": {"dd": 0.05, "description_fr": "Ordinateurs portables professionnels", "description_en": "Professional laptops"},
            "8471300090": {"dd": 0.05, "description_fr": "Autres ordinateurs portables", "description_en": "Other laptops"},
        }
    },
    "851712": {
        "default_dd": 0.10,
        "description_fr": "Téléphones portables",
        "description_en": "Mobile phones",
        "sub_positions": {
            "8517120010": {"dd": 0.00, "description_fr": "Smartphones CKD (kit)", "description_en": "Smartphone CKD kits"},
            "8517120020": {"dd": 0.05, "description_fr": "Téléphones basiques", "description_en": "Feature phones"},
            "8517120030": {"dd": 0.10, "description_fr": "Smartphones importés", "description_en": "Imported smartphones"},
        }
    },
    
    # ÉLECTROMÉNAGER
    "841821": {
        "default_dd": 0.20,
        "description_fr": "Réfrigérateurs ménagers",
        "description_en": "Household refrigerators",
        "sub_positions": {
            "8418210010": {"dd": 0.20, "description_fr": "Réfrigérateurs <200L", "description_en": "Refrigerators <200L"},
            "8418210020": {"dd": 0.20, "description_fr": "Réfrigérateurs 200-400L", "description_en": "Refrigerators 200-400L"},
            "8418210030": {"dd": 0.25, "description_fr": "Réfrigérateurs >400L", "description_en": "Refrigerators >400L"},
            "8418210040": {"dd": 0.10, "description_fr": "Réfrigérateurs solaires", "description_en": "Solar refrigerators"},
        }
    },
    
    # MÉDICAMENTS - Tous exonérés
    "300220": {
        "default_dd": 0.00,
        "description_fr": "Vaccins",
        "description_en": "Vaccines",
        "sub_positions": {
            "3002200010": {"dd": 0.00, "description_fr": "Vaccins pour humains", "description_en": "Human vaccines"},
            "3002200020": {"dd": 0.00, "description_fr": "Vaccins vétérinaires", "description_en": "Veterinary vaccines"},
        }
    },
    "300490": {
        "default_dd": 0.00,
        "description_fr": "Autres médicaments",
        "description_en": "Other medicaments",
        "sub_positions": {
            "3004900010": {"dd": 0.00, "description_fr": "Antipaludéens", "description_en": "Antimalarials"},
            "3004900020": {"dd": 0.00, "description_fr": "Antirétroviraux", "description_en": "Antiretrovirals"},
            "3004900030": {"dd": 0.00, "description_fr": "Antibiotiques", "description_en": "Antibiotics"},
            "3004900090": {"dd": 0.00, "description_fr": "Autres médicaments conditionnés", "description_en": "Other packaged medicines"},
        }
    },
    
    # PRODUITS PÉTROLIERS
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut léger", "description_en": "Light crude oil"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole brut lourd", "description_en": "Heavy crude oil"},
        }
    },
    "271012": {
        "default_dd": 0.05,
        "description_fr": "Essences légères",
        "description_en": "Light oils",
        "sub_positions": {
            "2710121000": {"dd": 0.05, "description_fr": "Essence sans plomb", "description_en": "Unleaded petrol"},
            "2710122000": {"dd": 0.05, "description_fr": "Essence aviation", "description_en": "Aviation gasoline"},
            "2710123000": {"dd": 0.02, "description_fr": "Naphta pour pétrochimie", "description_en": "Naphtha for petrochemicals"},
        }
    },
    "271019": {
        "default_dd": 0.05,
        "description_fr": "Autres huiles de pétrole",
        "description_en": "Other petroleum oils",
        "sub_positions": {
            "2710191000": {"dd": 0.05, "description_fr": "Gasoil/Diesel", "description_en": "Gas oil/Diesel"},
            "2710192000": {"dd": 0.05, "description_fr": "Fuel oil", "description_en": "Fuel oil"},
            "2710193000": {"dd": 0.02, "description_fr": "Kérosène", "description_en": "Kerosene"},
            "2710194000": {"dd": 0.05, "description_fr": "Huiles de graissage", "description_en": "Lubricating oils"},
        }
    },
}

# =============================================================================
# CÔTE D'IVOIRE (CIV) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes CI - TEC CEDEAO
# =============================================================================

CIV_HS6_DETAILED = {
    # CACAO - Produit d'exportation principal
    "180100": {
        "default_dd": 0.00,
        "description_fr": "Cacao en fèves",
        "description_en": "Cocoa beans",
        "sub_positions": {
            "1801001000": {"dd": 0.00, "description_fr": "Fèves de cacao grade I", "description_en": "Cocoa beans grade I"},
            "1801002000": {"dd": 0.00, "description_fr": "Fèves de cacao grade II", "description_en": "Cocoa beans grade II"},
            "1801009000": {"dd": 0.00, "description_fr": "Autres fèves de cacao", "description_en": "Other cocoa beans"},
        }
    },
    "180310": {
        "default_dd": 0.10,
        "description_fr": "Pâte de cacao non dégraissée",
        "description_en": "Cocoa paste, not defatted",
        "sub_positions": {
            "1803101000": {"dd": 0.10, "description_fr": "Masse de cacao", "description_en": "Cocoa mass"},
            "1803109000": {"dd": 0.10, "description_fr": "Liqueur de cacao", "description_en": "Cocoa liquor"},
        }
    },
    "180400": {
        "default_dd": 0.10,
        "description_fr": "Beurre de cacao",
        "description_en": "Cocoa butter",
        "sub_positions": {
            "1804001000": {"dd": 0.10, "description_fr": "Beurre de cacao pressé", "description_en": "Pressed cocoa butter"},
            "1804002000": {"dd": 0.10, "description_fr": "Beurre de cacao désodorisé", "description_en": "Deodorized cocoa butter"},
        }
    },
    "180620": {
        "default_dd": 0.20,
        "description_fr": "Chocolat en blocs >2kg",
        "description_en": "Chocolate blocks >2kg",
        "sub_positions": {
            "1806201000": {"dd": 0.20, "description_fr": "Couverture chocolat", "description_en": "Chocolate coating"},
            "1806202000": {"dd": 0.20, "description_fr": "Chocolat industriel", "description_en": "Industrial chocolate"},
        }
    },
    
    # NOIX DE CAJOU
    "080131": {
        "default_dd": 0.00,
        "description_fr": "Noix de cajou en coques",
        "description_en": "Cashew nuts in shell",
        "sub_positions": {
            "0801310010": {"dd": 0.00, "description_fr": "Noix de cajou brutes", "description_en": "Raw cashew nuts"},
            "0801310020": {"dd": 0.00, "description_fr": "Noix de cajou séchées", "description_en": "Dried cashew nuts"},
        }
    },
    "080132": {
        "default_dd": 0.10,
        "description_fr": "Noix de cajou décortiquées",
        "description_en": "Cashew nuts, shelled",
        "sub_positions": {
            "0801320010": {"dd": 0.10, "description_fr": "Noix de cajou blanches W320", "description_en": "White cashews W320"},
            "0801320020": {"dd": 0.10, "description_fr": "Noix de cajou blanches W240", "description_en": "White cashews W240"},
            "0801320030": {"dd": 0.05, "description_fr": "Brisures de cajou", "description_en": "Cashew pieces"},
        }
    },
    
    # CAOUTCHOUC
    "400110": {
        "default_dd": 0.00,
        "description_fr": "Latex de caoutchouc naturel",
        "description_en": "Natural rubber latex",
        "sub_positions": {
            "4001100010": {"dd": 0.00, "description_fr": "Latex centrifugé 60%", "description_en": "Centrifuged latex 60%"},
            "4001100020": {"dd": 0.00, "description_fr": "Latex concentré", "description_en": "Concentrated latex"},
        }
    },
    "400121": {
        "default_dd": 0.05,
        "description_fr": "Feuilles fumées de caoutchouc",
        "description_en": "Smoked rubber sheets",
        "sub_positions": {
            "4001210010": {"dd": 0.05, "description_fr": "RSS1 (Ribbed Smoked Sheet)", "description_en": "RSS1"},
            "4001210020": {"dd": 0.05, "description_fr": "RSS3", "description_en": "RSS3"},
        }
    },
    
    # VÉHICULES - TEC CEDEAO
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703210010": {"dd": 0.20, "description_fr": "Voitures neuves ≤1000cc", "description_en": "New cars ≤1000cc"},
            "8703210020": {"dd": 0.20, "description_fr": "Voitures occasion ≤1000cc", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870322": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "sub_positions": {
            "8703220010": {"dd": 0.20, "description_fr": "Voitures neuves 1000-1500cc", "description_en": "New cars 1000-1500cc"},
            "8703220020": {"dd": 0.20, "description_fr": "Voitures occasion 1000-1500cc", "description_en": "Used cars 1000-1500cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703230010": {"dd": 0.20, "description_fr": "Voitures neuves 1500-3000cc", "description_en": "New cars 1500-3000cc"},
            "8703230020": {"dd": 0.20, "description_fr": "Voitures occasion 1500-3000cc <5 ans", "description_en": "Used cars <5 years 1500-3000cc"},
            "8703230030": {"dd": 0.25, "description_fr": "Voitures occasion 1500-3000cc >5 ans", "description_en": "Used cars >5 years 1500-3000cc"},
        }
    },
    
    # RIZ - TEC CEDEAO
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz semi-blanchi ou blanchi",
        "description_en": "Semi-milled or wholly milled rice",
        "sub_positions": {
            "1006300010": {"dd": 0.10, "description_fr": "Riz blanchi parfumé", "description_en": "Perfumed milled rice"},
            "1006300020": {"dd": 0.10, "description_fr": "Riz blanchi brisé 5%", "description_en": "Milled rice 5% broken"},
            "1006300030": {"dd": 0.10, "description_fr": "Riz blanchi brisé 25%", "description_en": "Milled rice 25% broken"},
            "1006300090": {"dd": 0.10, "description_fr": "Autre riz blanchi", "description_en": "Other milled rice"},
        }
    },
    
    # MACHINES
    "847130": {
        "default_dd": 0.05,
        "description_fr": "Ordinateurs portables",
        "description_en": "Laptop computers",
        "sub_positions": {
            "8471300010": {"dd": 0.00, "description_fr": "Ordinateurs éducatifs", "description_en": "Educational computers"},
            "8471300090": {"dd": 0.05, "description_fr": "Autres ordinateurs portables", "description_en": "Other laptops"},
        }
    },
    
    # MÉDICAMENTS
    "300220": {
        "default_dd": 0.00,
        "description_fr": "Vaccins",
        "description_en": "Vaccines",
        "sub_positions": {
            "3002200010": {"dd": 0.00, "description_fr": "Vaccins PEV", "description_en": "EPI vaccines"},
            "3002200090": {"dd": 0.00, "description_fr": "Autres vaccins", "description_en": "Other vaccines"},
        }
    },
    "300490": {
        "default_dd": 0.00,
        "description_fr": "Autres médicaments",
        "description_en": "Other medicaments",
        "sub_positions": {
            "3004900010": {"dd": 0.00, "description_fr": "Médicaments essentiels OMS", "description_en": "WHO essential medicines"},
            "3004900090": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicines"},
        }
    },
}

# =============================================================================
# AFRIQUE DU SUD (ZAF) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: SARS - SACU Tariff Schedule
# =============================================================================

ZAF_HS6_DETAILED = {
    # VÉHICULES - Secteur stratégique avec tarifs détaillés
    "870321": {
        "default_dd": 0.25,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "87032100.17": {"dd": 0.25, "description_fr": "Voitures neuves ≤1000cc", "description_en": "New cars ≤1000cc"},
            "87032100.25": {"dd": 0.25, "description_fr": "Voitures occasion ≤1000cc", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870322": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "sub_positions": {
            "87032200.17": {"dd": 0.25, "description_fr": "Voitures neuves 1000-1500cc", "description_en": "New cars 1000-1500cc"},
            "87032200.25": {"dd": 0.25, "description_fr": "Voitures occasion 1000-1500cc", "description_en": "Used cars 1000-1500cc"},
        }
    },
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "87032310.17": {"dd": 0.25, "description_fr": "Berlines neuves 1500-2000cc", "description_en": "New sedans 1500-2000cc"},
            "87032320.17": {"dd": 0.25, "description_fr": "Berlines neuves 2000-3000cc", "description_en": "New sedans 2000-3000cc"},
            "87032310.25": {"dd": 0.25, "description_fr": "Berlines occasion 1500-2000cc", "description_en": "Used sedans 1500-2000cc"},
            "87032320.25": {"dd": 0.25, "description_fr": "Berlines occasion 2000-3000cc", "description_en": "Used sedans 2000-3000cc"},
        }
    },
    "870340": {
        "default_dd": 0.25,
        "description_fr": "Véhicules électriques",
        "description_en": "Electric vehicles",
        "sub_positions": {
            "87034000.17": {"dd": 0.18, "description_fr": "Véhicules électriques neufs", "description_en": "New electric vehicles"},
            "87034000.25": {"dd": 0.25, "description_fr": "Véhicules électriques occasion", "description_en": "Used electric vehicles"},
        }
    },
    
    # TEXTILES - Protection industrie locale forte
    "610910": {
        "default_dd": 0.45,
        "description_fr": "T-shirts en coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "61091000.10": {"dd": 0.45, "description_fr": "T-shirts coton adultes", "description_en": "Adult cotton T-shirts"},
            "61091000.20": {"dd": 0.45, "description_fr": "T-shirts coton enfants", "description_en": "Children's cotton T-shirts"},
            "61091000.30": {"dd": 0.30, "description_fr": "T-shirts coton travail protégé", "description_en": "Protected work cotton T-shirts"},
        }
    },
    "620342": {
        "default_dd": 0.45,
        "description_fr": "Pantalons hommes coton",
        "description_en": "Men's cotton trousers",
        "sub_positions": {
            "62034200.10": {"dd": 0.45, "description_fr": "Jeans hommes", "description_en": "Men's jeans"},
            "62034200.20": {"dd": 0.45, "description_fr": "Pantalons habillés hommes", "description_en": "Men's dress trousers"},
            "62034200.30": {"dd": 0.30, "description_fr": "Pantalons travail", "description_en": "Work trousers"},
        }
    },
    
    # MINERAIS - Exportations
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "71081200.10": {"dd": 0.00, "description_fr": "Or en lingots", "description_en": "Gold bars"},
            "71081200.20": {"dd": 0.00, "description_fr": "Or en poudre", "description_en": "Gold powder"},
            "71081200.90": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    "711011": {
        "default_dd": 0.00,
        "description_fr": "Platine brut",
        "description_en": "Platinum, unwrought",
        "sub_positions": {
            "71101100.10": {"dd": 0.00, "description_fr": "Platine en éponge", "description_en": "Platinum sponge"},
            "71101100.20": {"dd": 0.00, "description_fr": "Platine en lingots", "description_en": "Platinum ingots"},
        }
    },
    
    # VIN - Exportation
    "220421": {
        "default_dd": 0.00,
        "description_fr": "Vins en contenants ≤2L",
        "description_en": "Wine in containers ≤2L",
        "sub_positions": {
            "22042100.01": {"dd": 0.00, "description_fr": "Vins rouges ≤2L", "description_en": "Red wine ≤2L"},
            "22042100.02": {"dd": 0.00, "description_fr": "Vins blancs ≤2L", "description_en": "White wine ≤2L"},
            "22042100.03": {"dd": 0.00, "description_fr": "Vins rosés ≤2L", "description_en": "Rosé wine ≤2L"},
        }
    },
    
    # MACHINES
    "847130": {
        "default_dd": 0.00,
        "description_fr": "Ordinateurs portables",
        "description_en": "Laptop computers",
        "sub_positions": {
            "84713000.10": {"dd": 0.00, "description_fr": "Ordinateurs portables standard", "description_en": "Standard laptops"},
            "84713000.90": {"dd": 0.00, "description_fr": "Autres ordinateurs portables", "description_en": "Other laptops"},
        }
    },
    "851712": {
        "default_dd": 0.00,
        "description_fr": "Téléphones portables",
        "description_en": "Mobile phones",
        "sub_positions": {
            "85171200.10": {"dd": 0.00, "description_fr": "Smartphones", "description_en": "Smartphones"},
            "85171200.20": {"dd": 0.00, "description_fr": "Téléphones basiques", "description_en": "Feature phones"},
        }
    },
    
    # MÉDICAMENTS
    "300220": {
        "default_dd": 0.00,
        "description_fr": "Vaccins",
        "description_en": "Vaccines",
        "sub_positions": {
            "30022000.10": {"dd": 0.00, "description_fr": "Vaccins humains", "description_en": "Human vaccines"},
            "30022000.20": {"dd": 0.00, "description_fr": "Vaccins vétérinaires", "description_en": "Veterinary vaccines"},
        }
    },
    "300490": {
        "default_dd": 0.00,
        "description_fr": "Autres médicaments",
        "description_en": "Other medicaments",
        "sub_positions": {
            "30049000.10": {"dd": 0.00, "description_fr": "ARV", "description_en": "Antiretrovirals"},
            "30049000.90": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicines"},
        }
    },
}

# =============================================================================
# KENYA (KEN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: KRA - EAC CET
# =============================================================================

KEN_HS6_DETAILED = {
    # THÉ - Premier exportateur africain
    "090230": {
        "default_dd": 0.00,
        "description_fr": "Thé noir fermenté ≤3kg",
        "description_en": "Black tea, fermented ≤3kg",
        "sub_positions": {
            "0902301000": {"dd": 0.00, "description_fr": "Thé noir CTC", "description_en": "Black CTC tea"},
            "0902302000": {"dd": 0.00, "description_fr": "Thé noir orthodoxe", "description_en": "Orthodox black tea"},
            "0902309000": {"dd": 0.00, "description_fr": "Autre thé noir", "description_en": "Other black tea"},
        }
    },
    "090240": {
        "default_dd": 0.00,
        "description_fr": "Thé noir fermenté >3kg",
        "description_en": "Black tea, fermented >3kg",
        "sub_positions": {
            "0902401000": {"dd": 0.00, "description_fr": "Thé noir vrac CTC", "description_en": "Bulk CTC black tea"},
            "0902402000": {"dd": 0.00, "description_fr": "Thé noir vrac orthodoxe", "description_en": "Bulk orthodox black tea"},
        }
    },
    
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café non torréfié, non décaféiné",
        "description_en": "Coffee, not roasted, not decaf",
        "sub_positions": {
            "0901110010": {"dd": 0.00, "description_fr": "Café Arabica AA", "description_en": "Arabica AA coffee"},
            "0901110020": {"dd": 0.00, "description_fr": "Café Arabica AB", "description_en": "Arabica AB coffee"},
            "0901110030": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901110090": {"dd": 0.00, "description_fr": "Autre café vert", "description_en": "Other green coffee"},
        }
    },
    
    # FLEURS COUPÉES - Premier exportateur
    "060311": {
        "default_dd": 0.00,
        "description_fr": "Roses fraîches coupées",
        "description_en": "Fresh cut roses",
        "sub_positions": {
            "0603110010": {"dd": 0.00, "description_fr": "Roses rouges premium", "description_en": "Premium red roses"},
            "0603110020": {"dd": 0.00, "description_fr": "Roses mixtes", "description_en": "Mixed roses"},
            "0603110030": {"dd": 0.00, "description_fr": "Roses spray", "description_en": "Spray roses"},
        }
    },
    
    # RIZ - Produit sensible EAC
    "100630": {
        "default_dd": 0.75,
        "description_fr": "Riz semi-blanchi ou blanchi",
        "description_en": "Semi-milled or wholly milled rice",
        "sub_positions": {
            "1006300010": {"dd": 0.75, "description_fr": "Riz Basmati", "description_en": "Basmati rice"},
            "1006300020": {"dd": 0.75, "description_fr": "Riz Pishori (local)", "description_en": "Pishori rice (local)"},
            "1006300030": {"dd": 0.75, "description_fr": "Riz long grain autre", "description_en": "Other long grain rice"},
            "1006300040": {"dd": 0.75, "description_fr": "Riz brisé 5%", "description_en": "Rice 5% broken"},
            "1006300090": {"dd": 0.75, "description_fr": "Autre riz blanchi", "description_en": "Other milled rice"},
        }
    },
    
    # VÉHICULES - EAC avec variations par âge
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703230010": {"dd": 0.25, "description_fr": "Voitures neuves 1500-3000cc", "description_en": "New cars 1500-3000cc"},
            "8703230020": {"dd": 0.25, "description_fr": "Voitures occasion <3 ans", "description_en": "Used cars <3 years"},
            "8703230030": {"dd": 0.35, "description_fr": "Voitures occasion 3-8 ans", "description_en": "Used cars 3-8 years"},
            "8703230040": {"dd": 0.00, "description_fr": "Voitures occasion >8 ans (interdites)", "description_en": "Used cars >8 years (prohibited)"},
        }
    },
    
    # MACHINES - EAC 0%
    "847130": {
        "default_dd": 0.00,
        "description_fr": "Ordinateurs portables",
        "description_en": "Laptop computers",
        "sub_positions": {
            "8471300010": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
        }
    },
    "851712": {
        "default_dd": 0.00,
        "description_fr": "Téléphones portables",
        "description_en": "Mobile phones",
        "sub_positions": {
            "8517120010": {"dd": 0.00, "description_fr": "Smartphones", "description_en": "Smartphones"},
            "8517120020": {"dd": 0.00, "description_fr": "Téléphones basiques", "description_en": "Feature phones"},
        }
    },
    
    # MÉDICAMENTS
    "300220": {
        "default_dd": 0.00,
        "description_fr": "Vaccins",
        "description_en": "Vaccines",
        "sub_positions": {
            "3002200010": {"dd": 0.00, "description_fr": "Vaccins PEV", "description_en": "EPI vaccines"},
            "3002200090": {"dd": 0.00, "description_fr": "Autres vaccins", "description_en": "Other vaccines"},
        }
    },
    "300490": {
        "default_dd": 0.00,
        "description_fr": "Autres médicaments",
        "description_en": "Other medicaments",
        "sub_positions": {
            "3004900010": {"dd": 0.00, "description_fr": "ARV", "description_en": "Antiretrovirals"},
            "3004900020": {"dd": 0.00, "description_fr": "Antipaludéens", "description_en": "Antimalarials"},
            "3004900090": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicines"},
        }
    },
}

# =============================================================================
# CONSOLIDATION DES TARIFS DÉTAILLÉS - 54 PAYS AFRICAINS
# =============================================================================

# Importer les dictionnaires régionaux
from etl.country_hs6_detailed_cedeao import CEDEAO_HS6_DETAILED
from etl.country_hs6_detailed_cemac import CEMAC_HS6_DETAILED
from etl.country_hs6_detailed_eac_sadc import EAC_SADC_HS6_DETAILED
from etl.country_hs6_detailed_north_africa import NORTH_AFRICA_HS6_DETAILED

# Dictionnaire de base (4 pays déjà définis dans ce fichier)
COUNTRY_HS6_DETAILED = {
    "NGA": NGA_HS6_DETAILED,
    "CIV": CIV_HS6_DETAILED,
    "ZAF": ZAF_HS6_DETAILED,
    "KEN": KEN_HS6_DETAILED,
}

# Fusion de tous les dictionnaires régionaux
COUNTRY_HS6_DETAILED.update(CEDEAO_HS6_DETAILED)       # +13 pays CEDEAO (hors NGA, CIV)
COUNTRY_HS6_DETAILED.update(CEMAC_HS6_DETAILED)        # +8 pays CEMAC + RDC + STP
COUNTRY_HS6_DETAILED.update(EAC_SADC_HS6_DETAILED)     # +22 pays EAC/COMESA/SADC (hors KEN, ZAF)
COUNTRY_HS6_DETAILED.update(NORTH_AFRICA_HS6_DETAILED) # +7 pays Afrique du Nord

# Statistiques des données
def get_detailed_tariff_stats():
    """Retourne les statistiques des tarifs détaillés"""
    total_countries = len(COUNTRY_HS6_DETAILED)
    total_hs6_codes = sum(len(tariffs) for tariffs in COUNTRY_HS6_DETAILED.values())
    total_sub_positions = sum(
        len(hs6_data.get("sub_positions", {}))
        for tariffs in COUNTRY_HS6_DETAILED.values()
        for hs6_data in tariffs.values()
    )
    return {
        "total_countries": total_countries,
        "total_hs6_codes": total_hs6_codes,
        "total_sub_positions": total_sub_positions,
        "countries": list(COUNTRY_HS6_DETAILED.keys())
    }


# =============================================================================
# FONCTIONS D'ACCÈS AUX SOUS-POSITIONS
# =============================================================================

def get_detailed_tariff(country_code: str, hs_code: str) -> Optional[Dict]:
    """
    Obtenir le tarif détaillé avec sous-positions pour un pays et code HS
    
    Args:
        country_code: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        
    Returns:
        Dict avec taux par défaut et sous-positions, ou None
    """
    country_code = country_code.upper()
    hs6 = hs_code[:6].zfill(6)
    
    country_tariffs = COUNTRY_HS6_DETAILED.get(country_code, {})
    return country_tariffs.get(hs6)


def get_sub_position_rate(country_code: str, full_code: str) -> Tuple[Optional[float], str, str]:
    """
    Obtenir le taux spécifique pour une sous-position nationale
    
    Args:
        country_code: Code ISO3 du pays
        full_code: Code complet (8-12 chiffres)
        
    Returns:
        Tuple (taux ou None, description, source)
    """
    country_code = country_code.upper()
    hs6 = full_code[:6].zfill(6)
    
    country_tariffs = COUNTRY_HS6_DETAILED.get(country_code, {})
    hs6_data = country_tariffs.get(hs6)
    
    if not hs6_data:
        return (None, "", "Non disponible")
    
    # Chercher la sous-position exacte
    sub_positions = hs6_data.get("sub_positions", {})
    
    # Essayer différents formats de code
    for sp_code, sp_data in sub_positions.items():
        # Normaliser les codes pour comparaison
        sp_normalized = sp_code.replace(".", "").replace(" ", "")
        full_normalized = full_code.replace(".", "").replace(" ", "")
        
        if sp_normalized == full_normalized or sp_normalized.startswith(full_normalized) or full_normalized.startswith(sp_normalized):
            return (sp_data["dd"], sp_data.get("description_fr", ""), f"Sous-position {sp_code}")
    
    # Retourner le taux par défaut si pas de sous-position trouvée
    return (hs6_data["default_dd"], hs6_data.get("description_fr", ""), "Taux par défaut HS6")


def get_all_sub_positions(country_code: str, hs6_code: str) -> List[Dict]:
    """
    Obtenir toutes les sous-positions pour un code HS6 dans un pays
    
    Returns:
        Liste des sous-positions avec leurs taux
    """
    country_code = country_code.upper()
    hs6 = hs6_code[:6].zfill(6)
    
    country_tariffs = COUNTRY_HS6_DETAILED.get(country_code, {})
    hs6_data = country_tariffs.get(hs6)
    
    if not hs6_data:
        return []
    
    result = []
    for sp_code, sp_data in hs6_data.get("sub_positions", {}).items():
        result.append({
            "code": sp_code,
            "dd_rate": sp_data["dd"],
            "dd_rate_pct": f"{sp_data['dd'] * 100:.1f}%",
            "description_fr": sp_data.get("description_fr", ""),
            "description_en": sp_data.get("description_en", "")
        })
    
    return sorted(result, key=lambda x: x["code"])


def has_varying_rates(country_code: str, hs6_code: str) -> Tuple[bool, float, float]:
    """
    Vérifier si un code HS6 a des taux variables selon les sous-positions
    
    Returns:
        Tuple (a_variations, taux_min, taux_max)
    """
    sub_positions = get_all_sub_positions(country_code, hs6_code)
    
    if not sub_positions or len(sub_positions) <= 1:
        return (False, 0, 0)
    
    rates = [sp["dd_rate"] for sp in sub_positions]
    min_rate = min(rates)
    max_rate = max(rates)
    
    return (min_rate != max_rate, min_rate, max_rate)


def get_tariff_summary(country_code: str, hs6_code: str) -> Dict:
    """
    Obtenir un résumé complet du tarif avec variations
    """
    country_code = country_code.upper()
    hs6 = hs6_code[:6].zfill(6)
    
    country_tariffs = COUNTRY_HS6_DETAILED.get(country_code, {})
    hs6_data = country_tariffs.get(hs6)
    
    if not hs6_data:
        return {
            "hs6_code": hs6,
            "country_code": country_code,
            "has_detailed_tariffs": False
        }
    
    sub_positions = get_all_sub_positions(country_code, hs6)
    has_variations, min_rate, max_rate = has_varying_rates(country_code, hs6)
    
    return {
        "hs6_code": hs6,
        "country_code": country_code,
        "has_detailed_tariffs": True,
        "default_dd": hs6_data["default_dd"],
        "default_dd_pct": f"{hs6_data['default_dd'] * 100:.1f}%",
        "description_fr": hs6_data.get("description_fr", ""),
        "description_en": hs6_data.get("description_en", ""),
        "has_varying_rates": has_variations,
        "rate_range": {
            "min": min_rate,
            "min_pct": f"{min_rate * 100:.1f}%",
            "max": max_rate,
            "max_pct": f"{max_rate * 100:.1f}%"
        } if has_variations else None,
        "sub_positions_count": len(sub_positions),
        "sub_positions": sub_positions
    }
