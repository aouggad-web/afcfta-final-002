"""
Tarifs douaniers spécifiques au niveau SH6 pour les produits africains clés
Sources: OMC ITC, CNUCED TRAINS, WITS Banque Mondiale, Douanes nationales
Dernière mise à jour: Janvier 2025

Ce fichier contient des taux de droits de douane précis pour les codes SH6
les plus échangés en Afrique, permettant des calculs plus précis que les
taux par chapitre.
"""

from typing import Dict, Optional, Tuple

# =============================================================================
# TARIFS SH6 SPÉCIFIQUES - PRODUITS AGRICOLES AFRICAINS CLÉS
# =============================================================================

# Format: {code_sh6: {"normal": taux_npf, "zlecaf": taux_zlecaf, "description_fr": ..., "description_en": ...}}

HS6_TARIFFS_AGRICULTURE = {
    # CACAO - Produit phare Côte d'Ivoire, Ghana
    "180100": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Cacao en fèves brut", "description_en": "Cocoa beans, raw"},
    "180200": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Coques et pellicules de cacao", "description_en": "Cocoa shells and skins"},
    "180310": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Pâte de cacao non dégraissée", "description_en": "Cocoa paste, not defatted"},
    "180320": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Pâte de cacao dégraissée", "description_en": "Cocoa paste, defatted"},
    "180400": {"normal": 0.08, "zlecaf": 0.02, "description_fr": "Beurre de cacao", "description_en": "Cocoa butter"},
    "180500": {"normal": 0.06, "zlecaf": 0.02, "description_fr": "Poudre de cacao non sucrée", "description_en": "Cocoa powder, unsweetened"},
    "180610": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Poudre de cacao sucrée", "description_en": "Cocoa powder, sweetened"},
    "180620": {"normal": 0.20, "zlecaf": 0.05, "description_fr": "Chocolat en blocs > 2kg", "description_en": "Chocolate blocks > 2kg"},
    "180631": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "Chocolat fourré", "description_en": "Filled chocolate"},
    "180632": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "Chocolat non fourré", "description_en": "Unfilled chocolate"},
    
    # CAFÉ - Éthiopie, Kenya, Ouganda
    "090111": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Café non torréfié, non décaféiné", "description_en": "Coffee, not roasted, not decaf"},
    "090112": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Café non torréfié, décaféiné", "description_en": "Coffee, not roasted, decaf"},
    "090121": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Café torréfié, non décaféiné", "description_en": "Coffee, roasted, not decaf"},
    "090122": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Café torréfié, décaféiné", "description_en": "Coffee, roasted, decaf"},
    "090190": {"normal": 0.08, "zlecaf": 0.02, "description_fr": "Coques et pellicules de café", "description_en": "Coffee husks and skins"},
    
    # THÉ - Kenya, Rwanda
    "090210": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Thé vert non fermenté ≤3kg", "description_en": "Green tea, not fermented ≤3kg"},
    "090220": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Thé vert non fermenté >3kg", "description_en": "Green tea, not fermented >3kg"},
    "090230": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Thé noir fermenté ≤3kg", "description_en": "Black tea, fermented ≤3kg"},
    "090240": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Thé noir fermenté >3kg", "description_en": "Black tea, fermented >3kg"},
    
    # COTON - Mali, Burkina Faso, Bénin
    "520100": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Coton non cardé ni peigné", "description_en": "Cotton, not carded or combed"},
    "520210": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Déchets de coton", "description_en": "Cotton waste"},
    "520291": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Déchets de fils de coton", "description_en": "Yarn waste of cotton"},
    "520300": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Coton cardé ou peigné", "description_en": "Cotton, carded or combed"},
    "520411": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Fils de coton ≥85% simple", "description_en": "Cotton yarn ≥85%, single"},
    "520512": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Fils de coton peigné simple", "description_en": "Combed cotton yarn, single"},
    
    # ARACHIDE - Sénégal, Gambie, Niger
    "120241": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Arachides en coques", "description_en": "Groundnuts in shell"},
    "120242": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Arachides décortiquées", "description_en": "Groundnuts, shelled"},
    "150810": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Huile d'arachide brute", "description_en": "Groundnut oil, crude"},
    "150890": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Huile d'arachide raffinée", "description_en": "Groundnut oil, refined"},
    
    # KARITÉ - Burkina Faso, Ghana, Mali
    "151590": {"normal": 0.08, "zlecaf": 0.02, "description_fr": "Beurre de karité", "description_en": "Shea butter"},
    "151520": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Huile de karité", "description_en": "Shea oil"},
    
    # SÉSAME - Soudan, Éthiopie, Tanzanie
    "120740": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Graines de sésame", "description_en": "Sesame seeds"},
    "151550": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Huile de sésame", "description_en": "Sesame oil"},
    
    # NOIX DE CAJOU - Côte d'Ivoire, Tanzanie, Mozambique
    "080131": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Noix de cajou en coques", "description_en": "Cashew nuts in shell"},
    "080132": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Noix de cajou décortiquées", "description_en": "Cashew nuts, shelled"},
    
    # BANANE - Côte d'Ivoire, Cameroun
    "080310": {"normal": 0.20, "zlecaf": 0.05, "description_fr": "Bananes fraîches ou séchées", "description_en": "Bananas, fresh or dried"},
    "080390": {"normal": 0.20, "zlecaf": 0.05, "description_fr": "Plantains", "description_en": "Plantains"},
    
    # ANANAS - Côte d'Ivoire, Ghana
    "080430": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Ananas frais ou séchés", "description_en": "Pineapples, fresh or dried"},
    "200820": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Ananas préparés ou conservés", "description_en": "Pineapples, prepared"},
    
    # MANGUE - Sénégal, Mali, Burkina Faso
    "080450": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Mangues fraîches ou séchées", "description_en": "Mangoes, fresh or dried"},
    
    # CÉRÉALES
    "100110": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Blé dur", "description_en": "Durum wheat"},
    "100190": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Blé tendre", "description_en": "Other wheat"},
    "100510": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Maïs de semence", "description_en": "Maize seed"},
    "100590": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Maïs autre", "description_en": "Other maize"},
    "100610": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Riz paddy", "description_en": "Rice in the husk"},
    "100620": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Riz décortiqué", "description_en": "Husked rice"},
    "100630": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Riz semi-blanchi ou blanchi", "description_en": "Semi-milled or milled rice"},
    "100640": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Brisures de riz", "description_en": "Broken rice"},
    "100710": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Sorgho", "description_en": "Grain sorghum"},
    "100810": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Mil", "description_en": "Millet"},
    
    # POISSON - Maroc, Mauritanie, Sénégal
    "030211": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Truites fraîches", "description_en": "Trout, fresh"},
    "030231": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Thon albacore frais", "description_en": "Yellowfin tuna, fresh"},
    "030232": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Thon listao frais", "description_en": "Skipjack tuna, fresh"},
    "030311": {"normal": 0.12, "zlecaf": 0.04, "description_fr": "Saumon rouge congelé", "description_en": "Sockeye salmon, frozen"},
    "030331": {"normal": 0.12, "zlecaf": 0.04, "description_fr": "Sole congelée", "description_en": "Sole, frozen"},
    "030341": {"normal": 0.12, "zlecaf": 0.04, "description_fr": "Thon albacore congelé", "description_en": "Yellowfin tuna, frozen"},
    "030489": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Filets de poisson congelés", "description_en": "Fish fillets, frozen"},
    "030551": {"normal": 0.08, "zlecaf": 0.02, "description_fr": "Morue séchée", "description_en": "Dried cod"},
    "030617": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Crevettes congelées", "description_en": "Shrimps, frozen"},
    "160414": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Thon en conserve", "description_en": "Canned tuna"},
    "160420": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Autres préparations de poisson", "description_en": "Other fish preparations"},
}

# =============================================================================
# TARIFS SH6 SPÉCIFIQUES - PRODUITS MINIERS ET ÉNERGÉTIQUES
# =============================================================================

HS6_TARIFFS_MINING = {
    # PÉTROLE BRUT - Nigeria, Angola, Algérie, Libye
    "270900": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Huiles brutes de pétrole", "description_en": "Crude petroleum oils"},
    "271012": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Essences légères", "description_en": "Light oils"},
    "271019": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Autres huiles de pétrole", "description_en": "Other petroleum oils"},
    "271112": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Propane liquéfié", "description_en": "Propane, liquefied"},
    "271113": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Butane liquéfié", "description_en": "Butane, liquefied"},
    "271121": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Gaz naturel gazeux", "description_en": "Natural gas, gaseous"},
    "271311": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Coke de pétrole non calciné", "description_en": "Petroleum coke, not calcined"},
    
    # OR - Afrique du Sud, Ghana, Mali, Burkina Faso
    "710812": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Or sous formes brutes", "description_en": "Gold in unwrought forms"},
    "710813": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Or mi-ouvré", "description_en": "Gold, semi-manufactured"},
    "710820": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Or monétaire", "description_en": "Monetary gold"},
    
    # DIAMANTS - Botswana, RDC, Afrique du Sud, Angola
    "710210": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Diamants non triés", "description_en": "Diamonds, unsorted"},
    "710221": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Diamants industriels bruts", "description_en": "Industrial diamonds, unworked"},
    "710231": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Diamants gemmes bruts", "description_en": "Gem diamonds, unworked"},
    "710239": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Diamants gemmes travaillés", "description_en": "Gem diamonds, worked"},
    
    # CUIVRE - RDC, Zambie
    "260300": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerais de cuivre", "description_en": "Copper ores"},
    "740200": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Cuivre non affiné", "description_en": "Unrefined copper"},
    "740311": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Cathodes de cuivre", "description_en": "Copper cathodes"},
    "740400": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Déchets de cuivre", "description_en": "Copper waste"},
    "740710": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Barres de cuivre affiné", "description_en": "Refined copper bars"},
    
    # COBALT - RDC
    "810520": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Mattes de cobalt", "description_en": "Cobalt mattes"},
    "282200": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Oxydes de cobalt", "description_en": "Cobalt oxides"},
    
    # ALUMINIUM/BAUXITE - Guinée, Ghana
    "260600": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerais d'aluminium (bauxite)", "description_en": "Aluminum ores (bauxite)"},
    "281820": {"normal": 0.03, "zlecaf": 0.00, "description_fr": "Alumine", "description_en": "Aluminum oxide"},
    "760110": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Aluminium non allié brut", "description_en": "Unwrought aluminum"},
    "760120": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Alliages d'aluminium bruts", "description_en": "Unwrought aluminum alloys"},
    
    # FER/ACIER - Afrique du Sud, Mauritanie
    "260111": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerai de fer non aggloméré", "description_en": "Iron ore, non-agglomerated"},
    "260112": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerai de fer aggloméré", "description_en": "Iron ore, agglomerated"},
    "720110": {"normal": 0.03, "zlecaf": 0.00, "description_fr": "Fontes brutes non alliées", "description_en": "Non-alloy pig iron"},
    "720712": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Demi-produits en fer", "description_en": "Iron semi-finished products"},
    "721049": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Produits plats en fer", "description_en": "Flat-rolled iron products"},
    
    # MANGANÈSE - Afrique du Sud, Gabon
    "260200": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerais de manganèse", "description_en": "Manganese ores"},
    "811100": {"normal": 0.03, "zlecaf": 0.00, "description_fr": "Manganèse brut", "description_en": "Unwrought manganese"},
    
    # PHOSPHATES - Maroc
    "251010": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Phosphates naturels", "description_en": "Natural phosphates"},
    "310310": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Superphosphates", "description_en": "Superphosphates"},
    "310390": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Autres engrais phosphatés", "description_en": "Other phosphatic fertilizers"},
    
    # URANIUM - Niger, Namibie
    "261210": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Minerais d'uranium", "description_en": "Uranium ores"},
    "284410": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Uranium naturel", "description_en": "Natural uranium"},
}

# =============================================================================
# TARIFS SH6 SPÉCIFIQUES - PRODUITS MANUFACTURÉS AFRICAINS
# =============================================================================

HS6_TARIFFS_MANUFACTURED = {
    # TEXTILES - Maroc, Tunisie, Égypte, Maurice
    "610910": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "T-shirts en coton", "description_en": "Cotton T-shirts"},
    "610990": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "T-shirts autres matières", "description_en": "Other T-shirts"},
    "620342": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "Pantalons hommes coton", "description_en": "Men's cotton trousers"},
    "620343": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "Pantalons hommes synthétique", "description_en": "Men's synthetic trousers"},
    "620462": {"normal": 0.25, "zlecaf": 0.08, "description_fr": "Pantalons femmes coton", "description_en": "Women's cotton trousers"},
    "620520": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Chemises hommes coton", "description_en": "Men's cotton shirts"},
    "620530": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Chemises hommes synthétique", "description_en": "Men's synthetic shirts"},
    "630231": {"normal": 0.20, "zlecaf": 0.07, "description_fr": "Linge de lit coton", "description_en": "Cotton bed linen"},
    
    # AUTOMOBILES - Maroc, Afrique du Sud
    "870321": {"normal": 0.25, "zlecaf": 0.10, "description_fr": "Voitures ≤1000cc", "description_en": "Cars ≤1000cc"},
    "870322": {"normal": 0.25, "zlecaf": 0.10, "description_fr": "Voitures 1000-1500cc", "description_en": "Cars 1000-1500cc"},
    "870323": {"normal": 0.25, "zlecaf": 0.10, "description_fr": "Voitures 1500-3000cc", "description_en": "Cars 1500-3000cc"},
    "870324": {"normal": 0.30, "zlecaf": 0.12, "description_fr": "Voitures >3000cc", "description_en": "Cars >3000cc"},
    "870421": {"normal": 0.20, "zlecaf": 0.08, "description_fr": "Camions ≤5 tonnes", "description_en": "Trucks ≤5 tonnes"},
    "870422": {"normal": 0.20, "zlecaf": 0.08, "description_fr": "Camions 5-20 tonnes", "description_en": "Trucks 5-20 tonnes"},
    "870431": {"normal": 0.20, "zlecaf": 0.08, "description_fr": "Camions >20 tonnes", "description_en": "Trucks >20 tonnes"},
    "871120": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Motos 50-250cc", "description_en": "Motorcycles 50-250cc"},
    "871130": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Motos 250-500cc", "description_en": "Motorcycles 250-500cc"},
    
    # ÉLECTRONIQUE - Afrique du Sud, Égypte
    "851712": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Téléphones portables", "description_en": "Mobile phones"},
    "852872": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Téléviseurs couleur", "description_en": "Color TVs"},
    "841510": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Climatiseurs muraux", "description_en": "Wall air conditioners"},
    "841821": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Réfrigérateurs ménagers", "description_en": "Household refrigerators"},
    "845011": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Machines à laver ≤10kg", "description_en": "Washing machines ≤10kg"},
    
    # CIMENT ET MATÉRIAUX - Égypte, Nigeria, Afrique du Sud
    "252310": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Ciment Portland blanc", "description_en": "White Portland cement"},
    "252321": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Ciment Portland ordinaire", "description_en": "Ordinary Portland cement"},
    "252329": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Autres ciments Portland", "description_en": "Other Portland cement"},
    "252390": {"normal": 0.10, "zlecaf": 0.03, "description_fr": "Autres ciments hydrauliques", "description_en": "Other hydraulic cements"},
    "700510": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Verre flotté", "description_en": "Float glass"},
    "690490": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Briques de construction", "description_en": "Building bricks"},
    "690721": {"normal": 0.15, "zlecaf": 0.05, "description_fr": "Carreaux céramiques", "description_en": "Ceramic tiles"},
    
    # PHARMACEUTIQUE - Afrique du Sud, Maroc, Égypte
    "300210": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Antisérums", "description_en": "Antisera"},
    "300220": {"normal": 0.00, "zlecaf": 0.00, "description_fr": "Vaccins", "description_en": "Vaccines"},
    "300410": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Médicaments pénicilline", "description_en": "Penicillin medicines"},
    "300420": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Médicaments antibiotiques", "description_en": "Antibiotic medicines"},
    "300431": {"normal": 0.05, "zlecaf": 0.00, "description_fr": "Médicaments insuline", "description_en": "Insulin medicines"},
    "300490": {"normal": 0.08, "zlecaf": 0.02, "description_fr": "Autres médicaments", "description_en": "Other medicaments"},
    
    # ENGRAIS - Maroc, Égypte
    "310210": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Urée", "description_en": "Urea"},
    "310230": {"normal": 0.05, "zlecaf": 0.02, "description_fr": "Nitrate d'ammonium", "description_en": "Ammonium nitrate"},
    "310240": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Mélanges nitrate/sulfate", "description_en": "Nitrate/sulphate mixtures"},
    "310520": {"normal": 0.08, "zlecaf": 0.03, "description_fr": "Engrais NPK", "description_en": "NPK fertilizers"},
}

# =============================================================================
# CONSOLIDATION DE TOUS LES TARIFS SH6
# =============================================================================

# Fusionner tous les dictionnaires de tarifs SH6
HS6_TARIFFS = {
    **HS6_TARIFFS_AGRICULTURE,
    **HS6_TARIFFS_MINING,
    **HS6_TARIFFS_MANUFACTURED
}


# =============================================================================
# FONCTIONS D'ACCÈS AUX TARIFS SH6
# =============================================================================

def get_hs6_tariff(hs6_code: str) -> Optional[Dict]:
    """
    Obtenir les tarifs spécifiques pour un code SH6
    
    Args:
        hs6_code: Code SH à 6 chiffres
        
    Returns:
        Dict avec les taux normal et ZLECAf, ou None si non trouvé
    """
    hs6_code = str(hs6_code).zfill(6)
    return HS6_TARIFFS.get(hs6_code)


def get_hs6_tariff_rates(hs6_code: str) -> Tuple[float, float]:
    """
    Obtenir les taux de tarif (normal, zlecaf) pour un code SH6
    
    Args:
        hs6_code: Code SH à 6 chiffres
        
    Returns:
        Tuple (taux_normal, taux_zlecaf) ou taux par défaut si non trouvé
    """
    tariff = get_hs6_tariff(hs6_code)
    if tariff:
        return (tariff["normal"], tariff["zlecaf"])
    # Retourner None pour utiliser les taux par chapitre
    return (None, None)


def search_hs6_tariffs(query: str, language: str = 'fr', limit: int = 20) -> list:
    """
    Rechercher des codes SH6 avec leurs tarifs par mot-clé
    
    Args:
        query: Terme de recherche
        language: 'fr' ou 'en'
        limit: Nombre maximum de résultats
        
    Returns:
        Liste de codes SH6 correspondants avec tarifs
    """
    query_lower = query.lower()
    results = []
    desc_key = f"description_{language}"
    
    for code, data in HS6_TARIFFS.items():
        description = data.get(desc_key, data.get("description_fr", ""))
        if query_lower in description.lower() or query_lower in code:
            results.append({
                "code": code,
                "description": description,
                "normal_rate": data["normal"],
                "zlecaf_rate": data["zlecaf"],
                "savings_pct": round((data["normal"] - data["zlecaf"]) / data["normal"] * 100, 1) if data["normal"] > 0 else 0
            })
            if len(results) >= limit:
                break
    
    return results


def get_hs6_tariffs_by_chapter(chapter: str) -> list:
    """
    Obtenir tous les codes SH6 avec tarifs pour un chapitre donné
    
    Args:
        chapter: Code chapitre à 2 chiffres
        
    Returns:
        Liste des codes SH6 du chapitre avec leurs tarifs
    """
    chapter = str(chapter).zfill(2)
    results = []
    
    for code, data in HS6_TARIFFS.items():
        if code.startswith(chapter):
            results.append({
                "code": code,
                "description_fr": data.get("description_fr", ""),
                "description_en": data.get("description_en", ""),
                "normal_rate": data["normal"],
                "zlecaf_rate": data["zlecaf"]
            })
    
    return sorted(results, key=lambda x: x["code"])


def get_hs6_statistics() -> Dict:
    """
    Obtenir des statistiques sur les tarifs SH6 disponibles
    """
    total_codes = len(HS6_TARIFFS)
    
    # Statistiques par chapitre
    chapters = {}
    for code in HS6_TARIFFS.keys():
        ch = code[:2]
        chapters[ch] = chapters.get(ch, 0) + 1
    
    # Taux moyens
    normal_rates = [d["normal"] for d in HS6_TARIFFS.values()]
    zlecaf_rates = [d["zlecaf"] for d in HS6_TARIFFS.values()]
    
    return {
        "total_hs6_codes_with_tariffs": total_codes,
        "chapters_covered": len(chapters),
        "codes_by_chapter": chapters,
        "average_normal_rate": round(sum(normal_rates) / len(normal_rates) * 100, 2),
        "average_zlecaf_rate": round(sum(zlecaf_rates) / len(zlecaf_rates) * 100, 2),
        "average_savings_pct": round((sum(normal_rates) - sum(zlecaf_rates)) / sum(normal_rates) * 100, 1) if sum(normal_rates) > 0 else 0,
        "categories": {
            "agriculture": len(HS6_TARIFFS_AGRICULTURE),
            "mining": len(HS6_TARIFFS_MINING),
            "manufactured": len(HS6_TARIFFS_MANUFACTURED)
        },
        "source": "OMC ITC, CNUCED TRAINS, WITS Banque Mondiale",
        "last_updated": "2025-01"
    }
