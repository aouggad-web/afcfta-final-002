"""
EXTENSION BASE HS6 - CHAPITRES 25-40
=====================================
Minéraux, Produits chimiques, Plastiques, Caoutchouc
Ressources minérales et produits industriels du commerce africain

Sources:
- WCO Harmonized System 2022
- UNCTAD TRAINS Database
- African Union AfCFTA Tariff Schedules
"""

HS6_EXTENDED_CH25_40 = {
    # =========================================================================
    # CHAPITRE 25 - PRODUITS MINÉRAUX (Compléments)
    # =========================================================================
    "250200": {
        "chapter": "25",
        "description_fr": "Pyrites de fer non grillées",
        "description_en": "Unroasted iron pyrites",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250300": {
        "chapter": "25",
        "description_fr": "Soufre",
        "description_en": "Sulfur",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250410": {
        "chapter": "25",
        "description_fr": "Graphite naturel en poudre",
        "description_en": "Natural graphite powder",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250490": {
        "chapter": "25",
        "description_fr": "Graphite naturel autre",
        "description_en": "Other natural graphite",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250510": {
        "chapter": "25",
        "description_fr": "Sables siliceux",
        "description_en": "Silica sands",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250590": {
        "chapter": "25",
        "description_fr": "Autres sables naturels",
        "description_en": "Other natural sands",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250610": {
        "chapter": "25",
        "description_fr": "Quartz",
        "description_en": "Quartz",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250700": {
        "chapter": "25",
        "description_fr": "Kaolin et autres argiles kaoliniques",
        "description_en": "Kaolin and other kaolinic clays",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250810": {
        "chapter": "25",
        "description_fr": "Bentonite",
        "description_en": "Bentonite",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250830": {
        "chapter": "25",
        "description_fr": "Argiles réfractaires",
        "description_en": "Refractory clays",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250840": {
        "chapter": "25",
        "description_fr": "Autres argiles",
        "description_en": "Other clays",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "250900": {
        "chapter": "25",
        "description_fr": "Craie",
        "description_en": "Chalk",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251010": {
        "chapter": "25",
        "description_fr": "Phosphates de calcium naturels non broyés",
        "description_en": "Natural calcium phosphates, unground",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251020": {
        "chapter": "25",
        "description_fr": "Phosphates de calcium naturels broyés",
        "description_en": "Natural calcium phosphates, ground",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Broyage en Afrique", "requirement_en": "Ground in Africa", "regional_content": 40}
    },
    "251110": {
        "chapter": "25",
        "description_fr": "Sulfate de baryum naturel (barytine)",
        "description_en": "Natural barium sulfate (barytes)",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251200": {
        "chapter": "25",
        "description_fr": "Farines siliceuses fossiles",
        "description_en": "Siliceous fossil meals",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251310": {
        "chapter": "25",
        "description_fr": "Pierre ponce",
        "description_en": "Pumice stone",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251320": {
        "chapter": "25",
        "description_fr": "Émeri, corindon naturel",
        "description_en": "Emery, natural corundum",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251511": {
        "chapter": "25",
        "description_fr": "Marbres bruts ou dégrossis",
        "description_en": "Crude or roughly trimmed marble",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251512": {
        "chapter": "25",
        "description_fr": "Marbres simplement débités",
        "description_en": "Simply cut marble",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "251612": {
        "chapter": "25",
        "description_fr": "Granit simplement débité",
        "description_en": "Simply cut granite",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "251710": {
        "chapter": "25",
        "description_fr": "Cailloux, graviers, pierres concassées",
        "description_en": "Pebbles, gravel, crushed stone",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "251810": {
        "chapter": "25",
        "description_fr": "Dolomie non calcinée",
        "description_en": "Dolomite not calcined",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252010": {
        "chapter": "25",
        "description_fr": "Gypse et anhydrite",
        "description_en": "Gypsum and anhydrite",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252020": {
        "chapter": "25",
        "description_fr": "Plâtres",
        "description_en": "Plasters",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252100": {
        "chapter": "25",
        "description_fr": "Castines et pierres à chaux",
        "description_en": "Limestone flux and limestone",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252210": {
        "chapter": "25",
        "description_fr": "Chaux vive",
        "description_en": "Quicklime",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252220": {
        "chapter": "25",
        "description_fr": "Chaux éteinte",
        "description_en": "Slaked lime",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252310": {
        "chapter": "25",
        "description_fr": "Ciments non pulvérisés (clinkers)",
        "description_en": "Cement clinkers",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252321": {
        "chapter": "25",
        "description_fr": "Ciment Portland blanc",
        "description_en": "White Portland cement",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252390": {
        "chapter": "25",
        "description_fr": "Autres ciments hydrauliques",
        "description_en": "Other hydraulic cements",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "252410": {
        "chapter": "25",
        "description_fr": "Amiante crocidolite",
        "description_en": "Crocidolite asbestos",
        "category": "minerals",
        "sensitivity": "excluded",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Réglementation spéciale - Santé", "requirement_en": "Special regulation - Health", "regional_content": 100}
    },
    "252490": {
        "chapter": "25",
        "description_fr": "Autres amiantes",
        "description_en": "Other asbestos",
        "category": "minerals",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Réglementation spéciale - Santé", "requirement_en": "Special regulation - Health", "regional_content": 100}
    },
    "252510": {
        "chapter": "25",
        "description_fr": "Mica brut ou clivé",
        "description_en": "Crude or rifted mica",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252610": {
        "chapter": "25",
        "description_fr": "Stéatite naturelle non broyée",
        "description_en": "Natural steatite, not crushed",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252620": {
        "chapter": "25",
        "description_fr": "Stéatite broyée ou pulvérisée",
        "description_en": "Crushed or powdered steatite",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Broyage en Afrique", "requirement_en": "Crushed in Africa", "regional_content": 40}
    },
    "252910": {
        "chapter": "25",
        "description_fr": "Feldspath",
        "description_en": "Feldspar",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "252921": {
        "chapter": "25",
        "description_fr": "Spath fluor",
        "description_en": "Fluorspar",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "253010": {
        "chapter": "25",
        "description_fr": "Vermiculite, perlite et chlorites",
        "description_en": "Vermiculite, perlite and chlorites",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 26 - MINERAIS (Compléments)
    # =========================================================================
    "260112": {
        "chapter": "26",
        "description_fr": "Minerais de fer agglomérés",
        "description_en": "Agglomerated iron ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Agglomération en Afrique", "requirement_en": "Agglomerated in Africa", "regional_content": 40}
    },
    "260400": {
        "chapter": "26",
        "description_fr": "Minerais de nickel",
        "description_en": "Nickel ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - extrait en Afrique", "requirement_en": "Wholly obtained - mined in Africa", "regional_content": 100}
    },
    "260500": {
        "chapter": "26",
        "description_fr": "Minerais de cobalt",
        "description_en": "Cobalt ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade", "certification"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - certification ITSCI", "requirement_en": "Wholly obtained - ITSCI certified", "regional_content": 100}
    },
    "260700": {
        "chapter": "26",
        "description_fr": "Minerais de plomb",
        "description_en": "Lead ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "260900": {
        "chapter": "26",
        "description_fr": "Minerais d'étain",
        "description_en": "Tin ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade", "certification"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - certification ITSCI", "requirement_en": "Wholly obtained - ITSCI certified", "regional_content": 100}
    },
    "261310": {
        "chapter": "26",
        "description_fr": "Minerais de molybdène grillés",
        "description_en": "Roasted molybdenum ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Grillage en Afrique", "requirement_en": "Roasted in Africa", "regional_content": 40}
    },
    "261390": {
        "chapter": "26",
        "description_fr": "Minerais de molybdène autres",
        "description_en": "Other molybdenum ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261400": {
        "chapter": "26",
        "description_fr": "Minerais de titane",
        "description_en": "Titanium ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261510": {
        "chapter": "26",
        "description_fr": "Minerais de zirconium",
        "description_en": "Zirconium ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261610": {
        "chapter": "26",
        "description_fr": "Minerais d'argent",
        "description_en": "Silver ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261690": {
        "chapter": "26",
        "description_fr": "Minerais de métaux précieux autres",
        "description_en": "Other precious metal ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261710": {
        "chapter": "26",
        "description_fr": "Minerais d'antimoine",
        "description_en": "Antimony ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "261800": {
        "chapter": "26",
        "description_fr": "Scories granulées",
        "description_en": "Granulated slag",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "261900": {
        "chapter": "26",
        "description_fr": "Scories, laitiers et déchets de fer/acier",
        "description_en": "Slag, dross and iron/steel waste",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "262011": {
        "chapter": "26",
        "description_fr": "Cendres de zinc (hard zinc spelter)",
        "description_en": "Hard zinc spelter",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262019": {
        "chapter": "26",
        "description_fr": "Autres cendres de zinc",
        "description_en": "Other zinc ash",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262021": {
        "chapter": "26",
        "description_fr": "Boues d'essence au plomb",
        "description_en": "Leaded gasoline sludges",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262029": {
        "chapter": "26",
        "description_fr": "Autres cendres de plomb",
        "description_en": "Other lead ash",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262030": {
        "chapter": "26",
        "description_fr": "Cendres de cuivre",
        "description_en": "Copper ash and residues",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262040": {
        "chapter": "26",
        "description_fr": "Cendres d'aluminium",
        "description_en": "Aluminum ash and residues",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262091": {
        "chapter": "26",
        "description_fr": "Cendres d'antimoine",
        "description_en": "Antimony ash",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262099": {
        "chapter": "26",
        "description_fr": "Cendres de métaux autres",
        "description_en": "Other metal ash and residues",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique", "requirement_en": "Processed in Africa", "regional_content": 40}
    },
    "262110": {
        "chapter": "26",
        "description_fr": "Cendres de déchets municipaux",
        "description_en": "Municipal waste ash",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 27 - COMBUSTIBLES (Compléments)
    # =========================================================================
    "270111": {
        "chapter": "27",
        "description_fr": "Anthracite",
        "description_en": "Anthracite",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "270119": {
        "chapter": "27",
        "description_fr": "Autres houilles",
        "description_en": "Other coal",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "270120": {
        "chapter": "27",
        "description_fr": "Briquettes de houille",
        "description_en": "Coal briquettes",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "270210": {
        "chapter": "27",
        "description_fr": "Lignite non aggloméré",
        "description_en": "Lignite, not agglomerated",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "270300": {
        "chapter": "27",
        "description_fr": "Tourbe",
        "description_en": "Peat",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "270400": {
        "chapter": "27",
        "description_fr": "Cokes et semi-cokes",
        "description_en": "Coke and semi-coke",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "270500": {
        "chapter": "27",
        "description_fr": "Gaz de houille et gaz similaires",
        "description_en": "Coal gas and similar gases",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Produit en Afrique - 40% VA", "requirement_en": "Produced in Africa - 40% VA", "regional_content": 40}
    },
    "270600": {
        "chapter": "27",
        "description_fr": "Goudrons de houille",
        "description_en": "Coal tar",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillation en Afrique", "requirement_en": "Distilled in Africa", "regional_content": 40}
    },
    "270710": {
        "chapter": "27",
        "description_fr": "Benzols",
        "description_en": "Benzol",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillation en Afrique", "requirement_en": "Distilled in Africa", "regional_content": 40}
    },
    "270720": {
        "chapter": "27",
        "description_fr": "Toluols",
        "description_en": "Toluol",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillation en Afrique", "requirement_en": "Distilled in Africa", "regional_content": 40}
    },
    "270730": {
        "chapter": "27",
        "description_fr": "Xylols",
        "description_en": "Xylol",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillation en Afrique", "requirement_en": "Distilled in Africa", "regional_content": 40}
    },
    "270750": {
        "chapter": "27",
        "description_fr": "Autres mélanges d'hydrocarbures aromatiques",
        "description_en": "Other aromatic hydrocarbon mixtures",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Mélange en Afrique", "requirement_en": "Blended in Africa", "regional_content": 40}
    },
    "270810": {
        "chapter": "27",
        "description_fr": "Brai de goudron de houille",
        "description_en": "Coal tar pitch",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Distillation en Afrique", "requirement_en": "Distilled in Africa", "regional_content": 40}
    },
    "270820": {
        "chapter": "27",
        "description_fr": "Coke de brai",
        "description_en": "Pitch coke",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique", "requirement_en": "Manufactured in Africa", "regional_content": 40}
    },
    "271012": {
        "chapter": "27",
        "description_fr": "Huiles légères de pétrole",
        "description_en": "Light petroleum oils",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271091": {
        "chapter": "27",
        "description_fr": "Huiles usagées",
        "description_en": "Waste oils",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "271210": {
        "chapter": "27",
        "description_fr": "Vaseline",
        "description_en": "Petroleum jelly",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271220": {
        "chapter": "27",
        "description_fr": "Paraffine",
        "description_en": "Paraffin wax",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271290": {
        "chapter": "27",
        "description_fr": "Autres cires de pétrole",
        "description_en": "Other petroleum waxes",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271311": {
        "chapter": "27",
        "description_fr": "Coke de pétrole non calciné",
        "description_en": "Petroleum coke, not calcined",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271312": {
        "chapter": "27",
        "description_fr": "Coke de pétrole calciné",
        "description_en": "Petroleum coke, calcined",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "271320": {
        "chapter": "27",
        "description_fr": "Bitume de pétrole",
        "description_en": "Petroleum bitumen",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271390": {
        "chapter": "27",
        "description_fr": "Autres résidus de pétrole",
        "description_en": "Other petroleum residues",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "271410": {
        "chapter": "27",
        "description_fr": "Schistes bitumineux",
        "description_en": "Bituminous shale",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "271500": {
        "chapter": "27",
        "description_fr": "Mélanges bitumineux",
        "description_en": "Bituminous mixtures",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Mélange en Afrique - 40% VA", "requirement_en": "Blended in Africa - 40% VA", "regional_content": 40}
    },
    "271600": {
        "chapter": "27",
        "description_fr": "Énergie électrique",
        "description_en": "Electrical energy",
        "category": "energy",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu - produit en Afrique", "requirement_en": "Wholly obtained - produced in Africa", "regional_content": 100}
    },
    
    # =========================================================================
    # CHAPITRE 28-40 - PRODUITS CHIMIQUES ET PLASTIQUES (Sélection)
    # =========================================================================
    "280110": {
        "chapter": "28",
        "description_fr": "Chlore",
        "description_en": "Chlorine",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "280461": {
        "chapter": "28",
        "description_fr": "Silicium de pureté ≥99,99%",
        "description_en": "Silicon ≥99.99% pure",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Raffiné en Afrique - 40% VA", "requirement_en": "Refined in Africa - 40% VA", "regional_content": 40}
    },
    "281410": {
        "chapter": "28",
        "description_fr": "Ammoniac anhydre",
        "description_en": "Anhydrous ammonia",
        "category": "fertilizers",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "283620": {
        "chapter": "28",
        "description_fr": "Carbonate de sodium (soude)",
        "description_en": "Sodium carbonate (soda ash)",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "290110": {
        "chapter": "29",
        "description_fr": "Hydrocarbures acycliques saturés",
        "description_en": "Saturated acyclic hydrocarbons",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "290121": {
        "chapter": "29",
        "description_fr": "Éthylène",
        "description_en": "Ethylene",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "290122": {
        "chapter": "29",
        "description_fr": "Propène (propylène)",
        "description_en": "Propene (propylene)",
        "category": "chemicals",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "390110": {
        "chapter": "39",
        "description_fr": "Polyéthylène de densité <0.94",
        "description_en": "Polyethylene density <0.94",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Polymérisé en Afrique - 40% VA", "requirement_en": "Polymerized in Africa - 40% VA", "regional_content": 40}
    },
    "390120": {
        "chapter": "39",
        "description_fr": "Polyéthylène de densité ≥0.94",
        "description_en": "Polyethylene density ≥0.94",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Polymérisé en Afrique - 40% VA", "requirement_en": "Polymerized in Africa - 40% VA", "regional_content": 40}
    },
    "390210": {
        "chapter": "39",
        "description_fr": "Polypropylène",
        "description_en": "Polypropylene",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Polymérisé en Afrique - 40% VA", "requirement_en": "Polymerized in Africa - 40% VA", "regional_content": 40}
    },
    "390311": {
        "chapter": "39",
        "description_fr": "Polystyrène expansible",
        "description_en": "Expansible polystyrene",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Polymérisé en Afrique - 40% VA", "requirement_en": "Polymerized in Africa - 40% VA", "regional_content": 40}
    },
    "390410": {
        "chapter": "39",
        "description_fr": "Polychlorure de vinyle (PVC)",
        "description_en": "Polyvinyl chloride (PVC)",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Polymérisé en Afrique - 40% VA", "requirement_en": "Polymerized in Africa - 40% VA", "regional_content": 40}
    },
    "392010": {
        "chapter": "39",
        "description_fr": "Films et feuilles de polymères d'éthylène",
        "description_en": "Ethylene polymer films and sheets",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392310": {
        "chapter": "39",
        "description_fr": "Boîtes, caisses et articles similaires en plastique",
        "description_en": "Plastic boxes, cases and similar articles",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392321": {
        "chapter": "39",
        "description_fr": "Sacs en polymères d'éthylène",
        "description_en": "Bags of ethylene polymers",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392329": {
        "chapter": "39",
        "description_fr": "Sacs en autres matières plastiques",
        "description_en": "Bags of other plastics",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392410": {
        "chapter": "39",
        "description_fr": "Vaisselle en plastique",
        "description_en": "Plastic tableware",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392490": {
        "chapter": "39",
        "description_fr": "Autres articles de ménage en plastique",
        "description_en": "Other plastic household articles",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "392610": {
        "chapter": "39",
        "description_fr": "Articles de bureau en plastique",
        "description_en": "Plastic office articles",
        "category": "plastics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    
    # =========================================================================
    # CHAPITRE 40 - CAOUTCHOUC (Compléments)
    # =========================================================================
    "400121": {
        "chapter": "40",
        "description_fr": "Feuilles fumées de caoutchouc naturel",
        "description_en": "Smoked sheets of natural rubber",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "400129": {
        "chapter": "40",
        "description_fr": "Autres formes de caoutchouc naturel",
        "description_en": "Other forms of natural rubber",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Transformation en Afrique - 40% VA", "requirement_en": "Processed in Africa - 40% VA", "regional_content": 40}
    },
    "400130": {
        "chapter": "40",
        "description_fr": "Balata, gutta-percha",
        "description_en": "Balata, gutta-percha",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "400211": {
        "chapter": "40",
        "description_fr": "Latex de caoutchouc styrène-butadiène",
        "description_en": "Styrene-butadiene rubber latex",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400219": {
        "chapter": "40",
        "description_fr": "Autres caoutchoucs styrène-butadiène",
        "description_en": "Other styrene-butadiene rubber",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400510": {
        "chapter": "40",
        "description_fr": "Caoutchouc vulcanisé chargé de noir de carbone",
        "description_en": "Vulcanized rubber compounded with carbon black",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400700": {
        "chapter": "40",
        "description_fr": "Fils et cordes en caoutchouc vulcanisé",
        "description_en": "Vulcanized rubber thread and cord",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400811": {
        "chapter": "40",
        "description_fr": "Plaques de caoutchouc cellulaire",
        "description_en": "Cellular rubber plates",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400821": {
        "chapter": "40",
        "description_fr": "Plaques de caoutchouc non cellulaire",
        "description_en": "Non-cellular rubber plates",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "400910": {
        "chapter": "40",
        "description_fr": "Tubes et tuyaux en caoutchouc vulcanisé",
        "description_en": "Vulcanized rubber tubes and pipes",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401011": {
        "chapter": "40",
        "description_fr": "Courroies transporteuses en caoutchouc vulcanisé",
        "description_en": "Vulcanized rubber conveyor belts",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401110": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour voitures de tourisme",
        "description_en": "New pneumatic tires for passenger cars",
        "category": "rubber",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401120": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour autobus et camions",
        "description_en": "New pneumatic tires for buses and trucks",
        "category": "rubber",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401130": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour avions",
        "description_en": "New pneumatic tires for aircraft",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401140": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour motocycles",
        "description_en": "New pneumatic tires for motorcycles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401150": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour bicyclettes",
        "description_en": "New pneumatic tires for bicycles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401161": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs à chevrons pour véhicules agricoles",
        "description_en": "New herringbone tires for agricultural vehicles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401163": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour engins de génie civil",
        "description_en": "New tires for construction vehicles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401170": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour véhicules agricoles autres",
        "description_en": "Other new tires for agricultural vehicles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401180": {
        "chapter": "40",
        "description_fr": "Pneumatiques neufs pour engins industriels",
        "description_en": "New tires for industrial equipment",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401190": {
        "chapter": "40",
        "description_fr": "Autres pneumatiques neufs",
        "description_en": "Other new pneumatic tires",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401211": {
        "chapter": "40",
        "description_fr": "Pneumatiques rechapés pour voitures de tourisme",
        "description_en": "Retreaded tires for passenger cars",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Rechapé en Afrique - 40% VA", "requirement_en": "Retreaded in Africa - 40% VA", "regional_content": 40}
    },
    "401212": {
        "chapter": "40",
        "description_fr": "Pneumatiques rechapés pour autobus et camions",
        "description_en": "Retreaded tires for buses and trucks",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Rechapé en Afrique - 40% VA", "requirement_en": "Retreaded in Africa - 40% VA", "regional_content": 40}
    },
    "401220": {
        "chapter": "40",
        "description_fr": "Pneumatiques usagés",
        "description_en": "Used pneumatic tires",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "type"],
        "rule_of_origin": {"type": "wholly_obtained", "requirement_fr": "Entièrement obtenu", "requirement_en": "Wholly obtained", "regional_content": 100}
    },
    "401310": {
        "chapter": "40",
        "description_fr": "Chambres à air pour voitures de tourisme",
        "description_en": "Inner tubes for passenger cars",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401320": {
        "chapter": "40",
        "description_fr": "Chambres à air pour bicyclettes",
        "description_en": "Inner tubes for bicycles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401390": {
        "chapter": "40",
        "description_fr": "Autres chambres à air",
        "description_en": "Other inner tubes",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401511": {
        "chapter": "40",
        "description_fr": "Gants de chirurgie en caoutchouc",
        "description_en": "Surgical rubber gloves",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401519": {
        "chapter": "40",
        "description_fr": "Autres gants en caoutchouc",
        "description_en": "Other rubber gloves",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401610": {
        "chapter": "40",
        "description_fr": "Ouvrages en caoutchouc cellulaire",
        "description_en": "Cellular rubber articles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401693": {
        "chapter": "40",
        "description_fr": "Joints en caoutchouc vulcanisé",
        "description_en": "Vulcanized rubber gaskets",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401699": {
        "chapter": "40",
        "description_fr": "Autres ouvrages en caoutchouc vulcanisé",
        "description_en": "Other vulcanized rubber articles",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
    "401700": {
        "chapter": "40",
        "description_fr": "Caoutchouc durci",
        "description_en": "Hard rubber",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {"type": "substantial_transformation", "requirement_fr": "Fabriqué en Afrique - 40% VA", "requirement_en": "Manufactured in Africa - 40% VA", "regional_content": 40}
    },
}
