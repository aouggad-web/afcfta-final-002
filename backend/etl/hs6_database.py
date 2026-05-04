"""
BASE HS6 COMPLÈTE AVEC SOUS-POSITIONS NATIONALES
=================================================
Architecture unifiée pour :
- Calculateur de tarifs (avec sous-positions 8-12 chiffres)
- Règles d'origine ZLECAf
- Statistiques commerciales

Sources:
- WCO Harmonized System 2022
- Tarifs intégrés nationaux africains
- Commission de l'Union Africaine

Dernière mise à jour: Janvier 2025
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import des extensions de la base HS6
from .hs6_extended_ch01_06 import HS6_EXTENDED as HS6_EXTENDED_CH01_06
from .hs6_extended_ch07_15 import HS6_EXTENDED_CH07_15
from .hs6_extended_ch16_24 import HS6_EXTENDED_CH16_24
from .hs6_extended_ch25_40 import HS6_EXTENDED_CH25_40
from .hs6_extended_ch41_63 import HS6_EXTENDED_CH41_63
from .hs6_extended_ch72_89 import HS6_EXTENDED_CH72_89
from .hs6_extended_ch32_38 import HS6_EXTENDED_CH32_38
from .hs6_extended_ch42_49 import HS6_EXTENDED_CH42_49

# Import de la base CSV complète (5762 codes SH2022)
from .hs6_csv_database import HS6_CSV_DATABASE

# Import des règles d'origine ZLECAf officielles
from .afcfta_rules_of_origin import (
    get_rule_of_origin as get_afcfta_rule,
    get_chapter_status_summary,
    CHAPTER_RULES,
    ORIGIN_TYPES
)

# =============================================================================
# STRUCTURE DE BASE HS6
# =============================================================================

@dataclass
class HS6Code:
    """Structure d'un code HS6 avec métadonnées"""
    code: str
    chapter: str
    description_fr: str
    description_en: str
    category: str  # vehicles, agriculture, minerals, textiles, etc.
    sensitivity: str  # normal, sensitive, excluded (pour ZLECAf)
    has_sub_positions: bool
    typical_sub_position_types: List[str]  # new_used, quality_grade, origin, etc.

# =============================================================================
# BASE HS6 COMPLÈTE - PRODUITS CLÉS AFRIQUE
# =============================================================================

HS6_DATABASE = {
    # =========================================================================
    # CHAPITRE 01 - ANIMAUX VIVANTS
    # =========================================================================
    "010290": {
        "chapter": "01",
        "description_fr": "Autres bovins vivants",
        "description_en": "Other live bovine animals",
        "category": "livestock",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter", "age"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - 100% africain",
            "requirement_en": "Wholly obtained - 100% African",
            "regional_content": 100
        }
    },
    "010410": {
        "chapter": "01",
        "description_fr": "Ovins vivants",
        "description_en": "Live sheep",
        "category": "livestock",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - 100% africain",
            "requirement_en": "Wholly obtained - 100% African",
            "regional_content": 100
        }
    },
    "010420": {
        "chapter": "01",
        "description_fr": "Caprins vivants",
        "description_en": "Live goats",
        "category": "livestock",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["breeding_slaughter"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - 100% africain",
            "requirement_en": "Wholly obtained - 100% African",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 02 - VIANDES
    # =========================================================================
    "020130": {
        "chapter": "02",
        "description_fr": "Viande de bovins désossée, fraîche",
        "description_en": "Bovine meat, boneless, fresh",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "cut_type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - animal né et élevé en Afrique",
            "requirement_en": "Wholly obtained - animal born and raised in Africa",
            "regional_content": 100
        }
    },
    "020230": {
        "chapter": "02",
        "description_fr": "Viande de bovins désossée, congelée",
        "description_en": "Bovine meat, boneless, frozen",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "cut_type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - animal né et élevé en Afrique",
            "requirement_en": "Wholly obtained - animal born and raised in Africa",
            "regional_content": 100
        }
    },
    "020714": {
        "chapter": "02",
        "description_fr": "Morceaux de volailles congelés",
        "description_en": "Poultry cuts, frozen",
        "category": "meat",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["cut_type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 03 - POISSONS
    # =========================================================================
    "030289": {
        "chapter": "03",
        "description_fr": "Autres poissons frais/réfrigérés",
        "description_en": "Other fresh/chilled fish",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "fishing_method"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Pêché dans les eaux africaines",
            "requirement_en": "Caught in African waters",
            "regional_content": 100
        }
    },
    "030342": {
        "chapter": "03",
        "description_fr": "Thon congelé",
        "description_en": "Frozen tuna",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Pêché dans les eaux africaines",
            "requirement_en": "Caught in African waters",
            "regional_content": 100
        }
    },
    "030389": {
        "chapter": "03",
        "description_fr": "Autres poissons congelés",
        "description_en": "Other frozen fish",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "fishing_method"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Pêché dans les eaux africaines",
            "requirement_en": "Caught in African waters",
            "regional_content": 100
        }
    },
    "030617": {
        "chapter": "03",
        "description_fr": "Crevettes congelées",
        "description_en": "Frozen shrimps",
        "category": "fish",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "farmed_wild"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Pêché ou élevé en Afrique",
            "requirement_en": "Caught or farmed in Africa",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 07-08 - FRUITS ET LÉGUMES
    # =========================================================================
    "070200": {
        "chapter": "07",
        "description_fr": "Tomates fraîches",
        "description_en": "Fresh tomatoes",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    "070310": {
        "chapter": "07",
        "description_fr": "Oignons et échalotes",
        "description_en": "Onions and shallots",
        "category": "vegetables",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "export_local"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "080131": {
        "chapter": "08",
        "description_fr": "Noix de cajou en coques",
        "description_en": "Cashew nuts in shell",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "080132": {
        "chapter": "08",
        "description_fr": "Noix de cajou décortiquées",
        "description_en": "Shelled cashew nuts",
        "category": "nuts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "size"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation substantielle en Afrique",
            "requirement_en": "Substantial transformation in Africa",
            "regional_content": 40
        }
    },
    "080390": {
        "chapter": "08",
        "description_fr": "Bananes fraîches/séchées",
        "description_en": "Fresh/dried bananas",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "export_local"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "080410": {
        "chapter": "08",
        "description_fr": "Dattes fraîches",
        "description_en": "Fresh dates",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "080510": {
        "chapter": "08",
        "description_fr": "Oranges fraîches",
        "description_en": "Fresh oranges",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "080520": {
        "chapter": "08",
        "description_fr": "Mandarines, clémentines",
        "description_en": "Mandarins, clementines",
        "category": "fruits",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 09 - CAFÉ, THÉ, ÉPICES
    # =========================================================================
    "090111": {
        "chapter": "09",
        "description_fr": "Café non torréfié non décaféiné",
        "description_en": "Coffee not roasted not decaffeinated",
        "category": "coffee",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade", "region"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    "090121": {
        "chapter": "09",
        "description_fr": "Café torréfié non décaféiné",
        "description_en": "Coffee roasted not decaffeinated",
        "category": "coffee",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "roast_level"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Torréfaction en Afrique, 35% valeur ajoutée",
            "requirement_en": "Roasted in Africa, 35% value added",
            "regional_content": 35
        }
    },
    "090230": {
        "chapter": "09",
        "description_fr": "Thé noir",
        "description_en": "Black tea",
        "category": "tea",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "processing"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    "090510": {
        "chapter": "09",
        "description_fr": "Vanille",
        "description_en": "Vanilla",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "090710": {
        "chapter": "09",
        "description_fr": "Clous de girofle",
        "description_en": "Cloves",
        "category": "spices",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["form"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 10 - CÉRÉALES
    # =========================================================================
    "100190": {
        "chapter": "10",
        "description_fr": "Blé et méteil autre",
        "description_en": "Other wheat and meslin",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "100590": {
        "chapter": "10",
        "description_fr": "Maïs autre",
        "description_en": "Other maize",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "use"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "100610": {
        "chapter": "10",
        "description_fr": "Riz paddy (non décortiqué)",
        "description_en": "Rice in the husk (paddy)",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "100620": {
        "chapter": "10",
        "description_fr": "Riz décortiqué (cargo)",
        "description_en": "Husked (brown) rice",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation substantielle - 35% valeur ajoutée",
            "requirement_en": "Substantial transformation - 35% value added",
            "regional_content": 35
        }
    },
    "100630": {
        "chapter": "10",
        "description_fr": "Riz semi-blanchi ou blanchi",
        "description_en": "Semi-milled or wholly milled rice",
        "category": "cereals",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade", "processing"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation substantielle - 35% valeur ajoutée",
            "requirement_en": "Substantial transformation - 35% value added",
            "regional_content": 35
        }
    },
    
    # =========================================================================
    # CHAPITRE 12 - OLÉAGINEUX
    # =========================================================================
    "120242": {
        "chapter": "12",
        "description_fr": "Arachides décortiquées",
        "description_en": "Shelled groundnuts",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "120740": {
        "chapter": "12",
        "description_fr": "Graines de sésame",
        "description_en": "Sesame seeds",
        "category": "oilseeds",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 13 - GOMMES ET RÉSINES
    # =========================================================================
    "130120": {
        "chapter": "13",
        "description_fr": "Gomme arabique",
        "description_en": "Gum arabic",
        "category": "gums",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety", "quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "130190": {
        "chapter": "13",
        "description_fr": "Autres gommes et résines naturelles",
        "description_en": "Other natural gums and resins",
        "category": "gums",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 15 - HUILES
    # =========================================================================
    "150910": {
        "chapter": "15",
        "description_fr": "Huile d'olive vierge",
        "description_en": "Virgin olive oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "organic"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Olives cultivées et pressées en Afrique",
            "requirement_en": "Olives grown and pressed in Africa",
            "regional_content": 100
        }
    },
    "151110": {
        "chapter": "15",
        "description_fr": "Huile de palme brute",
        "description_en": "Crude palm oil",
        "category": "oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 17 - SUCRES
    # =========================================================================
    "170114": {
        "chapter": "17",
        "description_fr": "Sucre de canne brut",
        "description_en": "Raw cane sugar",
        "category": "sugar",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Canne cultivée et transformée en Afrique",
            "requirement_en": "Cane grown and processed in Africa",
            "regional_content": 100
        }
    },
    "170199": {
        "chapter": "17",
        "description_fr": "Sucre de canne raffiné",
        "description_en": "Refined cane sugar",
        "category": "sugar",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["local_imported", "quality"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Raffinage en Afrique - 40% valeur ajoutée",
            "requirement_en": "Refined in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 18 - CACAO
    # =========================================================================
    "180100": {
        "chapter": "18",
        "description_fr": "Cacao en fèves",
        "description_en": "Cocoa beans",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    "180310": {
        "chapter": "18",
        "description_fr": "Pâte de cacao non dégraissée",
        "description_en": "Cocoa paste, not defatted",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation en Afrique - 35% valeur ajoutée",
            "requirement_en": "Processed in Africa - 35% value added",
            "regional_content": 35
        }
    },
    "180400": {
        "chapter": "18",
        "description_fr": "Beurre, graisse et huile de cacao",
        "description_en": "Cocoa butter, fat and oil",
        "category": "cocoa",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation en Afrique - 35% valeur ajoutée",
            "requirement_en": "Processed in Africa - 35% value added",
            "regional_content": 35
        }
    },
    
    # =========================================================================
    # CHAPITRE 24 - TABAC
    # =========================================================================
    "240110": {
        "chapter": "24",
        "description_fr": "Tabac brut non écôté",
        "description_en": "Raw tobacco, not stemmed",
        "category": "tobacco",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["variety"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 25 - PRODUITS MINÉRAUX
    # =========================================================================
    "250100": {
        "chapter": "25",
        "description_fr": "Sel",
        "description_en": "Salt",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin", "use"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "252329": {
        "chapter": "25",
        "description_fr": "Ciment Portland",
        "description_en": "Portland cement",
        "category": "construction",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "local_imported"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "253110": {
        "chapter": "25",
        "description_fr": "Phosphates de calcium naturels",
        "description_en": "Natural calcium phosphates",
        "category": "minerals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["quality_grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 26 - MINERAIS
    # =========================================================================
    "260111": {
        "chapter": "26",
        "description_fr": "Minerais de fer non agglomérés",
        "description_en": "Iron ores non-agglomerated",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - extrait en Afrique",
            "requirement_en": "Wholly obtained - mined in Africa",
            "regional_content": 100
        }
    },
    "260200": {
        "chapter": "26",
        "description_fr": "Minerais de manganèse",
        "description_en": "Manganese ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "260300": {
        "chapter": "26",
        "description_fr": "Minerais de cuivre",
        "description_en": "Copper ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - extrait en Afrique",
            "requirement_en": "Wholly obtained - mined in Africa",
            "regional_content": 100
        }
    },
    "260600": {
        "chapter": "26",
        "description_fr": "Minerais d'aluminium (bauxite)",
        "description_en": "Aluminum ores (bauxite)",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "260800": {
        "chapter": "26",
        "description_fr": "Minerais de zinc",
        "description_en": "Zinc ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "261000": {
        "chapter": "26",
        "description_fr": "Minerais de chrome",
        "description_en": "Chromium ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "261100": {
        "chapter": "26",
        "description_fr": "Minerais de tungstène",
        "description_en": "Tungsten ores",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["certification"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "261210": {
        "chapter": "26",
        "description_fr": "Minerais d'uranium",
        "description_en": "Uranium ores",
        "category": "ores",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "261590": {
        "chapter": "26",
        "description_fr": "Minerais de niobium/tantale (coltan)",
        "description_en": "Niobium/tantalum ores (coltan)",
        "category": "ores",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["certification"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - certification ITSCI",
            "requirement_en": "Wholly obtained - ITSCI certified",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 27 - COMBUSTIBLES
    # =========================================================================
    "270900": {
        "chapter": "27",
        "description_fr": "Huiles brutes de pétrole",
        "description_en": "Crude petroleum oils",
        "category": "oil_gas",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - extrait en Afrique",
            "requirement_en": "Wholly obtained - extracted in Africa",
            "regional_content": 100
        }
    },
    "271019": {
        "chapter": "27",
        "description_fr": "Autres huiles de pétrole (diesel, essence)",
        "description_en": "Other petroleum oils (diesel, gasoline)",
        "category": "oil_gas",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Raffiné en Afrique - 40% valeur ajoutée",
            "requirement_en": "Refined in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "271111": {
        "chapter": "27",
        "description_fr": "Gaz naturel liquéfié (GNL)",
        "description_en": "Liquefied natural gas (LNG)",
        "category": "oil_gas",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "271121": {
        "chapter": "27",
        "description_fr": "Gaz naturel gazeux",
        "description_en": "Natural gas in gaseous state",
        "category": "oil_gas",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "270112": {
        "chapter": "27",
        "description_fr": "Houille bitumineuse",
        "description_en": "Bituminous coal",
        "category": "coal",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 31 - ENGRAIS
    # =========================================================================
    "310210": {
        "chapter": "31",
        "description_fr": "Urée",
        "description_en": "Urea",
        "category": "fertilizers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "310420": {
        "chapter": "31",
        "description_fr": "Chlorure de potassium",
        "description_en": "Potassium chloride",
        "category": "fertilizers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "310520": {
        "chapter": "31",
        "description_fr": "Engrais phosphatés",
        "description_en": "Phosphatic fertilizers",
        "category": "fertilizers",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 33 - HUILES ESSENTIELLES
    # =========================================================================
    "330129": {
        "chapter": "33",
        "description_fr": "Huiles essentielles autres",
        "description_en": "Other essential oils",
        "category": "essential_oils",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 40 - CAOUTCHOUC
    # =========================================================================
    "400110": {
        "chapter": "40",
        "description_fr": "Latex de caoutchouc naturel",
        "description_en": "Natural rubber latex",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "400122": {
        "chapter": "40",
        "description_fr": "Caoutchouc naturel techniquement spécifié (TSR)",
        "description_en": "Technically specified natural rubber (TSNR)",
        "category": "rubber",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformation en Afrique - 40% valeur ajoutée",
            "requirement_en": "Processed in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 44 - BOIS
    # =========================================================================
    "440320": {
        "chapter": "44",
        "description_fr": "Bois bruts traités",
        "description_en": "Treated rough wood",
        "category": "wood",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    "440341": {
        "chapter": "44",
        "description_fr": "Bois tropicaux (okoumé, etc.)",
        "description_en": "Tropical wood (okoume, etc.)",
        "category": "wood",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["species", "certification"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 52 - COTON
    # =========================================================================
    "520100": {
        "chapter": "52",
        "description_fr": "Coton non cardé ni peigné",
        "description_en": "Cotton, not carded or combed",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "quality_grade"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - cultivé en Afrique",
            "requirement_en": "Wholly obtained - grown in Africa",
            "regional_content": 100
        }
    },
    "520512": {
        "chapter": "52",
        "description_fr": "Fils de coton simples >714 dtex",
        "description_en": "Single cotton yarn >714 dtex",
        "category": "cotton",
        "sensitivity": "normal",
        "has_sub_positions": False,
        "typical_sub_position_types": [],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Filé en Afrique - coton africain ou 40% VA",
            "requirement_en": "Spun in Africa - African cotton or 40% VA",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 61-62 - VÊTEMENTS
    # =========================================================================
    "610910": {
        "chapter": "61",
        "description_fr": "T-shirts en coton, en bonneterie",
        "description_en": "Cotton T-shirts, knitted",
        "category": "textiles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin", "use"],
        "rule_of_origin": {
            "type": "double_transformation",
            "requirement_fr": "Double transformation - tissu et confection en Afrique",
            "requirement_en": "Double transformation - fabric and assembly in Africa",
            "regional_content": 40
        }
    },
    "620342": {
        "chapter": "62",
        "description_fr": "Pantalons hommes coton",
        "description_en": "Men's cotton trousers",
        "category": "textiles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "double_transformation",
            "requirement_fr": "Double transformation - tissu et confection en Afrique",
            "requirement_en": "Double transformation - fabric and assembly in Africa",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 71 - MÉTAUX PRÉCIEUX
    # =========================================================================
    "710231": {
        "chapter": "71",
        "description_fr": "Diamants non industriels bruts",
        "description_en": "Non-industrial rough diamonds",
        "category": "precious",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["certification"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - certification Kimberley",
            "requirement_en": "Wholly obtained - Kimberley certified",
            "regional_content": 100
        }
    },
    "710812": {
        "chapter": "71",
        "description_fr": "Or sous formes brutes",
        "description_en": "Gold in unwrought forms",
        "category": "precious",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type", "origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu - extrait en Afrique",
            "requirement_en": "Wholly obtained - mined in Africa",
            "regional_content": 100
        }
    },
    "711011": {
        "chapter": "71",
        "description_fr": "Platine brut",
        "description_en": "Unwrought platinum",
        "category": "precious",
        "sensitivity": "excluded",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "wholly_obtained",
            "requirement_fr": "Entièrement obtenu",
            "requirement_en": "Wholly obtained",
            "regional_content": 100
        }
    },
    
    # =========================================================================
    # CHAPITRE 74-76 - MÉTAUX NON FERREUX
    # =========================================================================
    "740311": {
        "chapter": "74",
        "description_fr": "Cathodes de cuivre raffiné",
        "description_en": "Refined copper cathodes",
        "category": "metals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["grade"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Raffiné en Afrique - 40% valeur ajoutée",
            "requirement_en": "Refined in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "750110": {
        "chapter": "75",
        "description_fr": "Nickel brut non allié",
        "description_en": "Unwrought non-alloyed nickel",
        "category": "metals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Raffiné en Afrique - 40% valeur ajoutée",
            "requirement_en": "Refined in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "760110": {
        "chapter": "76",
        "description_fr": "Aluminium non allié",
        "description_en": "Non-alloyed aluminum",
        "category": "metals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fondu en Afrique - 40% valeur ajoutée",
            "requirement_en": "Smelted in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 81 - AUTRES MÉTAUX
    # =========================================================================
    "810520": {
        "chapter": "81",
        "description_fr": "Cobalt et articles en cobalt",
        "description_en": "Cobalt and cobalt articles",
        "category": "metals",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformé en Afrique - 40% valeur ajoutée",
            "requirement_en": "Processed in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 84 - MACHINES
    # =========================================================================
    "843041": {
        "chapter": "84",
        "description_fr": "Machines de sondage/forage",
        "description_en": "Boring/sinking machinery",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% valeur ajoutée",
            "requirement_en": "Assembled in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "843351": {
        "chapter": "84",
        "description_fr": "Moissonneuses-batteuses",
        "description_en": "Combine harvester-threshers",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% valeur ajoutée",
            "requirement_en": "Assembled in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "847130": {
        "chapter": "84",
        "description_fr": "Ordinateurs portables",
        "description_en": "Laptop computers",
        "category": "electronics",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% valeur ajoutée",
            "requirement_en": "Assembled in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "847490": {
        "chapter": "84",
        "description_fr": "Parties machines traitement matériaux",
        "description_en": "Parts of material processing machines",
        "category": "machinery",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 85 - ÉQUIPEMENTS ÉLECTRIQUES
    # =========================================================================
    "854430": {
        "chapter": "85",
        "description_fr": "Jeux de fils pour véhicules",
        "description_en": "Wiring sets for vehicles",
        "category": "automotive_parts",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 87 - VÉHICULES
    # =========================================================================
    "870321": {
        "chapter": "87",
        "description_fr": "Voitures ≤1000cc",
        "description_en": "Cars ≤1000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "assembly"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% contenu régional",
            "requirement_en": "Assembled in Africa - 40% regional content",
            "regional_content": 40
        }
    },
    "870322": {
        "chapter": "87",
        "description_fr": "Voitures 1000-1500cc",
        "description_en": "Cars 1000-1500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "assembly"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% contenu régional",
            "requirement_en": "Assembled in Africa - 40% regional content",
            "regional_content": 40
        }
    },
    "870323": {
        "chapter": "87",
        "description_fr": "Voitures 1500-3000cc",
        "description_en": "Cars 1500-3000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "age", "assembly"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% contenu régional",
            "requirement_en": "Assembled in Africa - 40% regional content",
            "regional_content": 40
        }
    },
    "870324": {
        "chapter": "87",
        "description_fr": "Voitures >3000cc",
        "description_en": "Cars >3000cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% contenu régional",
            "requirement_en": "Assembled in Africa - 40% regional content",
            "regional_content": 40
        }
    },
    "870332": {
        "chapter": "87",
        "description_fr": "Voitures diesel >1500cc",
        "description_en": "Diesel cars >1500cc",
        "category": "vehicles",
        "sensitivity": "sensitive",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used", "assembly"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 40% contenu régional",
            "requirement_en": "Assembled in Africa - 40% regional content",
            "regional_content": 40
        }
    },
    "870340": {
        "chapter": "87",
        "description_fr": "Véhicules électriques",
        "description_en": "Electric vehicles",
        "category": "vehicles",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["new_used"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Assemblé en Afrique - 35% contenu régional (incitation)",
            "requirement_en": "Assembled in Africa - 35% regional content (incentive)",
            "regional_content": 35
        }
    },
    
    # =========================================================================
    # CHAPITRE 94 - MEUBLES
    # =========================================================================
    "940360": {
        "chapter": "94",
        "description_fr": "Autres meubles en bois",
        "description_en": "Other wooden furniture",
        "category": "furniture",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    "940390": {
        "chapter": "94",
        "description_fr": "Parties de meubles",
        "description_en": "Parts of furniture",
        "category": "furniture",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["use"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CONSERVES ET PRÉPARATIONS
    # =========================================================================
    "160414": {
        "chapter": "16",
        "description_fr": "Thon en conserve",
        "description_en": "Canned tuna",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["origin"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformé en Afrique - poisson africain ou 35% VA",
            "requirement_en": "Processed in Africa - African fish or 35% VA",
            "regional_content": 35
        }
    },
    "200990": {
        "chapter": "20",
        "description_fr": "Concentrés de fruits",
        "description_en": "Fruit concentrates",
        "category": "processed_food",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Transformé en Afrique - fruits africains ou 40% VA",
            "requirement_en": "Processed in Africa - African fruits or 40% VA",
            "regional_content": 40
        }
    },
    
    # =========================================================================
    # CHAPITRE 30 - MÉDICAMENTS
    # =========================================================================
    "300220": {
        "chapter": "30",
        "description_fr": "Vaccins",
        "description_en": "Vaccines",
        "category": "pharma",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 30% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 30% value added",
            "regional_content": 30
        }
    },
    "300490": {
        "chapter": "30",
        "description_fr": "Autres médicaments",
        "description_en": "Other medicaments",
        "category": "pharma",
        "sensitivity": "normal",
        "has_sub_positions": True,
        "typical_sub_position_types": ["type"],
        "rule_of_origin": {
            "type": "substantial_transformation",
            "requirement_fr": "Fabriqué en Afrique - 40% valeur ajoutée",
            "requirement_en": "Manufactured in Africa - 40% value added",
            "regional_content": 40
        }
    },
}


# =============================================================================
# TYPES DE SOUS-POSITIONS STANDARDISÉS
# =============================================================================

SUB_POSITION_TYPES = {
    "new_used": {
        "fr": "Neuf / Occasion",
        "en": "New / Used",
        "options": [
            {"code_suffix": "1000", "fr": "Neuf", "en": "New"},
            {"code_suffix": "9000", "fr": "Occasion", "en": "Used"},
        ]
    },
    "age": {
        "fr": "Âge du véhicule",
        "en": "Vehicle age",
        "options": [
            {"code_suffix": "9200", "fr": "< 5 ans", "en": "< 5 years"},
            {"code_suffix": "9100", "fr": "5-10 ans", "en": "5-10 years"},
            {"code_suffix": "9000", "fr": "> 10 ans", "en": "> 10 years"},
        ]
    },
    "assembly": {
        "fr": "Type d'assemblage",
        "en": "Assembly type",
        "options": [
            {"code_suffix": "1000", "fr": "CKD (montage local)", "en": "CKD (local assembly)"},
            {"code_suffix": "2000", "fr": "CBU (complet)", "en": "CBU (complete)"},
        ]
    },
    "quality_grade": {
        "fr": "Grade de qualité",
        "en": "Quality grade",
        "options": [
            {"code_suffix": "1000", "fr": "Grade 1 / Premium", "en": "Grade 1 / Premium"},
            {"code_suffix": "2000", "fr": "Grade 2 / Standard", "en": "Grade 2 / Standard"},
            {"code_suffix": "9000", "fr": "Autre", "en": "Other"},
        ]
    },
    "variety": {
        "fr": "Variété",
        "en": "Variety",
        "options": [
            {"code_suffix": "1000", "fr": "Variété 1", "en": "Variety 1"},
            {"code_suffix": "2000", "fr": "Variété 2", "en": "Variety 2"},
            {"code_suffix": "9000", "fr": "Autre", "en": "Other"},
        ]
    },
    "breeding_slaughter": {
        "fr": "Usage",
        "en": "Use",
        "options": [
            {"code_suffix": "1000", "fr": "Reproduction", "en": "Breeding"},
            {"code_suffix": "9000", "fr": "Boucherie", "en": "Slaughter"},
        ]
    },
    "farmed_wild": {
        "fr": "Origine",
        "en": "Origin",
        "options": [
            {"code_suffix": "1000", "fr": "Élevage", "en": "Farmed"},
            {"code_suffix": "9000", "fr": "Sauvage", "en": "Wild"},
        ]
    },
    "local_imported": {
        "fr": "Provenance",
        "en": "Source",
        "options": [
            {"code_suffix": "1000", "fr": "Production locale", "en": "Local production"},
            {"code_suffix": "9000", "fr": "Importé", "en": "Imported"},
        ]
    },
    "certification": {
        "fr": "Certification",
        "en": "Certification",
        "options": [
            {"code_suffix": "1000", "fr": "Certifié", "en": "Certified"},
            {"code_suffix": "9000", "fr": "Non certifié", "en": "Not certified"},
        ]
    },
    "use": {
        "fr": "Utilisation",
        "en": "Use",
        "options": [
            {"code_suffix": "0010", "fr": "Usage spécifique", "en": "Specific use"},
            {"code_suffix": "0090", "fr": "Autre usage", "en": "Other use"},
        ]
    },
    "type": {
        "fr": "Type",
        "en": "Type",
        "options": [
            {"code_suffix": "1000", "fr": "Type 1", "en": "Type 1"},
            {"code_suffix": "2000", "fr": "Type 2", "en": "Type 2"},
            {"code_suffix": "9000", "fr": "Autre", "en": "Other"},
        ]
    },
    "origin": {
        "fr": "Origine géographique",
        "en": "Geographic origin",
        "options": [
            {"code_suffix": "0010", "fr": "Origine spécifique", "en": "Specific origin"},
            {"code_suffix": "0090", "fr": "Autre origine", "en": "Other origin"},
        ]
    },
    "organic": {
        "fr": "Agriculture",
        "en": "Agriculture",
        "options": [
            {"code_suffix": "1000", "fr": "Biologique", "en": "Organic"},
            {"code_suffix": "2000", "fr": "Conventionnel", "en": "Conventional"},
        ]
    },
    "species": {
        "fr": "Espèce",
        "en": "Species",
        "options": [
            {"code_suffix": "1000", "fr": "Espèce 1", "en": "Species 1"},
            {"code_suffix": "2000", "fr": "Espèce 2", "en": "Species 2"},
            {"code_suffix": "9000", "fr": "Autre espèce", "en": "Other species"},
        ]
    },
}


# =============================================================================
# FUSION DES DONNÉES D'EXTENSION DANS LA BASE PRINCIPALE
# =============================================================================

# D'abord, intégrer la base CSV complète (5762 codes SH2022)
HS6_DATABASE.update(HS6_CSV_DATABASE)

# Ensuite, les extensions manuelles (priorité sur CSV pour les données enrichies)
HS6_DATABASE.update(HS6_EXTENDED_CH01_06)
HS6_DATABASE.update(HS6_EXTENDED_CH07_15)
HS6_DATABASE.update(HS6_EXTENDED_CH16_24)
HS6_DATABASE.update(HS6_EXTENDED_CH25_40)
HS6_DATABASE.update(HS6_EXTENDED_CH41_63)
HS6_DATABASE.update(HS6_EXTENDED_CH72_89)
HS6_DATABASE.update(HS6_EXTENDED_CH32_38)
HS6_DATABASE.update(HS6_EXTENDED_CH42_49)


# =============================================================================
# FONCTIONS D'ACCÈS À LA BASE HS6
# =============================================================================

def get_hs6_info(hs6_code: str, language: str = "fr") -> Optional[Dict]:
    """Obtenir les informations complètes d'un code HS6 avec règles d'origine ZLECAf"""
    hs6 = hs6_code[:6].zfill(6)
    info = HS6_DATABASE.get(hs6)
    if info:
        desc_key = f"description_{language}"
        
        # Récupérer la règle d'origine ZLECAf officielle
        afcfta_rule = get_afcfta_rule(hs6, language)
        
        return {
            "code": hs6,
            "description": info.get(desc_key, info.get("description_fr")),
            "chapter": info["chapter"],
            "category": info["category"],
            "sensitivity": info["sensitivity"],
            "has_sub_positions": info["has_sub_positions"],
            "sub_position_types": info.get("typical_sub_position_types", []),
            "rule_of_origin": afcfta_rule
        }
    return None


def get_sub_position_suggestions(hs6_code: str, language: str = "fr") -> List[Dict]:
    """
    Obtenir les suggestions de sous-positions pour un code HS6
    Retourne les types de distinctions possibles
    """
    hs6 = hs6_code[:6].zfill(6)
    info = HS6_DATABASE.get(hs6)
    
    if not info or not info.get("has_sub_positions"):
        return []
    
    suggestions = []
    for sp_type in info.get("typical_sub_position_types", []):
        type_info = SUB_POSITION_TYPES.get(sp_type)
        if type_info:
            suggestions.append({
                "type": sp_type,
                "label": type_info.get(language, type_info["fr"]),
                "options": [
                    {
                        "code_suffix": opt["code_suffix"],
                        "label": opt.get(language, opt["fr"]),
                        "full_code": hs6 + opt["code_suffix"]
                    }
                    for opt in type_info["options"]
                ]
            })
    
    return suggestions


def get_rule_of_origin(hs6_code: str, language: str = "fr") -> Optional[Dict]:
    """Obtenir la règle d'origine ZLECAf pour un code HS6"""
    hs6 = hs6_code[:6].zfill(6)
    info = HS6_DATABASE.get(hs6)
    
    if info and "rule_of_origin" in info:
        rule = info["rule_of_origin"]
        req_key = f"requirement_{language}"
        return {
            "hs6_code": hs6,
            "type": rule["type"],
            "requirement": rule.get(req_key, rule.get("requirement_fr")),
            "regional_content": rule["regional_content"]
        }
    return None


def search_hs6_codes(query: str, language: str = "fr", limit: int = 20) -> List[Dict]:
    """Rechercher des codes HS6 par mot-clé (avec support des accents)"""
    import unicodedata
    
    def normalize(text: str) -> str:
        """Normalise le texte en retirant les accents"""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text.lower())
            if unicodedata.category(c) != 'Mn'
        )
    
    query_normalized = normalize(query)
    results = []
    
    for code, info in HS6_DATABASE.items():
        desc_fr = normalize(info.get("description_fr", ""))
        desc_en = normalize(info.get("description_en", ""))
        category = normalize(info.get("category", ""))
        
        if query_normalized in code or query_normalized in desc_fr or query_normalized in desc_en or query_normalized in category:
            desc_key = f"description_{language}"
            results.append({
                "code": code,
                "description": info.get(desc_key, info.get("description_fr")),
                "category": info["category"],
                "sensitivity": info["sensitivity"],
                "has_sub_positions": info["has_sub_positions"]
            })
        
        if len(results) >= limit:
            break
    
    return results


def get_all_categories() -> List[str]:
    """Obtenir toutes les catégories de produits"""
    categories = set()
    for info in HS6_DATABASE.values():
        categories.add(info["category"])
    return sorted(list(categories))


def get_codes_by_category(category: str, language: str = "fr") -> List[Dict]:
    """Obtenir tous les codes HS6 d'une catégorie"""
    results = []
    for code, info in HS6_DATABASE.items():
        if info["category"] == category:
            desc_key = f"description_{language}"
            results.append({
                "code": code,
                "description": info.get(desc_key, info.get("description_fr")),
                "sensitivity": info["sensitivity"],
                "has_sub_positions": info["has_sub_positions"]
            })
    return sorted(results, key=lambda x: x["code"])


def get_database_stats() -> Dict:
    """Obtenir les statistiques de la base HS6"""
    categories = {}
    sensitivities = {"normal": 0, "sensitive": 0, "excluded": 0}
    with_sub_positions = 0
    
    for info in HS6_DATABASE.values():
        cat = info["category"]
        categories[cat] = categories.get(cat, 0) + 1
        sensitivities[info["sensitivity"]] += 1
        if info["has_sub_positions"]:
            with_sub_positions += 1
    
    return {
        "total_codes": len(HS6_DATABASE),
        "with_sub_positions": with_sub_positions,
        "categories": categories,
        "sensitivities": sensitivities
    }
