"""
EXTENSION BASE HS6 - CODES SUPPLÉMENTAIRES
==========================================
Codes HS6 additionnels pour enrichir la base principale.
Couvre tous les chapitres du Système Harmonisé (01-97)

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

# =============================================================================
# CODES HS6 SUPPLÉMENTAIRES PAR CHAPITRE
# =============================================================================

HS6_EXTENDED = {
    # =========================================================================
    # CHAPITRE 01 - ANIMAUX VIVANTS (Compléments)
    # =========================================================================
    "010110": {
        "chapter": "01",
        "description_fr": "Chevaux reproducteurs de race pure",
        "description_en": "Pure-bred breeding horses",
        "category": "livestock",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010121": {
        "chapter": "01",
        "description_fr": "Chevaux vivants (non reproducteurs)",
        "description_en": "Live horses (non-breeding)",
        "category": "livestock",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010221": {
        "chapter": "01",
        "description_fr": "Bovins reproducteurs de race pure",
        "description_en": "Pure-bred breeding bovine animals",
        "category": "livestock",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010310": {
        "chapter": "01",
        "description_fr": "Porcins reproducteurs de race pure",
        "description_en": "Pure-bred breeding swine",
        "category": "livestock",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010391": {
        "chapter": "01",
        "description_fr": "Autres porcins < 50 kg",
        "description_en": "Other swine < 50 kg",
        "category": "livestock",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010511": {
        "chapter": "01",
        "description_fr": "Volailles vivantes - coqs et poules ≤185g",
        "description_en": "Live poultry - fowls ≤185g",
        "category": "poultry",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010512": {
        "chapter": "01",
        "description_fr": "Dindes vivantes ≤185g",
        "description_en": "Live turkeys ≤185g",
        "category": "poultry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010594": {
        "chapter": "01",
        "description_fr": "Volailles vivantes autres (poulets >185g)",
        "description_en": "Other live poultry (fowls >185g)",
        "category": "poultry",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "010611": {
        "chapter": "01",
        "description_fr": "Primates vivants",
        "description_en": "Live primates",
        "category": "wildlife",
        "sensitivity": "excluded",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "CITES applicable", "requirement_en": "CITES applicable", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 02 - VIANDES (Compléments)
    # =========================================================================
    "020110": {
        "chapter": "02",
        "description_fr": "Carcasses ou demi-carcasses de bovins, fraîches",
        "description_en": "Bovine carcasses or half-carcasses, fresh",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020120": {
        "chapter": "02",
        "description_fr": "Morceaux de bovins non désossés, frais",
        "description_en": "Bovine cuts, bone-in, fresh",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type", "quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020210": {
        "chapter": "02",
        "description_fr": "Carcasses de bovins, congelées",
        "description_en": "Bovine carcasses, frozen",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020220": {
        "chapter": "02",
        "description_fr": "Morceaux de bovins non désossés, congelés",
        "description_en": "Bovine cuts, bone-in, frozen",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020311": {
        "chapter": "02",
        "description_fr": "Carcasses de porcins, fraîches",
        "description_en": "Swine carcasses, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020319": {
        "chapter": "02",
        "description_fr": "Viande de porcins, fraîche autre",
        "description_en": "Other fresh swine meat",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020410": {
        "chapter": "02",
        "description_fr": "Carcasses d'agneau, fraîches",
        "description_en": "Lamb carcasses, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020421": {
        "chapter": "02",
        "description_fr": "Carcasses d'ovins, fraîches",
        "description_en": "Sheep carcasses, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020422": {
        "chapter": "02",
        "description_fr": "Morceaux d'ovins non désossés, frais",
        "description_en": "Sheep cuts, bone-in, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020423": {
        "chapter": "02",
        "description_fr": "Morceaux d'ovins désossés, frais",
        "description_en": "Sheep cuts, boneless, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020450": {
        "chapter": "02",
        "description_fr": "Viande de chèvre",
        "description_en": "Goat meat",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020500": {
        "chapter": "02",
        "description_fr": "Viande d'équidés (cheval, âne)",
        "description_en": "Meat of horses, asses, mules",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020610": {
        "chapter": "02",
        "description_fr": "Abats de bovins, frais",
        "description_en": "Bovine offal, fresh",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020711": {
        "chapter": "02",
        "description_fr": "Coqs et poules non découpés, frais",
        "description_en": "Fowls, not cut, fresh",
        "category": "poultry",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020712": {
        "chapter": "02",
        "description_fr": "Coqs et poules non découpés, congelés",
        "description_en": "Fowls, not cut, frozen",
        "category": "poultry",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020713": {
        "chapter": "02",
        "description_fr": "Morceaux de volailles, frais",
        "description_en": "Poultry cuts, fresh",
        "category": "poultry",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020727": {
        "chapter": "02",
        "description_fr": "Dindes découpées, congelées",
        "description_en": "Turkey cuts, frozen",
        "category": "poultry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020810": {
        "chapter": "02",
        "description_fr": "Viande de lapin fraîche",
        "description_en": "Fresh rabbit meat",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020830": {
        "chapter": "02",
        "description_fr": "Viande de primates",
        "description_en": "Primate meat",
        "category": "wildlife",
        "sensitivity": "excluded",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "CITES - Interdit", "requirement_en": "CITES - Prohibited", "regional_content": 100}
    },
    "020890": {
        "chapter": "02",
        "description_fr": "Autres viandes (gibier, autruche)",
        "description_en": "Other meat (game, ostrich)",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "020900": {
        "chapter": "02",
        "description_fr": "Graisse de porc et de volaille",
        "description_en": "Pig fat and poultry fat",
        "category": "meat",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 03 - POISSONS (Compléments)
    # =========================================================================
    "030111": {
        "chapter": "03",
        "description_fr": "Poissons d'ornement, eau douce",
        "description_en": "Ornamental fish, freshwater",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030119": {
        "chapter": "03",
        "description_fr": "Poissons d'ornement, eau de mer",
        "description_en": "Ornamental fish, saltwater",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030191": {
        "chapter": "03",
        "description_fr": "Truites vivantes",
        "description_en": "Live trout",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030192": {
        "chapter": "03",
        "description_fr": "Anguilles vivantes",
        "description_en": "Live eels",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030193": {
        "chapter": "03",
        "description_fr": "Carpes vivantes",
        "description_en": "Live carp",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030194": {
        "chapter": "03",
        "description_fr": "Thons rouges vivants",
        "description_en": "Live Atlantic bluefin tuna",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030199": {
        "chapter": "03",
        "description_fr": "Autres poissons vivants",
        "description_en": "Other live fish",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "030211": {
        "chapter": "03",
        "description_fr": "Truites fraîches/réfrigérées",
        "description_en": "Fresh/chilled trout",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030213": {
        "chapter": "03",
        "description_fr": "Saumons du Pacifique frais",
        "description_en": "Fresh Pacific salmon",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030214": {
        "chapter": "03",
        "description_fr": "Saumon atlantique frais",
        "description_en": "Fresh Atlantic salmon",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché ou élevé en Afrique", "requirement_en": "Caught or farmed in Africa", "regional_content": 100}
    },
    "030221": {
        "chapter": "03",
        "description_fr": "Flétan frais",
        "description_en": "Fresh halibut",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030222": {
        "chapter": "03",
        "description_fr": "Plie fraîche",
        "description_en": "Fresh plaice",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030223": {
        "chapter": "03",
        "description_fr": "Sole fraîche",
        "description_en": "Fresh sole",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030231": {
        "chapter": "03",
        "description_fr": "Tilapia frais",
        "description_en": "Fresh tilapia",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché ou élevé en Afrique", "requirement_en": "Caught or farmed in Africa", "regional_content": 100}
    },
    "030232": {
        "chapter": "03",
        "description_fr": "Poissons-chats (silures) frais",
        "description_en": "Fresh catfish",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché ou élevé en Afrique", "requirement_en": "Caught or farmed in Africa", "regional_content": 100}
    },
    "030233": {
        "chapter": "03",
        "description_fr": "Perche du Nil fraîche",
        "description_en": "Fresh Nile perch",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030241": {
        "chapter": "03",
        "description_fr": "Harengs frais",
        "description_en": "Fresh herrings",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030242": {
        "chapter": "03",
        "description_fr": "Anchois frais",
        "description_en": "Fresh anchovies",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030243": {
        "chapter": "03",
        "description_fr": "Sardines fraîches",
        "description_en": "Fresh sardines",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030244": {
        "chapter": "03",
        "description_fr": "Maquereaux frais",
        "description_en": "Fresh mackerel",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030251": {
        "chapter": "03",
        "description_fr": "Morue fraîche",
        "description_en": "Fresh cod",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030254": {
        "chapter": "03",
        "description_fr": "Merlu frais",
        "description_en": "Fresh hake",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Pêché en eaux africaines", "requirement_en": "Caught in African waters", "regional_content": 100}
    },
    "030271": {
        "chapter": "03",
        "description_fr": "Tilapia frais entier",
        "description_en": "Fresh whole tilapia",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Élevé en Afrique", "requirement_en": "Farmed in Africa", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 04 - PRODUITS LAITIERS, OEUFS
    # =========================================================================
    "040110": {
        "chapter": "04",
        "description_fr": "Lait écrémé en poudre",
        "description_en": "Skimmed milk powder",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040120": {
        "chapter": "04",
        "description_fr": "Lait entier en poudre",
        "description_en": "Whole milk powder",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040130": {
        "chapter": "04",
        "description_fr": "Lait concentré non sucré",
        "description_en": "Unsweetened concentrated milk",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040140": {
        "chapter": "04",
        "description_fr": "Lait concentré sucré",
        "description_en": "Sweetened concentrated milk",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040150": {
        "chapter": "04",
        "description_fr": "Lait et crème concentrés",
        "description_en": "Concentrated milk and cream",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040210": {
        "chapter": "04",
        "description_fr": "Lait en poudre teneur MG ≤1.5%",
        "description_en": "Milk powder fat content ≤1.5%",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040221": {
        "chapter": "04",
        "description_fr": "Lait en poudre sans sucre >1.5% MG",
        "description_en": "Milk powder unsweetened >1.5% fat",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040229": {
        "chapter": "04",
        "description_fr": "Lait en poudre sucré >1.5% MG",
        "description_en": "Milk powder sweetened >1.5% fat",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "040310": {
        "chapter": "04",
        "description_fr": "Yaourt",
        "description_en": "Yogurt",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040390": {
        "chapter": "04",
        "description_fr": "Babeurre, lait caillé",
        "description_en": "Buttermilk, curdled milk",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040410": {
        "chapter": "04",
        "description_fr": "Lactosérum",
        "description_en": "Whey",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040490": {
        "chapter": "04",
        "description_fr": "Produits lactés autres",
        "description_en": "Other dairy products",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040510": {
        "chapter": "04",
        "description_fr": "Beurre",
        "description_en": "Butter",
        "category": "dairy",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040520": {
        "chapter": "04",
        "description_fr": "Pâtes à tartiner laitières",
        "description_en": "Dairy spreads",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "040590": {
        "chapter": "04",
        "description_fr": "Matières grasses du lait autres",
        "description_en": "Other milk fats",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040610": {
        "chapter": "04",
        "description_fr": "Fromages frais non affinés",
        "description_en": "Fresh unripened cheese",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040620": {
        "chapter": "04",
        "description_fr": "Fromages râpés ou en poudre",
        "description_en": "Grated or powdered cheese",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "040630": {
        "chapter": "04",
        "description_fr": "Fromages fondus",
        "description_en": "Processed cheese",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040640": {
        "chapter": "04",
        "description_fr": "Fromages à pâte persillée",
        "description_en": "Blue-veined cheese",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "040690": {
        "chapter": "04",
        "description_fr": "Autres fromages",
        "description_en": "Other cheese",
        "category": "dairy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "040700": {
        "chapter": "04",
        "description_fr": "Oeufs en coquille",
        "description_en": "Eggs in shell",
        "category": "eggs",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use", "species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "040811": {
        "chapter": "04",
        "description_fr": "Jaunes d'oeufs séchés",
        "description_en": "Dried egg yolks",
        "category": "eggs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040819": {
        "chapter": "04",
        "description_fr": "Jaunes d'oeufs autres",
        "description_en": "Other egg yolks",
        "category": "eggs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040891": {
        "chapter": "04",
        "description_fr": "Oeufs séchés sans coquille",
        "description_en": "Dried eggs, not in shell",
        "category": "eggs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040899": {
        "chapter": "04",
        "description_fr": "Oeufs autres",
        "description_en": "Other eggs",
        "category": "eggs",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "040900": {
        "chapter": "04",
        "description_fr": "Miel naturel",
        "description_en": "Natural honey",
        "category": "honey",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - récolté en Afrique", "requirement_en": "Wholly obtained - harvested in Africa", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 05 - PRODUITS ANIMAUX AUTRES
    # =========================================================================
    "050400": {
        "chapter": "05",
        "description_fr": "Boyaux, vessies, estomacs d'animaux",
        "description_en": "Guts, bladders, stomachs of animals",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "050510": {
        "chapter": "05",
        "description_fr": "Plumes pour literie",
        "description_en": "Feathers for stuffing",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "050590": {
        "chapter": "05",
        "description_fr": "Autres plumes et duvet",
        "description_en": "Other feathers and down",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "050610": {
        "chapter": "05",
        "description_fr": "Osséine et os traités à l'acide",
        "description_en": "Ossein and acid-treated bones",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "050690": {
        "chapter": "05",
        "description_fr": "Os et cornillons non travaillés",
        "description_en": "Unworked bones and horn-cores",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "050710": {
        "chapter": "05",
        "description_fr": "Ivoire brut",
        "description_en": "Raw ivory",
        "category": "wildlife",
        "sensitivity": "excluded",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "CITES - Commerce interdit", "requirement_en": "CITES - Trade prohibited", "regional_content": 100}
    },
    "050790": {
        "chapter": "05",
        "description_fr": "Corne, bois de cervidés",
        "description_en": "Horn, antlers",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "050800": {
        "chapter": "05",
        "description_fr": "Corail et matières similaires",
        "description_en": "Coral and similar materials",
        "category": "animal_products",
        "sensitivity": "excluded",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "CITES applicable", "requirement_en": "CITES applicable", "regional_content": 100}
    },
    "050900": {
        "chapter": "05",
        "description_fr": "Éponges naturelles",
        "description_en": "Natural sponges",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "051000": {
        "chapter": "05",
        "description_fr": "Ambre gris, castoréum, civette",
        "description_en": "Ambergris, castoreum, civet",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "051110": {
        "chapter": "05",
        "description_fr": "Sperme de bovins",
        "description_en": "Bovine semen",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "051191": {
        "chapter": "05",
        "description_fr": "Produits de poissons (laitances)",
        "description_en": "Fish products (roes)",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "051199": {
        "chapter": "05",
        "description_fr": "Autres produits d'origine animale",
        "description_en": "Other products of animal origin",
        "category": "animal_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 06 - PLANTES VIVANTES
    # =========================================================================
    "060110": {
        "chapter": "06",
        "description_fr": "Bulbes, oignons, tubercules en repos",
        "description_en": "Bulbs, tubers in dormant state",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060120": {
        "chapter": "06",
        "description_fr": "Bulbes, oignons en végétation",
        "description_en": "Bulbs, tubers in growth",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060210": {
        "chapter": "06",
        "description_fr": "Boutures non racinées, greffons",
        "description_en": "Unrooted cuttings, slips",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060220": {
        "chapter": "06",
        "description_fr": "Arbres et arbustes fruitiers",
        "description_en": "Fruit trees and shrubs",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060230": {
        "chapter": "06",
        "description_fr": "Rhododendrons et azalées",
        "description_en": "Rhododendrons and azaleas",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060240": {
        "chapter": "06",
        "description_fr": "Rosiers greffés ou non",
        "description_en": "Roses, grafted or not",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060290": {
        "chapter": "06",
        "description_fr": "Autres plantes vivantes",
        "description_en": "Other live plants",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060319": {
        "chapter": "06",
        "description_fr": "Autres fleurs coupées fraîches",
        "description_en": "Other fresh cut flowers",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "060312": {
        "chapter": "06",
        "description_fr": "Oeillets frais",
        "description_en": "Fresh carnations",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "060313": {
        "chapter": "06",
        "description_fr": "Orchidées fraîches",
        "description_en": "Fresh orchids",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "060314": {
        "chapter": "06",
        "description_fr": "Chrysanthèmes frais",
        "description_en": "Fresh chrysanthemums",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "060315": {
        "chapter": "06",
        "description_fr": "Lis frais",
        "description_en": "Fresh lilies",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "060390": {
        "chapter": "06",
        "description_fr": "Fleurs coupées séchées",
        "description_en": "Dried cut flowers",
        "category": "flowers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "060410": {
        "chapter": "06",
        "description_fr": "Mousses et lichens",
        "description_en": "Mosses and lichens",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060420": {
        "chapter": "06",
        "description_fr": "Feuillages frais",
        "description_en": "Fresh foliage",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "060490": {
        "chapter": "06",
        "description_fr": "Feuillages, branches séchés",
        "description_en": "Dried foliage, branches",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
}
