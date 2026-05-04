"""
Tarifs douaniers SH6 pour TOUS les pays africains - Partie 2
EAC (7 pays) + SADC (16 pays) + Afrique du Nord (6 pays) + Autres (6 pays)
Sources: OMC ITC, CNUCED TRAINS, TEC EAC, SACU, Administrations nationales
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# EAC - COMMUNAUTÉ D'AFRIQUE DE L'EST
# =============================================================================

# =============================================================================
# TANZANIE (TZA) - TAUX SH6 RÉELS
# Source: TRA Tanzania, EAC CET
# TVA: 18%
# =============================================================================

TZA_HS6_TARIFFS = {
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"dd": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # THÉ
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté ≤3kg", "description_en": "Black tea, fermented ≤3kg"},
    "090240": {"dd": 0.00, "description_fr": "Thé noir fermenté >3kg", "description_en": "Black tea, fermented >3kg"},
    
    # NOIX DE CAJOU
    "080131": {"dd": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    "080132": {"dd": 0.10, "description_fr": "Noix de cajou décortiquées", "description_en": "Cashew nuts, shelled"},
    
    # TABAC
    "240110": {"dd": 0.25, "description_fr": "Tabac non écôté", "description_en": "Tobacco, not stemmed"},
    "240120": {"dd": 0.25, "description_fr": "Tabac écôté", "description_en": "Tobacco, stemmed"},
    
    # CLOUS DE GIROFLE
    "090710": {"dd": 0.00, "description_fr": "Clous de girofle", "description_en": "Cloves"},
    
    # RIZ - EAC Sensitive
    "100610": {"dd": 0.00, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"dd": 0.35, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.75, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - EAC CET
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé", "description_en": "Cotton, not carded"},
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES - EAC 0%
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# OUGANDA (UGA) - TAUX SH6 RÉELS
# Source: URA Uganda, EAC CET
# TVA: 18%
# =============================================================================

UGA_HS6_TARIFFS = {
    # CAFÉ - Principal export
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # THÉ
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté", "description_en": "Black tea, fermented"},
    
    # POISSON - Lac Victoria
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé", "description_en": "Cotton, not carded"},
    
    # FLEURS
    "060311": {"dd": 0.00, "description_fr": "Roses fraîches coupées", "description_en": "Fresh cut roses"},
    "060319": {"dd": 0.00, "description_fr": "Autres fleurs coupées", "description_en": "Other cut flowers"},
    
    # RIZ - EAC Sensitive
    "100620": {"dd": 0.35, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.75, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# RWANDA (RWA) - TAUX SH6 RÉELS
# Source: RRA Rwanda, EAC CET
# TVA: 18%
# =============================================================================

RWA_HS6_TARIFFS = {
    # OR ET MINERAIS
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "261590": {"dd": 0.00, "description_fr": "Minerais de niobium et tantale", "description_en": "Niobium and tantalum ores"},
    "260900": {"dd": 0.00, "description_fr": "Minerais d'étain", "description_en": "Tin ores"},
    "261100": {"dd": 0.00, "description_fr": "Minerais de tungstène", "description_en": "Tungsten ores"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # THÉ
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté", "description_en": "Black tea, fermented"},
    
    # RIZ - EAC Sensitive
    "100620": {"dd": 0.35, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.75, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# BURUNDI (BDI) - TAUX SH6 RÉELS
# Source: OBR Burundi, EAC CET
# TVA: 18%
# =============================================================================

BDI_HS6_TARIFFS = {
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # CAFÉ - Principal export
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # THÉ
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté", "description_en": "Black tea, fermented"},
    
    # MINERAIS
    "261590": {"dd": 0.00, "description_fr": "Minerais de niobium et tantale", "description_en": "Niobium and tantalum ores"},
    
    # RIZ
    "100620": {"dd": 0.35, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.75, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# RD CONGO (COD) - TAUX SH6 RÉELS
# Source: DGDA RDC, EAC CET (membre depuis 2022)
# TVA: 16%
# =============================================================================

COD_HS6_TARIFFS = {
    # CUIVRE ET COBALT - Principaux exports
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    "740200": {"dd": 0.00, "description_fr": "Cuivre non affiné", "description_en": "Unrefined copper"},
    "740311": {"dd": 0.05, "description_fr": "Cathodes de cuivre", "description_en": "Copper cathodes"},
    "810520": {"dd": 0.00, "description_fr": "Mattes de cobalt", "description_en": "Cobalt mattes"},
    "282200": {"dd": 0.05, "description_fr": "Oxydes de cobalt", "description_en": "Cobalt oxides"},
    
    # OR ET DIAMANTS
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # COLTAN
    "261590": {"dd": 0.00, "description_fr": "Minerais de niobium et tantale", "description_en": "Niobium and tantalum ores"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    
    # BOIS
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    "440729": {"dd": 0.10, "description_fr": "Bois sciés tropicaux", "description_en": "Sawn tropical wood"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # RIZ
    "100630": {"dd": 0.25, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SOUDAN DU SUD (SSD) - TAUX SH6 RÉELS
# Source: South Sudan Customs, EAC CET
# TVA: 18%
# =============================================================================

SSD_HS6_TARIFFS = {
    # PÉTROLE - Principal export
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # RIZ
    "100630": {"dd": 0.25, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}


# =============================================================================
# SADC - AUTRES PAYS (hors SACU)
# =============================================================================

# =============================================================================
# ANGOLA (AGO) - TAUX SH6 RÉELS
# Source: AGT Angola
# TVA: 14%
# =============================================================================

AGO_HS6_TARIFFS = {
    # PÉTROLE - Principal export
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.02, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271111": {"dd": 0.00, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    
    # DIAMANTS
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # CAFÉ
    "090111": {"dd": 0.02, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # RIZ
    "100630": {"dd": 0.20, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.02, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.02, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.02, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.30, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.02, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.02, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MOZAMBIQUE (MOZ) - TAUX SH6 RÉELS
# Source: AT Mozambique
# TVA: 17%
# =============================================================================

MOZ_HS6_TARIFFS = {
    # ALUMINIUM
    "760110": {"dd": 0.00, "description_fr": "Aluminium non allié brut", "description_en": "Unwrought aluminum"},
    "760120": {"dd": 0.025, "description_fr": "Alliages d'aluminium bruts", "description_en": "Unwrought aluminum alloys"},
    
    # CHARBON
    "270112": {"dd": 0.00, "description_fr": "Houille bitumineuse", "description_en": "Bituminous coal"},
    
    # GAZ NATUREL
    "271111": {"dd": 0.00, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    
    # CREVETTES
    "030617": {"dd": 0.00, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    
    # SUCRE
    "170114": {"dd": 0.20, "description_fr": "Sucre de canne brut", "description_en": "Raw cane sugar"},
    "170199": {"dd": 0.20, "description_fr": "Sucre de canne raffiné", "description_en": "Refined cane sugar"},
    
    # NOIX DE CAJOU
    "080131": {"dd": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    
    # TABAC
    "240110": {"dd": 0.00, "description_fr": "Tabac non écôté", "description_en": "Tobacco, not stemmed"},
    
    # RIZ
    "100630": {"dd": 0.20, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.25, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.025, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.025, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# ZAMBIE (ZMB) - TAUX SH6 RÉELS
# Source: ZRA Zambia
# TVA: 16%
# =============================================================================

ZMB_HS6_TARIFFS = {
    # CUIVRE - Principal export
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    "740200": {"dd": 0.00, "description_fr": "Cuivre non affiné", "description_en": "Unrefined copper"},
    "740311": {"dd": 0.00, "description_fr": "Cathodes de cuivre", "description_en": "Copper cathodes"},
    "740710": {"dd": 0.05, "description_fr": "Barres de cuivre affiné", "description_en": "Refined copper bars"},
    
    # COBALT
    "810520": {"dd": 0.00, "description_fr": "Mattes de cobalt", "description_en": "Cobalt mattes"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # TABAC
    "240110": {"dd": 0.00, "description_fr": "Tabac non écôté", "description_en": "Tobacco, not stemmed"},
    
    # MAÏS
    "100510": {"dd": 0.05, "description_fr": "Maïs de semence", "description_en": "Maize seed"},
    "100590": {"dd": 0.05, "description_fr": "Maïs autre", "description_en": "Other maize"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.15, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.15, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.15, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.25, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# ZIMBABWE (ZWE) - TAUX SH6 RÉELS
# Source: ZIMRA Zimbabwe
# TVA: 15%
# =============================================================================

ZWE_HS6_TARIFFS = {
    # OR ET PLATINE
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "711011": {"dd": 0.00, "description_fr": "Platine brut", "description_en": "Platinum, unwrought"},
    
    # DIAMANTS
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # NICKEL
    "750110": {"dd": 0.00, "description_fr": "Mattes de nickel", "description_en": "Nickel mattes"},
    
    # TABAC
    "240110": {"dd": 0.00, "description_fr": "Tabac non écôté", "description_en": "Tobacco, not stemmed"},
    "240120": {"dd": 0.05, "description_fr": "Tabac écôté", "description_en": "Tobacco, stemmed"},
    
    # FERROCHROME
    "720241": {"dd": 0.00, "description_fr": "Ferrochrome >4% carbone", "description_en": "Ferrochrome >4% carbon"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé", "description_en": "Cotton, not carded"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.15, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.15, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.15, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.40, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MALAWI (MWI) - TAUX SH6 RÉELS
# Source: MRA Malawi
# TVA: 16.5%
# =============================================================================

MWI_HS6_TARIFFS = {
    # TABAC - Principal export
    "240110": {"dd": 0.00, "description_fr": "Tabac non écôté", "description_en": "Tobacco, not stemmed"},
    "240120": {"dd": 0.00, "description_fr": "Tabac écôté", "description_en": "Tobacco, stemmed"},
    
    # THÉ
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté", "description_en": "Black tea, fermented"},
    
    # SUCRE
    "170114": {"dd": 0.20, "description_fr": "Sucre de canne brut", "description_en": "Raw cane sugar"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # LÉGUMINEUSES
    "071339": {"dd": 0.00, "description_fr": "Haricots secs", "description_en": "Dried beans"},
    "071340": {"dd": 0.00, "description_fr": "Lentilles sèches", "description_en": "Dried lentils"},
    
    # RIZ
    "100630": {"dd": 0.20, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.30, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.10, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MADAGASCAR (MDG) - TAUX SH6 RÉELS
# Source: DGI Madagascar
# TVA: 20%
# =============================================================================

MDG_HS6_TARIFFS = {
    # VANILLE - Premier producteur mondial
    "090510": {"dd": 0.00, "description_fr": "Vanille non broyée", "description_en": "Vanilla, neither crushed nor ground"},
    "090520": {"dd": 0.00, "description_fr": "Vanille broyée", "description_en": "Vanilla, crushed or ground"},
    
    # CLOUS DE GIROFLE
    "090710": {"dd": 0.00, "description_fr": "Clous de girofle", "description_en": "Cloves"},
    
    # NICKEL ET COBALT
    "750110": {"dd": 0.00, "description_fr": "Mattes de nickel", "description_en": "Nickel mattes"},
    "810520": {"dd": 0.00, "description_fr": "Mattes de cobalt", "description_en": "Cobalt mattes"},
    
    # ILMÉNITE (Titane)
    "261400": {"dd": 0.00, "description_fr": "Minerais de titane", "description_en": "Titanium ores"},
    
    # CREVETTES
    "030617": {"dd": 0.00, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    
    # TEXTILES - Zones franches
    "610910": {"dd": 0.20, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.20, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.10, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.10, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.10, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.05, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MAURICE (MUS) - TAUX SH6 RÉELS
# Source: MRA Maurice
# TVA: 15%
# =============================================================================

MUS_HS6_TARIFFS = {
    # SUCRE
    "170114": {"dd": 0.00, "description_fr": "Sucre de canne brut", "description_en": "Raw cane sugar"},
    "170199": {"dd": 0.00, "description_fr": "Sucre de canne raffiné", "description_en": "Refined cane sugar"},
    
    # TEXTILES - Industrie majeure
    "610910": {"dd": 0.15, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.15, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620520": {"dd": 0.15, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    
    # THON EN CONSERVE
    "160414": {"dd": 0.00, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # RIZ
    "100630": {"dd": 0.15, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.15, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.15, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.15, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SEYCHELLES (SYC) - TAUX SH6 RÉELS
# Source: SRC Seychelles
# TVA: 15%
# =============================================================================

SYC_HS6_TARIFFS = {
    # THON
    "030341": {"dd": 0.00, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "160414": {"dd": 0.00, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # POISSON
    "030489": {"dd": 0.00, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
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
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# COMORES (COM) - TAUX SH6 RÉELS
# Source: DGI Comores
# TVA: 10%
# =============================================================================

COM_HS6_TARIFFS = {
    # VANILLE
    "090510": {"dd": 0.00, "description_fr": "Vanille non broyée", "description_en": "Vanilla, neither crushed nor ground"},
    
    # CLOUS DE GIROFLE
    "090710": {"dd": 0.00, "description_fr": "Clous de girofle", "description_en": "Cloves"},
    
    # YLANG-YLANG
    "330129": {"dd": 0.00, "description_fr": "Huiles essentielles", "description_en": "Essential oils"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
