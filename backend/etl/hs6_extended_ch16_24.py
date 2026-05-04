"""
EXTENSION BASE HS6 - CHAPITRES 16-24
=====================================
Préparations alimentaires, Boissons, Tabac
Produits transformés du commerce africain

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

HS6_EXTENDED_CH16_24 = {
    # =========================================================================
    # CHAPITRE 16 - PRÉPARATIONS DE VIANDES ET POISSONS
    # =========================================================================
    "160100": {
        "chapter": "16",
        "description_fr": "Saucisses et produits similaires",
        "description_en": "Sausages and similar products",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160210": {
        "chapter": "16",
        "description_fr": "Préparations homogénéisées de viande",
        "description_en": "Homogenized meat preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160220": {
        "chapter": "16",
        "description_fr": "Foies préparés",
        "description_en": "Prepared livers",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160231": {
        "chapter": "16",
        "description_fr": "Préparations de dindes",
        "description_en": "Turkey preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160232": {
        "chapter": "16",
        "description_fr": "Préparations de volailles",
        "description_en": "Poultry preparations",
        "category": "processed_food",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160241": {
        "chapter": "16",
        "description_fr": "Jambons et morceaux de porcins",
        "description_en": "Hams and pork cuts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160249": {
        "chapter": "16",
        "description_fr": "Autres préparations de porcins",
        "description_en": "Other pork preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160250": {
        "chapter": "16",
        "description_fr": "Préparations de bovins",
        "description_en": "Bovine preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160290": {
        "chapter": "16",
        "description_fr": "Autres préparations de viandes",
        "description_en": "Other meat preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "160411": {
        "chapter": "16",
        "description_fr": "Saumons préparés",
        "description_en": "Prepared salmon",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - poisson africain ou 35% VA", "requirement_en": "Processed in Africa - African fish or 35% VA", "regional_content": 35}
    },
    "160412": {
        "chapter": "16",
        "description_fr": "Harengs préparés",
        "description_en": "Prepared herrings",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - poisson africain ou 35% VA", "requirement_en": "Processed in Africa - African fish or 35% VA", "regional_content": 35}
    },
    "160413": {
        "chapter": "16",
        "description_fr": "Sardines préparées",
        "description_en": "Prepared sardines",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - poisson africain ou 35% VA", "requirement_en": "Processed in Africa - African fish or 35% VA", "regional_content": 35}
    },
    "160415": {
        "chapter": "16",
        "description_fr": "Maquereaux préparés",
        "description_en": "Prepared mackerel",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - poisson africain ou 35% VA", "requirement_en": "Processed in Africa - African fish or 35% VA", "regional_content": 35}
    },
    "160416": {
        "chapter": "16",
        "description_fr": "Anchois préparés",
        "description_en": "Prepared anchovies",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160419": {
        "chapter": "16",
        "description_fr": "Autres poissons préparés entiers",
        "description_en": "Other whole prepared fish",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160420": {
        "chapter": "16",
        "description_fr": "Autres préparations de poissons",
        "description_en": "Other fish preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160431": {
        "chapter": "16",
        "description_fr": "Caviar",
        "description_en": "Caviar",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "origin"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 35}
    },
    "160432": {
        "chapter": "16",
        "description_fr": "Succédanés du caviar",
        "description_en": "Caviar substitutes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 35}
    },
    "160510": {
        "chapter": "16",
        "description_fr": "Crabes préparés",
        "description_en": "Prepared crabs",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160521": {
        "chapter": "16",
        "description_fr": "Crevettes préparées non conditionnées",
        "description_en": "Prepared shrimp not in containers",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160529": {
        "chapter": "16",
        "description_fr": "Crevettes préparées autres",
        "description_en": "Other prepared shrimp",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "160553": {
        "chapter": "16",
        "description_fr": "Moules préparées",
        "description_en": "Prepared mussels",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 35}
    },
    "160554": {
        "chapter": "16",
        "description_fr": "Seiches et calamars préparés",
        "description_en": "Prepared cuttlefish and squid",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 35}
    },
    "160555": {
        "chapter": "16",
        "description_fr": "Poulpes préparés",
        "description_en": "Prepared octopus",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 35}
    },
    
    # =========================================================================
    # CHAPITRE 17 - SUCRES ET SUCRERIES (Compléments)
    # =========================================================================
    "170191": {
        "chapter": "17",
        "description_fr": "Sucre blanc avec aromatisants",
        "description_en": "White sugar with flavorings",
        "category": "sugar",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffinage en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "170210": {
        "chapter": "17",
        "description_fr": "Lactose et sirop de lactose",
        "description_en": "Lactose and lactose syrup",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "170220": {
        "chapter": "17",
        "description_fr": "Sucre d'érable",
        "description_en": "Maple sugar",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "170230": {
        "chapter": "17",
        "description_fr": "Glucose et sirop de glucose",
        "description_en": "Glucose and glucose syrup",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "170240": {
        "chapter": "17",
        "description_fr": "Glucose chimiquement pur",
        "description_en": "Chemically pure glucose",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "170250": {
        "chapter": "17",
        "description_fr": "Fructose chimiquement pur",
        "description_en": "Chemically pure fructose",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "170260": {
        "chapter": "17",
        "description_fr": "Autres fructoses et sirops de fructose",
        "description_en": "Other fructose and fructose syrup",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "170290": {
        "chapter": "17",
        "description_fr": "Autres sucres (sucre inverti, miel artificiel)",
        "description_en": "Other sugars (invert sugar, artificial honey)",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "170310": {
        "chapter": "17",
        "description_fr": "Mélasse de canne",
        "description_en": "Cane molasses",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "170390": {
        "chapter": "17",
        "description_fr": "Autres mélasses",
        "description_en": "Other molasses",
        "category": "sugar",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "170410": {
        "chapter": "17",
        "description_fr": "Gommes à mâcher",
        "description_en": "Chewing gum",
        "category": "confectionery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "170490": {
        "chapter": "17",
        "description_fr": "Autres sucreries sans cacao",
        "description_en": "Other sugar confectionery without cocoa",
        "category": "confectionery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 18 - CACAO (Compléments)
    # =========================================================================
    "180200": {
        "chapter": "18",
        "description_fr": "Coques, pellicules de cacao",
        "description_en": "Cocoa shells and husks",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "180320": {
        "chapter": "18",
        "description_fr": "Pâte de cacao dégraissée",
        "description_en": "Defatted cocoa paste",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "180500": {
        "chapter": "18",
        "description_fr": "Poudre de cacao sans sucre",
        "description_en": "Cocoa powder without sugar",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "180610": {
        "chapter": "18",
        "description_fr": "Poudre de cacao sucrée",
        "description_en": "Sweetened cocoa powder",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "180620": {
        "chapter": "18",
        "description_fr": "Préparations alimentaires au cacao (>2kg)",
        "description_en": "Cocoa food preparations (>2kg)",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "180631": {
        "chapter": "18",
        "description_fr": "Chocolat fourré en blocs",
        "description_en": "Filled chocolate in blocks",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "180632": {
        "chapter": "18",
        "description_fr": "Chocolat non fourré en blocs",
        "description_en": "Unfilled chocolate in blocks",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "180690": {
        "chapter": "18",
        "description_fr": "Autres chocolats et préparations",
        "description_en": "Other chocolates and preparations",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 19 - PRÉPARATIONS DE CÉRÉALES
    # =========================================================================
    "190110": {
        "chapter": "19",
        "description_fr": "Préparations pour nourrissons",
        "description_en": "Infant food preparations",
        "category": "processed_food",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190120": {
        "chapter": "19",
        "description_fr": "Préparations pour boulangerie",
        "description_en": "Bakery preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190190": {
        "chapter": "19",
        "description_fr": "Autres préparations alimentaires de farines",
        "description_en": "Other flour food preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190211": {
        "chapter": "19",
        "description_fr": "Pâtes non cuites aux oeufs",
        "description_en": "Uncooked pasta with eggs",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190219": {
        "chapter": "19",
        "description_fr": "Autres pâtes non cuites",
        "description_en": "Other uncooked pasta",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190220": {
        "chapter": "19",
        "description_fr": "Pâtes farcies",
        "description_en": "Stuffed pasta",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190230": {
        "chapter": "19",
        "description_fr": "Autres pâtes alimentaires",
        "description_en": "Other pasta",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190240": {
        "chapter": "19",
        "description_fr": "Couscous",
        "description_en": "Couscous",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190300": {
        "chapter": "19",
        "description_fr": "Tapioca et substituts",
        "description_en": "Tapioca and substitutes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "190410": {
        "chapter": "19",
        "description_fr": "Produits céréaliers soufflés (cornflakes)",
        "description_en": "Puffed cereal products (cornflakes)",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190420": {
        "chapter": "19",
        "description_fr": "Préparations de flocons de céréales",
        "description_en": "Cereal flake preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190430": {
        "chapter": "19",
        "description_fr": "Bulgur",
        "description_en": "Bulgur wheat",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "190490": {
        "chapter": "19",
        "description_fr": "Autres céréales en grains",
        "description_en": "Other cereal grains",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "190510": {
        "chapter": "19",
        "description_fr": "Pain croustillant (crispbread)",
        "description_en": "Crispbread",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190520": {
        "chapter": "19",
        "description_fr": "Pain d'épices",
        "description_en": "Gingerbread",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190531": {
        "chapter": "19",
        "description_fr": "Biscuits sucrés",
        "description_en": "Sweet biscuits",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190532": {
        "chapter": "19",
        "description_fr": "Gaufres et gaufrettes",
        "description_en": "Waffles and wafers",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190540": {
        "chapter": "19",
        "description_fr": "Biscottes et pain grillé",
        "description_en": "Rusks and toasted bread",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "190590": {
        "chapter": "19",
        "description_fr": "Autres produits de boulangerie",
        "description_en": "Other bakery products",
        "category": "bakery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 20 - PRÉPARATIONS DE LÉGUMES ET FRUITS
    # =========================================================================
    "200110": {
        "chapter": "20",
        "description_fr": "Concombres et cornichons au vinaigre",
        "description_en": "Cucumbers and gherkins in vinegar",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200190": {
        "chapter": "20",
        "description_fr": "Autres légumes au vinaigre",
        "description_en": "Other vegetables in vinegar",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200210": {
        "chapter": "20",
        "description_fr": "Tomates entières ou en morceaux",
        "description_en": "Whole or cut tomatoes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200290": {
        "chapter": "20",
        "description_fr": "Autres tomates préparées",
        "description_en": "Other prepared tomatoes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200310": {
        "chapter": "20",
        "description_fr": "Champignons préparés",
        "description_en": "Prepared mushrooms",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200490": {
        "chapter": "20",
        "description_fr": "Autres légumes préparés",
        "description_en": "Other prepared vegetables",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200510": {
        "chapter": "20",
        "description_fr": "Légumes homogénéisés",
        "description_en": "Homogenized vegetables",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200520": {
        "chapter": "20",
        "description_fr": "Pommes de terre préparées",
        "description_en": "Prepared potatoes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200540": {
        "chapter": "20",
        "description_fr": "Pois préparés",
        "description_en": "Prepared peas",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200551": {
        "chapter": "20",
        "description_fr": "Haricots en grains préparés",
        "description_en": "Prepared shelled beans",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200560": {
        "chapter": "20",
        "description_fr": "Asperges préparées",
        "description_en": "Prepared asparagus",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200570": {
        "chapter": "20",
        "description_fr": "Olives préparées",
        "description_en": "Prepared olives",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200580": {
        "chapter": "20",
        "description_fr": "Maïs doux préparé",
        "description_en": "Prepared sweet corn",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200591": {
        "chapter": "20",
        "description_fr": "Pousses de bambou préparées",
        "description_en": "Prepared bamboo shoots",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200600": {
        "chapter": "20",
        "description_fr": "Légumes et fruits confits au sucre",
        "description_en": "Vegetables and fruits preserved by sugar",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200710": {
        "chapter": "20",
        "description_fr": "Préparations homogénéisées (confitures)",
        "description_en": "Homogenized preparations (jams)",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200791": {
        "chapter": "20",
        "description_fr": "Confitures et marmelades d'agrumes",
        "description_en": "Citrus jams and marmalades",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200799": {
        "chapter": "20",
        "description_fr": "Autres confitures et marmelades",
        "description_en": "Other jams and marmalades",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200811": {
        "chapter": "20",
        "description_fr": "Cacahuètes préparées",
        "description_en": "Prepared groundnuts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200819": {
        "chapter": "20",
        "description_fr": "Autres fruits à coques préparés",
        "description_en": "Other prepared nuts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200820": {
        "chapter": "20",
        "description_fr": "Ananas préparés",
        "description_en": "Prepared pineapples",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - fruits africains ou 40% VA", "requirement_en": "Processed in Africa - African fruits or 40% VA", "regional_content": 40}
    },
    "200830": {
        "chapter": "20",
        "description_fr": "Agrumes préparés",
        "description_en": "Prepared citrus",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200840": {
        "chapter": "20",
        "description_fr": "Poires préparées",
        "description_en": "Prepared pears",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200850": {
        "chapter": "20",
        "description_fr": "Abricots préparés",
        "description_en": "Prepared apricots",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200860": {
        "chapter": "20",
        "description_fr": "Cerises préparées",
        "description_en": "Prepared cherries",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200870": {
        "chapter": "20",
        "description_fr": "Pêches préparées",
        "description_en": "Prepared peaches",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200880": {
        "chapter": "20",
        "description_fr": "Fraises préparées",
        "description_en": "Prepared strawberries",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200893": {
        "chapter": "20",
        "description_fr": "Canneberges préparées",
        "description_en": "Prepared cranberries",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200897": {
        "chapter": "20",
        "description_fr": "Mélanges de fruits préparés",
        "description_en": "Prepared fruit mixtures",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200899": {
        "chapter": "20",
        "description_fr": "Autres fruits préparés",
        "description_en": "Other prepared fruits",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200911": {
        "chapter": "20",
        "description_fr": "Jus d'orange congelé",
        "description_en": "Frozen orange juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200912": {
        "chapter": "20",
        "description_fr": "Jus d'orange non congelé",
        "description_en": "Non-frozen orange juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200919": {
        "chapter": "20",
        "description_fr": "Autres jus d'orange",
        "description_en": "Other orange juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200921": {
        "chapter": "20",
        "description_fr": "Jus de pamplemousse",
        "description_en": "Grapefruit juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200929": {
        "chapter": "20",
        "description_fr": "Autres jus d'agrumes",
        "description_en": "Other citrus juices",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200931": {
        "chapter": "20",
        "description_fr": "Jus d'un seul agrume",
        "description_en": "Single citrus fruit juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200941": {
        "chapter": "20",
        "description_fr": "Jus d'ananas",
        "description_en": "Pineapple juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - fruits africains ou 40% VA", "requirement_en": "Processed in Africa - African fruits or 40% VA", "regional_content": 40}
    },
    "200949": {
        "chapter": "20",
        "description_fr": "Autres jus d'ananas",
        "description_en": "Other pineapple juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200950": {
        "chapter": "20",
        "description_fr": "Jus de tomate",
        "description_en": "Tomato juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200961": {
        "chapter": "20",
        "description_fr": "Jus de raisin non concentré",
        "description_en": "Non-concentrated grape juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200971": {
        "chapter": "20",
        "description_fr": "Jus de pomme non concentré",
        "description_en": "Non-concentrated apple juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200981": {
        "chapter": "20",
        "description_fr": "Jus de canneberge",
        "description_en": "Cranberry juice",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "200989": {
        "chapter": "20",
        "description_fr": "Autres jus de fruits ou légumes",
        "description_en": "Other fruit or vegetable juices",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 21 - PRÉPARATIONS ALIMENTAIRES DIVERSES
    # =========================================================================
    "210111": {
        "chapter": "21",
        "description_fr": "Extraits de café",
        "description_en": "Coffee extracts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "210112": {
        "chapter": "21",
        "description_fr": "Préparations à base d'extraits de café",
        "description_en": "Preparations based on coffee extracts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "210120": {
        "chapter": "21",
        "description_fr": "Extraits de thé ou maté",
        "description_en": "Tea or maté extracts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 35% VA", "requirement_en": "Processed in Africa - 35% VA", "regional_content": 35}
    },
    "210130": {
        "chapter": "21",
        "description_fr": "Chicorée torréfiée et extraits",
        "description_en": "Roasted chicory and extracts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "210210": {
        "chapter": "21",
        "description_fr": "Levures actives",
        "description_en": "Active yeasts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210220": {
        "chapter": "21",
        "description_fr": "Levures inactives",
        "description_en": "Inactive yeasts",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210230": {
        "chapter": "21",
        "description_fr": "Poudres à lever préparées",
        "description_en": "Prepared baking powders",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210310": {
        "chapter": "21",
        "description_fr": "Sauce soja",
        "description_en": "Soy sauce",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210320": {
        "chapter": "21",
        "description_fr": "Ketchup et autres sauces tomates",
        "description_en": "Ketchup and other tomato sauces",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210330": {
        "chapter": "21",
        "description_fr": "Farine de moutarde et moutarde préparée",
        "description_en": "Mustard flour and prepared mustard",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210390": {
        "chapter": "21",
        "description_fr": "Autres sauces et condiments",
        "description_en": "Other sauces and condiments",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210410": {
        "chapter": "21",
        "description_fr": "Préparations pour soupes et potages",
        "description_en": "Soup and broth preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210420": {
        "chapter": "21",
        "description_fr": "Préparations alimentaires composites",
        "description_en": "Composite food preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210500": {
        "chapter": "21",
        "description_fr": "Glaces de consommation",
        "description_en": "Ice cream",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "210690": {
        "chapter": "21",
        "description_fr": "Autres préparations alimentaires",
        "description_en": "Other food preparations",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 22 - BOISSONS
    # =========================================================================
    "220110": {
        "chapter": "22",
        "description_fr": "Eaux minérales et eaux gazéifiées",
        "description_en": "Mineral and aerated waters",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "220190": {
        "chapter": "22",
        "description_fr": "Autres eaux non sucrées",
        "description_en": "Other unsweetened waters",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "220210": {
        "chapter": "22",
        "description_fr": "Eaux avec sucre ou édulcorants",
        "description_en": "Waters with sugar or sweeteners",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220291": {
        "chapter": "22",
        "description_fr": "Bières sans alcool",
        "description_en": "Non-alcoholic beers",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220299": {
        "chapter": "22",
        "description_fr": "Autres boissons non alcoolisées",
        "description_en": "Other non-alcoholic beverages",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220300": {
        "chapter": "22",
        "description_fr": "Bières de malt",
        "description_en": "Beer made from malt",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Brassé en Afrique - 40% VA", "requirement_en": "Brewed in Africa - 40% VA", "regional_content": 40}
    },
    "220410": {
        "chapter": "22",
        "description_fr": "Vins mousseux",
        "description_en": "Sparkling wines",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Vinifié en Afrique - raisins africains ou 40% VA", "requirement_en": "Vinified in Africa - African grapes or 40% VA", "regional_content": 40}
    },
    "220421": {
        "chapter": "22",
        "description_fr": "Vins de raisins frais en récipients ≤2L",
        "description_en": "Fresh grape wines in containers ≤2L",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Vinifié en Afrique - raisins africains ou 40% VA", "requirement_en": "Vinified in Africa - African grapes or 40% VA", "regional_content": 40}
    },
    "220429": {
        "chapter": "22",
        "description_fr": "Autres vins de raisins frais",
        "description_en": "Other fresh grape wines",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Vinifié en Afrique - 40% VA", "requirement_en": "Vinified in Africa - 40% VA", "regional_content": 40}
    },
    "220430": {
        "chapter": "22",
        "description_fr": "Moûts de raisins",
        "description_en": "Grape musts",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "220510": {
        "chapter": "22",
        "description_fr": "Vermouths et vins aromatisés",
        "description_en": "Vermouths and aromatized wines",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220590": {
        "chapter": "22",
        "description_fr": "Autres vermouths",
        "description_en": "Other vermouths",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220600": {
        "chapter": "22",
        "description_fr": "Cidre, poiré, hydromel",
        "description_en": "Cider, perry, mead",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220710": {
        "chapter": "22",
        "description_fr": "Alcool éthylique non dénaturé >80%",
        "description_en": "Undenatured ethyl alcohol >80%",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220720": {
        "chapter": "22",
        "description_fr": "Alcool éthylique dénaturé",
        "description_en": "Denatured ethyl alcohol",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220820": {
        "chapter": "22",
        "description_fr": "Eaux-de-vie de raisins",
        "description_en": "Grape brandies",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220830": {
        "chapter": "22",
        "description_fr": "Whiskies",
        "description_en": "Whiskies",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220840": {
        "chapter": "22",
        "description_fr": "Rhum et tafia",
        "description_en": "Rum and tafia",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220850": {
        "chapter": "22",
        "description_fr": "Gin et genièvre",
        "description_en": "Gin and Geneva",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220860": {
        "chapter": "22",
        "description_fr": "Vodka",
        "description_en": "Vodka",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillé en Afrique - 40% VA", "requirement_en": "Distilled in Africa - 40% VA", "regional_content": 40}
    },
    "220870": {
        "chapter": "22",
        "description_fr": "Liqueurs et crèmes",
        "description_en": "Liqueurs and cordials",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220890": {
        "chapter": "22",
        "description_fr": "Autres spiritueux",
        "description_en": "Other spirits",
        "category": "beverages",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "220900": {
        "chapter": "22",
        "description_fr": "Vinaigres et succédanés",
        "description_en": "Vinegar and substitutes",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 23 - RÉSIDUS ET ALIMENTS POUR ANIMAUX
    # =========================================================================
    "230110": {
        "chapter": "23",
        "description_fr": "Farines de viandes ou d'abats",
        "description_en": "Flours of meat or offal",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "230120": {
        "chapter": "23",
        "description_fr": "Farines de poissons",
        "description_en": "Fish meal",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - poisson africain ou 35% VA", "requirement_en": "Processed in Africa - African fish or 35% VA", "regional_content": 35}
    },
    "230210": {
        "chapter": "23",
        "description_fr": "Sons et résidus de maïs",
        "description_en": "Maize bran and residues",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "230230": {
        "chapter": "23",
        "description_fr": "Sons et résidus de blé",
        "description_en": "Wheat bran and residues",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "230240": {
        "chapter": "23",
        "description_fr": "Sons et résidus d'autres céréales",
        "description_en": "Other cereal bran and residues",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "230250": {
        "chapter": "23",
        "description_fr": "Sons et résidus de légumineuses",
        "description_en": "Legume bran and residues",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "230310": {
        "chapter": "23",
        "description_fr": "Résidus d'amidonnerie",
        "description_en": "Starch manufacturing residues",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "230400": {
        "chapter": "23",
        "description_fr": "Tourteaux de soja",
        "description_en": "Soybean oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230500": {
        "chapter": "23",
        "description_fr": "Tourteaux d'arachide",
        "description_en": "Groundnut oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230610": {
        "chapter": "23",
        "description_fr": "Tourteaux de coton",
        "description_en": "Cottonseed oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230641": {
        "chapter": "23",
        "description_fr": "Tourteaux de colza",
        "description_en": "Rapeseed oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230650": {
        "chapter": "23",
        "description_fr": "Tourteaux de noix de coco",
        "description_en": "Coconut oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230660": {
        "chapter": "23",
        "description_fr": "Tourteaux de palmiste",
        "description_en": "Palm kernel oilcake",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230690": {
        "chapter": "23",
        "description_fr": "Autres tourteaux",
        "description_en": "Other oilcakes",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "230800": {
        "chapter": "23",
        "description_fr": "Matières végétales pour alimentation animale",
        "description_en": "Vegetable materials for animal feeding",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "230910": {
        "chapter": "23",
        "description_fr": "Aliments pour chiens et chats (conditionnés)",
        "description_en": "Dog and cat food (retail)",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "230990": {
        "chapter": "23",
        "description_fr": "Autres préparations pour animaux",
        "description_en": "Other animal feed preparations",
        "category": "animal_feed",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 24 - TABAC (Compléments)
    # =========================================================================
    "240120": {
        "chapter": "24",
        "description_fr": "Tabac partiellement ou totalement écôté",
        "description_en": "Partly or wholly stemmed tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "240130": {
        "chapter": "24",
        "description_fr": "Déchets de tabac",
        "description_en": "Tobacco refuse",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "240210": {
        "chapter": "24",
        "description_fr": "Cigares et cigarillos",
        "description_en": "Cigars and cigarillos",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - tabac africain ou 40% VA", "requirement_en": "Manufactured in Africa - African tobacco or 40% VA", "regional_content": 40}
    },
    "240220": {
        "chapter": "24",
        "description_fr": "Cigarettes contenant du tabac",
        "description_en": "Cigarettes containing tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - tabac africain ou 40% VA", "requirement_en": "Manufactured in Africa - African tobacco or 40% VA", "regional_content": 40}
    },
    "240290": {
        "chapter": "24",
        "description_fr": "Autres cigarettes et cigares",
        "description_en": "Other cigarettes and cigars",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "240311": {
        "chapter": "24",
        "description_fr": "Tabac à pipe à fumer",
        "description_en": "Pipe tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "240319": {
        "chapter": "24",
        "description_fr": "Autres tabacs à fumer",
        "description_en": "Other smoking tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "240391": {
        "chapter": "24",
        "description_fr": "Tabac homogénéisé ou reconstitué",
        "description_en": "Homogenized or reconstituted tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "240399": {
        "chapter": "24",
        "description_fr": "Autres tabacs manufacturés",
        "description_en": "Other manufactured tobacco",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
}
