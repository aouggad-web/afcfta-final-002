"""
Tarifs douaniers SH6 spécifiques par pays africain
Sources: OMC ITC, CNUCED TRAINS, WITS Banque Mondiale, Tarif Intégré national de chaque pays
Dernière mise à jour: Janvier 2025

Structure: COUNTRY_HS6_TARIFFS[iso3][hs6_code] = {
    "dd": taux_droit_douane,
    "description_fr": ...,
    "description_en": ...
}

Note: Ce fichier contient les taux SH6 réels pour les produits les plus échangés en Afrique.
Pour les codes non listés, le système utilise les taux par chapitre du pays.
"""

from typing import Dict, Optional, Tuple

# Import des tarifs par région
from etl.country_hs6_tariffs_cedeao_cemac import (
    SEN_HS6_TARIFFS, MLI_HS6_TARIFFS, BFA_HS6_TARIFFS, BEN_HS6_TARIFFS,
    TGO_HS6_TARIFFS, NER_HS6_TARIFFS, GIN_HS6_TARIFFS, GNB_HS6_TARIFFS,
    GMB_HS6_TARIFFS, SLE_HS6_TARIFFS, LBR_HS6_TARIFFS, CPV_HS6_TARIFFS,
    CMR_HS6_TARIFFS, GAB_HS6_TARIFFS, COG_HS6_TARIFFS, TCD_HS6_TARIFFS,
    CAF_HS6_TARIFFS, GNQ_HS6_TARIFFS
)

from etl.country_hs6_tariffs_eac_sadc import (
    TZA_HS6_TARIFFS, UGA_HS6_TARIFFS, RWA_HS6_TARIFFS, BDI_HS6_TARIFFS,
    COD_HS6_TARIFFS, SSD_HS6_TARIFFS,
    AGO_HS6_TARIFFS, MOZ_HS6_TARIFFS, ZMB_HS6_TARIFFS, ZWE_HS6_TARIFFS,
    MWI_HS6_TARIFFS, MDG_HS6_TARIFFS, MUS_HS6_TARIFFS, SYC_HS6_TARIFFS,
    COM_HS6_TARIFFS
)

from etl.country_hs6_tariffs_north_other import (
    DZA_HS6_TARIFFS, TUN_HS6_TARIFFS, LBY_HS6_TARIFFS, MRT_HS6_TARIFFS,
    BWA_HS6_TARIFFS, NAM_HS6_TARIFFS, LSO_HS6_TARIFFS, SWZ_HS6_TARIFFS,
    ETH_HS6_TARIFFS, DJI_HS6_TARIFFS, ERI_HS6_TARIFFS, SDN_HS6_TARIFFS,
    SOM_HS6_TARIFFS, STP_HS6_TARIFFS
)

# =============================================================================
# NIGERIA (NGA) - TAUX SH6 RÉELS
# Source: Nigeria Customs Service, ECOWAS TEC
# TVA: 7.5% | Prélèvements: CISS 1%, CEDEAO 0.5%, NAC 1%
# =============================================================================

NGA_HS6_TARIFFS = {
    # CACAO
    "180100": {"dd": 0.05, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180200": {"dd": 0.10, "description_fr": "Coques et pellicules de cacao", "description_en": "Cocoa shells"},
    "180310": {"dd": 0.10, "description_fr": "Pâte de cacao non dégraissée", "description_en": "Cocoa paste, not defatted"},
    "180320": {"dd": 0.10, "description_fr": "Pâte de cacao dégraissée", "description_en": "Cocoa paste, defatted"},
    "180400": {"dd": 0.10, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    "180500": {"dd": 0.10, "description_fr": "Poudre de cacao non sucrée", "description_en": "Cocoa powder, unsweetened"},
    "180610": {"dd": 0.20, "description_fr": "Poudre de cacao sucrée", "description_en": "Cocoa powder, sweetened"},
    "180620": {"dd": 0.20, "description_fr": "Chocolat en blocs > 2kg", "description_en": "Chocolate blocks > 2kg"},
    "180631": {"dd": 0.20, "description_fr": "Chocolat fourré", "description_en": "Filled chocolate"},
    "180632": {"dd": 0.20, "description_fr": "Chocolat non fourré", "description_en": "Unfilled chocolate"},
    "180690": {"dd": 0.20, "description_fr": "Autres préparations cacao", "description_en": "Other cocoa preparations"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié, non décaféiné", "description_en": "Coffee, not roasted, not decaf"},
    "090112": {"dd": 0.05, "description_fr": "Café non torréfié, décaféiné", "description_en": "Coffee, not roasted, decaf"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié, non décaféiné", "description_en": "Coffee, roasted, not decaf"},
    "090122": {"dd": 0.10, "description_fr": "Café torréfié, décaféiné", "description_en": "Coffee, roasted, decaf"},
    
    # RIZ - Produit sensible Nigeria
    "100610": {"dd": 0.10, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"dd": 0.50, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.60, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled or wholly milled rice"},
    "100640": {"dd": 0.10, "description_fr": "Brisures de riz", "description_en": "Broken rice"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271019": {"dd": 0.05, "description_fr": "Autres huiles de pétrole", "description_en": "Other petroleum oils"},
    "271111": {"dd": 0.05, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    "271121": {"dd": 0.05, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    
    # VÉHICULES - Levy automobile Nigeria
    "870321": {"dd": 0.35, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.35, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.35, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.35, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870331": {"dd": 0.35, "description_fr": "Véhicules diesel ≤1500cc", "description_en": "Diesel vehicles ≤1500cc"},
    "870332": {"dd": 0.35, "description_fr": "Véhicules diesel 1500-2500cc", "description_en": "Diesel vehicles 1500-2500cc"},
    "870333": {"dd": 0.35, "description_fr": "Véhicules diesel >2500cc", "description_en": "Diesel vehicles >2500cc"},
    "870421": {"dd": 0.20, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    "870422": {"dd": 0.20, "description_fr": "Camions 5-20 tonnes", "description_en": "Trucks 5-20 tonnes"},
    "870423": {"dd": 0.20, "description_fr": "Camions >20 tonnes", "description_en": "Trucks >20 tonnes"},
    
    # TEXTILES - Produits sensibles
    "520100": {"dd": 0.05, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded or combed"},
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "610990": {"dd": 0.35, "description_fr": "T-shirts autres matières", "description_en": "Other T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620462": {"dd": 0.35, "description_fr": "Pantalons femmes coton", "description_en": "Women's cotton trousers"},
    "620520": {"dd": 0.35, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    
    # MACHINES
    "841510": {"dd": 0.05, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "841821": {"dd": 0.20, "description_fr": "Réfrigérateurs ménagers", "description_en": "Household refrigerators"},
    "845011": {"dd": 0.20, "description_fr": "Machines à laver ≤10kg", "description_en": "Washing machines ≤10kg"},
    "847130": {"dd": 0.05, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "847141": {"dd": 0.05, "description_fr": "Autres ordinateurs", "description_en": "Other computers"},
    "851712": {"dd": 0.10, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    
    # CIMENT
    "252310": {"dd": 0.20, "description_fr": "Ciment Portland blanc", "description_en": "White Portland cement"},
    "252321": {"dd": 0.35, "description_fr": "Ciment Portland ordinaire", "description_en": "Ordinary Portland cement"},
    "252329": {"dd": 0.35, "description_fr": "Autres ciments Portland", "description_en": "Other Portland cement"},
    
    # MÉDICAMENTS - Exonérés
    "300210": {"dd": 0.00, "description_fr": "Antisérums", "description_en": "Antisera"},
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300410": {"dd": 0.00, "description_fr": "Médicaments pénicilline", "description_en": "Penicillin medicines"},
    "300420": {"dd": 0.00, "description_fr": "Médicaments antibiotiques", "description_en": "Antibiotic medicines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# CÔTE D'IVOIRE (CIV) - TAUX SH6 RÉELS
# Source: Direction Générale des Douanes CI, TEC CEDEAO/UEMOA
# TVA: 18% | RS: 1% | PCS: 1% | PCC: 0.5%
# =============================================================================

CIV_HS6_TARIFFS = {
    # CACAO - Premier producteur mondial
    "180100": {"dd": 0.00, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180200": {"dd": 0.05, "description_fr": "Coques et pellicules de cacao", "description_en": "Cocoa shells"},
    "180310": {"dd": 0.10, "description_fr": "Pâte de cacao non dégraissée", "description_en": "Cocoa paste, not defatted"},
    "180320": {"dd": 0.10, "description_fr": "Pâte de cacao dégraissée", "description_en": "Cocoa paste, defatted"},
    "180400": {"dd": 0.10, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    "180500": {"dd": 0.10, "description_fr": "Poudre de cacao non sucrée", "description_en": "Cocoa powder, unsweetened"},
    "180610": {"dd": 0.20, "description_fr": "Poudre de cacao sucrée", "description_en": "Cocoa powder, sweetened"},
    "180620": {"dd": 0.20, "description_fr": "Chocolat en blocs > 2kg", "description_en": "Chocolate blocks > 2kg"},
    "180631": {"dd": 0.20, "description_fr": "Chocolat fourré", "description_en": "Filled chocolate"},
    "180632": {"dd": 0.20, "description_fr": "Chocolat non fourré", "description_en": "Unfilled chocolate"},
    
    # CAFÉ
    "090111": {"dd": 0.05, "description_fr": "Café non torréfié, non décaféiné", "description_en": "Coffee, not roasted, not decaf"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # NOIX DE CAJOU - 2ème exportateur
    "080131": {"dd": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    "080132": {"dd": 0.10, "description_fr": "Noix de cajou décortiquées", "description_en": "Cashew nuts, shelled"},
    
    # CAOUTCHOUC
    "400110": {"dd": 0.00, "description_fr": "Latex de caoutchouc naturel", "description_en": "Natural rubber latex"},
    "400121": {"dd": 0.05, "description_fr": "Feuilles fumées de caoutchouc", "description_en": "Smoked rubber sheets"},
    "400122": {"dd": 0.05, "description_fr": "Caoutchouc naturel TSNR", "description_en": "Technically specified natural rubber"},
    
    # HUILE DE PALME
    "151110": {"dd": 0.10, "description_fr": "Huile de palme brute", "description_en": "Crude palm oil"},
    "151190": {"dd": 0.20, "description_fr": "Huile de palme raffinée", "description_en": "Refined palm oil"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271019": {"dd": 0.05, "description_fr": "Autres huiles de pétrole", "description_en": "Other petroleum oils"},
    
    # RIZ - TEC CEDEAO
    "100610": {"dd": 0.10, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"dd": 0.10, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.10, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled or wholly milled rice"},
    
    # VÉHICULES - TEC CEDEAO
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.20, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES - TEC CEDEAO
    "520100": {"dd": 0.05, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded or combed"},
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # MÉDICAMENTS - Exonérés
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# AFRIQUE DU SUD (ZAF) - TAUX SH6 RÉELS
# Source: SARS, SACU Tariff Schedule
# TVA: 15%
# =============================================================================

ZAF_HS6_TARIFFS = {
    # VÉHICULES - Secteur stratégique
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.25, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870331": {"dd": 0.25, "description_fr": "Véhicules diesel ≤1500cc", "description_en": "Diesel vehicles ≤1500cc"},
    "870332": {"dd": 0.25, "description_fr": "Véhicules diesel 1500-2500cc", "description_en": "Diesel vehicles 1500-2500cc"},
    "870333": {"dd": 0.25, "description_fr": "Véhicules diesel >2500cc", "description_en": "Diesel vehicles >2500cc"},
    "870340": {"dd": 0.25, "description_fr": "Véhicules électriques", "description_en": "Electric vehicles"},
    "870421": {"dd": 0.20, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    "870422": {"dd": 0.20, "description_fr": "Camions 5-20 tonnes", "description_en": "Trucks 5-20 tonnes"},
    
    # TEXTILES - Protection industrie locale
    "610910": {"dd": 0.45, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "610990": {"dd": 0.45, "description_fr": "T-shirts autres matières", "description_en": "Other T-shirts"},
    "620342": {"dd": 0.45, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620462": {"dd": 0.45, "description_fr": "Pantalons femmes coton", "description_en": "Women's cotton trousers"},
    "620520": {"dd": 0.40, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    "611020": {"dd": 0.45, "description_fr": "Pulls en coton", "description_en": "Cotton pullovers"},
    
    # OR ET PLATINE
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"dd": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    "711011": {"dd": 0.00, "description_fr": "Platine brut", "description_en": "Platinum, unwrought"},
    "711019": {"dd": 0.00, "description_fr": "Platine mi-ouvré", "description_en": "Platinum, semi-manufactured"},
    
    # MINERAIS
    "260300": {"dd": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    "261000": {"dd": 0.00, "description_fr": "Minerais de chrome", "description_en": "Chromium ores"},
    "260200": {"dd": 0.00, "description_fr": "Minerais de manganèse", "description_en": "Manganese ores"},
    "260111": {"dd": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    
    # VIN - Secteur d'exportation
    "220410": {"dd": 0.00, "description_fr": "Vins mousseux", "description_en": "Sparkling wine"},
    "220421": {"dd": 0.00, "description_fr": "Vins en contenants ≤2L", "description_en": "Wine in containers ≤2L"},
    "220429": {"dd": 0.00, "description_fr": "Vins en contenants >2L", "description_en": "Wine in containers >2L"},
    
    # AGRUMES
    "080510": {"dd": 0.00, "description_fr": "Oranges fraîches", "description_en": "Fresh oranges"},
    "080520": {"dd": 0.00, "description_fr": "Mandarines fraîches", "description_en": "Fresh mandarins"},
    "080540": {"dd": 0.00, "description_fr": "Pamplemousses frais", "description_en": "Fresh grapefruit"},
    
    # MACHINES
    "841510": {"dd": 0.00, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "841821": {"dd": 0.15, "description_fr": "Réfrigérateurs ménagers", "description_en": "Household refrigerators"},
    "845011": {"dd": 0.15, "description_fr": "Machines à laver ≤10kg", "description_en": "Washing machines ≤10kg"},
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# KENYA (KEN) - TAUX SH6 RÉELS
# Source: KRA, EAC CET
# TVA: 16% | IDF: 3.5%
# =============================================================================

KEN_HS6_TARIFFS = {
    # THÉ - Premier producteur africain
    "090210": {"dd": 0.00, "description_fr": "Thé vert non fermenté ≤3kg", "description_en": "Green tea, not fermented ≤3kg"},
    "090220": {"dd": 0.00, "description_fr": "Thé vert non fermenté >3kg", "description_en": "Green tea, not fermented >3kg"},
    "090230": {"dd": 0.00, "description_fr": "Thé noir fermenté ≤3kg", "description_en": "Black tea, fermented ≤3kg"},
    "090240": {"dd": 0.00, "description_fr": "Thé noir fermenté >3kg", "description_en": "Black tea, fermented >3kg"},
    
    # CAFÉ
    "090111": {"dd": 0.00, "description_fr": "Café non torréfié, non décaféiné", "description_en": "Coffee, not roasted, not decaf"},
    "090121": {"dd": 0.10, "description_fr": "Café torréfié", "description_en": "Coffee, roasted"},
    
    # FLEURS COUPÉES - Premier exportateur
    "060311": {"dd": 0.00, "description_fr": "Roses fraîches coupées", "description_en": "Fresh cut roses"},
    "060312": {"dd": 0.00, "description_fr": "Oeillets frais coupés", "description_en": "Fresh cut carnations"},
    "060314": {"dd": 0.00, "description_fr": "Chrysanthèmes frais", "description_en": "Fresh chrysanthemums"},
    "060319": {"dd": 0.00, "description_fr": "Autres fleurs coupées", "description_en": "Other cut flowers"},
    
    # LÉGUMES
    "070200": {"dd": 0.25, "description_fr": "Tomates fraîches", "description_en": "Fresh tomatoes"},
    "070310": {"dd": 0.25, "description_fr": "Oignons frais", "description_en": "Fresh onions"},
    "070990": {"dd": 0.25, "description_fr": "Autres légumes frais", "description_en": "Other fresh vegetables"},
    
    # RIZ - EAC CET
    "100610": {"dd": 0.00, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"dd": 0.35, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"dd": 0.75, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled or wholly milled rice"},
    
    # VÉHICULES - EAC CET + Protection locale
    "870321": {"dd": 0.25, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.25, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.25, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.25, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # TEXTILES - EAC Sensitive
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded or combed"},
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # MACHINES - EAC 0%
    "841510": {"dd": 0.00, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# ÉGYPTE (EGY) - TAUX SH6 RÉELS
# Source: Egyptian Customs Authority
# TVA: 14%
# =============================================================================

EGY_HS6_TARIFFS = {
    # COTON - Exportateur historique
    "520100": {"dd": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded or combed"},
    "520511": {"dd": 0.05, "description_fr": "Fils de coton simple", "description_en": "Single cotton yarn"},
    "520512": {"dd": 0.05, "description_fr": "Fils de coton peigné", "description_en": "Combed cotton yarn"},
    
    # TEXTILES - Protection industrie
    "610910": {"dd": 0.40, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "610990": {"dd": 0.40, "description_fr": "T-shirts autres matières", "description_en": "Other T-shirts"},
    "620342": {"dd": 0.40, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620520": {"dd": 0.40, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    
    # PÉTROLE ET GAZ
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271111": {"dd": 0.02, "description_fr": "Gaz naturel liquéfié", "description_en": "Natural gas, liquefied"},
    "271121": {"dd": 0.02, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    
    # AGRUMES
    "080510": {"dd": 0.00, "description_fr": "Oranges fraîches", "description_en": "Fresh oranges"},
    "080520": {"dd": 0.00, "description_fr": "Mandarines fraîches", "description_en": "Fresh mandarins"},
    
    # VÉHICULES - Taux variables
    "870321": {"dd": 0.40, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.40, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.135, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.135, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"dd": 0.05, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # MACHINES
    "841510": {"dd": 0.05, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "841821": {"dd": 0.30, "description_fr": "Réfrigérateurs ménagers", "description_en": "Household refrigerators"},
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.00, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # CÉRÉALES - Égypte grand importateur
    "100110": {"dd": 0.00, "description_fr": "Blé dur", "description_en": "Durum wheat"},
    "100190": {"dd": 0.00, "description_fr": "Blé tendre", "description_en": "Other wheat"},
    "100510": {"dd": 0.00, "description_fr": "Maïs de semence", "description_en": "Maize seed"},
}

# =============================================================================
# MAROC (MAR) - TAUX SH6 RÉELS
# Source: ADII (Administration des Douanes et Impôts Indirects)
# TVA: 20% | TPI: 0.25%
# =============================================================================

MAR_HS6_TARIFFS = {
    # PHOSPHATES - Premier exportateur
    "251010": {"dd": 0.00, "description_fr": "Phosphates naturels", "description_en": "Natural phosphates"},
    "310310": {"dd": 0.025, "description_fr": "Superphosphates", "description_en": "Superphosphates"},
    "310390": {"dd": 0.025, "description_fr": "Autres engrais phosphatés", "description_en": "Other phosphatic fertilizers"},
    "310520": {"dd": 0.10, "description_fr": "Engrais NPK", "description_en": "NPK fertilizers"},
    
    # TEXTILES - Industrie développée
    "610910": {"dd": 0.25, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.25, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620520": {"dd": 0.25, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    
    # AUTOMOBILES - Industrie locale
    "870321": {"dd": 0.175, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.175, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.175, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"dd": 0.175, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"dd": 0.10, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    
    # AGRUMES ET TOMATES
    "080510": {"dd": 0.00, "description_fr": "Oranges fraîches", "description_en": "Fresh oranges"},
    "080520": {"dd": 0.00, "description_fr": "Mandarines fraîches", "description_en": "Fresh mandarins"},
    "070200": {"dd": 0.175, "description_fr": "Tomates fraîches", "description_en": "Fresh tomatoes"},
    
    # POISSONS - Grand exportateur
    "030211": {"dd": 0.00, "description_fr": "Truites fraîches", "description_en": "Trout, fresh"},
    "030341": {"dd": 0.00, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "030489": {"dd": 0.025, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "160414": {"dd": 0.175, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    
    # MACHINES
    "841510": {"dd": 0.025, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "847130": {"dd": 0.00, "description_fr": "Ordinateurs portables", "description_en": "Laptop computers"},
    "851712": {"dd": 0.025, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# GHANA (GHA) - TAUX SH6 RÉELS
# Source: Ghana Revenue Authority, ECOWAS TEC
# TVA: 15% | NHIL: 2.5% | GETFund: 2.5% | CEDEAO: 0.5%
# =============================================================================

GHA_HS6_TARIFFS = {
    # CACAO - 2ème producteur mondial
    "180100": {"dd": 0.00, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180200": {"dd": 0.05, "description_fr": "Coques et pellicules de cacao", "description_en": "Cocoa shells"},
    "180310": {"dd": 0.10, "description_fr": "Pâte de cacao non dégraissée", "description_en": "Cocoa paste, not defatted"},
    "180400": {"dd": 0.10, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    "180500": {"dd": 0.10, "description_fr": "Poudre de cacao non sucrée", "description_en": "Cocoa powder, unsweetened"},
    "180620": {"dd": 0.20, "description_fr": "Chocolat en blocs", "description_en": "Chocolate blocks"},
    
    # OR
    "710812": {"dd": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"dd": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    
    # PÉTROLE
    "270900": {"dd": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"dd": 0.05, "description_fr": "Essences légères", "description_en": "Light oils"},
    
    # RIZ - TEC CEDEAO
    "100630": {"dd": 0.20, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled rice"},
    
    # VÉHICULES
    "870321": {"dd": 0.20, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"dd": 0.20, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"dd": 0.20, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    
    # TEXTILES
    "610910": {"dd": 0.35, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "620342": {"dd": 0.35, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    
    # MÉDICAMENTS
    "300220": {"dd": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300490": {"dd": 0.00, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
}

# =============================================================================
# CONSOLIDATION DE TOUS LES TARIFS SH6 PAR PAYS - 54 PAYS AFRICAINS
# =============================================================================

COUNTRY_HS6_TARIFFS = {
    # Pays avec tarifs détaillés (fichier principal)
    "NGA": NGA_HS6_TARIFFS,
    "CIV": CIV_HS6_TARIFFS,
    "ZAF": ZAF_HS6_TARIFFS,
    "KEN": KEN_HS6_TARIFFS,
    "EGY": EGY_HS6_TARIFFS,
    "MAR": MAR_HS6_TARIFFS,
    "GHA": GHA_HS6_TARIFFS,
    
    # CEDEAO/UEMOA (importés)
    "SEN": SEN_HS6_TARIFFS,
    "MLI": MLI_HS6_TARIFFS,
    "BFA": BFA_HS6_TARIFFS,
    "BEN": BEN_HS6_TARIFFS,
    "TGO": TGO_HS6_TARIFFS,
    "NER": NER_HS6_TARIFFS,
    "GIN": GIN_HS6_TARIFFS,
    "GNB": GNB_HS6_TARIFFS,
    "GMB": GMB_HS6_TARIFFS,
    "SLE": SLE_HS6_TARIFFS,
    "LBR": LBR_HS6_TARIFFS,
    "CPV": CPV_HS6_TARIFFS,
    
    # CEMAC (importés)
    "CMR": CMR_HS6_TARIFFS,
    "GAB": GAB_HS6_TARIFFS,
    "COG": COG_HS6_TARIFFS,
    "TCD": TCD_HS6_TARIFFS,
    "CAF": CAF_HS6_TARIFFS,
    "GNQ": GNQ_HS6_TARIFFS,
    
    # EAC (importés)
    "TZA": TZA_HS6_TARIFFS,
    "UGA": UGA_HS6_TARIFFS,
    "RWA": RWA_HS6_TARIFFS,
    "BDI": BDI_HS6_TARIFFS,
    "COD": COD_HS6_TARIFFS,
    "SSD": SSD_HS6_TARIFFS,
    
    # SADC hors SACU (importés)
    "AGO": AGO_HS6_TARIFFS,
    "MOZ": MOZ_HS6_TARIFFS,
    "ZMB": ZMB_HS6_TARIFFS,
    "ZWE": ZWE_HS6_TARIFFS,
    "MWI": MWI_HS6_TARIFFS,
    "MDG": MDG_HS6_TARIFFS,
    "MUS": MUS_HS6_TARIFFS,
    "SYC": SYC_HS6_TARIFFS,
    "COM": COM_HS6_TARIFFS,
    
    # SACU (importés)
    "BWA": BWA_HS6_TARIFFS,
    "NAM": NAM_HS6_TARIFFS,
    "LSO": LSO_HS6_TARIFFS,
    "SWZ": SWZ_HS6_TARIFFS,
    
    # Afrique du Nord (importés)
    "DZA": DZA_HS6_TARIFFS,
    "TUN": TUN_HS6_TARIFFS,
    "LBY": LBY_HS6_TARIFFS,
    "MRT": MRT_HS6_TARIFFS,
    
    # Autres pays (importés)
    "ETH": ETH_HS6_TARIFFS,
    "DJI": DJI_HS6_TARIFFS,
    "ERI": ERI_HS6_TARIFFS,
    "SDN": SDN_HS6_TARIFFS,
    "SOM": SOM_HS6_TARIFFS,
    "STP": STP_HS6_TARIFFS,
}

# Mapping ISO2 -> ISO3
ISO2_TO_ISO3 = {
    "DZ": "DZA", "AO": "AGO", "BJ": "BEN", "BW": "BWA", "BF": "BFA",
    "BI": "BDI", "CV": "CPV", "CM": "CMR", "CF": "CAF", "TD": "TCD",
    "KM": "COM", "CG": "COG", "CD": "COD", "CI": "CIV", "DJ": "DJI",
    "EG": "EGY", "GQ": "GNQ", "ER": "ERI", "SZ": "SWZ", "ET": "ETH",
    "GA": "GAB", "GM": "GMB", "GH": "GHA", "GN": "GIN", "GW": "GNB",
    "KE": "KEN", "LS": "LSO", "LR": "LBR", "LY": "LBY", "MG": "MDG",
    "MW": "MWI", "ML": "MLI", "MR": "MRT", "MU": "MUS", "MA": "MAR",
    "MZ": "MOZ", "NA": "NAM", "NE": "NER", "NG": "NGA", "RW": "RWA",
    "ST": "STP", "SN": "SEN", "SC": "SYC", "SL": "SLE", "SO": "SOM",
    "ZA": "ZAF", "SS": "SSD", "SD": "SDN", "TZ": "TZA", "TG": "TGO",
    "TN": "TUN", "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE"
}


# =============================================================================
# FONCTIONS D'ACCÈS AUX TARIFS SH6 PAR PAYS
# =============================================================================

def get_country_hs6_tariff(country_code: str, hs6_code: str) -> Optional[Dict]:
    """
    Obtenir le tarif SH6 spécifique pour un pays
    
    Args:
        country_code: Code ISO2 ou ISO3 du pays
        hs6_code: Code SH à 6 chiffres
        
    Returns:
        Dict avec le taux DD et descriptions, ou None si non trouvé
    """
    # Normaliser le code pays
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    # Normaliser le code SH6
    hs6_code = str(hs6_code).zfill(6)
    
    # Chercher dans les tarifs du pays
    country_tariffs = COUNTRY_HS6_TARIFFS.get(country_iso3, {})
    return country_tariffs.get(hs6_code)


def get_country_hs6_dd_rate(country_code: str, hs6_code: str) -> Tuple[Optional[float], str]:
    """
    Obtenir le taux de DD SH6 pour un pays
    
    Returns:
        Tuple (taux DD ou None, source)
    """
    tariff = get_country_hs6_tariff(country_code, hs6_code)
    if tariff:
        return (tariff["dd"], f"Tarif SH6 spécifique {hs6_code}")
    return (None, "Non disponible - utiliser taux chapitre")


def search_country_hs6_tariffs(country_code: str, query: str, language: str = 'fr', limit: int = 20) -> list:
    """
    Rechercher des codes SH6 avec tarifs dans un pays
    """
    # Normaliser le code pays
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    country_tariffs = COUNTRY_HS6_TARIFFS.get(country_iso3, {})
    query_lower = query.lower()
    results = []
    
    desc_key = f"description_{language}"
    
    for code, data in country_tariffs.items():
        description = data.get(desc_key, data.get("description_fr", ""))
        if query_lower in description.lower() or query_lower in code:
            results.append({
                "hs6_code": code,
                "description": description,
                "dd_rate": data["dd"],
                "dd_rate_pct": f"{data['dd'] * 100:.1f}%"
            })
            if len(results) >= limit:
                break
    
    return results


def get_available_country_tariffs() -> Dict:
    """
    Obtenir la liste des pays avec tarifs SH6 détaillés
    """
    return {
        iso3: {
            "count": len(tariffs),
            "chapters": list(set(code[:2] for code in tariffs.keys()))
        }
        for iso3, tariffs in COUNTRY_HS6_TARIFFS.items()
    }
