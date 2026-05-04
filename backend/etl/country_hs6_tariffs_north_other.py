"""
Tarifs douaniers SH6 pour TOUS les pays africains - Partie 3
Afrique du Nord (6 pays) + SACU (5 pays) + Autres (6 pays)
Sources: OMC ITC, CNUCED TRAINS, Administrations douanières nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# AFRIQUE DU NORD
# =============================================================================

# =============================================================================
# ALGÉRIE (DZA) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Algérie
# TVA: 19%
# =============================================================================

DZA_HS6_TARIFFS = {
    # PÉTROLE ET GAZ - Principaux exports
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271111": {"dd": 0.00, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    "271121": {"dd": 0.00, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271019": {"dd": 0.05, "description_fr": "Autres huiles de pétrole", "description_en": "Other petroleum oils"},
    
    # ENGRAIS
    "310210": {"dd": 0.05, "description_fr": "Urée", "description_en": "Urea"},
    "310230": {"dd": 0.05, "description_fr": "Nitrate d'ammonium", "description_en": "Ammonium nitrate"},
    
    # MINERAI DE FER
    "260111": {"dd": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    
    # DATTES
    "080410": {"dd": 0.00, "description_fr": "Dattes fraîches ou séchées", "description_en": "Dates, fresh or dried"},
    
    # RIZ - Importateur
    "100630": {"dd": 0.05, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - Protection industrie locale
    "870321": {"dd": 0.30, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.30, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.30, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.30, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"dd": 0.15, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES
    "610910": {"dd": 0.30, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.30, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # CÉRÉALES - Grand importateur
    "100110": {"dd": 0.05, "description_fr": "Blé dur", "description_en": "Durum wheat"},
    "100190": {"dd": 0.05, "description_fr": "Blé tendre", "description_en": "Other wheat"},
    "100590": {"dd": 0.05, "description_fr": "Maïs autre", "description_en": "Other maize"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    "841821": {"dd": 0.30, "description_fr": "Réfrigérateurs ménagers", "description_en": "Household refrigerators"},
}

# =============================================================================
# TUNISIE (TUN) - TAUX SH6 RÉELS
# Source: Douanes Tunisiennes
# TVA: 19%
# =============================================================================

TUN_HS6_TARIFFS = {
    # HUILE D'OLIVE
    "150910": {"dd": 0.00, "description_fr": "Huile d'olive vierge", "description_en": "Virgin olive oil"},
    "150990": {"dd": 0.00, "description_fr": "Autres huiles d'olive", "description_en": "Other olive oil"},
    
    # DATTES
    "080410": {"dd": 0.00, "description_fr": "Dattes fraîches ou séchées", "description_en": "Dates, fresh or dried"},
    
    # PHOSPHATES
    "251010": {"dd": 0.00, "description_fr": "Phosphates naturels", "description_en": "Natural phosphates"},
    "310310": {"dd": 0.05, "description_fr": "Superphosphates", "description_en": "Superphosphates"},
    
    # TEXTILES - Industrie majeure
    "610910": {"dd": 0.30, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.30, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620520": {"dd": 0.30, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.10, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # ÉLECTRONIQUE - Zone franche
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# LIBYE (LBY) - TAUX SH6 RÉELS
# Source: Libyan Customs Authority
# TVA: 0% (pas de TVA)
# =============================================================================

LBY_HS6_TARIFFS = {
    # PÉTROLE - Export quasi-exclusif
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271111": {"dd": 0.00, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    "271012": {"dd": 0.00, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # RIZ
    "100630": {"dd": 0.05, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.05, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.05, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.05, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.10, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MAURITANIE (MRT) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Mauritanie
# TVA: 16%
# =============================================================================

MRT_HS6_TARIFFS = {
    # MINERAI DE FER - Principal export
    "260111": {"dd": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    "260112": {"dd": 0.00, "description_fr": "Minerai de fer aggloméré", "description_en": "Iron ore, agglomerated"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # CUIVRE
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    
    # POISSON
    "030341": {"dd": 0.00, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "030489": {"dd": 0.05, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "030617": {"dd": 0.05, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # RIZ
    "100630": {"dd": 0.05, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.10, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.10, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.10, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.20, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}


# =============================================================================
# SACU - UNION DOUANIÈRE D'AFRIQUE AUSTRALE
# =============================================================================

# =============================================================================
# BOTSWANA (BWA) - TAUX SH6 RÉELS
# Source: BURS Botswana, SACU Tariff
# TVA: 14%
# =============================================================================

BWA_HS6_TARIFFS = {
    # DIAMANTS - Principal export
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    "710239": {"dd": 0.00, "description_fr": "Diamants gemmes travaillés", "description_en": "Gem diamonds, worked"},
    
    # CUIVRE ET NICKEL
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    "750110": {"dd": 0.00, "description_fr": "Mattes de nickel", "description_en": "Nickel mattes"},
    
    # VIANDE BOVINE
    "020130": {"dd": 0.00, "description_fr": "Viande bovine désossée fraîche", "description_en": "Fresh boneless beef"},
    "020230": {"dd": 0.00, "description_fr": "Viande bovine désossée congelée", "description_en": "Frozen boneless beef"},
    
    # VÉHICULES - SACU Tariff
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES - SACU Protection
    "610910": {"dd": 0.45, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.45, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # RIZ
    "100630": {"dd": 0.00, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# NAMIBIE (NAM) - TAUX SH6 RÉELS
# Source: NamRA Namibia, SACU Tariff
# TVA: 15%
# =============================================================================

NAM_HS6_TARIFFS = {
    # DIAMANTS
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # URANIUM
    "261210": {"dd": 0.00, "description_fr": "Minerais d'uranium", "description_en": "Uranium ores"},
    "284410": {"dd": 0.00, "description_fr": "Uranium naturel", "description_en": "Natural uranium"},
    
    # ZINC
    "260800": {"dd": 0.00, "description_fr": "Minerais de zinc", "description_en": "Zinc ores"},
    
    # POISSON
    "030489": {"dd": 0.00, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "160414": {"dd": 0.00, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # VIANDE BOVINE
    "020130": {"dd": 0.00, "description_fr": "Viande bovine désossée fraîche", "description_en": "Fresh boneless beef"},
    
    # VÉHICULES - SACU
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES - SACU
    "610910": {"dd": 0.45, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # RIZ
    "100630": {"dd": 0.00, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# LESOTHO (LSO) - TAUX SH6 RÉELS
# Source: LRA Lesotho, SACU Tariff
# TVA: 15%
# =============================================================================

LSO_HS6_TARIFFS = {
    # DIAMANTS
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # TEXTILES - Industrie majeure (AGOA)
    "610910": {"dd": 0.45, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.45, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "611020": {"dd": 0.45, "description_fr": "Pulls en coton", "description_en": "Cotton pullovers"},
    
    # LAINE
    "510111": {"dd": 0.00, "description_fr": "Laine en suint", "description_en": "Greasy shorn wool"},
    "510119": {"dd": 0.00, "description_fr": "Autres laines en suint", "description_en": "Other greasy wool"},
    
    # EAU
    "220110": {"dd": 0.00, "description_fr": "Eaux minérales", "description_en": "Mineral waters"},
    
    # VÉHICULES - SACU
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # RIZ
    "100630": {"dd": 0.00, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# ESWATINI (SWZ) - TAUX SH6 RÉELS
# Source: SRA Eswatini, SACU Tariff
# TVA: 15%
# =============================================================================

SWZ_HS6_TARIFFS = {
    # SUCRE - Principal export
    "170114": {"dd": 0.00, "description_fr": "Sucre de canne brut", "description_en": "Raw cane sugar"},
    "170199": {"dd": 0.00, "description_fr": "Sucre de canne raffiné", "description_en": "Refined cane sugar"},
    
    # TEXTILES
    "610910": {"dd": 0.45, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.45, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # AGRUMES
    "080510": {"dd": 0.00, "description_fr": "Oranges fraîches", "description_en": "Fresh oranges"},
    
    # CONCENTRÉ DE BOISSONS
    "210690": {"dd": 0.05, "description_fr": "Préparations alimentaires", "description_en": "Food preparations"},
    
    # VÉHICULES - SACU
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # RIZ
    "100630": {"dd": 0.00, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}


# =============================================================================
# AUTRES PAYS AFRICAINS
# =============================================================================

# =============================================================================
# ÉTHIOPIE (ETH) - TAUX SH6 RÉELS
# Source: MoR Ethiopia
# TVA: 15%
# =============================================================================

ETH_HS6_TARIFFS = {
    # CAFÉ - Principal export
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # FLEURS
    "060311": {"dd": 0.00, "description_fr": "Roses fraîches coupées", "description_en": "Fresh cut roses"},
    "060319": {"dd": 0.00, "description_fr": "Autres fleurs coupées", "description_en": "Other cut flowers"},
    
    # LÉGUMINEUSES
    "071339": {"dd": 0.00, "description_fr": "Haricots secs", "description_en": "Dried beans"},
    "071340": {"dd": 0.00, "description_fr": "Lentilles sèches", "description_en": "Dried lentils"},
    
    # SÉSAME
    "120740": {"dd": 0.00, "description_fr": "Graines de sésame", "description_en": "Sesame seeds"},
    
    # TEXTILES - Industrie en développement
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # CUIR
    "410411": {"dd": 0.00, "description_fr": "Cuirs de bovins pleine fleur", "description_en": "Full grain bovine leather"},
    "640391": {"dd": 0.30, "description_fr": "Chaussures semelle cuir", "description_en": "Leather sole footwear"},
    
    # RIZ
    "100630": {"dd": 0.25, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - Protection industrie
    "870321": {"dd": 0.35, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# DJIBOUTI (DJI) - TAUX SH6 RÉELS
# Source: Djibouti Customs
# TVA: 10%
# =============================================================================

DJI_HS6_TARIFFS = {
    # RÉEXPORTATION - Hub régional
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # TEXTILES
    "610910": {"dd": 0.20, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# ÉRYTHRÉE (ERI) - TAUX SH6 RÉELS
# Source: Eritrea Customs
# TVA: 5%
# =============================================================================

ERI_HS6_TARIFFS = {
    # OR ET CUIVRE
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    
    # ZINC
    "260800": {"dd": 0.00, "description_fr": "Minerais de zinc", "description_en": "Zinc ores"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.20, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SOUDAN (SDN) - TAUX SH6 RÉELS
# Source: Sudan Customs
# TVA: 17%
# =============================================================================

SDN_HS6_TARIFFS = {
    # OR - Principal export
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # PÉTROLE (Résiduel)
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    
    # SÉSAME
    "120740": {"dd": 0.00, "description_fr": "Graines de sésame", "description_en": "Sesame seeds"},
    
    # GOMME ARABIQUE
    "130120": {"dd": 0.00, "description_fr": "Gomme arabique", "description_en": "Gum arabic"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé", "description_en": "Cotton, not carded"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # RIZ
    "100630": {"dd": 0.20, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.25, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.10, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SOMALIE (SOM) - TAUX SH6 RÉELS
# Source: Estimations (système douanier en reconstruction)
# TVA: 0% (pas de TVA formelle)
# =============================================================================

SOM_HS6_TARIFFS = {
    # BÉTAIL - Principal export
    "010229": {"dd": 0.00, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.00, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    "010420": {"dd": 0.00, "description_fr": "Caprins vivants", "description_en": "Live goats"},
    
    # BANANE
    "080310": {"dd": 0.10, "description_fr": "Bananes fraîches", "description_en": "Bananas, fresh"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.15, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.15, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.15, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.15, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SÃO TOMÉ ET PRÍNCIPE (STP) - TAUX SH6 RÉELS
# Source: DGI São Tomé
# TVA: 15%
# =============================================================================

STP_HS6_TARIFFS = {
    # CACAO - Principal export
    "180100": {"dd": 0.00, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180400": {"dd": 0.05, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # HUILE DE PALME
    "151110": {"dd": 0.05, "description_fr": "Huile de palme brute", "description_en": "Crude palm oil"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.20, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}
