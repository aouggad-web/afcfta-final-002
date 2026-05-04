"""
Tarifs douaniers SH6 pour TOUS les pays africains - Partie 1
CEDEAO/ECOWAS (15 pays) + CEMAC (6 pays)
Sources: OMC ITC, CNUCED TRAINS, TEC CEDEAO, TEC CEMAC
Dernière mise à jour: Janvier 2025
"""

# =============================================================================
# SÉNÉGAL (SEN) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Sénégal, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1%
# =============================================================================

SEN_HS6_TARIFFS = {
    # ARACHIDE - Premier exportateur
    "120241": {"dd": 0.00, "description_fr": "Arachides en coques", "description_en": "Groundnuts in shell"},
    "120242": {"dd": 0.00, "description_fr": "Arachides décortiquées", "description_en": "Groundnuts, shelled"},
    "150810": {"dd": 0.05, "description_fr": "Huile d'arachide brute", "description_en": "Groundnut oil, crude"},
    "150890": {"dd": 0.10, "description_fr": "Huile d'arachide raffinée", "description_en": "Groundnut oil, refined"},
    
    # POISSON
    "030211": {"dd": 0.05, "description_fr": "Truites fraîches", "description_en": "Trout, fresh"},
    "030341": {"dd": 0.05, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "030617": {"dd": 0.10, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    "160414": {"dd": 0.20, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # PHOSPHATES
    "251010": {"dd": 0.00, "description_fr": "Phosphates naturels", "description_en": "Natural phosphates"},
    "310310": {"dd": 0.05, "description_fr": "Superphosphates", "description_en": "Superphosphates"},
    
    # RIZ - TEC CEDEAO
    "100610": {"dd": 0.10, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"dd": 0.10, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # CIMENT
    "252321": {"dd": 0.20, "description_fr": "Ciment Portland ordinaire", "description_en": "Ordinary Portland cement"},
    
    # VÉHICULES - TEC CEDEAO
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES
    "520100": {"dd": 0.05, "description_fr": "Coton non cardé", "description_en": "Cotton, not carded"},
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# MALI (MLI) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Mali, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1%
# =============================================================================

MLI_HS6_TARIFFS = {
    # OR - Premier exportateur
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"dd": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    "520210": {"dd": 0.05, "description_fr": "Déchets de coton", "description_en": "Cotton waste"},
    "520300": {"dd": 0.05, "description_fr": "Coton cardé ou peigné", "description_en": "Cotton, carded or combed"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    "010420": {"dd": 0.05, "description_fr": "Caprins vivants", "description_en": "Live goats"},
    
    # RIZ
    "100610": {"dd": 0.10, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# BURKINA FASO (BFA) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes BF, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1%
# =============================================================================

BFA_HS6_TARIFFS = {
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"dd": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    "520210": {"dd": 0.05, "description_fr": "Déchets de coton", "description_en": "Cotton waste"},
    
    # KARITÉ
    "151590": {"dd": 0.05, "description_fr": "Beurre de karité", "description_en": "Shea butter"},
    
    # SÉSAME
    "120740": {"dd": 0.00, "description_fr": "Graines de sésame", "description_en": "Sesame seeds"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# BÉNIN (BEN) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Bénin, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1%
# =============================================================================

BEN_HS6_TARIFFS = {
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    "520210": {"dd": 0.05, "description_fr": "Déchets de coton", "description_en": "Cotton waste"},
    
    # NOIX DE CAJOU
    "080131": {"dd": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    "080132": {"dd": 0.10, "description_fr": "Noix de cajou décortiquées", "description_en": "Cashew nuts, shelled"},
    
    # KARITÉ
    "151590": {"dd": 0.05, "description_fr": "Beurre de karité", "description_en": "Shea butter"},
    
    # HUILE DE PALME
    "151110": {"dd": 0.10, "description_fr": "Huile de palme brute", "description_en": "Crude palm oil"},
    
    # RIZ - Réexportation
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - Réexportation importante
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.20, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# TOGO (TGO) - TAUX SH6 RÉELS
# Source: OTR Togo, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1%
# =============================================================================

TGO_HS6_TARIFFS = {
    # PHOSPHATES
    "251010": {"dd": 0.00, "description_fr": "Phosphates naturels", "description_en": "Natural phosphates"},
    "310310": {"dd": 0.05, "description_fr": "Superphosphates", "description_en": "Superphosphates"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    
    # CACAO
    "180100": {"dd": 0.05, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180400": {"dd": 0.10, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # CIMENT - Port de Lomé
    "252321": {"dd": 0.20, "description_fr": "Ciment Portland ordinaire", "description_en": "Ordinary Portland cement"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# NIGER (NER) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Niger, TEC CEDEAO/UEMOA
# TVA: 19% | RS: 1% | PCS: 1%
# =============================================================================

NER_HS6_TARIFFS = {
    # URANIUM
    "261210": {"dd": 0.00, "description_fr": "Minerais d'uranium", "description_en": "Uranium ores"},
    "284410": {"dd": 0.00, "description_fr": "Uranium naturel", "description_en": "Natural uranium"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # OIGNON
    "070310": {"dd": 0.20, "description_fr": "Oignons frais", "description_en": "Fresh onions"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# GUINÉE (GIN) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Guinée, TEC CEDEAO
# TVA: 18%
# =============================================================================

GIN_HS6_TARIFFS = {
    # BAUXITE - Premier réserves mondiales
    "260600": {"dd": 0.00, "description_fr": "Minerais d'aluminium (bauxite)", "description_en": "Aluminum ores (bauxite)"},
    "281820": {"dd": 0.03, "description_fr": "Alumine", "description_en": "Aluminum oxide"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # DIAMANTS
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# GUINÉE-BISSAU (GNB) - TAUX SH6 RÉELS
# Source: TEC CEDEAO/UEMOA
# TVA: 17%
# =============================================================================

GNB_HS6_TARIFFS = {
    # NOIX DE CAJOU - Principal export
    "080131": {"dd": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    "080132": {"dd": 0.10, "description_fr": "Noix de cajou décortiquées", "description_en": "Cashew nuts, shelled"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "030617": {"dd": 0.10, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# GAMBIE (GMB) - TAUX SH6 RÉELS
# Source: GRA Gambia, TEC CEDEAO
# TVA: 15%
# =============================================================================

GMB_HS6_TARIFFS = {
    # ARACHIDE
    "120241": {"dd": 0.00, "description_fr": "Arachides en coques", "description_en": "Groundnuts in shell"},
    "120242": {"dd": 0.00, "description_fr": "Arachides décortiquées", "description_en": "Groundnuts, shelled"},
    "150810": {"dd": 0.05, "description_fr": "Huile d'arachide brute", "description_en": "Groundnut oil, crude"},
    
    # POISSON
    "030489": {"dd": 0.10, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - Réexportation
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# SIERRA LEONE (SLE) - TAUX SH6 RÉELS
# Source: NRA Sierra Leone, TEC CEDEAO
# TVA: 15%
# =============================================================================

SLE_HS6_TARIFFS = {
    # DIAMANTS
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # MINERAI DE FER
    "260111": {"dd": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    
    # BAUXITE
    "260600": {"dd": 0.00, "description_fr": "Minerais d'aluminium (bauxite)", "description_en": "Aluminum ores"},
    
    # CACAO
    "180100": {"dd": 0.05, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# LIBÉRIA (LBR) - TAUX SH6 RÉELS
# Source: LRA Liberia, TEC CEDEAO
# TVA: 10%
# =============================================================================

LBR_HS6_TARIFFS = {
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # DIAMANTS
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # MINERAI DE FER
    "260111": {"dd": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    
    # CAOUTCHOUC
    "400110": {"dd": 0.00, "description_fr": "Latex de caoutchouc naturel", "description_en": "Natural rubber latex"},
    "400121": {"dd": 0.05, "description_fr": "Feuilles fumées de caoutchouc", "description_en": "Smoked rubber sheets"},
    
    # HUILE DE PALME
    "151110": {"dd": 0.10, "description_fr": "Huile de palme brute", "description_en": "Crude palm oil"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# CAP-VERT (CPV) - TAUX SH6 RÉELS
# Source: Alfândegas Cabo Verde, TEC CEDEAO
# TVA: 15%
# =============================================================================

CPV_HS6_TARIFFS = {
    # POISSON
    "030341": {"dd": 0.00, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "030489": {"dd": 0.05, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "160414": {"dd": 0.10, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}


# =============================================================================
# CEMAC - AFRIQUE CENTRALE
# =============================================================================

# =============================================================================
# CAMEROUN (CMR) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Cameroun, TEC CEMAC
# TVA: 19.25% | TCI: 1%
# =============================================================================

CMR_HS6_TARIFFS = {
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271121": {"dd": 0.05, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    
    # CACAO
    "180100": {"dd": 0.00, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180310": {"dd": 0.10, "description_fr": "Pâte de cacao non dégraissée", "description_en": "Cocoa paste, not defatted"},
    "180400": {"dd": 0.10, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # BANANE
    "080310": {"dd": 0.20, "description_fr": "Bananes fraîches", "description_en": "Bananas, fresh"},
    
    # BOIS
    "440110": {"dd": 0.00, "description_fr": "Bois de chauffage", "description_en": "Fuel wood"},
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    "440729": {"dd": 0.10, "description_fr": "Bois sciés tropicaux", "description_en": "Sawn tropical wood"},
    
    # ALUMINIUM
    "760110": {"dd": 0.05, "description_fr": "Aluminium non allié brut", "description_en": "Unwrought aluminum"},
    
    # COTON
    "520100": {"dd": 0.05, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES - TEC CEMAC
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES
    "610910": {"dd": 0.30, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.30, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # CIMENT
    "252321": {"dd": 0.20, "description_fr": "Ciment Portland ordinaire", "description_en": "Ordinary Portland cement"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # MACHINES
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# GABON (GAB) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Gabon, TEC CEMAC
# TVA: 18% | TCI: 1%
# =============================================================================

GAB_HS6_TARIFFS = {
    # PÉTROLE - Principal export
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # MANGANÈSE
    "260200": {"dd": 0.00, "description_fr": "Minerais de manganèse", "description_en": "Manganese ores"},
    "811100": {"dd": 0.03, "description_fr": "Manganèse brut", "description_en": "Unwrought manganese"},
    
    # BOIS
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    "440729": {"dd": 0.10, "description_fr": "Bois sciés tropicaux", "description_en": "Sawn tropical wood"},
    "441114": {"dd": 0.15, "description_fr": "Contreplaqués tropicaux", "description_en": "Tropical plywood"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# CONGO (COG) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Congo, TEC CEMAC
# TVA: 18% | TCI: 1%
# =============================================================================

COG_HS6_TARIFFS = {
    # PÉTROLE - Principal export
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # BOIS
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    "440729": {"dd": 0.10, "description_fr": "Bois sciés tropicaux", "description_en": "Sawn tropical wood"},
    
    # SUCRE
    "170114": {"dd": 0.20, "description_fr": "Sucre de canne brut", "description_en": "Raw cane sugar"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# TCHAD (TCD) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes Tchad, TEC CEMAC
# TVA: 18% | TCI: 1%
# =============================================================================

TCD_HS6_TARIFFS = {
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    
    # BÉTAIL
    "010229": {"dd": 0.05, "description_fr": "Bovins vivants autres", "description_en": "Other live bovine"},
    "010410": {"dd": 0.05, "description_fr": "Ovins vivants", "description_en": "Live sheep"},
    
    # GOMME ARABIQUE
    "130120": {"dd": 0.00, "description_fr": "Gomme arabique", "description_en": "Gum arabic"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# CENTRAFRIQUE (CAF) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes RCA, TEC CEMAC
# TVA: 19% | TCI: 1%
# =============================================================================

CAF_HS6_TARIFFS = {
    # DIAMANTS
    "710210": {"dd": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710231": {"dd": 0.00, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    
    # BOIS
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    "440729": {"dd": 0.10, "description_fr": "Bois sciés tropicaux", "description_en": "Sawn tropical wood"},
    
    # COTON
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié", "description_en": "Coffee, not roasted"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}

# =============================================================================
# GUINÉE ÉQUATORIALE (GNQ) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes GE, TEC CEMAC
# TVA: 15% | TCI: 1%
# =============================================================================

GNQ_HS6_TARIFFS = {
    # PÉTROLE ET GAZ - Principal export
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271111": {"dd": 0.00, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    "271121": {"dd": 0.05, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    
    # BOIS
    "440320": {"dd": 0.05, "description_fr": "Bois bruts tropicaux", "description_en": "Tropical logs"},
    
    # CACAO
    "180100": {"dd": 0.05, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    
    # RIZ
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
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
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
}
