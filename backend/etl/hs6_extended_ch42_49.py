"""
EXTENSION HS6 - CHAPITRES 42-49
Cuir, pelleteries, liège, vannerie, pâte de bois, papier, imprimés
"""

HS6_EXTENDED_CH42_49 = {
    # CHAPITRE 42 - OUVRAGES EN CUIR
    "420100": {
        "chapter": "42",
        "description_fr": "Articles de sellerie et de bourrellerie",
        "description_en": "Saddlery and harness",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420211": {
        "chapter": "42",
        "description_fr": "Malles et valises à surface extérieure en cuir",
        "description_en": "Trunks and suitcases with outer surface of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420212": {
        "chapter": "42",
        "description_fr": "Malles et valises à surface extérieure en plastique",
        "description_en": "Trunks and suitcases with outer surface of plastics",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420219": {
        "chapter": "42",
        "description_fr": "Autres malles et valises",
        "description_en": "Other trunks and suitcases",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420221": {
        "chapter": "42",
        "description_fr": "Sacs à main à surface extérieure en cuir",
        "description_en": "Handbags with outer surface of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420222": {
        "chapter": "42",
        "description_fr": "Sacs à main à surface extérieure en feuilles de plastique",
        "description_en": "Handbags with outer surface of plastic sheeting",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420229": {
        "chapter": "42",
        "description_fr": "Autres sacs à main",
        "description_en": "Other handbags",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420231": {
        "chapter": "42",
        "description_fr": "Articles de poche à surface extérieure en cuir",
        "description_en": "Articles carried in pocket with outer surface of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420232": {
        "chapter": "42",
        "description_fr": "Articles de poche à surface extérieure en plastique",
        "description_en": "Articles carried in pocket with outer surface of plastics",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420239": {
        "chapter": "42",
        "description_fr": "Autres articles de poche",
        "description_en": "Other articles carried in pocket",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420291": {
        "chapter": "42",
        "description_fr": "Autres contenants à surface extérieure en cuir",
        "description_en": "Other containers with outer surface of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420292": {
        "chapter": "42",
        "description_fr": "Autres contenants à surface extérieure en plastique",
        "description_en": "Other containers with outer surface of plastics",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420299": {
        "chapter": "42",
        "description_fr": "Autres contenants",
        "description_en": "Other containers",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420310": {
        "chapter": "42",
        "description_fr": "Vêtements en cuir naturel ou reconstitué",
        "description_en": "Articles of apparel of leather or of composition leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420321": {
        "chapter": "42",
        "description_fr": "Gants de sport en cuir",
        "description_en": "Sports gloves of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420329": {
        "chapter": "42",
        "description_fr": "Autres gants en cuir",
        "description_en": "Other gloves of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420330": {
        "chapter": "42",
        "description_fr": "Ceintures et baudriers en cuir",
        "description_en": "Belts and bandoliers of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420340": {
        "chapter": "42",
        "description_fr": "Autres accessoires du vêtement en cuir",
        "description_en": "Other clothing accessories of leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420400": {
        "chapter": "42",
        "description_fr": "Articles en cuir pour usages techniques",
        "description_en": "Articles of leather for technical uses",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420500": {
        "chapter": "42",
        "description_fr": "Autres ouvrages en cuir naturel ou reconstitué",
        "description_en": "Other articles of leather or of composition leather",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "420600": {
        "chapter": "42",
        "description_fr": "Ouvrages en boyaux, baudruches, vessies ou tendons",
        "description_en": "Articles of gut, goldbeater's skin, bladders or tendons",
        "category": "leather_goods",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },

    # CHAPITRE 43 - PELLETERIES ET FOURRURES
    "430110": {
        "chapter": "43",
        "description_fr": "Pelleteries brutes de visons",
        "description_en": "Raw furskins of mink",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "430130": {
        "chapter": "43",
        "description_fr": "Pelleteries brutes d'agneaux astrakan, breitschwanz, karakul",
        "description_en": "Raw furskins of lamb, Astrakhan, Broadtail, Caracul",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "430160": {
        "chapter": "43",
        "description_fr": "Pelleteries brutes de renards",
        "description_en": "Raw furskins of fox",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "430180": {
        "chapter": "43",
        "description_fr": "Autres pelleteries brutes",
        "description_en": "Other raw furskins",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "430190": {
        "chapter": "43",
        "description_fr": "Têtes, queues, pattes et autres morceaux de pelleteries",
        "description_en": "Heads, tails, paws and other pieces of raw furskins",
        "category": "furs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "430211": {
        "chapter": "43",
        "description_fr": "Pelleteries tannées de visons entières",
        "description_en": "Whole tanned furskins of mink",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "430219": {
        "chapter": "43",
        "description_fr": "Autres pelleteries tannées entières",
        "description_en": "Other whole tanned furskins",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "430220": {
        "chapter": "43",
        "description_fr": "Têtes, queues, pattes et autres morceaux de pelleteries tannées",
        "description_en": "Heads, tails, paws and other pieces of tanned furskins",
        "category": "furs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "430230": {
        "chapter": "43",
        "description_fr": "Pelleteries tannées assemblées en nappes",
        "description_en": "Tanned furskins assembled in plates",
        "category": "furs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "430310": {
        "chapter": "43",
        "description_fr": "Vêtements et accessoires du vêtement en pelleteries",
        "description_en": "Articles of apparel and clothing accessories of furskin",
        "category": "furs",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "430390": {
        "chapter": "43",
        "description_fr": "Autres articles en pelleteries",
        "description_en": "Other articles of furskin",
        "category": "furs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "430400": {
        "chapter": "43",
        "description_fr": "Pelleteries factices et articles en pelleteries factices",
        "description_en": "Artificial fur and articles thereof",
        "category": "furs",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },

    # CHAPITRE 45 - LIÈGE
    "450110": {
        "chapter": "45",
        "description_fr": "Liège naturel brut ou simplement préparé",
        "description_en": "Natural cork, raw or simply prepared",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "450190": {
        "chapter": "45",
        "description_fr": "Déchets de liège; liège concassé ou granulé",
        "description_en": "Waste cork; crushed, granulated or ground cork",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "450200": {
        "chapter": "45",
        "description_fr": "Liège naturel écroûté ou équarri",
        "description_en": "Natural cork, debacked or roughly squared",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "450310": {
        "chapter": "45",
        "description_fr": "Bouchons en liège naturel",
        "description_en": "Corks and stoppers of natural cork",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "450390": {
        "chapter": "45",
        "description_fr": "Autres ouvrages en liège naturel",
        "description_en": "Other articles of natural cork",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "450410": {
        "chapter": "45",
        "description_fr": "Liège aggloméré en cubes, plaques, feuilles",
        "description_en": "Agglomerated cork in blocks, plates, sheets",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "450490": {
        "chapter": "45",
        "description_fr": "Autres ouvrages en liège aggloméré",
        "description_en": "Other articles of agglomerated cork",
        "category": "cork",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },

    # CHAPITRE 46 - VANNERIE
    "460110": {
        "chapter": "46",
        "description_fr": "Tresses et articles similaires en matières à tresser",
        "description_en": "Plaits and similar products of plaiting materials",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460121": {
        "chapter": "46",
        "description_fr": "Nattes, paillassons et claies en bambou",
        "description_en": "Mats, matting and screens of bamboo",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460122": {
        "chapter": "46",
        "description_fr": "Nattes, paillassons et claies en rotin",
        "description_en": "Mats, matting and screens of rattan",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460129": {
        "chapter": "46",
        "description_fr": "Autres nattes, paillassons et claies en matières végétales",
        "description_en": "Other mats, matting and screens of vegetable materials",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460192": {
        "chapter": "46",
        "description_fr": "Autres articles en bambou",
        "description_en": "Other articles of bamboo",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460193": {
        "chapter": "46",
        "description_fr": "Autres articles en rotin",
        "description_en": "Other articles of rattan",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460194": {
        "chapter": "46",
        "description_fr": "Autres articles en matières végétales",
        "description_en": "Other articles of vegetable materials",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460199": {
        "chapter": "46",
        "description_fr": "Autres articles en matières à tresser",
        "description_en": "Other articles of plaiting materials",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460211": {
        "chapter": "46",
        "description_fr": "Ouvrages de vannerie en bambou",
        "description_en": "Basketwork of bamboo",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460212": {
        "chapter": "46",
        "description_fr": "Ouvrages de vannerie en rotin",
        "description_en": "Basketwork of rattan",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460219": {
        "chapter": "46",
        "description_fr": "Autres ouvrages de vannerie en matières végétales",
        "description_en": "Other basketwork of vegetable materials",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "460290": {
        "chapter": "46",
        "description_fr": "Autres ouvrages de vannerie",
        "description_en": "Other basketwork",
        "category": "basketry",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },

    # CHAPITRE 47 - PÂTES DE BOIS
    "470100": {
        "chapter": "47",
        "description_fr": "Pâtes mécaniques de bois",
        "description_en": "Mechanical wood pulp",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470200": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois à dissoudre",
        "description_en": "Chemical wood pulp, dissolving grades",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470311": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au sulfate, écrues, de conifères",
        "description_en": "Chemical wood pulp, soda or sulphate, unbleached, coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470319": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au sulfate, écrues, non conifères",
        "description_en": "Chemical wood pulp, soda or sulphate, unbleached, non-coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470321": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au sulfate, blanchies, de conifères",
        "description_en": "Chemical wood pulp, soda or sulphate, bleached, coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470329": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au sulfate, blanchies, non conifères",
        "description_en": "Chemical wood pulp, soda or sulphate, bleached, non-coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470411": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au bisulfite, écrues, de conifères",
        "description_en": "Chemical wood pulp, sulphite, unbleached, coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470419": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au bisulfite, écrues, non conifères",
        "description_en": "Chemical wood pulp, sulphite, unbleached, non-coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470421": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au bisulfite, blanchies, de conifères",
        "description_en": "Chemical wood pulp, sulphite, bleached, coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470429": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques de bois au bisulfite, blanchies, non conifères",
        "description_en": "Chemical wood pulp, sulphite, bleached, non-coniferous",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470500": {
        "chapter": "47",
        "description_fr": "Pâtes de bois mi-chimiques",
        "description_en": "Semi-chemical wood pulp",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470610": {
        "chapter": "47",
        "description_fr": "Pâtes de linters de coton",
        "description_en": "Pulp of cotton linters",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470620": {
        "chapter": "47",
        "description_fr": "Pâtes de fibres obtenues à partir de papier récupéré",
        "description_en": "Pulps of fibres derived from recovered paper",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470630": {
        "chapter": "47",
        "description_fr": "Pâtes de bambou",
        "description_en": "Bamboo pulp",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470691": {
        "chapter": "47",
        "description_fr": "Pâtes mécaniques d'autres matières fibreuses cellulosiques",
        "description_en": "Mechanical pulp of other fibrous cellulosic material",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470692": {
        "chapter": "47",
        "description_fr": "Pâtes chimiques d'autres matières fibreuses cellulosiques",
        "description_en": "Chemical pulp of other fibrous cellulosic material",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470693": {
        "chapter": "47",
        "description_fr": "Pâtes mi-chimiques d'autres matières fibreuses cellulosiques",
        "description_en": "Semi-chemical pulp of other fibrous cellulosic material",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470710": {
        "chapter": "47",
        "description_fr": "Papiers ou cartons kraft écrus",
        "description_en": "Unbleached kraft paper or paperboard",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470720": {
        "chapter": "47",
        "description_fr": "Autres papiers ou cartons récupérés non triés",
        "description_en": "Other unsorted recovered paper or paperboard",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "470730": {
        "chapter": "47",
        "description_fr": "Papiers ou cartons obtenus principalement à partir de pâte mécanique",
        "description_en": "Paper or paperboard made mainly of mechanical pulp",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "470790": {
        "chapter": "47",
        "description_fr": "Autres papiers ou cartons récupérés",
        "description_en": "Other recovered paper or paperboard",
        "category": "wood_pulp",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },

    # CHAPITRE 48 - PAPIERS ET CARTONS
    "480100": {
        "chapter": "48",
        "description_fr": "Papier journal en rouleaux ou en feuilles",
        "description_en": "Newsprint, in rolls or sheets",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480210": {
        "chapter": "48",
        "description_fr": "Papier fait main",
        "description_en": "Hand-made paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480220": {
        "chapter": "48",
        "description_fr": "Papier et carton support pour papier photosensible",
        "description_en": "Paper and paperboard for photosensitive paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480254": {
        "chapter": "48",
        "description_fr": "Papier pour écriture < 40 g/m2",
        "description_en": "Writing paper < 40 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480255": {
        "chapter": "48",
        "description_fr": "Papier pour écriture 40-150 g/m2",
        "description_en": "Writing paper 40-150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480256": {
        "chapter": "48",
        "description_fr": "Papier pour écriture > 150 g/m2",
        "description_en": "Writing paper > 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480261": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons en rouleaux",
        "description_en": "Other paper and paperboard in rolls",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480262": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons en feuilles",
        "description_en": "Other paper and paperboard in sheets",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480300": {
        "chapter": "48",
        "description_fr": "Papier des types utilisés pour papier de toilette",
        "description_en": "Toilet or facial tissue stock",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480411": {
        "chapter": "48",
        "description_fr": "Papier kraft pour sacs écrus",
        "description_en": "Unbleached kraft sack paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480419": {
        "chapter": "48",
        "description_fr": "Autres papiers kraft pour sacs",
        "description_en": "Other kraft sack paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480421": {
        "chapter": "48",
        "description_fr": "Papier kraft pour sacs écru non couché",
        "description_en": "Unbleached uncoated kraft sack paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480429": {
        "chapter": "48",
        "description_fr": "Autres papiers kraft non couchés",
        "description_en": "Other uncoated kraft paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480431": {
        "chapter": "48",
        "description_fr": "Papier kraft écru blanchis <= 150 g/m2",
        "description_en": "Unbleached kraft paper <= 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480439": {
        "chapter": "48",
        "description_fr": "Autres papiers kraft écrus",
        "description_en": "Other unbleached kraft paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480441": {
        "chapter": "48",
        "description_fr": "Papiers kraft blanchis <= 150 g/m2",
        "description_en": "Bleached kraft paper <= 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480442": {
        "chapter": "48",
        "description_fr": "Papiers kraft blanchis > 150 g/m2",
        "description_en": "Bleached kraft paper > 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480449": {
        "chapter": "48",
        "description_fr": "Autres papiers kraft blanchis",
        "description_en": "Other bleached kraft paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480451": {
        "chapter": "48",
        "description_fr": "Papier et carton pour couverture écrus",
        "description_en": "Unbleached testliner",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480452": {
        "chapter": "48",
        "description_fr": "Papier et carton pour couverture blanchis",
        "description_en": "Bleached testliner",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480459": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons pour couverture",
        "description_en": "Other testliner",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480511": {
        "chapter": "48",
        "description_fr": "Papier mi-chimique pour cannelure",
        "description_en": "Semi-chemical fluting paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480512": {
        "chapter": "48",
        "description_fr": "Papier paille pour cannelure",
        "description_en": "Straw fluting paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480519": {
        "chapter": "48",
        "description_fr": "Autres papiers pour cannelure",
        "description_en": "Other fluting paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480524": {
        "chapter": "48",
        "description_fr": "Papier et carton pour couverture multicouches <= 150 g/m2",
        "description_en": "Multi-ply testliner <= 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480525": {
        "chapter": "48",
        "description_fr": "Papier et carton pour couverture multicouches > 150 g/m2",
        "description_en": "Multi-ply testliner > 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480530": {
        "chapter": "48",
        "description_fr": "Papier sulfite d'emballage",
        "description_en": "Sulphite wrapping paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480540": {
        "chapter": "48",
        "description_fr": "Papier et carton filtres",
        "description_en": "Filter paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480550": {
        "chapter": "48",
        "description_fr": "Papier et carton feutres",
        "description_en": "Felt paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480591": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons <= 150 g/m2",
        "description_en": "Other paper and paperboard <= 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480592": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons 150-225 g/m2",
        "description_en": "Other paper and paperboard 150-225 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480593": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons > 225 g/m2",
        "description_en": "Other paper and paperboard > 225 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480610": {
        "chapter": "48",
        "description_fr": "Papier et carton sulfurisé (parchemin végétal)",
        "description_en": "Vegetable parchment",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480620": {
        "chapter": "48",
        "description_fr": "Papier résistant aux graisses (greaseproof)",
        "description_en": "Greaseproof papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480630": {
        "chapter": "48",
        "description_fr": "Papier-calque",
        "description_en": "Tracing papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480640": {
        "chapter": "48",
        "description_fr": "Papier cristal et autres papiers calandrés transparents",
        "description_en": "Glassine and other glazed transparent papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480700": {
        "chapter": "48",
        "description_fr": "Papier et carton composites non couchés",
        "description_en": "Composite paper and paperboard, not surface-coated",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480810": {
        "chapter": "48",
        "description_fr": "Papier et carton ondulés",
        "description_en": "Corrugated paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480840": {
        "chapter": "48",
        "description_fr": "Papier kraft crêpé ou plissé",
        "description_en": "Kraft paper, creped or crinkled",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480890": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons ondulés, crêpés, plissés",
        "description_en": "Other corrugated, creped, crinkled paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480910": {
        "chapter": "48",
        "description_fr": "Papier carbone et papiers similaires",
        "description_en": "Carbon paper and similar copying papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480920": {
        "chapter": "48",
        "description_fr": "Papier autocopiant",
        "description_en": "Self-copy paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "480990": {
        "chapter": "48",
        "description_fr": "Autres papiers pour copie ou report",
        "description_en": "Other copying or transfer papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481013": {
        "chapter": "48",
        "description_fr": "Papier et carton couchés au kaolin",
        "description_en": "Paper and paperboard coated with kaolin",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481014": {
        "chapter": "48",
        "description_fr": "Papier et carton couchés au kaolin en rouleaux",
        "description_en": "Paper and paperboard coated with kaolin in rolls",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481019": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons couchés au kaolin",
        "description_en": "Other paper and paperboard coated with kaolin",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481022": {
        "chapter": "48",
        "description_fr": "Papier couché léger (LWC)",
        "description_en": "Light-weight coated paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481029": {
        "chapter": "48",
        "description_fr": "Autres papiers couchés",
        "description_en": "Other coated paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481031": {
        "chapter": "48",
        "description_fr": "Papier et carton kraft blanchis couchés",
        "description_en": "Bleached kraft paper and paperboard, coated",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481032": {
        "chapter": "48",
        "description_fr": "Papier et carton kraft blanchis couchés > 150 g/m2",
        "description_en": "Bleached kraft paper and paperboard, coated > 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481039": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons kraft couchés",
        "description_en": "Other coated kraft paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481092": {
        "chapter": "48",
        "description_fr": "Carton multicouches couché au kaolin",
        "description_en": "Multi-ply paperboard coated with kaolin",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481099": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons couchés",
        "description_en": "Other coated paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481110": {
        "chapter": "48",
        "description_fr": "Papiers et cartons goudronnés, bitumés ou asphaltés",
        "description_en": "Tarred, bituminised or asphalted paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481141": {
        "chapter": "48",
        "description_fr": "Papiers et cartons auto-adhésifs",
        "description_en": "Self-adhesive paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481149": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons gommés ou adhésifs",
        "description_en": "Other gummed or adhesive paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481151": {
        "chapter": "48",
        "description_fr": "Papiers et cartons blanchis >= 150 g/m2",
        "description_en": "Bleached paper and paperboard >= 150 g/m2",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481159": {
        "chapter": "48",
        "description_fr": "Autres papiers et cartons enduits ou imprégnés",
        "description_en": "Other coated or impregnated paper and paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481160": {
        "chapter": "48",
        "description_fr": "Papiers et cartons enduits de cire ou stéarine",
        "description_en": "Paper and paperboard coated with wax or stearin",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481190": {
        "chapter": "48",
        "description_fr": "Autres papiers, cartons, ouate de cellulose enduits",
        "description_en": "Other coated paper, paperboard, cellulose wadding",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481200": {
        "chapter": "48",
        "description_fr": "Blocs et plaques filtrants en pâte à papier",
        "description_en": "Filter blocks and plates of paper pulp",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481310": {
        "chapter": "48",
        "description_fr": "Papier à cigarettes en cahiers ou en tubes",
        "description_en": "Cigarette paper in form of booklets or tubes",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481320": {
        "chapter": "48",
        "description_fr": "Papier à cigarettes en rouleaux",
        "description_en": "Cigarette paper in rolls",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481390": {
        "chapter": "48",
        "description_fr": "Autres papiers à cigarettes",
        "description_en": "Other cigarette paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481420": {
        "chapter": "48",
        "description_fr": "Papiers peints et revêtements muraux similaires",
        "description_en": "Wallpaper and similar wall coverings",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481490": {
        "chapter": "48",
        "description_fr": "Autres papiers peints",
        "description_en": "Other wallpaper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481500": {
        "chapter": "48",
        "description_fr": "Couvre-parquets à support de papier ou carton",
        "description_en": "Floor coverings on a base of paper or paperboard",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481610": {
        "chapter": "48",
        "description_fr": "Papier carbone et papiers similaires",
        "description_en": "Carbon paper and similar copying papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481620": {
        "chapter": "48",
        "description_fr": "Papier autocopiant",
        "description_en": "Self-copy paper",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481690": {
        "chapter": "48",
        "description_fr": "Autres papiers pour duplicata ou reports",
        "description_en": "Other duplicator stencils or transfer papers",
        "category": "paper",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481710": {
        "chapter": "48",
        "description_fr": "Enveloppes en papier ou carton",
        "description_en": "Envelopes of paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481720": {
        "chapter": "48",
        "description_fr": "Cartes-lettres, cartes postales et cartes pour correspondance",
        "description_en": "Letter cards, postcards and correspondence cards",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481730": {
        "chapter": "48",
        "description_fr": "Boîtes, pochettes et articles similaires contenant un assortiment d'articles de correspondance",
        "description_en": "Boxes, pouches containing correspondence articles",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481810": {
        "chapter": "48",
        "description_fr": "Papier hygiénique",
        "description_en": "Toilet paper",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481820": {
        "chapter": "48",
        "description_fr": "Mouchoirs, serviettes à démaquiller et essuie-mains",
        "description_en": "Handkerchiefs, cleansing tissues and towels",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481830": {
        "chapter": "48",
        "description_fr": "Nappes et serviettes de table",
        "description_en": "Tablecloths and serviettes",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481850": {
        "chapter": "48",
        "description_fr": "Vêtements et accessoires du vêtement en papier",
        "description_en": "Articles of apparel and clothing accessories of paper",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481890": {
        "chapter": "48",
        "description_fr": "Autres articles en papier des types utilisés à des fins sanitaires",
        "description_en": "Other articles of paper for sanitary purposes",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481910": {
        "chapter": "48",
        "description_fr": "Boîtes en papier ou carton ondulé",
        "description_en": "Cartons, boxes of corrugated paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481920": {
        "chapter": "48",
        "description_fr": "Boîtes pliantes en papier ou carton non ondulé",
        "description_en": "Folding cartons of non-corrugated paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481930": {
        "chapter": "48",
        "description_fr": "Sacs en papier largeur >= 40 cm",
        "description_en": "Sacks and bags of paper width >= 40 cm",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481940": {
        "chapter": "48",
        "description_fr": "Autres sacs, sachets et cornets en papier",
        "description_en": "Other sacks, bags and cones of paper",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481950": {
        "chapter": "48",
        "description_fr": "Autres emballages en papier ou carton",
        "description_en": "Other packing containers of paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "481960": {
        "chapter": "48",
        "description_fr": "Classeurs, chemises et couvertures à dossiers",
        "description_en": "Box files, letter trays and similar articles",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482010": {
        "chapter": "48",
        "description_fr": "Registres, livres comptables, carnets et articles similaires",
        "description_en": "Registers, account books, notebooks and similar articles",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482020": {
        "chapter": "48",
        "description_fr": "Cahiers d'écolier",
        "description_en": "Exercise books",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482030": {
        "chapter": "48",
        "description_fr": "Classeurs, reliures et couvertures",
        "description_en": "Binders, folders and file covers",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482040": {
        "chapter": "48",
        "description_fr": "Liasses et carnets manifold",
        "description_en": "Manifold business forms and interleaved carbon sets",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482050": {
        "chapter": "48",
        "description_fr": "Albums pour échantillons ou collections",
        "description_en": "Albums for samples or for collections",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482090": {
        "chapter": "48",
        "description_fr": "Autres articles de papeterie",
        "description_en": "Other articles of stationery",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482110": {
        "chapter": "48",
        "description_fr": "Étiquettes en papier ou carton imprimées",
        "description_en": "Printed labels of paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482190": {
        "chapter": "48",
        "description_fr": "Autres étiquettes en papier ou carton",
        "description_en": "Other labels of paper or paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482210": {
        "chapter": "48",
        "description_fr": "Tambours, bobines, busettes en pâte à papier",
        "description_en": "Bobbins, spools, cops of paper pulp",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482290": {
        "chapter": "48",
        "description_fr": "Autres tambours, bobines, busettes",
        "description_en": "Other bobbins, spools, cops",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482311": {
        "chapter": "48",
        "description_fr": "Papiers autoadhésifs en rouleaux",
        "description_en": "Self-adhesive paper in rolls",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482319": {
        "chapter": "48",
        "description_fr": "Autres papiers autoadhésifs",
        "description_en": "Other self-adhesive paper",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482320": {
        "chapter": "48",
        "description_fr": "Papier et carton filtres",
        "description_en": "Filter paper and paperboard",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482340": {
        "chapter": "48",
        "description_fr": "Papier à diagrammes pour appareils enregistreurs",
        "description_en": "Rolls, sheets of paper for recording apparatus",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482361": {
        "chapter": "48",
        "description_fr": "Plateaux, plats et assiettes en bambou",
        "description_en": "Trays, dishes and plates of bamboo",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482369": {
        "chapter": "48",
        "description_fr": "Autres plateaux, plats et assiettes en papier",
        "description_en": "Other trays, dishes and plates of paper",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482370": {
        "chapter": "48",
        "description_fr": "Articles moulés en pâte à papier",
        "description_en": "Moulded articles of paper pulp",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "482390": {
        "chapter": "48",
        "description_fr": "Autres ouvrages en papier, carton, ouate de cellulose",
        "description_en": "Other articles of paper, paperboard, cellulose wadding",
        "category": "paper_products",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },

    # CHAPITRE 49 - PRODUITS DE L'ÉDITION, PRESSE
    "490110": {
        "chapter": "49",
        "description_fr": "Livres, brochures et imprimés similaires en feuillets",
        "description_en": "Printed books, brochures and similar printed matter",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490191": {
        "chapter": "49",
        "description_fr": "Dictionnaires et encyclopédies",
        "description_en": "Dictionaries and encyclopaedias",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490199": {
        "chapter": "49",
        "description_fr": "Autres livres, brochures et imprimés similaires",
        "description_en": "Other printed books, brochures and similar",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490210": {
        "chapter": "49",
        "description_fr": "Journaux et publications périodiques paraissant au moins 4 fois/semaine",
        "description_en": "Newspapers and periodicals appearing at least 4 times a week",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490290": {
        "chapter": "49",
        "description_fr": "Autres journaux et publications périodiques",
        "description_en": "Other newspapers and periodicals",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490300": {
        "chapter": "49",
        "description_fr": "Albums ou livres d'images pour enfants",
        "description_en": "Children's picture, drawing or colouring books",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490400": {
        "chapter": "49",
        "description_fr": "Musique manuscrite ou imprimée",
        "description_en": "Music, printed or in manuscript",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490510": {
        "chapter": "49",
        "description_fr": "Globes terrestres ou célestes",
        "description_en": "Globes, printed",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "490591": {
        "chapter": "49",
        "description_fr": "Ouvrages cartographiques sous forme de livres",
        "description_en": "Cartographic works in book form",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490599": {
        "chapter": "49",
        "description_fr": "Autres ouvrages cartographiques",
        "description_en": "Other cartographic works",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490600": {
        "chapter": "49",
        "description_fr": "Plans et dessins d'architectes, d'ingénieurs",
        "description_en": "Plans and drawings for architectural, engineering purposes",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Produit en Afrique", "requirement_en": "Produced in Africa", "regional_content": 40}
    },
    "490700": {
        "chapter": "49",
        "description_fr": "Timbres-poste, timbres fiscaux et similaires",
        "description_en": "Postage, revenue or similar stamps",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "490810": {
        "chapter": "49",
        "description_fr": "Décalcomanies vitrifiables",
        "description_en": "Transfers (decalcomanias), vitrifiable",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "490890": {
        "chapter": "49",
        "description_fr": "Autres décalcomanies",
        "description_en": "Other transfers (decalcomanias)",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "490900": {
        "chapter": "49",
        "description_fr": "Cartes postales imprimées ou illustrées",
        "description_en": "Printed or illustrated postcards",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "491000": {
        "chapter": "49",
        "description_fr": "Calendriers de tous genres imprimés",
        "description_en": "Calendars of any kind, printed",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "491110": {
        "chapter": "49",
        "description_fr": "Imprimés publicitaires, catalogues commerciaux",
        "description_en": "Trade advertising material, commercial catalogues",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
    "491191": {
        "chapter": "49",
        "description_fr": "Images, gravures, photographies",
        "description_en": "Pictures, designs and photographs",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Produit en Afrique", "requirement_en": "Produced in Africa", "regional_content": 40}
    },
    "491199": {
        "chapter": "49",
        "description_fr": "Autres imprimés",
        "description_en": "Other printed matter",
        "category": "printed_matter",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Imprimé en Afrique", "requirement_en": "Printed in Africa", "regional_content": 40}
    },
}
