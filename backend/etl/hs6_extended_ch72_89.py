"""
EXTENSION BASE HS6 - CHAPITRES 72-89
=====================================
Métaux, Machines, Équipements électriques, Véhicules
Biens d'équipement et industriels du commerce africain

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

HS6_EXTENDED_CH72_89 = {
    # =========================================================================
    # CHAPITRE 72 - FER ET ACIER (Sélection)
    # =========================================================================
    "720110": {
        "chapter": "72",
        "description_fr": "Fontes brutes non alliées",
        "description_en": "Non-alloy pig iron",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fondu en Afrique - 40% VA", "requirement_en": "Smelted in Africa - 40% VA", "regional_content": 40}
    },
    "720211": {
        "chapter": "72",
        "description_fr": "Ferro-manganèse >2% carbone",
        "description_en": "Ferro-manganese >2% carbon",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "720221": {
        "chapter": "72",
        "description_fr": "Ferro-silicium >55%",
        "description_en": "Ferro-silicon >55%",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "720310": {
        "chapter": "72",
        "description_fr": "Produits ferreux obtenus par réduction directe",
        "description_en": "Direct reduction iron products",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "720410": {
        "chapter": "72",
        "description_fr": "Déchets de fonte",
        "description_en": "Cast iron waste",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "720421": {
        "chapter": "72",
        "description_fr": "Déchets d'acier inoxydable",
        "description_en": "Stainless steel waste",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "720610": {
        "chapter": "72",
        "description_fr": "Lingots de fer ou acier",
        "description_en": "Iron or steel ingots",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Coulé en Afrique - 40% VA", "requirement_en": "Cast in Africa - 40% VA", "regional_content": 40}
    },
    "720711": {
        "chapter": "72",
        "description_fr": "Demi-produits en fer <0,25% carbone",
        "description_en": "Iron semi-finished products <0.25% carbon",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "720810": {
        "chapter": "72",
        "description_fr": "Produits laminés plats en fer >600mm",
        "description_en": "Flat-rolled iron products >600mm",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "720825": {
        "chapter": "72",
        "description_fr": "Produits laminés plats en fer >600mm laminés à chaud",
        "description_en": "Flat-rolled iron products >600mm hot-rolled",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "720915": {
        "chapter": "72",
        "description_fr": "Produits laminés plats en fer laminés à froid >600mm épaisseur ≥3mm",
        "description_en": "Cold-rolled flat products >600mm thickness ≥3mm",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721011": {
        "chapter": "72",
        "description_fr": "Produits plats étamés ≥600mm",
        "description_en": "Tinplate flat products ≥600mm",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Revêtement en Afrique - 40% VA", "requirement_en": "Coated in Africa - 40% VA", "regional_content": 40}
    },
    "721041": {
        "chapter": "72",
        "description_fr": "Produits plats galvanisés ondulés",
        "description_en": "Corrugated galvanized flat products",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Galvanisation en Afrique - 40% VA", "requirement_en": "Galvanized in Africa - 40% VA", "regional_content": 40}
    },
    "721049": {
        "chapter": "72",
        "description_fr": "Autres produits plats galvanisés",
        "description_en": "Other galvanized flat products",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Galvanisation en Afrique - 40% VA", "requirement_en": "Galvanized in Africa - 40% VA", "regional_content": 40}
    },
    "721070": {
        "chapter": "72",
        "description_fr": "Produits plats peints ou plastifiés",
        "description_en": "Painted or plastic-coated flat products",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Revêtement en Afrique - 40% VA", "requirement_en": "Coated in Africa - 40% VA", "regional_content": 40}
    },
    "721310": {
        "chapter": "72",
        "description_fr": "Fil machine en fer avec crénelures",
        "description_en": "Ribbed iron wire rod",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721391": {
        "chapter": "72",
        "description_fr": "Fil machine en fer <6mm",
        "description_en": "Iron wire rod <6mm",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721410": {
        "chapter": "72",
        "description_fr": "Barres en fer forgées",
        "description_en": "Forged iron bars",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Forgé en Afrique - 40% VA", "requirement_en": "Forged in Africa - 40% VA", "regional_content": 40}
    },
    "721420": {
        "chapter": "72",
        "description_fr": "Barres en fer avec crénelures",
        "description_en": "Ribbed iron bars",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721510": {
        "chapter": "72",
        "description_fr": "Barres laminées à froid",
        "description_en": "Cold-formed bars",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "721610": {
        "chapter": "72",
        "description_fr": "Profilés en U en fer",
        "description_en": "U-section iron profiles",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721631": {
        "chapter": "72",
        "description_fr": "Profilés en U à ailes parallèles ≥80mm",
        "description_en": "Parallel-flange U-profiles ≥80mm",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "721710": {
        "chapter": "72",
        "description_fr": "Fil de fer non revêtu",
        "description_en": "Uncoated iron wire",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Tréfilé en Afrique - 40% VA", "requirement_en": "Drawn in Africa - 40% VA", "regional_content": 40}
    },
    "721720": {
        "chapter": "72",
        "description_fr": "Fil de fer zingué",
        "description_en": "Zinc-coated iron wire",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Revêtement en Afrique - 40% VA", "requirement_en": "Coated in Africa - 40% VA", "regional_content": 40}
    },
    "721790": {
        "chapter": "72",
        "description_fr": "Autres fils de fer revêtus",
        "description_en": "Other coated iron wire",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Revêtement en Afrique - 40% VA", "requirement_en": "Coated in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 73 - OUVRAGES EN FONTE/FER/ACIER (Sélection)
    # =========================================================================
    "730110": {
        "chapter": "73",
        "description_fr": "Palplanches en fer ou acier",
        "description_en": "Iron or steel sheet piling",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730210": {
        "chapter": "73",
        "description_fr": "Rails de chemin de fer",
        "description_en": "Railway rails",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Laminé en Afrique - 40% VA", "requirement_en": "Rolled in Africa - 40% VA", "regional_content": 40}
    },
    "730410": {
        "chapter": "73",
        "description_fr": "Tubes et tuyaux sans soudure en fer",
        "description_en": "Seamless iron pipes and tubes",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730511": {
        "chapter": "73",
        "description_fr": "Tubes soudés longitudinalement pour oléoducs",
        "description_en": "Longitudinally welded tubes for oil pipelines",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730610": {
        "chapter": "73",
        "description_fr": "Tubes de cuvelage pour puits de pétrole",
        "description_en": "Oil well casing tubes",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730711": {
        "chapter": "73",
        "description_fr": "Raccords de tuyauterie moulés en fonte",
        "description_en": "Cast iron pipe fittings",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730810": {
        "chapter": "73",
        "description_fr": "Ponts et éléments de ponts en fer",
        "description_en": "Iron bridges and bridge sections",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730890": {
        "chapter": "73",
        "description_fr": "Autres constructions en fer",
        "description_en": "Other iron constructions",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "730900": {
        "chapter": "73",
        "description_fr": "Réservoirs en fer >300L",
        "description_en": "Iron reservoirs >300L",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731010": {
        "chapter": "73",
        "description_fr": "Réservoirs en fer 50-300L",
        "description_en": "Iron reservoirs 50-300L",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731021": {
        "chapter": "73",
        "description_fr": "Boîtes de conserve en fer <50L",
        "description_en": "Iron cans <50L",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731100": {
        "chapter": "73",
        "description_fr": "Récipients pour gaz comprimés",
        "description_en": "Compressed gas containers",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731210": {
        "chapter": "73",
        "description_fr": "Câbles en fer non isolés",
        "description_en": "Non-insulated iron cables",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731290": {
        "chapter": "73",
        "description_fr": "Autres câbles en fer",
        "description_en": "Other iron cables",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731300": {
        "chapter": "73",
        "description_fr": "Ronces artificielles en fer",
        "description_en": "Barbed iron wire",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731411": {
        "chapter": "73",
        "description_fr": "Toiles métalliques en fer",
        "description_en": "Iron woven wire cloth",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731512": {
        "chapter": "73",
        "description_fr": "Chaînes à maillons à rouleaux",
        "description_en": "Roller chains",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731581": {
        "chapter": "73",
        "description_fr": "Chaînes à maillons soudés",
        "description_en": "Welded link chains",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731600": {
        "chapter": "73",
        "description_fr": "Ancres et grappins en fer",
        "description_en": "Iron anchors and grapnels",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731700": {
        "chapter": "73",
        "description_fr": "Pointes et clous en fer",
        "description_en": "Iron nails and tacks",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731811": {
        "chapter": "73",
        "description_fr": "Tire-fonds en fer",
        "description_en": "Iron coach screws",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731815": {
        "chapter": "73",
        "description_fr": "Vis à bois en fer",
        "description_en": "Iron wood screws",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "731816": {
        "chapter": "73",
        "description_fr": "Écrous en fer",
        "description_en": "Iron nuts",
        "category": "steel",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 84 - MACHINES ET APPAREILS (Sélection importante)
    # =========================================================================
    "840110": {
        "chapter": "84",
        "description_fr": "Réacteurs nucléaires",
        "description_en": "Nuclear reactors",
        "category": "machinery",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Réglementation spéciale", "requirement_en": "Special regulation", "regional_content": 40}
    },
    "840211": {
        "chapter": "84",
        "description_fr": "Chaudières à vapeur d'eau >45t/h",
        "description_en": "Steam boilers >45t/h",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "840310": {
        "chapter": "84",
        "description_fr": "Chaudières pour chauffage central",
        "description_en": "Central heating boilers",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "840710": {
        "chapter": "84",
        "description_fr": "Moteurs d'avions",
        "description_en": "Aircraft engines",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "840810": {
        "chapter": "84",
        "description_fr": "Moteurs diesel marins ≤1000kW",
        "description_en": "Marine diesel engines ≤1000kW",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "840820": {
        "chapter": "84",
        "description_fr": "Moteurs diesel pour véhicules routiers",
        "description_en": "Road vehicle diesel engines",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "841112": {
        "chapter": "84",
        "description_fr": "Turboréacteurs de poussée >25kN",
        "description_en": "Turbojets thrust >25kN",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "841191": {
        "chapter": "84",
        "description_fr": "Parties de turboréacteurs ou turbopropulseurs",
        "description_en": "Parts of turbojets or turboprops",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "841210": {
        "chapter": "84",
        "description_fr": "Propulseurs à réaction autres que turboréacteurs",
        "description_en": "Reaction engines other than turbojets",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "841381": {
        "chapter": "84",
        "description_fr": "Pompes pour liquides",
        "description_en": "Liquid pumps",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "841410": {
        "chapter": "84",
        "description_fr": "Pompes à vide",
        "description_en": "Vacuum pumps",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "841510": {
        "chapter": "84",
        "description_fr": "Machines pour climatisation",
        "description_en": "Air conditioning machines",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "841810": {
        "chapter": "84",
        "description_fr": "Réfrigérateurs-congélateurs combinés",
        "description_en": "Combined refrigerator-freezers",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "841821": {
        "chapter": "84",
        "description_fr": "Réfrigérateurs ménagers à compression",
        "description_en": "Household compression refrigerators",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "842010": {
        "chapter": "84",
        "description_fr": "Calandres et laminoirs",
        "description_en": "Calendering and rolling machines",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "843110": {
        "chapter": "84",
        "description_fr": "Parties de machines de levage",
        "description_en": "Parts of lifting machinery",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "843210": {
        "chapter": "84",
        "description_fr": "Charrues",
        "description_en": "Ploughs",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "843221": {
        "chapter": "84",
        "description_fr": "Herses à disques",
        "description_en": "Disc harrows",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "843320": {
        "chapter": "84",
        "description_fr": "Faucheuses pour tracteurs",
        "description_en": "Tractor mowers",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "843351": {
        "chapter": "84",
        "description_fr": "Moissonneuses-batteuses",
        "description_en": "Combine harvester-threshers",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847010": {
        "chapter": "84",
        "description_fr": "Calculatrices électroniques",
        "description_en": "Electronic calculators",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847110": {
        "chapter": "84",
        "description_fr": "Machines automatiques de traitement de données analogiques ou hybrides",
        "description_en": "Analogue or hybrid automatic data processing machines",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847130": {
        "chapter": "84",
        "description_fr": "Machines portables ≤10kg",
        "description_en": "Portable machines ≤10kg",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847141": {
        "chapter": "84",
        "description_fr": "Machines comprenant au moins une unité centrale et une périphérique",
        "description_en": "Machines with CPU and peripheral unit",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847150": {
        "chapter": "84",
        "description_fr": "Unités de traitement numériques",
        "description_en": "Digital processing units",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847160": {
        "chapter": "84",
        "description_fr": "Unités d'entrée ou de sortie",
        "description_en": "Input or output units",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "847170": {
        "chapter": "84",
        "description_fr": "Unités de mémoire",
        "description_en": "Storage units",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 85 - MACHINES ÉLECTRIQUES (Sélection importante)
    # =========================================================================
    "850110": {
        "chapter": "85",
        "description_fr": "Moteurs électriques ≤37,5W",
        "description_en": "Electric motors ≤37.5W",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "850131": {
        "chapter": "85",
        "description_fr": "Moteurs à courant continu ≤750W",
        "description_en": "DC motors ≤750W",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "850211": {
        "chapter": "85",
        "description_fr": "Groupes électrogènes diesel ≤75kVA",
        "description_en": "Diesel generating sets ≤75kVA",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "850220": {
        "chapter": "85",
        "description_fr": "Groupes électrogènes à essence",
        "description_en": "Petrol generating sets",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "850300": {
        "chapter": "85",
        "description_fr": "Parties de machines électriques rotatives",
        "description_en": "Parts of rotating electric machines",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "850410": {
        "chapter": "85",
        "description_fr": "Ballasts pour lampes à décharge",
        "description_en": "Ballasts for discharge lamps",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "850610": {
        "chapter": "85",
        "description_fr": "Piles au dioxyde de manganèse",
        "description_en": "Manganese dioxide batteries",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "850650": {
        "chapter": "85",
        "description_fr": "Piles au lithium",
        "description_en": "Lithium batteries",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "850710": {
        "chapter": "85",
        "description_fr": "Accumulateurs au plomb",
        "description_en": "Lead-acid accumulators",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "850760": {
        "chapter": "85",
        "description_fr": "Accumulateurs au lithium-ion",
        "description_en": "Lithium-ion accumulators",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "851710": {
        "chapter": "85",
        "description_fr": "Téléphones portables",
        "description_en": "Mobile phones",
        "category": "electronics",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "851762": {
        "chapter": "85",
        "description_fr": "Appareils pour la réception de la voix, d'images ou d'autres données",
        "description_en": "Machines for voice, image or data reception",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "852110": {
        "chapter": "85",
        "description_fr": "Appareils d'enregistrement vidéo",
        "description_en": "Video recording apparatus",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "852540": {
        "chapter": "85",
        "description_fr": "Caméras numériques",
        "description_en": "Digital cameras",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "852872": {
        "chapter": "85",
        "description_fr": "Récepteurs de télévision couleur",
        "description_en": "Color TV receivers",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "853110": {
        "chapter": "85",
        "description_fr": "Appareils avertisseurs d'incendie",
        "description_en": "Fire alarms",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "854110": {
        "chapter": "85",
        "description_fr": "Diodes autres que photodiodes",
        "description_en": "Diodes other than photodiodes",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "854140": {
        "chapter": "85",
        "description_fr": "Dispositifs photosensibles à semi-conducteur",
        "description_en": "Photosensitive semiconductor devices",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "854190": {
        "chapter": "85",
        "description_fr": "Parties de dispositifs à semi-conducteur",
        "description_en": "Parts of semiconductor devices",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 87 - VÉHICULES (Sélection importante)
    # =========================================================================
    "870110": {
        "chapter": "87",
        "description_fr": "Tracteurs agricoles à roues",
        "description_en": "Agricultural wheeled tractors",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870120": {
        "chapter": "87",
        "description_fr": "Tracteurs routiers pour semi-remorques",
        "description_en": "Road tractors for semi-trailers",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870130": {
        "chapter": "87",
        "description_fr": "Tracteurs à chenilles",
        "description_en": "Track-laying tractors",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870190": {
        "chapter": "87",
        "description_fr": "Autres tracteurs",
        "description_en": "Other tractors",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870210": {
        "chapter": "87",
        "description_fr": "Véhicules de transport en commun diesel >10 places",
        "description_en": "Diesel public transport vehicles >10 seats",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870290": {
        "chapter": "87",
        "description_fr": "Autres véhicules de transport en commun",
        "description_en": "Other public transport vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870310": {
        "chapter": "87",
        "description_fr": "Véhicules pour transport neige",
        "description_en": "Snow transport vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870321": {
        "chapter": "87",
        "description_fr": "Voitures essence ≤1000cm3",
        "description_en": "Petrol cars ≤1000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870322": {
        "chapter": "87",
        "description_fr": "Voitures essence 1000-1500cm3",
        "description_en": "Petrol cars 1000-1500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870323": {
        "chapter": "87",
        "description_fr": "Voitures essence 1500-3000cm3",
        "description_en": "Petrol cars 1500-3000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870324": {
        "chapter": "87",
        "description_fr": "Voitures essence >3000cm3",
        "description_en": "Petrol cars >3000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870331": {
        "chapter": "87",
        "description_fr": "Voitures diesel ≤1500cm3",
        "description_en": "Diesel cars ≤1500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870332": {
        "chapter": "87",
        "description_fr": "Voitures diesel 1500-2500cm3",
        "description_en": "Diesel cars 1500-2500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870333": {
        "chapter": "87",
        "description_fr": "Voitures diesel >2500cm3",
        "description_en": "Diesel cars >2500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870340": {
        "chapter": "87",
        "description_fr": "Véhicules hybrides rechargeables",
        "description_en": "Plug-in hybrid vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870350": {
        "chapter": "87",
        "description_fr": "Véhicules électriques purs",
        "description_en": "Pure electric vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870421": {
        "chapter": "87",
        "description_fr": "Camions diesel PTAC ≤5t",
        "description_en": "Diesel trucks GVW ≤5t",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870422": {
        "chapter": "87",
        "description_fr": "Camions diesel PTAC 5-20t",
        "description_en": "Diesel trucks GVW 5-20t",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870423": {
        "chapter": "87",
        "description_fr": "Camions diesel PTAC >20t",
        "description_en": "Diesel trucks GVW >20t",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870431": {
        "chapter": "87",
        "description_fr": "Camions essence PTAC ≤5t",
        "description_en": "Petrol trucks GVW ≤5t",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870510": {
        "chapter": "87",
        "description_fr": "Camions-grues",
        "description_en": "Crane lorries",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870540": {
        "chapter": "87",
        "description_fr": "Camions-bétonnières",
        "description_en": "Concrete-mixer lorries",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870590": {
        "chapter": "87",
        "description_fr": "Autres véhicules à usages spéciaux",
        "description_en": "Other special purpose vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "870600": {
        "chapter": "87",
        "description_fr": "Châssis de véhicules automobiles",
        "description_en": "Motor vehicle chassis",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "870710": {
        "chapter": "87",
        "description_fr": "Carrosseries de voitures",
        "description_en": "Car bodies",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "870810": {
        "chapter": "87",
        "description_fr": "Pare-chocs et leurs parties",
        "description_en": "Bumpers and parts",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "870821": {
        "chapter": "87",
        "description_fr": "Ceintures de sécurité",
        "description_en": "Safety seat belts",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "870891": {
        "chapter": "87",
        "description_fr": "Radiateurs",
        "description_en": "Radiators",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "870899": {
        "chapter": "87",
        "description_fr": "Autres parties de véhicules",
        "description_en": "Other vehicle parts",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "871110": {
        "chapter": "87",
        "description_fr": "Motocycles ≤50cm3",
        "description_en": "Motorcycles ≤50cc",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "871120": {
        "chapter": "87",
        "description_fr": "Motocycles 50-250cm3",
        "description_en": "Motorcycles 50-250cc",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "871200": {
        "chapter": "87",
        "description_fr": "Bicyclettes",
        "description_en": "Bicycles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "871310": {
        "chapter": "87",
        "description_fr": "Fauteuils roulants non mécaniques",
        "description_en": "Non-motorized wheelchairs",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "871411": {
        "chapter": "87",
        "description_fr": "Selles de motocycles",
        "description_en": "Motorcycle saddles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "871620": {
        "chapter": "87",
        "description_fr": "Remorques à usage agricole",
        "description_en": "Agricultural trailers",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "871639": {
        "chapter": "87",
        "description_fr": "Autres remorques pour transport de marchandises",
        "description_en": "Other goods transport trailers",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 88 & 89 - AÉRONEFS ET NAVIRES (Sélection)
    # =========================================================================
    "880110": {
        "chapter": "88",
        "description_fr": "Planeurs et deltaplanes",
        "description_en": "Gliders and hang gliders",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "880211": {
        "chapter": "88",
        "description_fr": "Hélicoptères à vide ≤2000kg",
        "description_en": "Helicopters unladen ≤2000kg",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "880220": {
        "chapter": "88",
        "description_fr": "Avions à vide ≤2000kg",
        "description_en": "Aeroplanes unladen ≤2000kg",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "880230": {
        "chapter": "88",
        "description_fr": "Avions 2000-15000kg à vide",
        "description_en": "Aeroplanes 2000-15000kg unladen",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "880240": {
        "chapter": "88",
        "description_fr": "Avions >15000kg à vide",
        "description_en": "Aeroplanes >15000kg unladen",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Assemblage en Afrique - 40% VA", "requirement_en": "Assembled in Africa - 40% VA", "regional_content": 40}
    },
    "880260": {
        "chapter": "88",
        "description_fr": "Engins spatiaux",
        "description_en": "Spacecraft",
        "category": "aircraft",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Réglementation spéciale", "requirement_en": "Special regulation", "regional_content": 40}
    },
    "880310": {
        "chapter": "88",
        "description_fr": "Hélices et rotors",
        "description_en": "Propellers and rotors",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "880320": {
        "chapter": "88",
        "description_fr": "Trains d'atterrissage",
        "description_en": "Undercarriages",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "880330": {
        "chapter": "88",
        "description_fr": "Autres parties d'avions et d'hélicoptères",
        "description_en": "Other parts of aeroplanes and helicopters",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "880400": {
        "chapter": "88",
        "description_fr": "Parachutes",
        "description_en": "Parachutes",
        "category": "aircraft",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "890110": {
        "chapter": "89",
        "description_fr": "Paquebots, navires de croisière",
        "description_en": "Cruise ships, passenger vessels",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890120": {
        "chapter": "89",
        "description_fr": "Navires-citernes",
        "description_en": "Tankers",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890130": {
        "chapter": "89",
        "description_fr": "Navires frigorifiques",
        "description_en": "Refrigerated vessels",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890190": {
        "chapter": "89",
        "description_fr": "Autres bateaux de transport",
        "description_en": "Other transport vessels",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890200": {
        "chapter": "89",
        "description_fr": "Bateaux de pêche",
        "description_en": "Fishing vessels",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890310": {
        "chapter": "89",
        "description_fr": "Canots gonflables",
        "description_en": "Inflatable boats",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "890391": {
        "chapter": "89",
        "description_fr": "Voiliers avec moteur auxiliaire",
        "description_en": "Sailboats with auxiliary motor",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890392": {
        "chapter": "89",
        "description_fr": "Bateaux à moteur autres",
        "description_en": "Other motorboats",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890400": {
        "chapter": "89",
        "description_fr": "Remorqueurs et pousseurs",
        "description_en": "Tugs and pusher craft",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890510": {
        "chapter": "89",
        "description_fr": "Dragues",
        "description_en": "Dredgers",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890520": {
        "chapter": "89",
        "description_fr": "Plates-formes de forage flottantes",
        "description_en": "Floating drilling platforms",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890590": {
        "chapter": "89",
        "description_fr": "Autres navires (bateaux-phares, grues flottantes)",
        "description_en": "Other vessels (light-vessels, floating cranes)",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "new_used"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Construit en Afrique - 40% VA", "requirement_en": "Built in Africa - 40% VA", "regional_content": 40}
    },
    "890800": {
        "chapter": "89",
        "description_fr": "Navires à dépecer",
        "description_en": "Vessels for breaking up",
        "category": "ships",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
}
