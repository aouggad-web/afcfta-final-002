"""
Tarifs douaniers avec SOUS-POSITIONS NATIONALES - Afrique du Nord (UMA)
Pays: Algérie, Égypte, Libye, Maroc, Tunisie, Soudan, Mauritanie

Sources: Administrations douanières nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# ALGÉRIE (DZA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes Algériennes
# =============================================================================

DZA_HS6_DETAILED = {
    # VÉHICULES - Restriction importations
    "870321": {
        "default_dd": 0.30,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.30, "description_fr": "Voitures ≤1000cc neuves CKD", "description_en": "New CKD cars ≤1000cc"},
            "8703212000": {"dd": 0.30, "description_fr": "Voitures ≤1000cc neuves CBU", "description_en": "New CBU cars ≤1000cc"},
            "8703219000": {"dd": 0.50, "description_fr": "Voitures ≤1000cc occasion (interdit)", "description_en": "Used cars ≤1000cc (prohibited)"},
        }
    },
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves CKD montage local", "description_en": "New CKD local assembly"},
            "8703232000": {"dd": 0.30, "description_fr": "Voitures neuves CBU", "description_en": "New CBU cars"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures occasion (interdit)", "description_en": "Used cars (prohibited)"},
        }
    },
    # PÉTROLE ET GAZ - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Saharan Blend", "description_en": "Saharan Blend"},
            "2709002000": {"dd": 0.00, "description_fr": "Condensat", "description_en": "Condensate"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    "271111": {
        "default_dd": 0.00,
        "description_fr": "Gaz naturel liquéfié",
        "description_en": "Liquefied natural gas",
        "sub_positions": {
            "2711110010": {"dd": 0.00, "description_fr": "GNL Sonatrach", "description_en": "Sonatrach LNG"},
            "2711110090": {"dd": 0.00, "description_fr": "Autre GNL", "description_en": "Other LNG"},
        }
    },
    # ENGRAIS - Secteur fort
    "310210": {
        "default_dd": 0.00,
        "description_fr": "Urée",
        "description_en": "Urea",
        "sub_positions": {
            "3102101000": {"dd": 0.00, "description_fr": "Urée Sorfert/Fertial", "description_en": "Sorfert/Fertial urea"},
            "3102109000": {"dd": 0.05, "description_fr": "Autre urée", "description_en": "Other urea"},
        }
    },
    # PHOSPHATES
    "253110": {
        "default_dd": 0.00,
        "description_fr": "Phosphates naturels",
        "description_en": "Natural phosphates",
        "sub_positions": {
            "2531101000": {"dd": 0.00, "description_fr": "Phosphate Djebel Onk", "description_en": "Djebel Onk phosphate"},
            "2531109000": {"dd": 0.00, "description_fr": "Autre phosphate", "description_en": "Other phosphate"},
        }
    },
    # DATTES
    "080410": {
        "default_dd": 0.00,
        "description_fr": "Dattes fraîches",
        "description_en": "Fresh dates",
        "sub_positions": {
            "0804101000": {"dd": 0.00, "description_fr": "Deglet Nour premium", "description_en": "Premium Deglet Nour"},
            "0804102000": {"dd": 0.00, "description_fr": "Deglet Nour standard", "description_en": "Standard Deglet Nour"},
            "0804109000": {"dd": 0.00, "description_fr": "Autres dattes", "description_en": "Other dates"},
        }
    },
    # CIMENT - Surproduction
    "252329": {
        "default_dd": 0.30,
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.15, "description_fr": "Ciment GICA local", "description_en": "Local GICA cement"},
            "2523299000": {"dd": 0.30, "description_fr": "Ciment importé", "description_en": "Imported cement"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.05,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.05, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
            "1006309000": {"dd": 0.05, "description_fr": "Autre riz", "description_en": "Other rice"},
        }
    },
}

# =============================================================================
# ÉGYPTE (EGY) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Egyptian Customs Authority
# =============================================================================

EGY_HS6_DETAILED = {
    # VÉHICULES - Production locale forte
    "870321": {
        "default_dd": 0.40,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.40, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703219000": {"dd": 0.55, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "870323": {
        "default_dd": 0.40,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.40, "description_fr": "Voitures neuves assemblage local", "description_en": "Local assembly new cars"},
            "8703232000": {"dd": 0.40, "description_fr": "Voitures neuves import", "description_en": "Imported new cars"},
            "8703239000": {"dd": 0.70, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.55, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # PÉTROLE ET GAZ
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut Belayim", "description_en": "Belayim crude"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude"},
        }
    },
    "271121": {
        "default_dd": 0.00,
        "description_fr": "Gaz naturel",
        "description_en": "Natural gas",
        "sub_positions": {
            "2711210010": {"dd": 0.00, "description_fr": "GNL Idku/Damiette", "description_en": "Idku/Damiette LNG"},
            "2711210090": {"dd": 0.00, "description_fr": "Autre gaz naturel", "description_en": "Other natural gas"},
        }
    },
    # TEXTILES - Industrie forte
    "520100": {
        "default_dd": 0.00,
        "description_fr": "Coton brut",
        "description_en": "Raw cotton",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton Giza extra longue soie", "description_en": "Giza extra long staple cotton"},
            "5201002000": {"dd": 0.00, "description_fr": "Coton Giza longue soie", "description_en": "Giza long staple cotton"},
            "5201009000": {"dd": 0.00, "description_fr": "Autre coton égyptien", "description_en": "Other Egyptian cotton"},
        }
    },
    # ORANGES
    "080510": {
        "default_dd": 0.00,
        "description_fr": "Oranges fraîches",
        "description_en": "Fresh oranges",
        "sub_positions": {
            "0805101000": {"dd": 0.00, "description_fr": "Oranges Valencia export", "description_en": "Valencia oranges export"},
            "0805102000": {"dd": 0.00, "description_fr": "Oranges Navel", "description_en": "Navel oranges"},
            "0805109000": {"dd": 0.00, "description_fr": "Autres oranges", "description_en": "Other oranges"},
        }
    },
    # ENGRAIS
    "310520": {
        "default_dd": 0.00,
        "description_fr": "Engrais azotés",
        "description_en": "Nitrogenous fertilizers",
        "sub_positions": {
            "3105201000": {"dd": 0.00, "description_fr": "Engrais Abu Qir", "description_en": "Abu Qir fertilizers"},
            "3105209000": {"dd": 0.05, "description_fr": "Autres engrais", "description_en": "Other fertilizers"},
        }
    },
    # RIZ - Production et import
    "100630": {
        "default_dd": 0.05,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.00, "description_fr": "Riz local", "description_en": "Local rice"},
            "1006302000": {"dd": 0.05, "description_fr": "Riz importé", "description_en": "Imported rice"},
        }
    },
}

# =============================================================================
# LIBYE (LBY) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Libyan Customs Authority
# =============================================================================

LBY_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.15,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.15, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.30, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # PÉTROLE - Export quasi exclusif
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Es Sider Light", "description_en": "Es Sider Light"},
            "2709002000": {"dd": 0.00, "description_fr": "El Sharara", "description_en": "El Sharara"},
            "2709003000": {"dd": 0.00, "description_fr": "Brega", "description_en": "Brega"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
}

# =============================================================================
# MAROC (MAR) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Administration des Douanes et Impôts Indirects
# =============================================================================

MAR_HS6_DETAILED = {
    # VÉHICULES - Industrie automobile développée
    "870321": {
        "default_dd": 0.25,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.17, "description_fr": "Voitures neuves CKD Renault/PSA", "description_en": "New CKD Renault/PSA"},
            "8703212000": {"dd": 0.25, "description_fr": "Voitures neuves CBU", "description_en": "New CBU cars"},
            "8703219000": {"dd": 0.40, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
        }
    },
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.17, "description_fr": "Voitures neuves montage local", "description_en": "Local assembly new cars"},
            "8703232000": {"dd": 0.25, "description_fr": "Voitures neuves import", "description_en": "Imported new cars"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.40, "description_fr": "Voitures occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.30, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # AUTOMOBILES - Export
    "870332": {
        "default_dd": 0.00,
        "description_fr": "Voitures diesel >1500cc",
        "description_en": "Diesel cars >1500cc",
        "sub_positions": {
            "8703321000": {"dd": 0.00, "description_fr": "Dacia Sandero/Logan export", "description_en": "Dacia Sandero/Logan export"},
            "8703329000": {"dd": 0.00, "description_fr": "Autres véhicules export", "description_en": "Other export vehicles"},
        }
    },
    # PHOSPHATES - Leader mondial
    "253110": {
        "default_dd": 0.00,
        "description_fr": "Phosphates naturels",
        "description_en": "Natural phosphates",
        "sub_positions": {
            "2531101000": {"dd": 0.00, "description_fr": "Phosphate OCP Khouribga", "description_en": "OCP Khouribga phosphate"},
            "2531102000": {"dd": 0.00, "description_fr": "Phosphate OCP Gantour", "description_en": "OCP Gantour phosphate"},
            "2531109000": {"dd": 0.00, "description_fr": "Autre phosphate", "description_en": "Other phosphate"},
        }
    },
    # ENGRAIS - Transformation
    "310520": {
        "default_dd": 0.00,
        "description_fr": "Engrais phosphatés",
        "description_en": "Phosphatic fertilizers",
        "sub_positions": {
            "3105201000": {"dd": 0.00, "description_fr": "DAP OCP", "description_en": "OCP DAP"},
            "3105202000": {"dd": 0.00, "description_fr": "MAP OCP", "description_en": "OCP MAP"},
            "3105203000": {"dd": 0.00, "description_fr": "TSP OCP", "description_en": "OCP TSP"},
            "3105209000": {"dd": 0.00, "description_fr": "Autres engrais OCP", "description_en": "Other OCP fertilizers"},
        }
    },
    # TEXTILES
    "610910": {
        "default_dd": 0.25,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.00, "description_fr": "T-shirts zones franches export", "description_en": "Free zone export T-shirts"},
            "6109109000": {"dd": 0.25, "description_fr": "Autres T-shirts", "description_en": "Other T-shirts"},
        }
    },
    # TOMATES
    "070200": {
        "default_dd": 0.00,
        "description_fr": "Tomates fraîches",
        "description_en": "Fresh tomatoes",
        "sub_positions": {
            "0702001000": {"dd": 0.00, "description_fr": "Tomates cerises export", "description_en": "Cherry tomatoes export"},
            "0702002000": {"dd": 0.00, "description_fr": "Tomates grappe", "description_en": "Vine tomatoes"},
            "0702009000": {"dd": 0.00, "description_fr": "Autres tomates", "description_en": "Other tomatoes"},
        }
    },
    # AGRUMES
    "080520": {
        "default_dd": 0.00,
        "description_fr": "Mandarines, clémentines",
        "description_en": "Mandarins, clementines",
        "sub_positions": {
            "0805201000": {"dd": 0.00, "description_fr": "Clémentines export", "description_en": "Clementines export"},
            "0805209000": {"dd": 0.00, "description_fr": "Autres agrumes", "description_en": "Other citrus"},
        }
    },
    # POISSON
    "030389": {
        "default_dd": 0.00,
        "description_fr": "Poissons congelés",
        "description_en": "Frozen fish",
        "sub_positions": {
            "0303891000": {"dd": 0.00, "description_fr": "Sardines congelées", "description_en": "Frozen sardines"},
            "0303892000": {"dd": 0.00, "description_fr": "Poulpe congelé", "description_en": "Frozen octopus"},
            "0303899000": {"dd": 0.00, "description_fr": "Autre poisson congelé", "description_en": "Other frozen fish"},
        }
    },
}

# =============================================================================
# TUNISIE (TUN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes Tunisiennes
# =============================================================================

TUN_HS6_DETAILED = {
    # VÉHICULES
    "870321": {
        "default_dd": 0.30,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703219000": {"dd": 0.50, "description_fr": "Voitures occasion (interdit)", "description_en": "Used cars (prohibited)"},
        }
    },
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures occasion (interdit)", "description_en": "Used cars (prohibited)"},
        }
    },
    # HUILE D'OLIVE - Premier export agricole
    "150910": {
        "default_dd": 0.00,
        "description_fr": "Huile d'olive vierge",
        "description_en": "Virgin olive oil",
        "sub_positions": {
            "1509101000": {"dd": 0.00, "description_fr": "Extra vierge export bio", "description_en": "Organic extra virgin export"},
            "1509102000": {"dd": 0.00, "description_fr": "Extra vierge export conventionnel", "description_en": "Conventional extra virgin export"},
            "1509103000": {"dd": 0.00, "description_fr": "Huile vierge bulk", "description_en": "Bulk virgin oil"},
            "1509109000": {"dd": 0.00, "description_fr": "Autre huile olive", "description_en": "Other olive oil"},
        }
    },
    # DATTES
    "080410": {
        "default_dd": 0.00,
        "description_fr": "Dattes fraîches",
        "description_en": "Fresh dates",
        "sub_positions": {
            "0804101000": {"dd": 0.00, "description_fr": "Deglet Nour premium", "description_en": "Premium Deglet Nour"},
            "0804102000": {"dd": 0.00, "description_fr": "Deglet Nour branchées", "description_en": "Branched Deglet Nour"},
            "0804109000": {"dd": 0.00, "description_fr": "Autres dattes", "description_en": "Other dates"},
        }
    },
    # TEXTILES - Zones franches
    "610910": {
        "default_dd": 0.30,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.00, "description_fr": "Textiles offshore export", "description_en": "Offshore export textiles"},
            "6109109000": {"dd": 0.30, "description_fr": "Autres textiles", "description_en": "Other textiles"},
        }
    },
    # CÂBLES ET COMPOSANTS AUTO
    "854430": {
        "default_dd": 0.00,
        "description_fr": "Jeux de fils pour véhicules",
        "description_en": "Wiring sets for vehicles",
        "sub_positions": {
            "8544301000": {"dd": 0.00, "description_fr": "Câblage auto export UE", "description_en": "EU export auto wiring"},
            "8544309000": {"dd": 0.10, "description_fr": "Autre câblage", "description_en": "Other wiring"},
        }
    },
    # PHOSPHATES
    "253110": {
        "default_dd": 0.00,
        "description_fr": "Phosphates naturels",
        "description_en": "Natural phosphates",
        "sub_positions": {
            "2531101000": {"dd": 0.00, "description_fr": "Phosphate CPG Gafsa", "description_en": "CPG Gafsa phosphate"},
            "2531109000": {"dd": 0.00, "description_fr": "Autre phosphate", "description_en": "Other phosphate"},
        }
    },
}

# =============================================================================
# SOUDAN (SDN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Sudan Customs Authority
# =============================================================================

SDN_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # OR - Principal export
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120020": {"dd": 0.00, "description_fr": "Or artisanal", "description_en": "Artisanal gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # PÉTROLE
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Nile Blend", "description_en": "Nile Blend crude"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # GOMME ARABIQUE - Leader mondial
    "130120": {
        "default_dd": 0.00,
        "description_fr": "Gomme arabique",
        "description_en": "Gum arabic",
        "sub_positions": {
            "1301201000": {"dd": 0.00, "description_fr": "Gomme arabique Hashab", "description_en": "Hashab gum arabic"},
            "1301202000": {"dd": 0.00, "description_fr": "Gomme arabique Talha", "description_en": "Talha gum arabic"},
            "1301209000": {"dd": 0.00, "description_fr": "Autre gomme arabique", "description_en": "Other gum arabic"},
        }
    },
    # SÉSAME
    "120740": {
        "default_dd": 0.00,
        "description_fr": "Graines de sésame",
        "description_en": "Sesame seeds",
        "sub_positions": {
            "1207401000": {"dd": 0.00, "description_fr": "Sésame blanc", "description_en": "White sesame"},
            "1207402000": {"dd": 0.00, "description_fr": "Sésame rouge", "description_en": "Red sesame"},
            "1207409000": {"dd": 0.00, "description_fr": "Autre sésame", "description_en": "Other sesame"},
        }
    },
    # BÉTAIL
    "010290": {
        "default_dd": 0.00,
        "description_fr": "Bovins vivants",
        "description_en": "Live cattle",
        "sub_positions": {
            "0102901000": {"dd": 0.00, "description_fr": "Bovins export Golfe", "description_en": "Cattle for Gulf export"},
            "0102909000": {"dd": 0.00, "description_fr": "Autres bovins", "description_en": "Other cattle"},
        }
    },
}

# =============================================================================
# MAURITANIE (MRT) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes de Mauritanie
# =============================================================================

MRT_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.35, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # MINERAI DE FER - Principal export
    "260111": {
        "default_dd": 0.00,
        "description_fr": "Minerais de fer",
        "description_en": "Iron ores",
        "sub_positions": {
            "2601111000": {"dd": 0.00, "description_fr": "Minerai fer SNIM Zouerate", "description_en": "SNIM Zouerate iron ore"},
            "2601119000": {"dd": 0.00, "description_fr": "Autre minerai fer", "description_en": "Other iron ore"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or Tasiast", "description_en": "Tasiast gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # POISSON
    "030389": {
        "default_dd": 0.00,
        "description_fr": "Poissons congelés",
        "description_en": "Frozen fish",
        "sub_positions": {
            "0303891000": {"dd": 0.00, "description_fr": "Poulpe congelé", "description_en": "Frozen octopus"},
            "0303892000": {"dd": 0.00, "description_fr": "Céphalopodes congelés", "description_en": "Frozen cephalopods"},
            "0303899000": {"dd": 0.00, "description_fr": "Autre poisson congelé", "description_en": "Other frozen fish"},
        }
    },
    # CUIVRE
    "260300": {
        "default_dd": 0.00,
        "description_fr": "Minerais de cuivre",
        "description_en": "Copper ores",
        "sub_positions": {
            "2603001000": {"dd": 0.00, "description_fr": "Concentré cuivre MCM", "description_en": "MCM copper concentrate"},
            "2603009000": {"dd": 0.00, "description_fr": "Autre minerai cuivre", "description_en": "Other copper ore"},
        }
    },
}

# =============================================================================
# DICTIONNAIRE UNIFIÉ AFRIQUE DU NORD
# =============================================================================

NORTH_AFRICA_HS6_DETAILED = {
    "DZA": DZA_HS6_DETAILED,
    "EGY": EGY_HS6_DETAILED,
    "LBY": LBY_HS6_DETAILED,
    "MAR": MAR_HS6_DETAILED,
    "TUN": TUN_HS6_DETAILED,
    "SDN": SDN_HS6_DETAILED,
    "MRT": MRT_HS6_DETAILED,
}
