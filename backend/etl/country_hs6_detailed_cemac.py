"""
Tarifs douaniers avec SOUS-POSITIONS NATIONALES - CEMAC
Pays membres: Cameroun, RCA, Tchad, Congo, Gabon, Guinée Équatoriale

Base: Tarif Extérieur Commun (TEC) CEMAC
Sources: Commission CEMAC, Administrations douanières nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# CAMEROUN (CMR) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Cameroun
# =============================================================================

CMR_HS6_DETAILED = {
    # VÉHICULES - Taxation par âge
    "870321": {
        "default_dd": 0.30,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.30, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.45, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703239000": {"dd": 0.60, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.45, "description_fr": "Voitures occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.35, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # PÉTROLE - Producteur majeur
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut Doba", "description_en": "Doba crude oil"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole brut Kribi", "description_en": "Kribi crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # CACAO
    "180100": {
        "default_dd": 0.00,
        "description_fr": "Cacao en fèves",
        "description_en": "Cocoa beans",
        "sub_positions": {
            "1801001000": {"dd": 0.00, "description_fr": "Fèves cacao grade 1", "description_en": "Grade 1 cocoa beans"},
            "1801002000": {"dd": 0.00, "description_fr": "Fèves cacao grade 2", "description_en": "Grade 2 cocoa beans"},
            "1801009000": {"dd": 0.00, "description_fr": "Autres fèves cacao", "description_en": "Other cocoa beans"},
        }
    },
    # BOIS - Premier exportateur
    "440320": {
        "default_dd": 0.00,
        "description_fr": "Bois bruts traités",
        "description_en": "Treated rough wood",
        "sub_positions": {
            "4403201000": {"dd": 0.00, "description_fr": "Grumes Azobé", "description_en": "Azobe logs"},
            "4403202000": {"dd": 0.00, "description_fr": "Grumes Iroko", "description_en": "Iroko logs"},
            "4403203000": {"dd": 0.00, "description_fr": "Grumes Sapelli", "description_en": "Sapelli logs"},
            "4403209000": {"dd": 0.00, "description_fr": "Autres grumes", "description_en": "Other logs"},
        }
    },
    # ALUMINIUM - Transformation locale
    "760110": {
        "default_dd": 0.00,
        "description_fr": "Aluminium non allié",
        "description_en": "Non-alloyed aluminum",
        "sub_positions": {
            "7601101000": {"dd": 0.00, "description_fr": "Aluminium ALUCAM", "description_en": "ALUCAM aluminum"},
            "7601109000": {"dd": 0.05, "description_fr": "Autre aluminium", "description_en": "Other aluminum"},
        }
    },
    # BANANES
    "080390": {
        "default_dd": 0.00,
        "description_fr": "Bananes fraîches/séchées",
        "description_en": "Fresh/dried bananas",
        "sub_positions": {
            "0803901000": {"dd": 0.00, "description_fr": "Bananes dessert export", "description_en": "Export dessert bananas"},
            "0803909000": {"dd": 0.00, "description_fr": "Autres bananes", "description_en": "Other bananas"},
        }
    },
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café non torréfié non décaféiné",
        "description_en": "Coffee not roasted not decaffeinated",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Arabica", "description_en": "Arabica coffee"},
            "0901112000": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café vert", "description_en": "Other green coffee"},
        }
    },
    # RIZ - Import
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.05, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.10, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
            "1006303000": {"dd": 0.10, "description_fr": "Riz parfumé", "description_en": "Fragrant rice"},
        }
    },
    # CIMENT
    "252329": {
        "default_dd": 0.30,
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.30, "description_fr": "Ciment Dangote/Cimencam", "description_en": "Dangote/Cimencam cement"},
            "2523299000": {"dd": 0.30, "description_fr": "Autre ciment importé", "description_en": "Other imported cement"},
        }
    },
}

# =============================================================================
# RÉPUBLIQUE CENTRAFRICAINE (CAF) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes RCA
# =============================================================================

CAF_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # DIAMANTS - Export principal
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants non industriels bruts",
        "description_en": "Non-industrial rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants certifiés Kimberley", "description_en": "Kimberley certified diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants bruts", "description_en": "Other rough diamonds"},
        }
    },
    # BOIS
    "440320": {
        "default_dd": 0.00,
        "description_fr": "Bois bruts traités",
        "description_en": "Treated rough wood",
        "sub_positions": {
            "4403201000": {"dd": 0.00, "description_fr": "Grumes Ayous", "description_en": "Ayous logs"},
            "4403209000": {"dd": 0.00, "description_fr": "Autres grumes", "description_en": "Other logs"},
        }
    },
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café non torréfié",
        "description_en": "Coffee not roasted",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café vert", "description_en": "Other green coffee"},
        }
    },
    # COTON
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton brut",
        "description_en": "Raw cotton",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton fibre SOCOCA", "description_en": "SOCOCA cotton fiber"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton", "description_en": "Other cotton"},
        }
    },
}

# =============================================================================
# TCHAD (TCD) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Tchad
# =============================================================================

TCD_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # PÉTROLE - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Doba", "description_en": "Doba crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # COTON
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton brut",
        "description_en": "Raw cotton",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton fibre CotonTchad", "description_en": "CotonTchad cotton fiber"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton", "description_en": "Other cotton"},
        }
    },
    # GOMME ARABIQUE - Leader mondial
    "130120": {
        "default_dd": 0.00,
        "description_fr": "Gomme arabique",
        "description_en": "Gum arabic",
        "sub_positions": {
            "1301201000": {"dd": 0.00, "description_fr": "Gomme arabique dure (Hashab)", "description_en": "Hard gum arabic (Hashab)"},
            "1301202000": {"dd": 0.00, "description_fr": "Gomme arabique friable (Talha)", "description_en": "Friable gum arabic (Talha)"},
            "1301209000": {"dd": 0.00, "description_fr": "Autre gomme arabique", "description_en": "Other gum arabic"},
        }
    },
    # BÉTAIL
    "010290": {
        "default_dd": 0.05,
        "description_fr": "Bovins vivants",
        "description_en": "Live cattle",
        "sub_positions": {
            "0102901000": {"dd": 0.05, "description_fr": "Bovins d'élevage", "description_en": "Breeding cattle"},
            "0102909000": {"dd": 0.05, "description_fr": "Bovins de boucherie", "description_en": "Cattle for slaughter"},
        }
    },
}

# =============================================================================
# CONGO-BRAZZAVILLE (COG) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Congo
# =============================================================================

COG_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # PÉTROLE - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut Djeno", "description_en": "Djeno crude oil"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole brut Nkossa", "description_en": "Nkossa crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # BOIS
    "440320": {
        "default_dd": 0.00,
        "description_fr": "Bois bruts traités",
        "description_en": "Treated rough wood",
        "sub_positions": {
            "4403201000": {"dd": 0.00, "description_fr": "Grumes Okoumé", "description_en": "Okoume logs"},
            "4403202000": {"dd": 0.00, "description_fr": "Grumes Sapelli", "description_en": "Sapelli logs"},
            "4403209000": {"dd": 0.00, "description_fr": "Autres grumes", "description_en": "Other logs"},
        }
    },
    # POTASSE
    "310420": {
        "default_dd": 0.00,
        "description_fr": "Chlorure de potassium",
        "description_en": "Potassium chloride",
        "sub_positions": {
            "3104201000": {"dd": 0.00, "description_fr": "Potasse Kongo", "description_en": "Kongo potash"},
            "3104209000": {"dd": 0.05, "description_fr": "Autre potasse", "description_en": "Other potash"},
        }
    },
    # SUCRE
    "170199": {
        "default_dd": 0.30,
        "description_fr": "Sucre de canne raffiné",
        "description_en": "Refined cane sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.20, "description_fr": "Sucre SARIS local", "description_en": "SARIS local sugar"},
            "1701999000": {"dd": 0.30, "description_fr": "Sucre importé", "description_en": "Imported sugar"},
        }
    },
}

# =============================================================================
# GABON (GAB) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Gabon
# =============================================================================

GAB_HS6_DETAILED = {
    # VÉHICULES
    "870321": {
        "default_dd": 0.30,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.30, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.45, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.40, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # PÉTROLE - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Rabi", "description_en": "Rabi crude oil"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole Gamba", "description_en": "Gamba crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # MANGANÈSE - Premier exportateur
    "260200": {
        "default_dd": 0.00,
        "description_fr": "Minerais de manganèse",
        "description_en": "Manganese ores",
        "sub_positions": {
            "2602001000": {"dd": 0.00, "description_fr": "Minerai Mn haute teneur COMILOG", "description_en": "COMILOG high grade Mn ore"},
            "2602009000": {"dd": 0.00, "description_fr": "Autre minerai manganèse", "description_en": "Other manganese ore"},
        }
    },
    # BOIS - Okoumé
    "440341": {
        "default_dd": 0.00,
        "description_fr": "Bois tropicaux Okoumé",
        "description_en": "Tropical wood Okoume",
        "sub_positions": {
            "4403411000": {"dd": 0.00, "description_fr": "Grumes Okoumé FSC", "description_en": "FSC Okoume logs"},
            "4403419000": {"dd": 0.00, "description_fr": "Autres grumes Okoumé", "description_en": "Other Okoume logs"},
        }
    },
    # HUILE DE PALME
    "151110": {
        "default_dd": 0.10,
        "description_fr": "Huile de palme brute",
        "description_en": "Crude palm oil",
        "sub_positions": {
            "1511101000": {"dd": 0.05, "description_fr": "Huile OLAM locale", "description_en": "Local OLAM oil"},
            "1511109000": {"dd": 0.10, "description_fr": "Huile palme importée", "description_en": "Imported palm oil"},
        }
    },
}

# =============================================================================
# GUINÉE ÉQUATORIALE (GNQ) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Dirección General de Aduanas
# =============================================================================

GNQ_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.30,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.30, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # PÉTROLE - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Zafiro", "description_en": "Zafiro crude oil"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole Ceiba", "description_en": "Ceiba crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # GAZ NATUREL LIQUÉFIÉ
    "271111": {
        "default_dd": 0.00,
        "description_fr": "Gaz naturel liquéfié",
        "description_en": "Liquefied natural gas",
        "sub_positions": {
            "2711110010": {"dd": 0.00, "description_fr": "GNL EG LNG", "description_en": "EG LNG"},
            "2711110090": {"dd": 0.00, "description_fr": "Autre GNL", "description_en": "Other LNG"},
        }
    },
    # BOIS
    "440341": {
        "default_dd": 0.00,
        "description_fr": "Bois tropicaux",
        "description_en": "Tropical wood",
        "sub_positions": {
            "4403411000": {"dd": 0.00, "description_fr": "Grumes Okoumé", "description_en": "Okoume logs"},
            "4403419000": {"dd": 0.00, "description_fr": "Autres grumes tropicaux", "description_en": "Other tropical logs"},
        }
    },
    # MÉTHANOL
    "290511": {
        "default_dd": 0.00,
        "description_fr": "Méthanol",
        "description_en": "Methanol",
        "sub_positions": {
            "2905110010": {"dd": 0.00, "description_fr": "Méthanol AMPCO", "description_en": "AMPCO methanol"},
            "2905110090": {"dd": 0.05, "description_fr": "Autre méthanol", "description_en": "Other methanol"},
        }
    },
}

# =============================================================================
# RDC (COD) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes et Accises (DGDA)
# =============================================================================

COD_HS6_DETAILED = {
    # VÉHICULES
    "870321": {
        "default_dd": 0.25,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.25, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures occasion <10 ans", "description_en": "Used cars <10 years"},
        }
    },
    # CUIVRE - Principal export
    "260300": {
        "default_dd": 0.00,
        "description_fr": "Minerais de cuivre",
        "description_en": "Copper ores",
        "sub_positions": {
            "2603001000": {"dd": 0.00, "description_fr": "Concentré cuivre Katanga", "description_en": "Katanga copper concentrate"},
            "2603009000": {"dd": 0.00, "description_fr": "Autre minerai cuivre", "description_en": "Other copper ore"},
        }
    },
    # COBALT - Leader mondial
    "810520": {
        "default_dd": 0.00,
        "description_fr": "Cobalt et articles en cobalt",
        "description_en": "Cobalt and cobalt articles",
        "sub_positions": {
            "8105201000": {"dd": 0.00, "description_fr": "Hydroxyde de cobalt", "description_en": "Cobalt hydroxide"},
            "8105202000": {"dd": 0.00, "description_fr": "Cobalt métal", "description_en": "Cobalt metal"},
            "8105209000": {"dd": 0.00, "description_fr": "Autre cobalt", "description_en": "Other cobalt"},
        }
    },
    # COLTAN
    "261590": {
        "default_dd": 0.00,
        "description_fr": "Minerais de niobium/tantale",
        "description_en": "Niobium/tantalum ores",
        "sub_positions": {
            "2615901000": {"dd": 0.00, "description_fr": "Coltan certifié ITSCI", "description_en": "ITSCI certified coltan"},
            "2615909000": {"dd": 0.00, "description_fr": "Autre coltan", "description_en": "Other coltan"},
        }
    },
    # DIAMANTS
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants bruts",
        "description_en": "Rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants MIBA", "description_en": "MIBA diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants", "description_en": "Other diamonds"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café non torréfié",
        "description_en": "Coffee not roasted",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Arabica Kivu", "description_en": "Kivu Arabica coffee"},
            "0901112000": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
    # BOIS
    "440320": {
        "default_dd": 0.00,
        "description_fr": "Bois bruts",
        "description_en": "Rough wood",
        "sub_positions": {
            "4403201000": {"dd": 0.00, "description_fr": "Grumes Wenge", "description_en": "Wenge logs"},
            "4403202000": {"dd": 0.00, "description_fr": "Grumes Afrormosia", "description_en": "Afrormosia logs"},
            "4403209000": {"dd": 0.00, "description_fr": "Autres grumes", "description_en": "Other logs"},
        }
    },
}

# =============================================================================
# SÃO TOMÉ ET PRÍNCIPE (STP) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Alfândegas de São Tomé
# =============================================================================

STP_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.30, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # CACAO - Export principal
    "180100": {
        "default_dd": 0.00,
        "description_fr": "Cacao en fèves",
        "description_en": "Cocoa beans",
        "sub_positions": {
            "1801001000": {"dd": 0.00, "description_fr": "Cacao fin de saveur", "description_en": "Fine flavor cocoa"},
            "1801009000": {"dd": 0.00, "description_fr": "Autre cacao", "description_en": "Other cocoa"},
        }
    },
    # HUILE DE PALME
    "151110": {
        "default_dd": 0.10,
        "description_fr": "Huile de palme",
        "description_en": "Palm oil",
        "sub_positions": {
            "1511101000": {"dd": 0.05, "description_fr": "Huile palme locale", "description_en": "Local palm oil"},
            "1511109000": {"dd": 0.10, "description_fr": "Huile palme importée", "description_en": "Imported palm oil"},
        }
    },
}

# =============================================================================
# DICTIONNAIRE UNIFIÉ CEMAC + RDC + STP
# =============================================================================

CEMAC_HS6_DETAILED = {
    "CMR": CMR_HS6_DETAILED,
    "CAF": CAF_HS6_DETAILED,
    "TCD": TCD_HS6_DETAILED,
    "COG": COG_HS6_DETAILED,
    "GAB": GAB_HS6_DETAILED,
    "GNQ": GNQ_HS6_DETAILED,
    "COD": COD_HS6_DETAILED,
    "STP": STP_HS6_DETAILED,
}
