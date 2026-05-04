"""
Tarifs douaniers avec SOUS-POSITIONS NATIONALES - CEDEAO
Pays membres: Bénin, Burkina Faso, Cap-Vert, Gambie, Ghana, Guinée, Guinée-Bissau, 
              Libéria, Mali, Niger, Sénégal, Sierra Leone, Togo
(Nigeria et Côte d'Ivoire déjà dans country_hs6_detailed.py)

Base: Tarif Extérieur Commun (TEC) CEDEAO avec adaptations nationales
Sources: ECOWAS Commission, Administrations douanières nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# BÉNIN (BEN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Bénin
# =============================================================================

BEN_HS6_DETAILED = {
    # VÉHICULES - TEC CEDEAO + Taxes nationales
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.20, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870322": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "sub_positions": {
            "8703221000": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc neuves", "description_en": "New cars 1000-1500cc"},
            "8703229000": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc occasion", "description_en": "Used cars 1000-1500cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures 1500-3000cc occasion >5 ans", "description_en": "Used cars >5 years 1500-3000cc"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc occasion <5 ans", "description_en": "Used cars <5 years 1500-3000cc"},
        }
    },
    # COTON - Secteur stratégique Bénin
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton brut pour transformation locale", "description_en": "Raw cotton for local processing"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton brut", "description_en": "Other raw cotton"},
        }
    },
    # RIZ - Importations importantes
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz semi-blanchi ou blanchi",
        "description_en": "Semi-milled or wholly milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.10, "description_fr": "Riz semi-blanchi", "description_en": "Semi-milled rice"},
            "1006302000": {"dd": 0.10, "description_fr": "Riz blanchi long grain", "description_en": "Long grain milled rice"},
            "1006303000": {"dd": 0.10, "description_fr": "Riz parfumé", "description_en": "Fragrant rice"},
            "1006309000": {"dd": 0.10, "description_fr": "Autre riz blanchi", "description_en": "Other milled rice"},
        }
    },
    # HUILE DE PALME - Transit régional
    "151110": {
        "default_dd": 0.20,
        "description_fr": "Huile de palme brute",
        "description_en": "Crude palm oil",
        "sub_positions": {
            "1511101000": {"dd": 0.10, "description_fr": "Huile palme brute pour raffinage", "description_en": "Crude palm oil for refining"},
            "1511109000": {"dd": 0.20, "description_fr": "Autre huile palme brute", "description_en": "Other crude palm oil"},
        }
    },
    # CIMENT - Infrastructure
    "252329": {
        "default_dd": 0.20,
        "description_fr": "Ciment Portland autre",
        "description_en": "Other Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.20, "description_fr": "Ciment Portland gris", "description_en": "Grey Portland cement"},
            "2523292000": {"dd": 0.20, "description_fr": "Ciment Portland blanc", "description_en": "White Portland cement"},
        }
    },
}

# =============================================================================
# BURKINA FASO (BFA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Burkina
# =============================================================================

BFA_HS6_DETAILED = {
    # VÉHICULES
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.20, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures 1500-3000cc occasion >8 ans", "description_en": "Used cars >8 years"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc occasion <8 ans", "description_en": "Used cars <8 years"},
        }
    },
    # COTON - Principal export
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton brut biologique", "description_en": "Organic raw cotton"},
            "5201002000": {"dd": 0.00, "description_fr": "Coton brut conventionnel", "description_en": "Conventional raw cotton"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton brut", "description_en": "Other raw cotton"},
        }
    },
    # OR - Exploitation minière croissante
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné lingots", "description_en": "Refined gold bars"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # CÉRÉALES - Sécurité alimentaire
    "100190": {
        "default_dd": 0.05,
        "description_fr": "Blé et méteil autre",
        "description_en": "Other wheat and meslin",
        "sub_positions": {
            "1001901000": {"dd": 0.05, "description_fr": "Blé tendre", "description_en": "Soft wheat"},
            "1001902000": {"dd": 0.05, "description_fr": "Blé dur", "description_en": "Durum wheat"},
        }
    },
    # ÉQUIPEMENTS AGRICOLES
    "843351": {
        "default_dd": 0.05,
        "description_fr": "Moissonneuses-batteuses",
        "description_en": "Combine harvester-threshers",
        "sub_positions": {
            "8433510010": {"dd": 0.00, "description_fr": "Moissonneuses programme agricole", "description_en": "Harvesters for agricultural program"},
            "8433510090": {"dd": 0.05, "description_fr": "Autres moissonneuses", "description_en": "Other harvesters"},
        }
    },
}

# =============================================================================
# CAP-VERT (CPV) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direção Nacional das Alfândegas
# =============================================================================

CPV_HS6_DETAILED = {
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
    # POISSON - Secteur clé
    "030289": {
        "default_dd": 0.05,
        "description_fr": "Autres poissons frais/réfrigérés",
        "description_en": "Other fresh/chilled fish",
        "sub_positions": {
            "0302891000": {"dd": 0.00, "description_fr": "Thon frais pêche locale", "description_en": "Fresh tuna local fishing"},
            "0302899000": {"dd": 0.05, "description_fr": "Autre poisson frais", "description_en": "Other fresh fish"},
        }
    },
    # CARBURANT - Insularité
    "271019": {
        "default_dd": 0.05,
        "description_fr": "Autres huiles de pétrole",
        "description_en": "Other petroleum oils",
        "sub_positions": {
            "2710191000": {"dd": 0.05, "description_fr": "Gasoil", "description_en": "Diesel"},
            "2710192000": {"dd": 0.05, "description_fr": "Essence", "description_en": "Gasoline"},
            "2710193000": {"dd": 0.00, "description_fr": "Carburant aviation", "description_en": "Aviation fuel"},
        }
    },
    # MATÉRIAUX CONSTRUCTION - Import massif
    "252329": {
        "default_dd": 0.10,
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.10, "description_fr": "Ciment Portland gris", "description_en": "Grey Portland cement"},
            "2523299000": {"dd": 0.10, "description_fr": "Autre ciment", "description_en": "Other cement"},
        }
    },
}

# =============================================================================
# GAMBIE (GMB) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Gambia Revenue Authority
# =============================================================================

GMB_HS6_DETAILED = {
    # VÉHICULES - Réexportation vers Sénégal
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.35, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # ARACHIDE - Export principal
    "120242": {
        "default_dd": 0.00,
        "description_fr": "Arachides décortiquées",
        "description_en": "Shelled groundnuts",
        "sub_positions": {
            "1202421000": {"dd": 0.00, "description_fr": "Arachides HPS export", "description_en": "HPS groundnuts for export"},
            "1202429000": {"dd": 0.00, "description_fr": "Autres arachides décortiquées", "description_en": "Other shelled groundnuts"},
        }
    },
    # RIZ - Alimentation de base
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.10, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.10, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
        }
    },
    # TOURISME - Équipements
    "940390": {
        "default_dd": 0.20,
        "description_fr": "Parties de meubles",
        "description_en": "Parts of furniture",
        "sub_positions": {
            "9403901000": {"dd": 0.10, "description_fr": "Mobilier hôtelier", "description_en": "Hotel furniture"},
            "9403909000": {"dd": 0.20, "description_fr": "Autre mobilier", "description_en": "Other furniture"},
        }
    },
}

# =============================================================================
# GHANA (GHA) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Ghana Revenue Authority - Customs Division
# =============================================================================

GHA_HS6_DETAILED = {
    # VÉHICULES - Taxation différenciée âge
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.20, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870322": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "sub_positions": {
            "8703221000": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc neuves", "description_en": "New cars 1000-1500cc"},
            "8703229000": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc occasion", "description_en": "Used cars 1000-1500cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703239000": {"dd": 0.50, "description_fr": "Voitures 1500-3000cc occasion >10 ans", "description_en": "Used cars >10 years"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc occasion 5-10 ans", "description_en": "Used cars 5-10 years"},
            "8703239200": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # CACAO - Principal export
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
    # OR - Deuxième export
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné LBMA", "description_en": "LBMA refined gold"},
            "7108120020": {"dd": 0.00, "description_fr": "Or doré (alluvionnaire)", "description_en": "Alluvial gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # PÉTROLE - Producteur depuis 2010
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut léger", "description_en": "Light crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # RIZ - Import majeur
    "100630": {
        "default_dd": 0.20,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.15, "description_fr": "Riz brisé 100%", "description_en": "100% broken rice"},
            "1006302000": {"dd": 0.20, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
            "1006303000": {"dd": 0.20, "description_fr": "Riz parfumé", "description_en": "Fragrant rice"},
        }
    },
    # ÉQUIPEMENTS MINIERS
    "847490": {
        "default_dd": 0.05,
        "description_fr": "Parties machines traitement matériaux",
        "description_en": "Parts of material processing machines",
        "sub_positions": {
            "8474901000": {"dd": 0.00, "description_fr": "Parties broyeurs mines", "description_en": "Mining crusher parts"},
            "8474909000": {"dd": 0.05, "description_fr": "Autres parties", "description_en": "Other parts"},
        }
    },
}

# =============================================================================
# GUINÉE (GIN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes de Guinée
# =============================================================================

GIN_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # BAUXITE - Premier exportateur mondial
    "260600": {
        "default_dd": 0.00,
        "description_fr": "Minerais d'aluminium et concentrés",
        "description_en": "Aluminum ores and concentrates",
        "sub_positions": {
            "2606001000": {"dd": 0.00, "description_fr": "Bauxite calcinée", "description_en": "Calcined bauxite"},
            "2606002000": {"dd": 0.00, "description_fr": "Bauxite non calcinée", "description_en": "Non-calcined bauxite"},
            "2606009000": {"dd": 0.00, "description_fr": "Autres minerais aluminium", "description_en": "Other aluminum ores"},
        }
    },
    # OR
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # ÉQUIPEMENTS MINIERS
    "843041": {
        "default_dd": 0.05,
        "description_fr": "Machines de sondage/forage",
        "description_en": "Boring/sinking machinery",
        "sub_positions": {
            "8430411000": {"dd": 0.00, "description_fr": "Foreuses mines programme", "description_en": "Mining drills program"},
            "8430419000": {"dd": 0.05, "description_fr": "Autres foreuses", "description_en": "Other drills"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.05, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.10, "description_fr": "Riz entier", "description_en": "Whole rice"},
        }
    },
}

# =============================================================================
# GUINÉE-BISSAU (GNB) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes
# =============================================================================

GNB_HS6_DETAILED = {
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
    # NOIX DE CAJOU - Principal export
    "080131": {
        "default_dd": 0.00,
        "description_fr": "Noix de cajou en coques",
        "description_en": "Cashew nuts in shell",
        "sub_positions": {
            "0801311000": {"dd": 0.00, "description_fr": "Cajou brut export", "description_en": "Raw cashew for export"},
            "0801319000": {"dd": 0.00, "description_fr": "Autre cajou en coque", "description_en": "Other cashew in shell"},
        }
    },
    # RIZ - Consommation
    "100630": {
        "default_dd": 0.10,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.10, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.10, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
        }
    },
}

# =============================================================================
# LIBÉRIA (LBR) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Liberia Revenue Authority
# =============================================================================

LBR_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.10,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.10, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.25, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # MINERAI DE FER - Export majeur
    "260111": {
        "default_dd": 0.00,
        "description_fr": "Minerais de fer non agglomérés",
        "description_en": "Iron ores non-agglomerated",
        "sub_positions": {
            "2601111000": {"dd": 0.00, "description_fr": "Minerai fer haute teneur", "description_en": "High grade iron ore"},
            "2601119000": {"dd": 0.00, "description_fr": "Autre minerai fer", "description_en": "Other iron ore"},
        }
    },
    # CAOUTCHOUC - Hévéa
    "400110": {
        "default_dd": 0.00,
        "description_fr": "Latex de caoutchouc naturel",
        "description_en": "Natural rubber latex",
        "sub_positions": {
            "4001101000": {"dd": 0.00, "description_fr": "Latex concentré", "description_en": "Concentrated latex"},
            "4001109000": {"dd": 0.00, "description_fr": "Autre latex", "description_en": "Other latex"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.05,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.05, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.05, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
        }
    },
}

# =============================================================================
# MALI (MLI) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Mali
# =============================================================================

MLI_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.45, "description_fr": "Voitures occasion >8 ans", "description_en": "Used cars >8 years"},
            "8703239100": {"dd": 0.35, "description_fr": "Voitures occasion <8 ans", "description_en": "Used cars <8 years"},
        }
    },
    # OR - Premier export
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # COTON
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton brut CMDT", "description_en": "CMDT raw cotton"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton brut", "description_en": "Other raw cotton"},
        }
    },
    # BÉTAIL - Élevage important
    "010290": {
        "default_dd": 0.05,
        "description_fr": "Autres bovins vivants",
        "description_en": "Other live bovine animals",
        "sub_positions": {
            "0102901000": {"dd": 0.05, "description_fr": "Bovins d'élevage", "description_en": "Breeding cattle"},
            "0102909000": {"dd": 0.05, "description_fr": "Bovins de boucherie", "description_en": "Cattle for slaughter"},
        }
    },
    # CÉRÉALES
    "100590": {
        "default_dd": 0.05,
        "description_fr": "Maïs autre",
        "description_en": "Other maize",
        "sub_positions": {
            "1005901000": {"dd": 0.05, "description_fr": "Maïs jaune", "description_en": "Yellow maize"},
            "1005909000": {"dd": 0.05, "description_fr": "Autre maïs", "description_en": "Other maize"},
        }
    },
}

# =============================================================================
# NIGER (NER) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Niger
# =============================================================================

NER_HS6_DETAILED = {
    # VÉHICULES
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion", "description_en": "Used cars"},
        }
    },
    # URANIUM - Export stratégique
    "261210": {
        "default_dd": 0.00,
        "description_fr": "Minerais d'uranium",
        "description_en": "Uranium ores",
        "sub_positions": {
            "2612101000": {"dd": 0.00, "description_fr": "Concentré uranium", "description_en": "Uranium concentrate"},
            "2612109000": {"dd": 0.00, "description_fr": "Autre minerai uranium", "description_en": "Other uranium ore"},
        }
    },
    # PÉTROLE - Production depuis 2011
    "270900": {
        "default_dd": 0.00,
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "sub_positions": {
            "2709001000": {"dd": 0.00, "description_fr": "Pétrole brut Agadem", "description_en": "Agadem crude oil"},
            "2709009000": {"dd": 0.00, "description_fr": "Autre pétrole brut", "description_en": "Other crude oil"},
        }
    },
    # OIGNON - Export régional
    "070310": {
        "default_dd": 0.05,
        "description_fr": "Oignons et échalotes",
        "description_en": "Onions and shallots",
        "sub_positions": {
            "0703101000": {"dd": 0.00, "description_fr": "Oignons violets export", "description_en": "Purple onions for export"},
            "0703109000": {"dd": 0.05, "description_fr": "Autres oignons", "description_en": "Other onions"},
        }
    },
    # BÉTAIL
    "010290": {
        "default_dd": 0.05,
        "description_fr": "Autres bovins vivants",
        "description_en": "Other live bovine animals",
        "sub_positions": {
            "0102901000": {"dd": 0.05, "description_fr": "Bovins d'élevage", "description_en": "Breeding cattle"},
            "0102909000": {"dd": 0.05, "description_fr": "Bovins de boucherie", "description_en": "Cattle for slaughter"},
        }
    },
}

# =============================================================================
# SÉNÉGAL (SEN) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Direction Générale des Douanes du Sénégal
# =============================================================================

SEN_HS6_DETAILED = {
    # VÉHICULES - Taxation par âge
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.20, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.35, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc neuves", "description_en": "New cars 1500-3000cc"},
            "8703239000": {"dd": 0.55, "description_fr": "Voitures occasion >8 ans", "description_en": "Used cars >8 years"},
            "8703239100": {"dd": 0.45, "description_fr": "Voitures occasion 5-8 ans", "description_en": "Used cars 5-8 years"},
            "8703239200": {"dd": 0.35, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # POISSON - Secteur clé
    "030389": {
        "default_dd": 0.10,
        "description_fr": "Autres poissons congelés",
        "description_en": "Other frozen fish",
        "sub_positions": {
            "0303891000": {"dd": 0.00, "description_fr": "Poisson pêche artisanale congelé", "description_en": "Frozen artisanal fish"},
            "0303899000": {"dd": 0.10, "description_fr": "Autre poisson congelé", "description_en": "Other frozen fish"},
        }
    },
    # PHOSPHATES
    "310520": {
        "default_dd": 0.05,
        "description_fr": "Engrais phosphatés",
        "description_en": "Phosphatic fertilizers",
        "sub_positions": {
            "3105201000": {"dd": 0.00, "description_fr": "Engrais ICS local", "description_en": "Local ICS fertilizer"},
            "3105209000": {"dd": 0.05, "description_fr": "Autre engrais phosphaté", "description_en": "Other phosphatic fertilizer"},
        }
    },
    # ARACHIDE
    "120242": {
        "default_dd": 0.00,
        "description_fr": "Arachides décortiquées",
        "description_en": "Shelled groundnuts",
        "sub_positions": {
            "1202421000": {"dd": 0.00, "description_fr": "Arachides HPS export", "description_en": "HPS groundnuts export"},
            "1202429000": {"dd": 0.00, "description_fr": "Autres arachides", "description_en": "Other groundnuts"},
        }
    },
    # OR - Nouveau secteur
    "710812": {
        "default_dd": 0.00,
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "sub_positions": {
            "7108120010": {"dd": 0.00, "description_fr": "Or raffiné", "description_en": "Refined gold"},
            "7108120090": {"dd": 0.00, "description_fr": "Autre or brut", "description_en": "Other unwrought gold"},
        }
    },
    # CIMENT - Production locale
    "252329": {
        "default_dd": 0.20,
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.20, "description_fr": "Ciment gris", "description_en": "Grey cement"},
            "2523292000": {"dd": 0.20, "description_fr": "Ciment blanc", "description_en": "White cement"},
        }
    },
}

# =============================================================================
# SIERRA LEONE (SLE) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: National Revenue Authority
# =============================================================================

SLE_HS6_DETAILED = {
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
    # MINERAI DE FER
    "260111": {
        "default_dd": 0.00,
        "description_fr": "Minerais de fer",
        "description_en": "Iron ores",
        "sub_positions": {
            "2601111000": {"dd": 0.00, "description_fr": "Minerai fer haute teneur", "description_en": "High grade iron ore"},
            "2601119000": {"dd": 0.00, "description_fr": "Autre minerai fer", "description_en": "Other iron ore"},
        }
    },
    # RIZ
    "100630": {
        "default_dd": 0.05,
        "description_fr": "Riz blanchi",
        "description_en": "Milled rice",
        "sub_positions": {
            "1006301000": {"dd": 0.05, "description_fr": "Riz brisé", "description_en": "Broken rice"},
            "1006302000": {"dd": 0.05, "description_fr": "Riz long grain", "description_en": "Long grain rice"},
        }
    },
}

# =============================================================================
# TOGO (TGO) - TARIFS AVEC SOUS-POSITIONS NATIONALES
# Source: Office Togolais des Recettes
# =============================================================================

TGO_HS6_DETAILED = {
    # VÉHICULES - Hub régional
    "870321": {
        "default_dd": 0.20,
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "sub_positions": {
            "8703211000": {"dd": 0.20, "description_fr": "Voitures ≤1000cc neuves", "description_en": "New cars ≤1000cc"},
            "8703219000": {"dd": 0.30, "description_fr": "Voitures ≤1000cc occasion", "description_en": "Used cars ≤1000cc"},
        }
    },
    "870323": {
        "default_dd": 0.20,
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "sub_positions": {
            "8703231000": {"dd": 0.20, "description_fr": "Voitures neuves", "description_en": "New cars"},
            "8703239000": {"dd": 0.40, "description_fr": "Voitures occasion >5 ans", "description_en": "Used cars >5 years"},
            "8703239100": {"dd": 0.30, "description_fr": "Voitures occasion <5 ans", "description_en": "Used cars <5 years"},
        }
    },
    # PHOSPHATES - Export majeur
    "253110": {
        "default_dd": 0.00,
        "description_fr": "Phosphates de calcium naturels",
        "description_en": "Natural calcium phosphates",
        "sub_positions": {
            "2531101000": {"dd": 0.00, "description_fr": "Phosphate brut export", "description_en": "Raw phosphate export"},
            "2531109000": {"dd": 0.00, "description_fr": "Autre phosphate", "description_en": "Other phosphate"},
        }
    },
    # COTON
    "520100": {
        "default_dd": 0.05,
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "sub_positions": {
            "5201001000": {"dd": 0.00, "description_fr": "Coton brut SOTOCO", "description_en": "SOTOCO raw cotton"},
            "5201009000": {"dd": 0.05, "description_fr": "Autre coton brut", "description_en": "Other raw cotton"},
        }
    },
    # CIMENT - Industrie locale
    "252329": {
        "default_dd": 0.20,
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "sub_positions": {
            "2523291000": {"dd": 0.20, "description_fr": "Ciment CimTogo", "description_en": "CimTogo cement"},
            "2523292000": {"dd": 0.20, "description_fr": "Autre ciment", "description_en": "Other cement"},
        }
    },
    # RÉEXPORTATION - Hub portuaire
    "940360": {
        "default_dd": 0.20,
        "description_fr": "Autres meubles en bois",
        "description_en": "Other wooden furniture",
        "sub_positions": {
            "9403601000": {"dd": 0.10, "description_fr": "Meubles transit régional", "description_en": "Regional transit furniture"},
            "9403609000": {"dd": 0.20, "description_fr": "Autres meubles bois", "description_en": "Other wooden furniture"},
        }
    },
}


# =============================================================================
# DICTIONNAIRE UNIFIÉ CEDEAO
# =============================================================================

CEDEAO_HS6_DETAILED = {
    "BEN": BEN_HS6_DETAILED,
    "BFA": BFA_HS6_DETAILED,
    "CPV": CPV_HS6_DETAILED,
    "GMB": GMB_HS6_DETAILED,
    "GHA": GHA_HS6_DETAILED,
    "GIN": GIN_HS6_DETAILED,
    "GNB": GNB_HS6_DETAILED,
    "LBR": LBR_HS6_DETAILED,
    "MLI": MLI_HS6_DETAILED,
    "NER": NER_HS6_DETAILED,
    "SEN": SEN_HS6_DETAILED,
    "SLE": SLE_HS6_DETAILED,
    "TGO": TGO_HS6_DETAILED,
}
