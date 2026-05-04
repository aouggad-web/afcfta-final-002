"""
EXTENSION BASE HS6 - CHAPITRES 41-63
=====================================
Cuirs, Peaux, Textiles, Vêtements
Industrie textile et confection africaine

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

HS6_EXTENDED_CH41_63 = {
    # =========================================================================
    # CHAPITRE 41 - CUIRS ET PEAUX
    # =========================================================================
    "410120": {
        "chapter": "41",
        "description_fr": "Peaux brutes de bovins entières ≤8kg",
        "description_en": "Whole bovine hides ≤8kg",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "410150": {
        "chapter": "41",
        "description_fr": "Peaux brutes de bovins entières >16kg",
        "description_en": "Whole bovine hides >16kg",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "410190": {
        "chapter": "41",
        "description_fr": "Autres peaux brutes de bovins",
        "description_en": "Other raw bovine hides",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "410210": {
        "chapter": "41",
        "description_fr": "Peaux brutes d'ovins lainées",
        "description_en": "Raw sheepskins with wool",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "410221": {
        "chapter": "41",
        "description_fr": "Peaux d'ovins picklées",
        "description_en": "Pickled sheepskins",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "410229": {
        "chapter": "41",
        "description_fr": "Autres peaux d'ovins épilées",
        "description_en": "Other dehaired sheepskins",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "410320": {
        "chapter": "41",
        "description_fr": "Peaux de reptiles brutes",
        "description_en": "Raw reptile skins",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - CITES", "requirement_en": "Wholly obtained - CITES", "regional_content": 100}
    },
    "410390": {
        "chapter": "41",
        "description_fr": "Autres peaux brutes",
        "description_en": "Other raw hides",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "410411": {
        "chapter": "41",
        "description_fr": "Cuirs de bovins pleine fleur",
        "description_en": "Full grain bovine leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410419": {
        "chapter": "41",
        "description_fr": "Autres cuirs de bovins",
        "description_en": "Other bovine leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410510": {
        "chapter": "41",
        "description_fr": "Peaux tannées d'ovins sans laine",
        "description_en": "Tanned sheepskins without wool",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410621": {
        "chapter": "41",
        "description_fr": "Cuirs de caprins à l'état humide",
        "description_en": "Wet goat leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410711": {
        "chapter": "41",
        "description_fr": "Cuirs préparés de porcs pleine fleur",
        "description_en": "Full grain pig leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410791": {
        "chapter": "41",
        "description_fr": "Cuirs d'autres animaux pleine fleur",
        "description_en": "Other animal leather full grain",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "410799": {
        "chapter": "41",
        "description_fr": "Autres cuirs préparés",
        "description_en": "Other prepared leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tannage en Afrique - 40% VA", "requirement_en": "Tanned in Africa - 40% VA", "regional_content": 40}
    },
    "411200": {
        "chapter": "41",
        "description_fr": "Cuirs de bovins préparés (chamoisés)",
        "description_en": "Prepared bovine leather (chamois)",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "411310": {
        "chapter": "41",
        "description_fr": "Cuirs de caprins préparés",
        "description_en": "Prepared goat leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "411410": {
        "chapter": "41",
        "description_fr": "Cuirs et peaux chamoisés",
        "description_en": "Chamois leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "411420": {
        "chapter": "41",
        "description_fr": "Cuirs et peaux vernis",
        "description_en": "Patent leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Finition en Afrique - 40% VA", "requirement_en": "Finished in Africa - 40% VA", "regional_content": 40}
    },
    "411510": {
        "chapter": "41",
        "description_fr": "Cuirs reconstitués",
        "description_en": "Composition leather",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "411520": {
        "chapter": "41",
        "description_fr": "Rognures de cuir",
        "description_en": "Leather parings",
        "category": "leather",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 50-55 - TEXTILES (Sélection)
    # =========================================================================
    "500100": {
        "chapter": "50",
        "description_fr": "Cocons de vers à soie",
        "description_en": "Silkworm cocoons",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "500200": {
        "chapter": "50",
        "description_fr": "Soie grège",
        "description_en": "Raw silk",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "510111": {
        "chapter": "51",
        "description_fr": "Laine en suint de tonte",
        "description_en": "Greasy shorn wool",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "510121": {
        "chapter": "51",
        "description_fr": "Laine dégraissée, non carbonisée",
        "description_en": "Degreased wool, not carbonized",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "510130": {
        "chapter": "51",
        "description_fr": "Laine carbonisée",
        "description_en": "Carbonized wool",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "520100": {
        "chapter": "52",
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "category": "cotton",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - cultivé en Afrique", "requirement_en": "Wholly obtained - grown in Africa", "regional_content": 100}
    },
    "520210": {
        "chapter": "52",
        "description_fr": "Déchets de coton non effilochés",
        "description_en": "Cotton waste not garnetted",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "520291": {
        "chapter": "52",
        "description_fr": "Déchets de coton effilochés",
        "description_en": "Garnetted cotton waste",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "520300": {
        "chapter": "52",
        "description_fr": "Coton cardé ou peigné",
        "description_en": "Cotton carded or combed",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Cardage/Peignage en Afrique", "requirement_en": "Carded/Combed in Africa", "regional_content": 40}
    },
    "520411": {
        "chapter": "52",
        "description_fr": "Fil de coton ≥85% coton, simple, non conditionné",
        "description_en": "Cotton sewing thread ≥85% cotton, single, not retail",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Filé en Afrique - 40% VA", "requirement_en": "Spun in Africa - 40% VA", "regional_content": 40}
    },
    "520512": {
        "chapter": "52",
        "description_fr": "Fils de coton simples peignés ≥14000 decitex",
        "description_en": "Single combed cotton yarn ≥14000 decitex",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Filé en Afrique - 40% VA", "requirement_en": "Spun in Africa - 40% VA", "regional_content": 40}
    },
    "520611": {
        "chapter": "52",
        "description_fr": "Fils de coton simples non peignés ≥714 decitex",
        "description_en": "Single uncombed cotton yarn ≥714 decitex",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Filé en Afrique - 40% VA", "requirement_en": "Spun in Africa - 40% VA", "regional_content": 40}
    },
    "520811": {
        "chapter": "52",
        "description_fr": "Tissus de coton écrus <85% coton",
        "description_en": "Unbleached cotton fabrics <85% cotton",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tissé en Afrique - 40% VA", "requirement_en": "Woven in Africa - 40% VA", "regional_content": 40}
    },
    "520912": {
        "chapter": "52",
        "description_fr": "Tissus de coton écrus ≥85% coton >100g/m2",
        "description_en": "Unbleached cotton fabrics ≥85% cotton >100g/m2",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tissé en Afrique - 40% VA", "requirement_en": "Woven in Africa - 40% VA", "regional_content": 40}
    },
    "521011": {
        "chapter": "52",
        "description_fr": "Tissus de coton blanchis <85% coton ≤200g/m2",
        "description_en": "Bleached cotton fabrics <85% cotton ≤200g/m2",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "521111": {
        "chapter": "52",
        "description_fr": "Tissus de coton ≥85% coton imprimés ≤200g/m2",
        "description_en": "Printed cotton fabrics ≥85% cotton ≤200g/m2",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Impression en Afrique - 40% VA", "requirement_en": "Printed in Africa - 40% VA", "regional_content": 40}
    },
    "521215": {
        "chapter": "52",
        "description_fr": "Autres tissus de coton imprimés ≥85% >200g/m2",
        "description_en": "Other printed cotton fabrics ≥85% >200g/m2",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Impression en Afrique - 40% VA", "requirement_en": "Printed in Africa - 40% VA", "regional_content": 40}
    },
    "530110": {
        "chapter": "53",
        "description_fr": "Lin brut ou roui",
        "description_en": "Raw or retted flax",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "530310": {
        "chapter": "53",
        "description_fr": "Jute et fibres libériennes brutes",
        "description_en": "Raw jute and bast fibres",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "530500": {
        "chapter": "53",
        "description_fr": "Coco, abaca, ramie",
        "description_en": "Coir, abaca, ramie",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "540110": {
        "chapter": "54",
        "description_fr": "Fils à coudre de filaments synthétiques",
        "description_en": "Synthetic filament sewing thread",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "540233": {
        "chapter": "54",
        "description_fr": "Fils texturés de polyester",
        "description_en": "Textured polyester yarns",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "540710": {
        "chapter": "54",
        "description_fr": "Tissus de filaments de nylon",
        "description_en": "Nylon filament fabrics",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tissé en Afrique - 40% VA", "requirement_en": "Woven in Africa - 40% VA", "regional_content": 40}
    },
    "550110": {
        "chapter": "55",
        "description_fr": "Câbles de filaments de nylon",
        "description_en": "Nylon filament tow",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "550320": {
        "chapter": "55",
        "description_fr": "Fibres discontinues de polyester",
        "description_en": "Polyester staple fibres",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "550690": {
        "chapter": "55",
        "description_fr": "Autres fibres synthétiques discontinues",
        "description_en": "Other synthetic staple fibres",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 60-63 - VÊTEMENTS ET ARTICLES TEXTILES
    # =========================================================================
    "600110": {
        "chapter": "60",
        "description_fr": "Étoffes de bonneterie à longs poils",
        "description_en": "Long pile knitted fabrics",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "600190": {
        "chapter": "60",
        "description_fr": "Autres étoffes de bonneterie",
        "description_en": "Other knitted fabrics",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "610110": {
        "chapter": "61",
        "description_fr": "Manteaux en bonneterie pour hommes",
        "description_en": "Men's knitted overcoats",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610120": {
        "chapter": "61",
        "description_fr": "Manteaux en bonneterie pour femmes",
        "description_en": "Women's knitted overcoats",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610210": {
        "chapter": "61",
        "description_fr": "Manteaux en bonneterie pour femmes de laine",
        "description_en": "Women's wool knitted overcoats",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610310": {
        "chapter": "61",
        "description_fr": "Costumes et vestons en bonneterie pour hommes",
        "description_en": "Men's knitted suits and jackets",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610410": {
        "chapter": "61",
        "description_fr": "Costumes tailleurs en bonneterie pour femmes",
        "description_en": "Women's knitted suits",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610510": {
        "chapter": "61",
        "description_fr": "Chemises en bonneterie pour hommes",
        "description_en": "Men's knitted shirts",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610610": {
        "chapter": "61",
        "description_fr": "Chemisiers en bonneterie pour femmes",
        "description_en": "Women's knitted blouses",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610711": {
        "chapter": "61",
        "description_fr": "Slips en bonneterie pour hommes",
        "description_en": "Men's knitted underpants",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610821": {
        "chapter": "61",
        "description_fr": "Slips en bonneterie pour femmes",
        "description_en": "Women's knitted briefs",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "610910": {
        "chapter": "61",
        "description_fr": "T-shirts en bonneterie",
        "description_en": "Knitted T-shirts",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "611010": {
        "chapter": "61",
        "description_fr": "Chandails, pull-overs en bonneterie de laine",
        "description_en": "Wool knitted sweaters, pullovers",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "611020": {
        "chapter": "61",
        "description_fr": "Chandails en bonneterie de coton",
        "description_en": "Cotton knitted sweaters",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "611110": {
        "chapter": "61",
        "description_fr": "Vêtements pour bébés en bonneterie",
        "description_en": "Knitted babies' garments",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "611211": {
        "chapter": "61",
        "description_fr": "Survêtements de sport en bonneterie de coton",
        "description_en": "Cotton knitted track suits",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620111": {
        "chapter": "62",
        "description_fr": "Manteaux pour hommes en laine",
        "description_en": "Men's wool overcoats",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620211": {
        "chapter": "62",
        "description_fr": "Manteaux pour femmes en laine",
        "description_en": "Women's wool overcoats",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620311": {
        "chapter": "62",
        "description_fr": "Costumes pour hommes en laine",
        "description_en": "Men's wool suits",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620411": {
        "chapter": "62",
        "description_fr": "Costumes tailleurs pour femmes en laine",
        "description_en": "Women's wool suits",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620520": {
        "chapter": "62",
        "description_fr": "Chemises pour hommes de coton",
        "description_en": "Men's cotton shirts",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "620630": {
        "chapter": "62",
        "description_fr": "Chemisiers pour femmes de coton",
        "description_en": "Women's cotton blouses",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "621010": {
        "chapter": "62",
        "description_fr": "Vêtements de feutre",
        "description_en": "Felt garments",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "621111": {
        "chapter": "62",
        "description_fr": "Maillots de bain pour hommes",
        "description_en": "Men's swimwear",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "621112": {
        "chapter": "62",
        "description_fr": "Maillots de bain pour femmes",
        "description_en": "Women's swimwear",
        "category": "clothing",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Confection en Afrique - 40% VA", "requirement_en": "Made in Africa - 40% VA", "regional_content": 40}
    },
    "630110": {
        "chapter": "63",
        "description_fr": "Couvertures électriques",
        "description_en": "Electric blankets",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630140": {
        "chapter": "63",
        "description_fr": "Couvertures de fibres synthétiques",
        "description_en": "Synthetic fibre blankets",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630210": {
        "chapter": "63",
        "description_fr": "Linge de lit en bonneterie",
        "description_en": "Knitted bed linen",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630221": {
        "chapter": "63",
        "description_fr": "Linge de lit imprimé de coton",
        "description_en": "Printed cotton bed linen",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630260": {
        "chapter": "63",
        "description_fr": "Linge de toilette de coton",
        "description_en": "Cotton toilet linen",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630291": {
        "chapter": "63",
        "description_fr": "Linge de toilette de coton autre",
        "description_en": "Other cotton toilet linen",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630311": {
        "chapter": "63",
        "description_fr": "Rideaux et stores de coton",
        "description_en": "Cotton curtains and blinds",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630411": {
        "chapter": "63",
        "description_fr": "Couvre-lits de bonneterie",
        "description_en": "Knitted bedspreads",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630510": {
        "chapter": "63",
        "description_fr": "Sacs d'emballage en jute",
        "description_en": "Jute packing sacks",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630520": {
        "chapter": "63",
        "description_fr": "Sacs d'emballage en coton",
        "description_en": "Cotton packing sacks",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630532": {
        "chapter": "63",
        "description_fr": "Conteneurs souples en synthétique",
        "description_en": "Synthetic flexible containers",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630612": {
        "chapter": "63",
        "description_fr": "Bâches de fibres synthétiques",
        "description_en": "Synthetic fibre tarpaulins",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630710": {
        "chapter": "63",
        "description_fr": "Serpillières, lavettes",
        "description_en": "Floor cloths, dish cloths",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "630900": {
        "chapter": "63",
        "description_fr": "Vêtements usagés",
        "description_en": "Worn clothing",
        "category": "clothing",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Réglementation spéciale", "requirement_en": "Special regulation", "regional_content": 100}
    },
    "631010": {
        "chapter": "63",
        "description_fr": "Chiffons et déchets textiles triés",
        "description_en": "Sorted textile rags and waste",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "631090": {
        "chapter": "63",
        "description_fr": "Autres chiffons et déchets textiles",
        "description_en": "Other textile rags and waste",
        "category": "textiles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
}
