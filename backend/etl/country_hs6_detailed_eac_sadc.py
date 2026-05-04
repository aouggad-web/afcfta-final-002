"""
Tarifs douaniers avec SOUS-POSITIONS NATIONALES - EAC, COMESA, SADC
Pays: Tanzanie, Ouganda, Rwanda, Burundi, Soudan du Sud (EAC)
      Éthiopie, Érythrée, Djibouti, Somalie, Comores, Madagascar, Maurice, Seychelles, Malawi, Zambie, Zimbabwe, Mozambique (COMESA/SADC)
      Botswana, Namibie, Lesotho, Eswatini (SACU avec Afrique du Sud)
      Angola (SADC)

Sources: EAC Secretariat, SADC Secretariat, Administrations douanières nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# TANZANIE (TZA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Tanzania Revenue Authority
# =============================================================================

TZA_HS6_DETAILED = {
    # VÉHICULES - Taxation par âge stricte
    "870321": {
        "default_dd": 0.25,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.25, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # OR - Premier export
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Arabica Kilimandjaro", "description_en": "Kilimanjaro Arabica"},
            "0901112000": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
    # NOIX DE CAJOU
    "080131": {
        "default_dd": 0.00,
        "description_fr": "Noix de cajou",
        "description_en": "Cashew nuts",
        "sub_positions": {
            "0801311000": {"dd": 0.00, "description_fr": "Cajou brut export", "description_en": "Raw cashew export"},
            "0801319000": {"dd": 0.00, "description_fr": "Autre cajou", "description_en": "Other cashew"},
        }
    },
    # COTON
    "520100": {
        "default_dd": 0.00,
        "description_fr": "Coton brut",
        "description_en": "Raw cotton",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton fibre export", "description_en": "Export cotton fiber"},
            "5201009000": {"dd": 0.00, "description_fr": "Autre coton", "description_en": "Other cotton"},
        }
    },
    # TABAC
    "240110": {
        "default_dd": 0.00,
        "description_fr": "Tabac brut",
        "description_en": "Raw tobacco",
        "sub_positions": {
            "2401101000": {"dd": 0.00, "description_fr": "Tabac Virginia", "description_en": "Virginia tobacco"},
            "2401109000": {"dd": 0.00, "description_fr": "Autre tabac", "description_en": "Other tobacco"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.75,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.50, "description_fr": "Riz local", "description_en": "Local rice"},
            "1006302000": {"dd": 0.75, "description_fr": "Riz importé", "description_en": "Imported rice"},
        }
    },
}

# =============================================================================
# OUGANDA (UGA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Uganda Revenue Authority
# =============================================================================

UGA_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion >8 ans", "description_en": "Used cars >8 years"},
            "8703239100": {"dd": 0.30, "description_fr": "Voitures occasion <8 ans", "description_en": "Used cars <8 years"},
        }
    },
    # CAFÉ - Premier export
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Arabica Bugisu", "description_en": "Bugisu Arabica"},
            "0901112000": {"dd": 0.00, "description_fr": "Café Robusta", "description_en": "Robusta coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # POISSON - Tilapia/Perche du Nil
    "030489": {
        "default_dd": 0.00,
        "description_fr": "Filets de poisson congelés",
        "description_en": "Frozen fish fillets",
        "sub_positions": {
            "0304891000": {"dd": 0.00, "description_fr": "Filets perche du Nil", "description_en": "Nile perch fillets"},
            "0304899000": {"dd": 0.00, "description_fr": "Autres filets", "description_en": "Other fillets"},
        }
    },
    # SUCRE
    "170199": {
        "default_dd": 0.100,
        "description_fr": "Sucre",
        "description_en": "Sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.35, "description_fr": "Sucre SCOUL local", "description_en": "SCOUL local sugar"},
            "1701999000": {"dd": 0.100, "description_fr": "Sucre importé", "description_en": "Imported sugar"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.75,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.60, "description_fr": "Riz local", "description_en": "Local rice"},
            "1006302000": {"dd": 0.75, "description_fr": "Riz importé", "description_en": "Imported rice"},
        }
    },
}

# =============================================================================
# RWANDA (RWA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Rwanda Revenue Authority
# =============================================================================

RWA_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion >7 ans", "description_en": "Used cars >7 years"},
            "8703239100": {"dd": 0.30, "description_fr": "Voitures occasion <7 ans", "description_en": "Used cars <7 years"},
        }
    },
    # CAFÉ - Premium spécialité
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café spécialité Bourbon", "description_en": "Specialty Bourbon coffee"},
            "0901112000": {"dd": 0.00, "description_fr": "Café fully washed", "description_en": "Fully washed coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
    # THÉ
    "090230": {
        "default_dd": 0.00,
        "description_fr": "Thé noir",
        "description_en": "Black tea",
        "sub_positions": {
            "0902301000": {"dd": 0.00, "description_fr": "Thé noir orthodox", "description_en": "Orthodox black tea"},
            "0902302000": {"dd": 0.00, "description_fr": "Thé noir CTC", "description_en": "CTC black tea"},
            "0902309000": {"dd": 0.00, "description_fr": "Autre thé noir", "description_en": "Other black tea"},
        }
    },
    # MINERAIS - Tungstène, Étain, Tantale
    "261100": {
        "default_dd": 0.00,
        "description_fr": "Minerais de tungstène",
        "description_en": "Tungsten ores",
        "sub_positions": {
            "2611001000": {"dd": 0.00, "description_fr": "Wolframite 3T certifié", "description_en": "3T certified wolframite"},
            "2611009000": {"dd": 0.00, "description_fr": "Autre tungstène", "description_en": "Other tungsten"},
        }
    },
    # RIZ - Protection forte
    "100630": {
        "default_dd": 0.75,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.50, "description_fr": "Riz local", "description_en": "Local rice"},
            "1006302000": {"dd": 0.75, "description_fr": "Riz importé", "description_en": "Imported rice"},
        }
    },
}

# =============================================================================
# BURUNDI (BDI) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Office Burundais des Recettes
# =============================================================================

BDI_HS6_DETAILED = {
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
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Arabica fully washed", "description_en": "Fully washed Arabica"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
    # THÉ
    "090230": {
        "default_dd": 0.00,
        "description_fr": "Thé noir",
        "description_en": "Black tea",
        "sub_positions": {
            "0902301000": {"dd": 0.00, "description_fr": "Thé noir OTB", "description_en": "OTB black tea"},
            "0902309000": {"dd": 0.00, "description_fr": "Autre thé", "description_en": "Other tea"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
}

# =============================================================================
# SOUDAN DU SUD (SSD) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: South Sudan Customs Service
# =============================================================================

SSD_HS6_DETAILED = {
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
    # PÉTROLE - Principal export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Dar Blend", "description_en": "Dar Blend crude"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole Nile Blend", "description_en": "Nile Blend crude"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole", "description_en": "Other crude"},
        }
    },
}

# =============================================================================
# ÉTHIOPIE (ETH) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Ethiopian Customs Commission
# =============================================================================

ETH_HS6_DETAILED = {
    # VÉHICULES - Taxation stricte
    "870321": {
        "default_dd": 0.35,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.35, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703219000": {"dd": 0.50, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "870323": {
        "default_dd": 0.35,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.35, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.60, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.50, "description_fr": "Voitures occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.40, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # CAFÉ - Origine Arabica
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Yirgacheffe", "description_en": "Yirgacheffe coffee"},
            "0901112000": {"dd": 0.00, "description_fr": "Café Sidamo", "description_en": "Sidamo coffee"},
            "0901113000": {"dd": 0.00, "description_fr": "Café Harar", "description_en": "Harar coffee"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café éthiopien", "description_en": "Other Ethiopian coffee"},
        }
    },
    # FLEURS COUPÉES
    "060311": {
        "default_dd": 0.00,
        "description_fr": "Roses fraîches",
        "description_en": "Fresh roses",
        "sub_positions": {
            "0603111000": {"dd": 0.00, "description_fr": "Roses premium longue tige", "description_en": "Premium long-stem roses"},
            "0603112000": {"dd": 0.00, "description_fr": "Roses standard", "description_en": "Standard roses"},
            "0603119000": {"dd": 0.00, "description_fr": "Autres roses", "description_en": "Other roses"},
        }
    },
    # SÉSAME
    "120740": {
        "default_dd": 0.00,
        "description_fr": "Graines de sésame",
        "description_en": "Sesame seeds",
        "sub_positions": {
            "1207401000": {"dd": 0.00, "description_fr": "Sésame blanc Humera", "description_en": "Humera white sesame"},
            "1207402000": {"dd": 0.00, "description_fr": "Sésame rouge Wollega", "description_en": "Wollega red sesame"},
            "1207409000": {"dd": 0.00, "description_fr": "Autre sésame", "description_en": "Other sesame"},
        }
    },
    # LÉGUMINEUSES
    "071340": {
        "default_dd": 0.00,
        "description_fr": "Lentilles",
        "description_en": "Lentils",
        "sub_positions": {
            "0713401000": {"dd": 0.00, "description_fr": "Lentilles rouges", "description_en": "Red lentils"},
            "0713409000": {"dd": 0.00, "description_fr": "Autres lentilles", "description_en": "Other lentils"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # TEXTILES - Industrie croissante
    "610910": {
        "default_dd": 0.35,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.20, "description_fr": "T-shirts parcs industriels", "description_en": "Industrial park T-shirts"},
            "6109109000": {"dd": 0.35, "description_fr": "Autres T-shirts", "description_en": "Other T-shirts"},
        }
    },
}

# =============================================================================
# ÉRYTHRÉE (ERI) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Eritrean Customs Authority
# =============================================================================

ERI_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.35, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # OR ET CUIVRE - Secteur minier
    "260300": {
        "default_dd": 0.00,
        "description_fr": "Minerais de cuivre",
        "description_en": "Copper ores",
        "sub_positions": {
            "2603001000": {"dd": 0.00, "description_fr": "Concentré cuivre Bisha", "description_en": "Bisha copper concentrate"},
            "2603009000": {"dd": 0.00, "description_fr": "Autre minerai cuivre", "description_en": "Other copper ore"},
        }
    },
    # ZINC
    "260800": {
        "default_dd": 0.00,
        "description_fr": "Minerais de zinc",
        "description_en": "Zinc ores",
        "sub_positions": {
            "2608001000": {"dd": 0.00, "description_fr": "Concentré zinc", "description_en": "Zinc concentrate"},
            "2608009000": {"dd": 0.00, "description_fr": "Autre minerai zinc", "description_en": "Other zinc ore"},
        }
    },
}

# =============================================================================
# DJIBOUTI (DJI) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Administration des Douanes de Djibouti
# =============================================================================

DJI_HS6_DETAILED = {
    # VÉHICULES - Transit régional
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.30, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # SERVICES PORTUAIRES - Hub logistique
    "271019": {
        "default_dd": 0.05,
        "description_fr": "Produits pétroliers",
        "description_en": "Petroleum products",
        "sub_positions": {
            "2710191000": {"dd": 0.05, "description_fr": "Gasoil transit Éthiopie", "description_en": "Ethiopia transit diesel"},
            "2710192000": {"dd": 0.05, "description_fr": "Essence", "description_en": "Gasoline"},
        }
    },
    # SEL
    "250100": {
        "default_dd": 0.00,
        "description_fr": "Sel",
        "description_en": "Salt",
        "sub_positions": {
            "2501001000": {"dd": 0.00, "description_fr": "Sel Lac Assal", "description_en": "Lake Assal salt"},
            "2501009000": {"dd": 0.00, "description_fr": "Autre sel", "description_en": "Other salt"},
        }
    },
}

# =============================================================================
# SOMALIE (SOM) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Somalia Customs Authority
# =============================================================================

SOM_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.15,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.15, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # BÉTAIL - Principal export
    "010410": {
        "default_dd": 0.00,
        "description_fr": "Ovins vivants",
        "description_en": "Live sheep",
        "sub_positions": {
            "0104101000": {"dd": 0.00, "description_fr": "Moutons export Golfe", "description_en": "Sheep for Gulf export"},
            "0104109000": {"dd": 0.00, "description_fr": "Autres ovins", "description_en": "Other sheep"},
        }
    },
    # ENCENS ET MYRRHE
    "130190": {
        "default_dd": 0.00,
        "description_fr": "Gommes et résines",
        "description_en": "Gums and resins",
        "sub_positions": {
            "1301901000": {"dd": 0.00, "description_fr": "Encens Boswellia", "description_en": "Boswellia frankincense"},
            "1301902000": {"dd": 0.00, "description_fr": "Myrrhe", "description_en": "Myrrh"},
            "1301909000": {"dd": 0.00, "description_fr": "Autres résines", "description_en": "Other resins"},
        }
    },
}

# =============================================================================
# COMORES (COM) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes des Comores
# =============================================================================

COM_HS6_DETAILED = {
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
    # VANILLE
    "090510": {
        "default_dd": 0.00,
        "description_fr": "Vanille",
        "description_en": "Vanilla",
        "sub_positions": {
            "0905101000": {"dd": 0.00, "description_fr": "Vanille Bourbon premium", "description_en": "Premium Bourbon vanilla"},
            "0905109000": {"dd": 0.00, "description_fr": "Autre vanille", "description_en": "Other vanilla"},
        }
    },
    # GIROFLE
    "090710": {
        "default_dd": 0.00,
        "description_fr": "Clous de girofle",
        "description_en": "Cloves",
        "sub_positions": {
            "0907101000": {"dd": 0.00, "description_fr": "Girofle entier", "description_en": "Whole cloves"},
            "0907109000": {"dd": 0.00, "description_fr": "Autre girofle", "description_en": "Other cloves"},
        }
    },
    # YLANG-YLANG
    "330129": {
        "default_dd": 0.00,
        "description_fr": "Huiles essentielles",
        "description_en": "Essential oils",
        "sub_positions": {
            "3301291000": {"dd": 0.00, "description_fr": "Huile ylang-ylang extra", "description_en": "Extra ylang-ylang oil"},
            "3301292000": {"dd": 0.00, "description_fr": "Huile ylang-ylang première", "description_en": "First grade ylang-ylang"},
            "3301299000": {"dd": 0.00, "description_fr": "Autres huiles essentielles", "description_en": "Other essential oils"},
        }
    },
}

# =============================================================================
# MADAGASCAR (MDG) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes de Madagascar
# =============================================================================

MDG_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.35, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.25, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # VANILLE - Leader mondial
    "090510": {
        "default_dd": 0.00,
        "description_fr": "Vanille",
        "description_en": "Vanilla",
        "sub_positions": {
            "0905101000": {"dd": 0.00, "description_fr": "Vanille Bourbon SAVA", "description_en": "SAVA Bourbon vanilla"},
            "0905102000": {"dd": 0.00, "description_fr": "Vanille préparée", "description_en": "Prepared vanilla"},
            "0905109000": {"dd": 0.00, "description_fr": "Autre vanille", "description_en": "Other vanilla"},
        }
    },
    # GIROFLE
    "090710": {
        "default_dd": 0.00,
        "description_fr": "Clous de girofle",
        "description_en": "Cloves",
        "sub_positions": {
            "0907101000": {"dd": 0.00, "description_fr": "Girofle entier export", "description_en": "Whole cloves export"},
            "0907109000": {"dd": 0.00, "description_fr": "Autre girofle", "description_en": "Other cloves"},
        }
    },
    # NICKEL ET COBALT
    "750110": {
        "default_dd": 0.00,
        "description_fr": "Nickel brut",
        "description_en": "Unwrought nickel",
        "sub_positions": {
            "7501101000": {"dd": 0.00, "description_fr": "Nickel Ambatovy", "description_en": "Ambatovy nickel"},
            "7501109000": {"dd": 0.00, "description_fr": "Autre nickel", "description_en": "Other nickel"},
        }
    },
    # TEXTILES - Zones franches
    "610910": {
        "default_dd": 0.20,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.00, "description_fr": "T-shirts zones franches export", "description_en": "Free zone export T-shirts"},
            "6109109000": {"dd": 0.20, "description_fr": "Autres T-shirts", "description_en": "Other T-shirts"},
        }
    },
    # CREVETTES
    "030617": {
        "default_dd": 0.00,
        "description_fr": "Crevettes congelées",
        "description_en": "Frozen shrimps",
        "sub_positions": {
            "0306171000": {"dd": 0.00, "description_fr": "Crevettes élevage", "description_en": "Farmed shrimps"},
            "0306179000": {"dd": 0.00, "description_fr": "Crevettes sauvages", "description_en": "Wild shrimps"},
        }
    },
}

# =============================================================================
# MAURICE (MUS) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Mauritius Revenue Authority
# =============================================================================

MUS_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.00,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.00, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.15, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # SUCRE
    "170114": {
        "default_dd": 0.00,
        "description_fr": "Sucre de canne brut",
        "description_en": "Raw cane sugar",
        "sub_positions": {
            "1701141000": {"dd": 0.00, "description_fr": "Sucre spécial export UE", "description_en": "EU special export sugar"},
            "1701149000": {"dd": 0.00, "description_fr": "Autre sucre brut", "description_en": "Other raw sugar"},
        }
    },
    # TEXTILES
    "610910": {
        "default_dd": 0.00,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.00, "description_fr": "T-shirts EPZ export", "description_en": "EPZ export T-shirts"},
            "6109109000": {"dd": 0.00, "description_fr": "Autres T-shirts", "description_en": "Other T-shirts"},
        }
    },
    # THON EN CONSERVE
    "160414": {
        "default_dd": 0.00,
        "description_fr": "Thon en conserve",
        "description_en": "Canned tuna",
        "sub_positions": {
            "1604141000": {"dd": 0.00, "description_fr": "Thon conserve export", "description_en": "Export canned tuna"},
            "1604149000": {"dd": 0.00, "description_fr": "Autre thon conserve", "description_en": "Other canned tuna"},
        }
    },
}

# =============================================================================
# SEYCHELLES (SYC) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Seychelles Revenue Commission
# =============================================================================

SYC_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.00,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.00, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.15, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # THON
    "030342": {
        "default_dd": 0.00,
        "description_fr": "Thon congelé",
        "description_en": "Frozen tuna",
        "sub_positions": {
            "0303421000": {"dd": 0.00, "description_fr": "Thon listao", "description_en": "Skipjack tuna"},
            "0303429000": {"dd": 0.00, "description_fr": "Autre thon", "description_en": "Other tuna"},
        }
    },
    # THON EN CONSERVE - IOT
    "160414": {
        "default_dd": 0.00,
        "description_fr": "Thon en conserve",
        "description_en": "Canned tuna",
        "sub_positions": {
            "1604141000": {"dd": 0.00, "description_fr": "Thon conserve IOT export", "description_en": "IOT export canned tuna"},
            "1604149000": {"dd": 0.00, "description_fr": "Autre conserve thon", "description_en": "Other canned tuna"},
        }
    },
}

# =============================================================================
# MALAWI (MWI) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Malawi Revenue Authority
# =============================================================================

MWI_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.35, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # TABAC - Principal export
    "240110": {
        "default_dd": 0.00,
        "description_fr": "Tabac brut",
        "description_en": "Raw tobacco",
        "sub_positions": {
            "2401101000": {"dd": 0.00, "description_fr": "Tabac Burley", "description_en": "Burley tobacco"},
            "2401102000": {"dd": 0.00, "description_fr": "Tabac flue-cured", "description_en": "Flue-cured tobacco"},
            "2401109000": {"dd": 0.00, "description_fr": "Autre tabac", "description_en": "Other tobacco"},
        }
    },
    # THÉ
    "090230": {
        "default_dd": 0.00,
        "description_fr": "Thé noir",
        "description_en": "Black tea",
        "sub_positions": {
            "0902301000": {"dd": 0.00, "description_fr": "Thé noir orthodox", "description_en": "Orthodox black tea"},
            "0902309000": {"dd": 0.00, "description_fr": "Autre thé", "description_en": "Other tea"},
        }
    },
    # SUCRE
    "170199": {
        "default_dd": 0.25,
        "description_fr": "Sucre",
        "description_en": "Sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.15, "description_fr": "Sucre Illovo local", "description_en": "Local Illovo sugar"},
            "1701999000": {"dd": 0.25, "description_fr": "Sucre importé", "description_en": "Imported sugar"},
        }
    },
}

# =============================================================================
# ZAMBIE (ZMB) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Zambia Revenue Authority
# =============================================================================

ZMB_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.30, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # CUIVRE - Principal export
    "740311": {
        "default_dd": 0.00,
        "description_fr": "Cathodes de cuivre",
        "description_en": "Copper cathodes",
        "sub_positions": {
            "7403111000": {"dd": 0.00, "description_fr": "Cathodes LME grade A", "description_en": "LME grade A cathodes"},
            "7403119000": {"dd": 0.00, "description_fr": "Autres cathodes", "description_en": "Other cathodes"},
        }
    },
    # COBALT
    "810520": {
        "default_dd": 0.00,
        "description_fr": "Cobalt",
        "description_en": "Cobalt",
        "sub_positions": {
            "8105201000": {"dd": 0.00, "description_fr": "Hydroxyde de cobalt", "description_en": "Cobalt hydroxide"},
            "8105209000": {"dd": 0.00, "description_fr": "Autre cobalt", "description_en": "Other cobalt"},
        }
    },
    # TABAC
    "240110": {
        "default_dd": 0.00,
        "description_fr": "Tabac brut",
        "description_en": "Raw tobacco",
        "sub_positions": {
            "2401101000": {"dd": 0.00, "description_fr": "Tabac Virginia", "description_en": "Virginia tobacco"},
            "2401109000": {"dd": 0.00, "description_fr": "Autre tabac", "description_en": "Other tobacco"},
        }
    },
    # SUCRE
    "170199": {
        "default_dd": 0.25,
        "description_fr": "Sucre",
        "description_en": "Sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.15, "description_fr": "Sucre Zambia Sugar local", "description_en": "Local Zambia Sugar"},
            "1701999000": {"dd": 0.25, "description_fr": "Sucre importé", "description_en": "Imported sugar"},
        }
    },
}

# =============================================================================
# ZIMBABWE (ZWE) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Zimbabwe Revenue Authority
# =============================================================================

ZWE_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.40,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.40, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.60, "description_fr": "Voitures occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.50, "description_fr": "Voitures occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.40, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or brut",
        "description_en": "Unwrought gold",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné Fidelity", "description_en": "Fidelity refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or", "description_en": "Other gold"},
        }
    },
    # TABAC
    "240110": {
        "default_dd": 0.00,
        "description_fr": "Tabac brut",
        "description_en": "Raw tobacco",
        "sub_positions": {
            "2401101000": {"dd": 0.00, "description_fr": "Tabac flue-cured", "description_en": "Flue-cured tobacco"},
            "2401102000": {"dd": 0.00, "description_fr": "Tabac Burley", "description_en": "Burley tobacco"},
            "2401109000": {"dd": 0.00, "description_fr": "Autre tabac", "description_en": "Other tobacco"},
        }
    },
    # PLATINE
    "711011": {
        "default_dd": 0.00,
        "description_fr": "Platine brut",
        "description_en": "Unwrought platinum",
        "sub_positions": {
            "7110111000": {"dd": 0.00, "description_fr": "Platine Zimplats", "description_en": "Zimplats platinum"},
            "7110119000": {"dd": 0.00, "description_fr": "Autre platine", "description_en": "Other platinum"},
        }
    },
    # CHROME
    "261000": {
        "default_dd": 0.00,
        "description_fr": "Minerais de chrome",
        "description_en": "Chromium ores",
        "sub_positions": {
            "2610001000": {"dd": 0.00, "description_fr": "Chrome métallurgique", "description_en": "Metallurgical chrome"},
            "2610009000": {"dd": 0.00, "description_fr": "Autre chrome", "description_en": "Other chrome"},
        }
    },
}

# =============================================================================
# MOZAMBIQUE (MOZ) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Autoridade Tributária de Moçambique
# =============================================================================

MOZ_HS6_DETAILED = {
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
    # ALUMINIUM - Mozal
    "760110": {
        "default_dd": 0.00,
        "description_fr": "Aluminium non allié",
        "description_en": "Non-alloyed aluminum",
        "sub_positions": {
            "7601101000": {"dd": 0.00, "description_fr": "Aluminium Mozal", "description_en": "Mozal aluminum"},
            "7601109000": {"dd": 0.05, "description_fr": "Autre aluminium", "description_en": "Other aluminum"},
        }
    },
    # CHARBON
    "270112": {
        "default_dd": 0.00,
        "description_fr": "Houille bitumineuse",
        "description_en": "Bituminous coal",
        "sub_positions": {
            "2701121000": {"dd": 0.00, "description_fr": "Charbon cokéfiable Tete", "description_en": "Tete coking coal"},
            "2701129000": {"dd": 0.00, "description_fr": "Autre charbon", "description_en": "Other coal"},
        }
    },
    # GAZ NATUREL - Rovuma
    "271121": {
        "default_dd": 0.00,
        "description_fr": "Gaz naturel",
        "description_en": "Natural gas",
        "sub_positions": {
            "2711210010": {"dd": 0.00, "description_fr": "GNL Rovuma", "description_en": "Rovuma LNG"},
            "2711210090": {"dd": 0.00, "description_fr": "Autre gaz naturel", "description_en": "Other natural gas"},
        }
    },
    # CREVETTES
    "030617": {
        "default_dd": 0.00,
        "description_fr": "Crevettes",
        "description_en": "Shrimps",
        "sub_positions": {
            "0306171000": {"dd": 0.00, "description_fr": "Langoustines Sofala", "description_en": "Sofala langoustines"},
            "0306179000": {"dd": 0.00, "description_fr": "Autres crevettes", "description_en": "Other shrimps"},
        }
    },
    # SUCRE
    "170199": {
        "default_dd": 0.20,
        "description_fr": "Sucre",
        "description_en": "Sugar",
        "sub_positions": {
            "1701991000": {"dd": 0.10, "description_fr": "Sucre local Xinavane", "description_en": "Xinavane local sugar"},
            "1701999000": {"dd": 0.20, "description_fr": "Sucre importé", "description_en": "Imported sugar"},
        }
    },
}

# =============================================================================
# ANGOLA (AGO) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Administração Geral Tributária
# =============================================================================

AGO_HS6_DETAILED = {
    # VÉHICULES
    "870321": {
        "default_dd": 0.10,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.10, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703219000": {"dd": 0.20, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "870323": {
        "default_dd": 0.10,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.10, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.30, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.20, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # PÉTROLE - Dominance export
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Pétrole brut",
        "description_en": "Crude oil",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole Cabinda", "description_en": "Cabinda crude"},
            "2709002000": {"dd": 0.00, "description_fr": "Pétrole Dalia", "description_en": "Dalia crude"},
            "2709003000": {"dd": 0.00, "description_fr": "Pétrole Girassol", "description_en": "Girassol crude"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # GAZ NATUREL
    "271121": {
        "default_dd": 0.00,
        "description_fr": "Gaz naturel",
        "description_en": "Natural gas",
        "sub_positions": {
            "2711210010": {"dd": 0.00, "description_fr": "GNL Angola LNG", "description_en": "Angola LNG"},
            "2711210090": {"dd": 0.00, "description_fr": "Autre gaz naturel", "description_en": "Other natural gas"},
        }
    },
    # DIAMANTS
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants bruts",
        "description_en": "Rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants Endiama", "description_en": "Endiama diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants", "description_en": "Other diamonds"},
        }
    },
    # CAFÉ
    "090111": {
        "default_dd": 0.00,
        "description_fr": "Café vert",
        "description_en": "Green coffee",
        "sub_positions": {
            "0901111000": {"dd": 0.00, "description_fr": "Café Robusta Kwanza", "description_en": "Kwanza Robusta"},
            "0901119000": {"dd": 0.00, "description_fr": "Autre café", "description_en": "Other coffee"},
        }
    },
}

# =============================================================================
# SACU (Botswana, Namibie, Lesotho, Eswatini) - Base commune avec ZAF
# =============================================================================

BWA_HS6_DETAILED = {
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants bruts",
        "description_en": "Rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants Debswana", "description_en": "Debswana diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants", "description_en": "Other diamonds"},
        }
    },
    "020230": {
        "default_dd": 0.00,
        "description_fr": "Viande bovine désossée",
        "description_en": "Boneless beef",
        "sub_positions": {
            "0202301000": {"dd": 0.00, "description_fr": "Boeuf BMC export UE", "description_en": "BMC beef EU export"},
            "0202309000": {"dd": 0.00, "description_fr": "Autre boeuf", "description_en": "Other beef"},
        }
    },
}

NAM_HS6_DETAILED = {
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants bruts",
        "description_en": "Rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants Namdeb", "description_en": "Namdeb diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants", "description_en": "Other diamonds"},
        }
    },
    "261390": {
        "default_dd": 0.00,
        "description_fr": "Minerais d'uranium",
        "description_en": "Uranium ores",
        "sub_positions": {
            "2613901000": {"dd": 0.00, "description_fr": "Yellowcake Rössing", "description_en": "Rössing yellowcake"},
            "2613909000": {"dd": 0.00, "description_fr": "Autre uranium", "description_en": "Other uranium"},
        }
    },
    "030379": {
        "default_dd": 0.00,
        "description_fr": "Poissons congelés",
        "description_en": "Frozen fish",
        "sub_positions": {
            "0303791000": {"dd": 0.00, "description_fr": "Merlu congelé", "description_en": "Frozen hake"},
            "0303799000": {"dd": 0.00, "description_fr": "Autre poisson congelé", "description_en": "Other frozen fish"},
        }
    },
}

LSO_HS6_DETAILED = {
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "710231": {
        "default_dd": 0.00,
        "description_fr": "Diamants bruts",
        "description_en": "Rough diamonds",
        "sub_positions": {
            "7102311000": {"dd": 0.00, "description_fr": "Diamants Letšeng", "description_en": "Letšeng diamonds"},
            "7102319000": {"dd": 0.00, "description_fr": "Autres diamants", "description_en": "Other diamonds"},
        }
    },
    "610910": {
        "default_dd": 0.00,
        "description_fr": "T-shirts coton",
        "description_en": "Cotton T-shirts",
        "sub_positions": {
            "6109101000": {"dd": 0.00, "description_fr": "Textiles AGOA export", "description_en": "AGOA export textiles"},
            "6109109000": {"dd": 0.20, "description_fr": "Autres textiles", "description_en": "Other textiles"},
        }
    },
}

SWZ_HS6_DETAILED = {
    "870323": {
        "default_dd": 0.25,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.25, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    "170114": {
        "default_dd": 0.00,
        "description_fr": "Sucre de canne brut",
        "description_en": "Raw cane sugar",
        "sub_positions": {
            "1701141000": {"dd": 0.00, "description_fr": "Sucre RSSC export", "description_en": "RSSC export sugar"},
            "1701149000": {"dd": 0.00, "description_fr": "Autre sucre brut", "description_en": "Other raw sugar"},
        }
    },
    "200990": {
        "default_dd": 0.00,
        "description_fr": "Concentrés de fruits",
        "description_en": "Fruit concentrates",
        "sub_positions": {
            "2009901000": {"dd": 0.00, "description_fr": "Concentré agrumes Coca-Cola", "description_en": "Coca-Cola citrus concentrate"},
            "2009909000": {"dd": 0.05, "description_fr": "Autres concentrés", "description_en": "Other concentrates"},
        }
    },
}

# =============================================================================
# DICTIONNAIRE UNIFIÉ EAC + COMESA + SADC
# =============================================================================

EAC_SADC_HS6_DETAILED = {
    # EAC
    "TZA": TZA_HS6_DETAILED,
    "UGA": UGA_HS6_DETAILED,
    "RWA": RWA_HS6_DETAILED,
    "BDI": BDI_HS6_DETAILED,
    "SSD": SSD_HS6_DETAILED,
    # Corne de l'Afrique
    "ETH": ETH_HS6_DETAILED,
    "ERI": ERI_HS6_DETAILED,
    "DJI": DJI_HS6_DETAILED,
    "SOM": SOM_HS6_DETAILED,
    # Îles Océan Indien
    "COM": COM_HS6_DETAILED,
    "MDG": MDG_HS6_DETAILED,
    "MUS": MUS_HS6_DETAILED,
    "SYC": SYC_HS6_DETAILED,
    # SADC (hors SACU)
    "MWI": MWI_HS6_DETAILED,
    "ZMB": ZMB_HS6_DETAILED,
    "ZWE": ZWE_HS6_DETAILED,
    "MOZ": MOZ_HS6_DETAILED,
    "AGO": AGO_HS6_DETAILED,
    # SACU
    "BWA": BWA_HS6_DETAILED,
    "NAM": NAM_HS6_DETAILED,
    "LSO": LSO_HS6_DETAILED,
    "SWZ": SWZ_HS6_DETAILED,
}
