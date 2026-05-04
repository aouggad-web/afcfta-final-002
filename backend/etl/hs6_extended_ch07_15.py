"""
EXTENSION BASE HS6 - CHAPITRES 07-15
=====================================
Légumes, Fruits, Café/Thé/Épices, Céréales, Oléagineux, Gommes, Huiles
Produits agricoles majeurs du commerce africain

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

HS6_EXTENDED_CH07_15 = {
    # =========================================================================
    # CHAPITRE 07 - LÉGUMES
    # =========================================================================
    "070110": {
        "chapter": "07",
        "description_fr": "Pommes de terre de semence",
        "description_en": "Seed potatoes",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "certification"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070190": {
        "chapter": "07",
        "description_fr": "Pommes de terre autres",
        "description_en": "Other potatoes",
        "category": "vegetables",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070320": {
        "chapter": "07",
        "description_fr": "Ail",
        "description_en": "Garlic",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070390": {
        "chapter": "07",
        "description_fr": "Poireaux et autres alliacées",
        "description_en": "Leeks and other alliaceous vegetables",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070410": {
        "chapter": "07",
        "description_fr": "Choux-fleurs et brocolis",
        "description_en": "Cauliflowers and broccoli",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070490": {
        "chapter": "07",
        "description_fr": "Autres choux",
        "description_en": "Other cabbages",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070610": {
        "chapter": "07",
        "description_fr": "Carottes et navets",
        "description_en": "Carrots and turnips",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070700": {
        "chapter": "07",
        "description_fr": "Concombres et cornichons",
        "description_en": "Cucumbers and gherkins",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070810": {
        "chapter": "07",
        "description_fr": "Pois (frais ou réfrigérés)",
        "description_en": "Peas (fresh or chilled)",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070820": {
        "chapter": "07",
        "description_fr": "Haricots (frais ou réfrigérés)",
        "description_en": "Beans (fresh or chilled)",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070930": {
        "chapter": "07",
        "description_fr": "Aubergines",
        "description_en": "Eggplants (aubergines)",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070951": {
        "chapter": "07",
        "description_fr": "Champignons frais",
        "description_en": "Fresh mushrooms",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "farmed_wild"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070960": {
        "chapter": "07",
        "description_fr": "Piments doux ou poivrons",
        "description_en": "Sweet peppers",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "070993": {
        "chapter": "07",
        "description_fr": "Courges, potirons",
        "description_en": "Pumpkins, squash",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071010": {
        "chapter": "07",
        "description_fr": "Pommes de terre congelées",
        "description_en": "Frozen potatoes",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "071320": {
        "chapter": "07",
        "description_fr": "Pois chiches secs",
        "description_en": "Dried chickpeas",
        "category": "legumes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071333": {
        "chapter": "07",
        "description_fr": "Haricots communs secs",
        "description_en": "Dried kidney beans",
        "category": "legumes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071335": {
        "chapter": "07",
        "description_fr": "Niébé (Vigna unguiculata)",
        "description_en": "Cowpeas (Vigna unguiculata)",
        "category": "legumes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071340": {
        "chapter": "07",
        "description_fr": "Lentilles sèches",
        "description_en": "Dried lentils",
        "category": "legumes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071410": {
        "chapter": "07",
        "description_fr": "Manioc (cassava)",
        "description_en": "Manioc (cassava)",
        "category": "roots_tubers",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071420": {
        "chapter": "07",
        "description_fr": "Patates douces",
        "description_en": "Sweet potatoes",
        "category": "roots_tubers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "071430": {
        "chapter": "07",
        "description_fr": "Ignames (Dioscorea spp.)",
        "description_en": "Yams (Dioscorea spp.)",
        "category": "roots_tubers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 08 - FRUITS (Compléments)
    # =========================================================================
    "080119": {
        "chapter": "08",
        "description_fr": "Noix de coco fraîches",
        "description_en": "Fresh coconuts",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080212": {
        "chapter": "08",
        "description_fr": "Amandes décortiquées",
        "description_en": "Shelled almonds",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "080261": {
        "chapter": "08",
        "description_fr": "Noix de macadamia en coques",
        "description_en": "Macadamia nuts in shell",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080262": {
        "chapter": "08",
        "description_fr": "Noix de macadamia décortiquées",
        "description_en": "Shelled macadamia nuts",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "080310": {
        "chapter": "08",
        "description_fr": "Bananes plantains",
        "description_en": "Plantains",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080430": {
        "chapter": "08",
        "description_fr": "Ananas frais ou secs",
        "description_en": "Fresh or dried pineapples",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "export_local"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080440": {
        "chapter": "08",
        "description_fr": "Avocats frais ou secs",
        "description_en": "Fresh or dried avocados",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080450": {
        "chapter": "08",
        "description_fr": "Goyaves, mangues et mangoustans",
        "description_en": "Guavas, mangoes and mangosteens",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080530": {
        "chapter": "08",
        "description_fr": "Citrons et limes",
        "description_en": "Lemons and limes",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080610": {
        "chapter": "08",
        "description_fr": "Raisins frais",
        "description_en": "Fresh grapes",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080711": {
        "chapter": "08",
        "description_fr": "Pastèques",
        "description_en": "Watermelons",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080720": {
        "chapter": "08",
        "description_fr": "Papayes",
        "description_en": "Papayas",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "080930": {
        "chapter": "08",
        "description_fr": "Pêches et nectarines",
        "description_en": "Peaches and nectarines",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "081010": {
        "chapter": "08",
        "description_fr": "Fraises fraîches",
        "description_en": "Fresh strawberries",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "081090": {
        "chapter": "08",
        "description_fr": "Autres fruits frais (litchis, fruits de la passion)",
        "description_en": "Other fresh fruits (litchis, passion fruit)",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 09 - CAFÉ, THÉ, ÉPICES (Compléments)
    # =========================================================================
    "090112": {
        "chapter": "09",
        "description_fr": "Café non torréfié décaféiné",
        "description_en": "Coffee not roasted decaffeinated",
        "category": "coffee",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Décaféination en Afrique", "requirement_en": "Decaffeinated in Africa", "regional_content": 40}
    },
    "090210": {
        "chapter": "09",
        "description_fr": "Thé vert non fermenté",
        "description_en": "Green tea (not fermented)",
        "category": "tea",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "090240": {
        "chapter": "09",
        "description_fr": "Thé noir en vrac",
        "description_en": "Black tea in bulk",
        "category": "tea",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "090411": {
        "chapter": "09",
        "description_fr": "Poivre non broyé",
        "description_en": "Pepper, not crushed",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "090420": {
        "chapter": "09",
        "description_fr": "Piments du genre Capsicum séchés",
        "description_en": "Dried fruits of genus Capsicum",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "090611": {
        "chapter": "09",
        "description_fr": "Cannelle non broyée",
        "description_en": "Cinnamon, not crushed",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "090810": {
        "chapter": "09",
        "description_fr": "Noix muscade",
        "description_en": "Nutmeg",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "091010": {
        "chapter": "09",
        "description_fr": "Gingembre",
        "description_en": "Ginger",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "091020": {
        "chapter": "09",
        "description_fr": "Safran",
        "description_en": "Saffron",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "091030": {
        "chapter": "09",
        "description_fr": "Curcuma",
        "description_en": "Turmeric (curcuma)",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 10 - CÉRÉALES (Compléments)
    # =========================================================================
    "100110": {
        "chapter": "10",
        "description_fr": "Blé dur",
        "description_en": "Durum wheat",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100310": {
        "chapter": "10",
        "description_fr": "Orge de semence",
        "description_en": "Seed barley",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100390": {
        "chapter": "10",
        "description_fr": "Orge autre",
        "description_en": "Other barley",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100510": {
        "chapter": "10",
        "description_fr": "Maïs de semence",
        "description_en": "Seed maize",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "certification"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100640": {
        "chapter": "10",
        "description_fr": "Riz en brisures",
        "description_en": "Broken rice",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100710": {
        "chapter": "10",
        "description_fr": "Sorgho à grains",
        "description_en": "Grain sorghum",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100821": {
        "chapter": "10",
        "description_fr": "Millet de semence",
        "description_en": "Seed millet",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100829": {
        "chapter": "10",
        "description_fr": "Millet autre",
        "description_en": "Other millet",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100840": {
        "chapter": "10",
        "description_fr": "Fonio (Digitaria spp.)",
        "description_en": "Fonio (Digitaria spp.)",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "100890": {
        "chapter": "10",
        "description_fr": "Autres céréales (teff, éleusine)",
        "description_en": "Other cereals (teff, eleusine)",
        "category": "cereals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 11 - PRODUITS DE MINOTERIE
    # =========================================================================
    "110100": {
        "chapter": "11",
        "description_fr": "Farines de blé ou de méteil",
        "description_en": "Wheat or meslin flour",
        "category": "flour",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Mouture en Afrique - 40% VA", "requirement_en": "Milled in Africa - 40% VA", "regional_content": 40}
    },
    "110220": {
        "chapter": "11",
        "description_fr": "Farine de maïs",
        "description_en": "Maize flour",
        "category": "flour",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Mouture en Afrique - 40% VA", "requirement_en": "Milled in Africa - 40% VA", "regional_content": 40}
    },
    "110620": {
        "chapter": "11",
        "description_fr": "Farine de manioc",
        "description_en": "Manioc flour",
        "category": "flour",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Mouture en Afrique", "requirement_en": "Milled in Africa", "regional_content": 40}
    },
    "110812": {
        "chapter": "11",
        "description_fr": "Amidon de maïs",
        "description_en": "Maize starch",
        "category": "starch",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "110814": {
        "chapter": "11",
        "description_fr": "Fécule de manioc",
        "description_en": "Manioc starch",
        "category": "starch",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 12 - OLÉAGINEUX (Compléments)
    # =========================================================================
    "120190": {
        "chapter": "12",
        "description_fr": "Fèves de soja autres",
        "description_en": "Other soya beans",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "120241": {
        "chapter": "12",
        "description_fr": "Arachides en coques",
        "description_en": "Groundnuts in shell",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "120600": {
        "chapter": "12",
        "description_fr": "Graines de tournesol",
        "description_en": "Sunflower seeds",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "120710": {
        "chapter": "12",
        "description_fr": "Noix et amandes de palmiste",
        "description_en": "Palm nuts and kernels",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "120721": {
        "chapter": "12",
        "description_fr": "Graines de coton de semence",
        "description_en": "Cotton seeds for sowing",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "121190": {
        "chapter": "12",
        "description_fr": "Plantes pour parfumerie/pharmacie",
        "description_en": "Plants for perfumery/pharmacy",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "121292": {
        "chapter": "12",
        "description_fr": "Canne à sucre fraîche",
        "description_en": "Fresh sugar cane",
        "category": "sugar",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 13 - GOMMES ET RÉSINES (Compléments)
    # =========================================================================
    "130219": {
        "chapter": "13",
        "description_fr": "Autres sucs et extraits végétaux",
        "description_en": "Other vegetable saps and extracts",
        "category": "gums",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 14 - MATIÈRES À TRESSER
    # =========================================================================
    "140110": {
        "chapter": "14",
        "description_fr": "Bambous",
        "description_en": "Bamboos",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "140120": {
        "chapter": "14",
        "description_fr": "Rotins",
        "description_en": "Rattans",
        "category": "plants",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 15 - GRAISSES ET HUILES (Compléments)
    # =========================================================================
    "150710": {
        "chapter": "15",
        "description_fr": "Huile de soja brute",
        "description_en": "Crude soybean oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Extraction en Afrique", "requirement_en": "Extracted in Africa", "regional_content": 40}
    },
    "150790": {
        "chapter": "15",
        "description_fr": "Huile de soja raffinée",
        "description_en": "Refined soybean oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffinage en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "150810": {
        "chapter": "15",
        "description_fr": "Huile d'arachide brute",
        "description_en": "Crude groundnut oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Extraction en Afrique", "requirement_en": "Extracted in Africa", "regional_content": 40}
    },
    "150890": {
        "chapter": "15",
        "description_fr": "Huile d'arachide raffinée",
        "description_en": "Refined groundnut oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffinage en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "151190": {
        "chapter": "15",
        "description_fr": "Huile de palme raffinée",
        "description_en": "Refined palm oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use", "local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffinage en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "151211": {
        "chapter": "15",
        "description_fr": "Huile de tournesol brute",
        "description_en": "Crude sunflower oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Extraction en Afrique", "requirement_en": "Extracted in Africa", "regional_content": 40}
    },
    "151219": {
        "chapter": "15",
        "description_fr": "Huile de tournesol raffinée",
        "description_en": "Refined sunflower oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffinage en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "151321": {
        "chapter": "15",
        "description_fr": "Huile de palmiste brute",
        "description_en": "Crude palm kernel oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Extraction en Afrique", "requirement_en": "Extracted in Africa", "regional_content": 40}
    },
    "151550": {
        "chapter": "15",
        "description_fr": "Huile de sésame",
        "description_en": "Sesame oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Extraction en Afrique", "requirement_en": "Extracted in Africa", "regional_content": 40}
    },
    "151710": {
        "chapter": "15",
        "description_fr": "Margarine",
        "description_en": "Margarine",
        "category": "fats",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "152110": {
        "chapter": "15",
        "description_fr": "Cires végétales",
        "description_en": "Vegetable waxes",
        "category": "waxes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "152190": {
        "chapter": "15",
        "description_fr": "Cires d'abeilles et d'autres insectes",
        "description_en": "Beeswax and other insect waxes",
        "category": "waxes",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
}
