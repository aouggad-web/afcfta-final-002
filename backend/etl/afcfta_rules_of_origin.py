"""
AfCFTA Rules of Origin Database - OFFICIAL DATA
Based on Appendix IV to Annexure 2 of the AfCFTA Agreement
Source: https://etariff.au-afcfta.org/assets/manuals/EN-APPENDIX-IV-AS-AT-COM-12-DECEMBER-2023.pdf

This module contains Product-Specific Rules (PSRs) for the African Continental Free Trade Area.
The data is extracted from the official AfCFTA e-Tariff Book published by the AU Secretariat.

Rule Types:
- WO: Wholly Obtained - Product must be wholly obtained in AfCFTA State Parties
- CTH: Change of Tariff Heading - Manufactured from materials of any heading other than the product
- CTSH: Change of Tariff Sub-heading - Manufactured from materials of any sub-heading other than the product
- CC: Change of Chapter - Manufactured from materials of any chapter other than the product
- VA: Value Added - Percentage of non-originating materials value threshold
- SP: Specific Process - Specific manufacturing process required

Data Source Version: December 2023 (COM-12) - Latest available official AfCFTA data
Implementation Date: January 2026

Note: This implementation uses the December 2023 AfCFTA rules of origin data,
which is the most recent official data published by the AU Secretariat as of
the implementation date (January 2026).
"""

# Rule type translations
ORIGIN_TYPES = {
    "WO": {"en": "Wholly Obtained", "fr": "Entièrement Obtenu"},
    "CC": {"en": "Change of Chapter", "fr": "Changement de Chapitre"},
    "CTH": {"en": "Change of Tariff Heading", "fr": "Changement de Position Tarifaire"},
    "CTSH": {"en": "Change of Tariff Subheading", "fr": "Changement de Sous-Position"},
    "VA": {"en": "Value Added", "fr": "Valeur Ajoutée"},
    "VA40": {"en": "Max 40% non-originating value", "fr": "Max 40% valeur non-originaire"},
    "VA50": {"en": "Max 50% non-originating value", "fr": "Max 50% valeur non-originaire"},
    "VA60": {"en": "Max 60% non-originating value", "fr": "Max 60% valeur non-originaire"},
    "VA65": {"en": "Max 65% non-originating value", "fr": "Max 65% valeur non-originaire"},
    "SP": {"en": "Specific Process", "fr": "Processus Spécifique"},
    "RVC": {"en": "Regional Value Content", "fr": "Contenu de Valeur Régionale"},
    "YARN": {"en": "Manufacture from yarn", "fr": "Fabrication à partir de fils"},
    "YTB": {"en": "Yet to be agreed", "fr": "En cours de négociation"},
}

# ============================================================================
# CHAPTER-LEVEL RULES (Appendix IV - Default rules by chapter)
# ============================================================================
CHAPTER_RULES = {
    # SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS (Chapters 1-5)
    "01": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Live animals - All animals must be wholly obtained",
        "description_fr": "Animaux vivants - Tous les animaux doivent être entièrement obtenus",
        "rule_text_en": "All animals of this Chapter must be wholly obtained",
        "rule_text_fr": "Tous les animaux de ce chapitre doivent être entièrement obtenus"
    },
    "02": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Meat and edible meat offal - Materials of Ch.1 & 2 must be wholly obtained",
        "description_fr": "Viandes et abats comestibles - Matières des Ch.1 & 2 entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of Chapters 1 and 2 used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières des chapitres 1 et 2 utilisées doivent être entièrement obtenues"
    },
    "03": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Fish and crustaceans - Materials of this Chapter must be wholly obtained",
        "description_fr": "Poissons et crustacés - Matières de ce chapitre entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "04": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Dairy products - Wholly obtained or max 60% non-originating (5 years)",
        "description_fr": "Produits laitiers - Entièrement obtenus ou max 60% non-originaire (5 ans)",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "05": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Other animal products - Materials must be wholly obtained",
        "description_fr": "Autres produits d'origine animale - Matières entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # SECTION II - VEGETABLE PRODUCTS (Chapters 6-14)
    "06": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Live trees and plants - Wholly obtained",
        "description_fr": "Plantes vivantes - Entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "07": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Edible vegetables - Wholly obtained",
        "description_fr": "Légumes comestibles - Entièrement obtenus",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "08": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Edible fruits and nuts - Wholly obtained",
        "description_fr": "Fruits comestibles - Entièrement obtenus",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "09": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Coffee, tea, maté and spices - Wholly obtained",
        "description_fr": "Café, thé, maté et épices - Entièrement obtenus",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "10": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Cereals - Wholly obtained",
        "description_fr": "Céréales - Entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "11": {
        "primary": "WO", "alt": "CTH", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Milling products - Ch.7,8,10 materials wholly obtained or CTH",
        "description_fr": "Produits de minoterie - Matières Ch.7,8,10 entièrement obtenues ou CTH",
        "rule_text_en": "Manufacture in which all Materials of Chapters 7, 8 and 10 used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières des chapitres 7, 8 et 10 utilisées doivent être entièrement obtenues"
    },
    "12": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Oil seeds and oleaginous fruits - Wholly obtained",
        "description_fr": "Graines oléagineuses - Entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "13": {
        "primary": "WO", "alt": "CTH", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Lac, gums, resins - Wholly obtained or CTH",
        "description_fr": "Gommes, résines - Entièrement obtenues ou CTH",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "14": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Vegetable plaiting materials - Wholly obtained",
        "description_fr": "Matières à tresser végétales - Entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # SECTION III - ANIMAL OR VEGETABLE FATS AND OILS (Chapter 15)
    "15": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Animal/vegetable fats and oils - Wholly obtained or max 60% (3 years)",
        "description_fr": "Graisses et huiles - Entièrement obtenues ou max 60% (3 ans)",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # SECTION IV - FOODSTUFFS (Chapters 16-24)
    "16": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Preparations of meat/fish - Ch.1,2,3 materials wholly obtained or max 60% (5 years)",
        "description_fr": "Préparations de viandes/poissons - Matières Ch.1,2,3 entièrement obtenues ou max 60% (5 ans)",
        "rule_text_en": "Manufacture in which all Materials of Chapters 1, 2 and 3 used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières des chapitres 1, 2 et 3 utilisées doivent être entièrement obtenues"
    },
    "17": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Sugars and sugar confectionery - Wholly obtained or max 60% (5 years)",
        "description_fr": "Sucres et sucreries - Entièrement obtenus ou max 60% (5 ans)",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "18": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Cocoa and cocoa preparations - Ch.17 & 18 materials wholly obtained",
        "description_fr": "Cacao et préparations - Matières Ch.17 & 18 entièrement obtenues",
        "rule_text_en": "Manufacture in which all Materials of Chapters 17 and 18 used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières des chapitres 17 et 18 utilisées doivent être entièrement obtenues"
    },
    "19": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Preparations of cereals - CTH, wheat of Ch.11 must be originating",
        "description_fr": "Préparations de céréales - CTH, blé du Ch.11 doit être originaire",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product provided that the wheat Products of Chapter 11 used must be originating",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit, sous réserve que les produits à base de blé du chapitre 11 utilisés soient originaires"
    },
    "20": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Preparations of vegetables/fruits - Wholly obtained or max 60% (5 years)",
        "description_fr": "Préparations de légumes/fruits - Entièrement obtenus ou max 60% (5 ans)",
        "rule_text_en": "Manufacture in which all the vegetables, fruit, nuts or other parts of plants used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle tous les légumes, fruits, noix ou autres parties de plantes utilisés doivent être entièrement obtenus"
    },
    "21": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Miscellaneous edible preparations - CTH or max 60% value",
        "description_fr": "Préparations alimentaires diverses - CTH ou max 60% valeur",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières utilisées ne dépasse pas 60% du prix départ usine"
    },
    "22": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Beverages, spirits and vinegar - CTH or wholly obtained",
        "description_fr": "Boissons et vinaigres - CTH ou entièrement obtenus",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "23": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Food industry residues; animal feed - CTH, Ch.2,3,4,10,11,12,17 originating",
        "description_fr": "Résidus industries alimentaires - CTH, Ch.2,3,4,10,11,12,17 originaires",
        "rule_text_en": "Manufacture from Materials of any Heading but Materials of Chapters 2, 3, 4, 10, 11, 12 and 17 used must be originating",
        "rule_text_fr": "Fabrication à partir de matières de toute position mais les matières des chapitres 2, 3, 4, 10, 11, 12 et 17 utilisées doivent être originaires"
    },
    "24": {
        "primary": "WO", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Tobacco - Wholly obtained or max 60% + max 30% weight from 24.01",
        "description_fr": "Tabacs - Entièrement obtenus ou max 60% + max 30% poids de 24.01",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # SECTION V - MINERAL PRODUCTS (Chapters 25-27)
    "25": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Salt; sulphur; earths and stone; cement - Wholly obtained",
        "description_fr": "Sel, soufre, terres, pierres, ciments - Entièrement obtenus",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "26": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Ores, slag and ash - Wholly obtained",
        "description_fr": "Minerais, scories et cendres - Entièrement obtenus",
        "rule_text_en": "Manufacture in which all the Materials must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières doivent être entièrement obtenues"
    },
    "27": {
        "primary": "CTH", "alt": "VA40", "max_non_orig": 40, "status": "AGREED",
        "description_en": "Mineral fuels, oils - CTH or max 40% value (refined products: 50%)",
        "description_fr": "Combustibles minéraux, huiles - CTH ou max 40% valeur (produits raffinés: 50%)",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of all the Materials used does not exceed 40% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur de toutes les matières utilisées ne dépasse pas 40% du prix départ usine"
    },
    
    # SECTION VI - PRODUCTS OF THE CHEMICAL INDUSTRIES (Chapters 28-38)
    "28": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Inorganic chemicals - CTH or max 60% value or chemical processing",
        "description_fr": "Produits chimiques inorganiques - CTH ou max 60% ou transformation chimique",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price or Chemical processing rules",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine, ou règles de transformation chimique"
    },
    "29": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Organic chemicals - CTH or max 60% value or chemical processing",
        "description_fr": "Produits chimiques organiques - CTH ou max 60% ou transformation chimique",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price or Chemical processing rules",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine, ou règles de transformation chimique"
    },
    "30": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Pharmaceutical products - CTH or max 60% value or chemical processing",
        "description_fr": "Produits pharmaceutiques - CTH ou max 60% ou transformation chimique",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "31": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Fertilizers - CTH or max 60% value",
        "description_fr": "Engrais - CTH ou max 60% valeur",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "32": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Tanning/dyeing extracts; paints; inks - CTH or max 60%",
        "description_fr": "Extraits tannants/tinctoriaux; peintures - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "33": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Essential oils; perfumery; cosmetics - CTH or max 60%",
        "description_fr": "Huiles essentielles; parfumerie; cosmétiques - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "34": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Soap; waxes; candles - CTH or max 60%",
        "description_fr": "Savons; cires; bougies - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "35": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Albuminoidal substances; glues - CTH or max 60%",
        "description_fr": "Matières albuminoïdes; colles - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "36": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Explosives; pyrotechnics; matches - CTH or max 60%",
        "description_fr": "Explosifs; pyrotechnie; allumettes - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "37": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Photographic/cinematographic goods - CTH or max 60%",
        "description_fr": "Produits photographiques/cinématographiques - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    "38": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Miscellaneous chemical products - CTH or max 60%",
        "description_fr": "Produits chimiques divers - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION VII - PLASTICS AND RUBBER (Chapters 39-40)
    "39": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Plastics and articles thereof - CTH or max 60%",
        "description_fr": "Matières plastiques et ouvrages - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "40": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Rubber and articles thereof - CTH or max 60%",
        "description_fr": "Caoutchouc et ouvrages - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION VIII - RAW HIDES AND SKINS, LEATHER (Chapters 41-43)
    "41": {
        "primary": "WO", "alt": "CC", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Raw hides and skins; leather - Wholly obtained or change of chapter",
        "description_fr": "Peaux brutes et cuirs - Entièrement obtenus ou changement de chapitre",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "42": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Leather articles; travel goods - CTH, Ch.41 materials originating after 5 years",
        "description_fr": "Articles en cuir; bagages - CTH, matières Ch.41 originaires après 5 ans",
        "rule_text_en": "Manufacture from any other Heading for 5 years, after which manufacture from any other Heading provided that materials from HS Chapter 41 are originating",
        "rule_text_fr": "Fabrication à partir de toute autre position pendant 5 ans, après quoi fabrication à partir de toute autre position à condition que les matières du chapitre 41 SH soient originaires"
    },
    "43": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Furskins and artificial fur - CTH or max 60%",
        "description_fr": "Pelleteries et fourrures artificielles - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION IX - WOOD AND ARTICLES OF WOOD (Chapters 44-46)
    "44": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Wood and articles of wood - CTH (tropical woods wholly obtained)",
        "description_fr": "Bois et ouvrages en bois - CTH (bois tropicaux entièrement obtenus)",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit"
    },
    "45": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Cork and articles of cork - CTH or max 60%",
        "description_fr": "Liège et ouvrages - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "46": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Manufactures of straw, basketware - CTH, Ch.14 materials wholly obtained",
        "description_fr": "Ouvrages en paille, vannerie - CTH, matières Ch.14 entièrement obtenues",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product provided that Materials of Chapter 14 are wholly obtained",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit, à condition que les matières du chapitre 14 soient entièrement obtenues"
    },
    
    # SECTION X - PULP OF WOOD; PAPER (Chapters 47-49)
    "47": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Pulp of wood - CTH or max 60%",
        "description_fr": "Pâte de bois - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "48": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Paper and paperboard - CTH or max 60%",
        "description_fr": "Papiers et cartons - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "49": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Printed books, newspapers - CTH or max 60%",
        "description_fr": "Produits de l'imprimerie - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XI - TEXTILES AND TEXTILE ARTICLES (Chapters 50-63)
    "50": {
        "primary": "CTH", "alt": "SP", "max_non_orig": 50, "status": "AGREED",
        "description_en": "Silk - CTH or specific process",
        "description_fr": "Soie - CTH ou processus spécifique",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "51": {
        "primary": "CTH", "alt": "SP", "max_non_orig": 0, "status": "PARTIAL",
        "description_en": "Wool, fine/coarse animal hair - CTH (some headings yet to be agreed)",
        "description_fr": "Laine, poils - CTH (certaines positions en négociation)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "52": {
        "primary": "WO", "alt": "YTB", "max_non_orig": 0, "status": "PARTIAL",
        "description_en": "Cotton - Wholly obtained (many headings yet to be agreed)",
        "description_fr": "Coton - Entièrement obtenu (plusieurs positions en négociation)",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "53": {
        "primary": "CTH", "alt": "SP", "max_non_orig": 50, "status": "PARTIAL",
        "description_en": "Other vegetable textile fibres - CTH or spinning",
        "description_fr": "Autres fibres textiles végétales - CTH ou filature",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "54": {
        "primary": "CTH", "alt": "YTB", "max_non_orig": 0, "status": "PARTIAL",
        "description_en": "Man-made filaments - CTH (woven fabrics yet to be agreed)",
        "description_fr": "Filaments synthétiques - CTH (tissus en négociation)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "55": {
        "primary": "CTH", "alt": "YTB", "max_non_orig": 0, "status": "PARTIAL",
        "description_en": "Man-made staple fibres - CTH (woven fabrics yet to be agreed)",
        "description_fr": "Fibres synthétiques discontinues - CTH (tissus en négociation)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "56": {
        "primary": "CTH", "alt": "VA50", "max_non_orig": 50, "status": "AGREED",
        "description_en": "Wadding, felt, nonwovens; special yarns - CTH or max 50%",
        "description_fr": "Ouates, feutres, non-tissés; fils spéciaux - CTH ou max 50%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "57": {
        "primary": "CTH", "alt": "SP", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Carpets and textile floor coverings - CTH or from yarn/fibres",
        "description_fr": "Tapis et revêtements de sol textiles - CTH ou à partir de fils/fibres",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture from yarn, synthetic/artificial filament yarn, natural fibres, or man-made staple fibres",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication à partir de fils, filaments synthétiques/artificiels, fibres naturelles ou fibres discontinues synthétiques"
    },
    "58": {
        "primary": "CTH", "alt": "SP", "max_non_orig": 50, "status": "PARTIAL",
        "description_en": "Special woven fabrics; lace; tapestries - CTH or specific process",
        "description_fr": "Tissus spéciaux; dentelles; tapisseries - CTH ou processus spécifique",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or specific processing",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou transformation spécifique"
    },
    "59": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Impregnated, coated, laminated textiles - CTH",
        "description_fr": "Textiles imprégnés, enduits, stratifiés - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "60": {
        "primary": "YTB", "alt": None, "max_non_orig": 0, "status": "YTB",
        "description_en": "Knitted or crocheted fabrics - Yet to be agreed",
        "description_fr": "Étoffes de bonneterie - En cours de négociation",
        "rule_text_en": "Yet to be agreed",
        "rule_text_fr": "En cours de négociation"
    },
    "61": {
        "primary": "YARN", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Knitted apparel - Manufacture from yarn (review after 5 years)",
        "description_fr": "Vêtements de bonneterie - Fabrication à partir de fils (révision après 5 ans)",
        "rule_text_en": "Manufacture from yarn, subject to a review after 5 years",
        "rule_text_fr": "Fabrication à partir de fils, sous réserve d'une révision après 5 ans"
    },
    "62": {
        "primary": "YARN", "alt": "CTH", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Woven apparel - Manufacture from yarn (review after 5 years)",
        "description_fr": "Vêtements tissés - Fabrication à partir de fils (révision après 5 ans)",
        "rule_text_en": "Manufacture from yarn, subject to review after 5 years",
        "rule_text_fr": "Fabrication à partir de fils, sous réserve de révision après 5 ans"
    },
    "63": {
        "primary": "CTH", "alt": "VA50", "max_non_orig": 50, "status": "PARTIAL",
        "description_en": "Other made-up textile articles - CTH or max 50% (some headings YTB)",
        "description_fr": "Autres articles textiles confectionnés - CTH ou max 50% (certains YTB)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # SECTION XII - FOOTWEAR, HEADGEAR (Chapters 64-67)
    "64": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Footwear - CTH with uppers from 64.06 originating",
        "description_fr": "Chaussures - CTH avec dessus de 64.06 originaires",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product and in which uppers of Heading 64.06 must be originating",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit et dans laquelle les dessus de la position 64.06 doivent être originaires"
    },
    "65": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Headgear - CTH",
        "description_fr": "Coiffures - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "66": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Umbrellas, walking-sticks - CTH",
        "description_fr": "Parapluies, cannes - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "67": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Prepared feathers; artificial flowers - CTH",
        "description_fr": "Plumes préparées; fleurs artificielles - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # SECTION XIII - ARTICLES OF STONE, GLASS (Chapters 68-70)
    "68": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Articles of stone, cement, asbestos - CTH (stone materials wholly obtained)",
        "description_fr": "Ouvrages en pierres, ciment, amiante - CTH (pierres entièrement obtenues)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "69": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Ceramic products - CTH",
        "description_fr": "Produits céramiques - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "70": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Glass and glassware - CTH or max 60%",
        "description_fr": "Verre et ouvrages en verre - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XIV - PRECIOUS METALS AND STONES (Chapter 71)
    "71": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Precious metals/stones; jewelry - CTH or max 60% (precious metals wholly obtained)",
        "description_fr": "Métaux/pierres précieux; bijouterie - CTH ou max 60% (métaux précieux entièrement obtenus)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XV - BASE METALS AND ARTICLES (Chapters 72-83)
    "72": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Iron and steel - CTH",
        "description_fr": "Fonte, fer et acier - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "73": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Articles of iron or steel - CTH",
        "description_fr": "Ouvrages en fonte, fer ou acier - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "74": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Copper and articles thereof - CTH or max 60%",
        "description_fr": "Cuivre et ouvrages - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "75": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Nickel and articles thereof - CTH or max 60% (unwrought wholly obtained)",
        "description_fr": "Nickel et ouvrages - CTH ou max 60% (brut entièrement obtenu)",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "76": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Aluminium and articles thereof - CTH",
        "description_fr": "Aluminium et ouvrages - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "78": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Lead and articles thereof - CTH",
        "description_fr": "Plomb et ouvrages - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "79": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Zinc and articles thereof - CTH or max 60%",
        "description_fr": "Zinc et ouvrages - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "80": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Tin and articles thereof - CTH",
        "description_fr": "Étain et ouvrages - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "81": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Other base metals; cermets - CTH",
        "description_fr": "Autres métaux communs; cermets - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "82": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Tools, cutlery of base metal - CTH",
        "description_fr": "Outils, coutellerie en métaux communs - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "83": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Miscellaneous articles of base metal - CTH",
        "description_fr": "Ouvrages divers en métaux communs - CTH",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit"
    },
    
    # SECTION XVI - MACHINERY AND MECHANICAL/ELECTRICAL EQUIPMENT (Chapters 84-85)
    "84": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Machinery and mechanical appliances - CTH or max 60%",
        "description_fr": "Machines et appareils mécaniques - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "85": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Electrical machinery and equipment - CTH or max 60%",
        "description_fr": "Machines et appareils électriques - CTH ou max 60%",
        "rule_text_en": "Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication dans laquelle la valeur de toutes les matières utilisées ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XVII - VEHICLES, AIRCRAFT, VESSELS (Chapters 86-89)
    "86": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Railway/tramway locomotives and rolling stock - CTH or max 60%",
        "description_fr": "Véhicules ferroviaires - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "87": {
        "primary": "VA60", "alt": "YTB", "max_non_orig": 60, "status": "PARTIAL",
        "description_en": "Vehicles other than railway - Max 60% (many headings yet to be agreed)",
        "description_fr": "Véhicules autres que ferroviaires - Max 60% (plusieurs positions en négociation)",
        "rule_text_en": "Manufacture in which the value of the Materials used does not exceed 60% of the ex-works price, with a review after 5 years",
        "rule_text_fr": "Fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine, avec révision après 5 ans"
    },
    "88": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Aircraft and spacecraft - CTH or max 60%",
        "description_fr": "Aéronefs et engins spatiaux - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "89": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Ships, boats and floating structures - CTH or max 60%",
        "description_fr": "Navires et structures flottantes - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XVIII - OPTICAL, MEASURING, MEDICAL INSTRUMENTS (Chapters 90-92)
    "90": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Optical, medical, measuring instruments - CTH or max 60%",
        "description_fr": "Instruments d'optique, médicaux, de mesure - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "91": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Clocks and watches - CTH or max 60%",
        "description_fr": "Horlogerie - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "92": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Musical instruments - CTH or max 60%",
        "description_fr": "Instruments de musique - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XIX - ARMS AND AMMUNITION (Chapter 93)
    "93": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Arms and ammunition - CTH or max 60%",
        "description_fr": "Armes et munitions - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading, except that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position, sauf celle du produit, ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XX - MISCELLANEOUS MANUFACTURED ARTICLES (Chapters 94-96)
    "94": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Furniture; bedding; lamps; prefabricated buildings - CTH or max 60%",
        "description_fr": "Meubles; literie; lampes; constructions préfabriquées - CTH ou max 60%",
        "rule_text_en": "Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication dans laquelle la valeur de toutes les matières utilisées ne dépasse pas 60% du prix départ usine"
    },
    "95": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Toys, games and sports equipment - CTH or max 60%",
        "description_fr": "Jouets, jeux et articles de sport - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "96": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Miscellaneous manufactured articles - CTH or max 60%",
        "description_fr": "Ouvrages divers - CTH ou max 60%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 60% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    
    # SECTION XXI - WORKS OF ART (Chapter 97)
    "97": {
        "primary": "CTH", "alt": "VA40", "max_non_orig": 40, "status": "AGREED",
        "description_en": "Works of art, collectors' pieces, antiques - CTH or max 40%",
        "description_fr": "Objets d'art, de collection, antiquités - CTH ou max 40%",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product or Manufacture in which the value of all the Materials used does not exceed 40% of the ex-works price",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit ou fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 40% du prix départ usine"
    },
}

# ============================================================================
# HEADING-LEVEL AND PRODUCT-SPECIFIC RULES (From Appendix IV)
# ============================================================================
HEADING_RULES = {
    # Chapter 4 - Dairy Products
    "0401": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Milk and cream, not concentrated",
        "description_fr": "Lait et crème, non concentrés",
        "rule_text_en": "Manufacture in which Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle les matières utilisées doivent être entièrement obtenues"
    },
    "0403": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Buttermilk, yoghurt, kephir",
        "description_fr": "Babeurre, yaourt, kéfir",
        "rule_text_en": "Manufacture in which the value of non-originating materials does not exceed 60% (5 years), then materials of 04.01 and 04.02 wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle la valeur des matières non originaires ne dépasse pas 60% (5 ans), puis matières de 04.01 et 04.02 entièrement obtenues"
    },
    "0406": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Cheese and curd",
        "description_fr": "Fromages et caillebotte",
        "rule_text_en": "Manufacture in which the value of non-originating materials does not exceed 60% (5 years), then materials of 04.01 and 04.02 wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle la valeur des matières non originaires ne dépasse pas 60% (5 ans), puis matières de 04.01 et 04.02 entièrement obtenues"
    },
    
    # Chapter 9 - Coffee, tea, spices
    "0910": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Ginger, saffron, turmeric, thyme, bay leaves, curry and other spices",
        "description_fr": "Gingembre, safran, curcuma, thym, laurier, curry et autres épices",
        "rule_text_en": "Manufacture in which Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle les matières utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 11 - Milling products
    "1101": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Wheat or meslin flour",
        "description_fr": "Farines de froment ou de méteil",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product, subject to a review after five years",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit, sous réserve de révision après cinq ans"
    },
    "1104": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Cereal grains otherwise worked",
        "description_fr": "Grains de céréales autrement travaillés",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "1105": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Flour of potatoes",
        "description_fr": "Farine de pommes de terre",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "1107": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Malt, whether or not roasted",
        "description_fr": "Malt, même torréfié",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 13
    "1302": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Vegetable saps and extracts; pectic substances; agar-agar",
        "description_fr": "Sucs et extraits végétaux; matières pectiques; agar-agar",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # Chapter 15 - Fats and Oils
    "1504": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Fats and oils of fish or marine mammals",
        "description_fr": "Graisses et huiles de poissons ou de mammifères marins",
        "rule_text_en": "Max 60% non-originating for 3 years, then wholly obtained (subject to objective review)",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis entièrement obtenu (sous réserve d'examen objectif)"
    },
    "1507": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Soya-bean oil",
        "description_fr": "Huile de soja",
        "rule_text_en": "Max 60% non-originating for 3 years, then wholly obtained",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis entièrement obtenu"
    },
    "1511": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Palm oil and its fractions",
        "description_fr": "Huile de palme et ses fractions",
        "rule_text_en": "Max 60% non-originating for 3 years, then wholly obtained",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis entièrement obtenu"
    },
    "1512": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Sunflower-seed or safflower oil",
        "description_fr": "Huile de tournesol ou de carthame",
        "rule_text_en": "Max 60% non-originating for 3 years, then wholly obtained",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis entièrement obtenu"
    },
    "1517": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Margarine; edible mixtures of fats/oils",
        "description_fr": "Margarine; mélanges comestibles de graisses/huiles",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # Chapter 16 - Meat/Fish preparations
    "1604": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Prepared or preserved fish",
        "description_fr": "Préparations et conserves de poissons",
        "rule_text_en": "Max 60% non-originating for 5 years, then Ch.3 materials wholly obtained",
        "rule_text_fr": "Max 60% non-originaire pendant 5 ans, puis matières Ch.3 entièrement obtenues"
    },
    "1605": {
        "primary": "VA60", "alt": "WO", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Crustaceans, molluscs prepared or preserved",
        "description_fr": "Crustacés, mollusques préparés ou conservés",
        "rule_text_en": "Max 60% non-originating for 5 years, then Ch.3 materials wholly obtained",
        "rule_text_fr": "Max 60% non-originaire pendant 5 ans, puis matières Ch.3 entièrement obtenues"
    },
    
    # Chapter 17 - Sugars
    "1702": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Other sugars; artificial honey; caramel",
        "description_fr": "Autres sucres; miel artificiel; caramel",
        "rule_text_en": "Max 60% non-originating for 5 years (subject to review)",
        "rule_text_fr": "Max 60% non-originaire pendant 5 ans (sous réserve de révision)"
    },
    "1704": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Sugar confectionery (including white chocolate)",
        "description_fr": "Sucreries (y compris chocolat blanc)",
        "rule_text_en": "Max 60% non-originating for 5 years (subject to review)",
        "rule_text_fr": "Max 60% non-originaire pendant 5 ans (sous réserve de révision)"
    },
    
    # Chapter 19
    "1901": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Malt extract; food preparations of flour, starch, malt extract",
        "description_fr": "Extraits de malt; préparations alimentaires de farines, amidons, extraits de malt",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    "1903": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Tapioca and substitutes therefor",
        "description_fr": "Tapioca et ses succédanés",
        "rule_text_en": "Manufacture from material of any Heading except that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position sauf celle du produit"
    },
    
    # Chapter 20 - Fruit/vegetable preparations
    "2009": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Fruit juices and vegetable juices",
        "description_fr": "Jus de fruits et jus de légumes",
        "rule_text_en": "All vegetables, fruit, nuts or other parts of plants used must be wholly obtained",
        "rule_text_fr": "Tous les légumes, fruits, noix ou autres parties de plantes utilisés doivent être entièrement obtenus"
    },
    
    # Chapter 21
    "2101": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Extracts of coffee, tea, maté; preparations thereof",
        "description_fr": "Extraits de café, thé, maté; préparations à base de ces produits",
        "rule_text_en": "Manufacture in which Materials of Chapter 9 used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle les matières du chapitre 9 utilisées doivent être entièrement obtenues"
    },
    "2102": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Yeasts; baking powders",
        "description_fr": "Levures; poudres à lever",
        "rule_text_en": "Manufacture in which the value of all Materials does not exceed 60% of ex-works price",
        "rule_text_fr": "Fabrication dans laquelle la valeur de toutes les matières ne dépasse pas 60% du prix départ usine"
    },
    "2105": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Ice cream and other edible ice",
        "description_fr": "Glaces de consommation",
        "rule_text_en": "Manufacture in which Materials of Ch.2,4,7,8,17,18 used must be originating",
        "rule_text_fr": "Fabrication dans laquelle les matières des Ch.2,4,7,8,17,18 utilisées doivent être originaires"
    },
    
    # Chapter 22 - Beverages
    "2201": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Waters, natural/mineral/aerated; ice and snow",
        "description_fr": "Eaux, naturelles/minérales/gazeuses; glace et neige",
        "rule_text_en": "Manufacture in which all the Materials must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières doivent être entièrement obtenues"
    },
    "2204": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Wine of fresh grapes",
        "description_fr": "Vins de raisins frais",
        "rule_text_en": "Manufacture from any Heading except that of the Product; grapes and grape-derived materials must be wholly obtained",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit; raisins et matières dérivées du raisin entièrement obtenus"
    },
    "2207": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Ethyl alcohol (80% vol or higher)",
        "description_fr": "Alcool éthylique (80% vol ou plus)",
        "rule_text_en": "Manufacture from any Heading except that of Product; grapes, grape derivatives and Ch.17 materials wholly obtained",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit; raisins, dérivés et matières Ch.17 entièrement obtenus"
    },
    "2208": {
        "primary": "CTH", "alt": "WO", "max_non_orig": 0, "status": "AGREED",
        "description_en": "Undenatured ethyl alcohol <80%; spirits and liqueurs",
        "description_fr": "Alcool éthylique non dénaturé <80%; spiritueux et liqueurs",
        "rule_text_en": "Manufacture from any Heading except that of Product; grapes, grape derivatives and Ch.17 materials wholly obtained",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit; raisins, dérivés et matières Ch.17 entièrement obtenus"
    },
    
    # Chapter 23 - Animal feed
    "2301": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Flours, meals of meat, fish, crustaceans",
        "description_fr": "Farines de viandes, poissons, crustacés",
        "rule_text_en": "Max 60% non-originating for 3 years, then Ch.2,3,4,10,11,12,17 materials originating",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis matières Ch.2,3,4,10,11,12,17 originaires"
    },
    "2309": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Preparations for animal feeding",
        "description_fr": "Préparations pour alimentation animale",
        "rule_text_en": "Max 60% non-originating for 3 years, then Ch.2,3,4,10,11,12,17 materials originating",
        "rule_text_fr": "Max 60% non-originaire pendant 3 ans, puis matières Ch.2,3,4,10,11,12,17 originaires"
    },
    
    # Chapter 24 - Tobacco
    "2402": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Cigars, cigarettes",
        "description_fr": "Cigares, cigarettes",
        "rule_text_en": "Max 60% non-originating; max 30% weight from Heading 2401",
        "rule_text_fr": "Max 60% non-originaire; max 30% poids de la position 2401"
    },
    "2403": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Other manufactured tobacco",
        "description_fr": "Autres tabacs fabriqués",
        "rule_text_en": "Max 60% non-originating; max 30% weight from Heading 2401",
        "rule_text_fr": "Max 60% non-originaire; max 30% poids de la position 2401"
    },
    
    # Chapter 27 - Mineral fuels
    "2701": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Coal; briquettes",
        "description_fr": "Houille; briquettes",
        "rule_text_en": "Manufacture from any Heading except that of Product or max 60% non-originating",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit ou max 60% non-originaire"
    },
    "2709": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Petroleum oils, crude",
        "description_fr": "Huiles brutes de pétrole",
        "rule_text_en": "Manufacture in which all the Materials must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières doivent être entièrement obtenues"
    },
    "2710": {
        "primary": "SP", "alt": "VA50", "max_non_orig": 50, "status": "AGREED",
        "description_en": "Petroleum oils (excluding crude); preparations",
        "description_fr": "Huiles de pétrole (autres que brutes); préparations",
        "rule_text_en": "Operations of refining and/or specific process(es) or CTH or max 50% non-originating",
        "rule_text_fr": "Opérations de raffinage et/ou processus spécifique(s) ou CTH ou max 50% non-originaire"
    },
    "2716": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Electrical energy",
        "description_fr": "Énergie électrique",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 28 - Inorganic chemicals
    "2805": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Alkali/alkaline-earth metals; rare-earth metals; mercury",
        "description_fr": "Métaux alcalins/alcalino-terreux; terres rares; mercure",
        "rule_text_en": "Manufacture in which value of Materials does not exceed 60% of ex-works price",
        "rule_text_fr": "Fabrication dans laquelle la valeur des matières ne dépasse pas 60% du prix départ usine"
    },
    
    # Chapter 39 - Plastics
    "3915": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Waste, parings and scrap of plastics",
        "description_fr": "Déchets, rognures et débris de matières plastiques",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 40 - Rubber
    "4001": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Natural rubber, balata, gutta-percha",
        "description_fr": "Caoutchouc naturel, balata, gutta-percha",
        "rule_text_en": "Manufacture in which all the Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "4012": {
        "primary": "SP", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Retreaded or used pneumatic tyres",
        "description_fr": "Pneumatiques rechapés ou usagés",
        "rule_text_en": "Retreading of used tyres",
        "rule_text_fr": "Rechapage de pneus usagés"
    },
    
    # Chapter 41 - Raw hides, skins, leather
    "4104": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Tanned/crust hides of bovine/equine animals",
        "description_fr": "Cuirs et peaux tannés/en croûte de bovins/équidés",
        "rule_text_en": "Manufacture in which Materials of Headings 41.01 to 41.03 used are wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle les matières des positions 41.01 à 41.03 utilisées sont entièrement obtenues"
    },
    "4114": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Chamois leather; patent leather; metallised leather",
        "description_fr": "Cuirs chamoisés; cuirs vernis; cuirs métallisés",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # Chapter 56 - Wadding, felt
    "5601": {
        "primary": "CTH", "alt": "VA50", "max_non_orig": 50, "status": "AGREED",
        "description_en": "Wadding of textile materials",
        "description_fr": "Ouates de matières textiles",
        "rule_text_en": "Manufacture from any Heading other than Product or max 50% non-originating",
        "rule_text_fr": "Fabrication à partir de toute position autre que le produit ou max 50% non-originaire"
    },
    
    # Chapter 63 - Made-up textile articles
    "6307": {
        "primary": "VA50", "alt": None, "max_non_orig": 50, "status": "AGREED",
        "description_en": "Other made-up articles, including dress patterns",
        "description_fr": "Autres articles confectionnés, y compris patrons",
        "rule_text_en": "Manufacture in which value of Materials does not exceed 50% of ex-works price",
        "rule_text_fr": "Fabrication dans laquelle la valeur des matières ne dépasse pas 50% du prix départ usine"
    },
    "6308": {
        "primary": "SP", "alt": None, "max_non_orig": 15, "status": "AGREED",
        "description_en": "Sets for making rugs, tapestries, etc.",
        "description_fr": "Assortiments pour confection de tapis, tapisseries, etc.",
        "rule_text_en": "Each item must satisfy its own rule; max 15% non-originating articles in set",
        "rule_text_fr": "Chaque article doit satisfaire sa propre règle; max 15% d'articles non originaires dans l'assortiment"
    },
    
    # Chapter 64 - Footwear
    "6406": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Parts of footwear; gaiters; removable insoles",
        "description_fr": "Parties de chaussures; guêtres; semelles intérieures amovibles",
        "rule_text_en": "Manufacture from Materials of any Heading other than that of the Product",
        "rule_text_fr": "Fabrication à partir de matières de toute position autre que celle du produit"
    },
    
    # Chapter 68 - Articles of stone
    "6801": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Setts, curbstones, flagstones of natural stone",
        "description_fr": "Pavés, bordures, dalles en pierre naturelle",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "6802": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Worked monumental or building stone",
        "description_fr": "Pierres de taille ou de construction travaillées",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "6803": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Worked slate",
        "description_fr": "Ardoise travaillée",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 71 - Precious metals/stones
    "7101": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Natural or cultured pearls",
        "description_fr": "Perles fines ou de culture",
        "rule_text_en": "Manufacture in which Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "7102": {
        "primary": "SP", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Diamonds, whether or not worked",
        "description_fr": "Diamants, même travaillés",
        "rule_text_en": "Manufacture from unworked, precious or semi-precious stones",
        "rule_text_fr": "Fabrication à partir de pierres précieuses ou fines brutes"
    },
    "7103": {
        "primary": "SP", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Precious/semi-precious stones (excl. diamonds)",
        "description_fr": "Pierres précieuses/fines (hors diamants)",
        "rule_text_en": "Manufacture from unworked, precious or semi-precious stones",
        "rule_text_fr": "Fabrication à partir de pierres précieuses ou fines brutes"
    },
    "7106": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Silver (including gold-plated), unwrought/powder/semi-manufactured",
        "description_fr": "Argent (y compris doré), brut/poudre/mi-ouvré",
        "rule_text_en": "Manufacture in which all Materials of this Chapter used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières de ce chapitre utilisées doivent être entièrement obtenues"
    },
    "7108": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Gold (including platinum-plated), unwrought/semi-manufactured/powder",
        "description_fr": "Or (y compris platiné), brut/mi-ouvré/poudre",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    "7110": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Platinum, unwrought/semi-manufactured/powder",
        "description_fr": "Platine, brut/mi-ouvré/poudre",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 75 - Nickel
    "7502": {
        "primary": "WO", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Unwrought nickel",
        "description_fr": "Nickel brut",
        "rule_text_en": "Manufacture in which all Materials used must be wholly obtained",
        "rule_text_fr": "Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues"
    },
    
    # Chapter 82 - Tools, cutlery
    "8211": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Knives with cutting blades",
        "description_fr": "Couteaux à lame tranchante",
        "rule_text_en": "Manufacture from any Heading except that of Product. However, knife blades of base metal may be used",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit. Toutefois, les lames en métaux communs peuvent être utilisées"
    },
    "8213": {
        "primary": "CTH", "alt": None, "max_non_orig": 0, "status": "AGREED",
        "description_en": "Scissors, tailors' shears and blades therefor",
        "description_fr": "Ciseaux, cisailles de tailleurs et leurs lames",
        "rule_text_en": "Manufacture from Materials of any Heading",
        "rule_text_fr": "Fabrication à partir de matières de toute position"
    },
    
    # Chapter 85 - Electrical equipment
    "8506": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Primary cells and primary batteries",
        "description_fr": "Piles et batteries de piles électriques",
        "rule_text_en": "Manufacture from any Heading except that of Product or max 60% non-originating",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit ou max 60% non-originaire"
    },
    
    # Chapter 87 - Vehicles
    "8702": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Motor vehicles for 10+ persons",
        "description_fr": "Véhicules pour 10+ personnes",
        "rule_text_en": "Max 60% non-originating, subject to review after 5 years",
        "rule_text_fr": "Max 60% non-originaire, sous réserve de révision après 5 ans"
    },
    "8709": {
        "primary": "VA65", "alt": None, "max_non_orig": 65, "status": "AGREED",
        "description_en": "Works trucks; tractors for railway platforms",
        "description_fr": "Chariots de manutention; tracteurs de quai",
        "rule_text_en": "Max 65% non-originating, subject to review after 5 years",
        "rule_text_fr": "Max 65% non-originaire, sous réserve de révision après 5 ans"
    },
    "8714": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Parts and accessories of vehicles 87.11-87.13",
        "description_fr": "Parties et accessoires de véhicules 87.11-87.13",
        "rule_text_en": "Max 60% non-originating",
        "rule_text_fr": "Max 60% non-originaire"
    },
    "8715": {
        "primary": "VA60", "alt": None, "max_non_orig": 60, "status": "AGREED",
        "description_en": "Baby carriages and parts thereof",
        "description_fr": "Landaus et parties",
        "rule_text_en": "Max 60% non-originating",
        "rule_text_fr": "Max 60% non-originaire"
    },
    "8716": {
        "primary": "VA65", "alt": None, "max_non_orig": 65, "status": "AGREED",
        "description_en": "Trailers and semi-trailers",
        "description_fr": "Remorques et semi-remorques",
        "rule_text_en": "Max 65% non-originating",
        "rule_text_fr": "Max 65% non-originaire"
    },
    
    # Chapter 94 - Furniture
    "9403": {
        "primary": "CTH", "alt": "VA60", "max_non_orig": 60, "status": "AGREED",
        "description_en": "Other furniture and parts thereof",
        "description_fr": "Autres meubles et leurs parties",
        "rule_text_en": "Manufacture from any Heading except that of Product or max 60% non-originating",
        "rule_text_fr": "Fabrication à partir de toute position sauf celle du produit ou max 60% non-originaire"
    },
}

# ============================================================================
# HEADINGS YET TO BE AGREED (YTB)
# ============================================================================
YTB_HEADINGS = [
    "5111", "5112", "5113",  # Woven fabrics of wool
    "5204", "5205", "5206", "5207", "5208", "5209", "5210", "5211", "5212",  # Cotton
    "5309",  # Woven fabrics of flax
    "5407", "5408",  # Woven fabrics of man-made filaments
    "5512", "5513", "5514", "5515", "5516",  # Woven fabrics of man-made staple fibres
    "5801", "5802", "5803", "5804", "5806", "5810",  # Special woven fabrics
    "6001", "6002", "6003", "6004", "6005", "6006",  # Knitted fabrics
    "6301", "6302", "6303", "6304", "6305", "6306",  # Made-up textile articles
    "8701", "8703", "8704", "8705", "8706", "8707", "8708", "8710", "8711", "8712",  # Vehicles
]


def get_chapter_rule(chapter: str, lang: str = "fr") -> dict:
    """Get default rule for a chapter"""
    chapter = chapter.zfill(2)
    if chapter in CHAPTER_RULES:
        rule = CHAPTER_RULES[chapter]
        desc_key = f"description_{lang}"
        rule_text_key = f"rule_text_{lang}"
        return {
            "primary_code": rule["primary"],
            "primary_name": ORIGIN_TYPES.get(rule["primary"], {}).get(lang, rule["primary"]),
            "alt_code": rule.get("alt"),
            "alt_name": ORIGIN_TYPES.get(rule.get("alt"), {}).get(lang, "") if rule.get("alt") else None,
            "max_non_originating": rule.get("max_non_orig", 0),
            "status": rule.get("status", "AGREED"),
            "description": rule.get(desc_key, ""),
            "rule_text": rule.get(rule_text_key, "")
        }
    return None


def get_heading_rule(heading: str, lang: str = "fr") -> dict:
    """Get rule for a specific heading (4 digits)"""
    heading = heading.replace(".", "")[:4]
    if heading in HEADING_RULES:
        rule = HEADING_RULES[heading]
        desc_key = f"description_{lang}"
        rule_text_key = f"rule_text_{lang}"
        return {
            "heading": heading,
            "primary_code": rule["primary"],
            "primary_name": ORIGIN_TYPES.get(rule["primary"], {}).get(lang, rule["primary"]),
            "alt_code": rule.get("alt"),
            "alt_name": ORIGIN_TYPES.get(rule.get("alt"), {}).get(lang, "") if rule.get("alt") else None,
            "max_non_originating": rule.get("max_non_orig", 0),
            "status": rule.get("status", "AGREED"),
            "description": rule.get(desc_key, ""),
            "rule_text": rule.get(rule_text_key, "")
        }
    return None


def is_ytb(hs_code: str) -> bool:
    """Check if a heading is yet to be agreed"""
    heading = hs_code.replace(".", "")[:4]
    return heading in YTB_HEADINGS


def get_rule_of_origin(hs_code: str, lang: str = "fr") -> dict:
    """
    Get rules of origin for an HS code.
    
    Priority order:
    1. Heading-specific rule (4-digit)
    2. Chapter-level rule (2-digit)
    
    Returns a complete rule structure with all metadata.
    """
    hs_clean = hs_code.replace(".", "").replace(" ", "")
    hs6 = hs_clean[:6].ljust(6, '0') if len(hs_clean) >= 6 else hs_clean.ljust(6, '0')
    heading = hs_clean[:4]
    chapter = hs_clean[:2].zfill(2)
    
    # Check if heading is yet to be agreed
    if is_ytb(hs_code):
        return {
            "hs6_code": hs6,
            "heading": heading,
            "chapter": chapter,
            "status": "YTB",
            "primary_rule": {
                "code": "YTB",
                "type": "YTB",
                "name": "En cours de négociation" if lang == "fr" else "Yet to be agreed",
                "description": "Les règles pour ce produit sont encore en négociation" if lang == "fr" else "Rules for this product are still under negotiation"
            },
            "alternative_rule": None,
            "regional_content": 40,  # Default minimum
            "notes": "Les négociations sont en cours pour établir les règles d'origine spécifiques à ce produit. Les règles génériques du chapitre peuvent s'appliquer en attendant." if lang == "fr" else "Negotiations are ongoing to establish product-specific rules of origin. Chapter-level generic rules may apply in the interim.",
            "source": "CHAPTER_FALLBACK",
            "source_detail": "AfCFTA Annex II Appendix IV - Heading under negotiation"
        }
    
    # Try heading-specific rule first
    heading_rule = get_heading_rule(heading, lang)
    if heading_rule:
        primary_code = heading_rule["primary_code"]
        alt_code = heading_rule.get("alt_code")
        max_non_orig = heading_rule.get("max_non_originating", 0)
        
        # Calculate regional content (inverse of max non-originating)
        # For Wholly Obtained (max_non_orig = 0), regional content is 100%
        regional_content = 100 - max_non_orig
        
        return {
            "hs6_code": hs6,
            "heading": heading,
            "chapter": chapter,
            "chapter_description": CHAPTER_RULES.get(chapter, {}).get(f"description_{lang}", ""),
            "status": heading_rule.get("status", "AGREED"),
            "primary_rule": {
                "code": primary_code,
                "type": primary_code,
                "name": heading_rule["primary_name"],
                "description": heading_rule.get("rule_text", heading_rule["primary_name"])
            },
            "alternative_rule": {
                "code": alt_code,
                "type": alt_code,
                "name": heading_rule["alt_name"],
                "description": ORIGIN_TYPES.get(alt_code, {}).get(lang, alt_code) if alt_code else None
            } if alt_code else None,
            "regional_content": regional_content,
            "notes": heading_rule.get("description", ""),
            "source": "HEADING",
            "source_detail": f"AfCFTA Annex II Appendix IV - Heading {heading}"
        }
    
    # Fall back to chapter rule
    chapter_rule = get_chapter_rule(chapter, lang)
    if chapter_rule:
        primary_code = chapter_rule["primary_code"]
        alt_code = chapter_rule.get("alt_code")
        max_non_orig = chapter_rule.get("max_non_originating", 0)
        
        # For Wholly Obtained (max_non_orig = 0), regional content is 100%
        regional_content = 100 - max_non_orig
        
        return {
            "hs6_code": hs6,
            "heading": heading,
            "chapter": chapter,
            "chapter_description": chapter_rule.get("description", ""),
            "status": chapter_rule.get("status", "AGREED"),
            "primary_rule": {
                "code": primary_code,
                "type": primary_code,
                "name": chapter_rule["primary_name"],
                "description": chapter_rule.get("rule_text", chapter_rule["primary_name"])
            },
            "alternative_rule": {
                "code": alt_code,
                "type": alt_code,
                "name": chapter_rule["alt_name"],
                "description": ORIGIN_TYPES.get(alt_code, {}).get(lang, alt_code) if alt_code else None
            } if alt_code else None,
            "regional_content": regional_content,
            "notes": "",
            "source": "CHAPTER",
            "source_detail": f"AfCFTA Annex II Appendix IV - Chapter {chapter}"
        }
    
    # No rule found
    return {
        "hs6_code": hs6,
        "heading": heading,
        "chapter": chapter,
        "status": "UNKNOWN",
        "primary_rule": None,
        "alternative_rule": None,
        "regional_content": 40,
        "notes": "Règles d'origine non définies pour ce code" if lang == "fr" else "Rules of origin not defined for this code",
        "source": "UNKNOWN",
        "source_detail": "No applicable rule found"
    }


def get_rule_summary(hs_code: str, lang: str = "fr") -> str:
    """Get a human-readable summary of the rule of origin for an HS code"""
    rule = get_rule_of_origin(hs_code, lang)
    
    if rule["status"] == "YTB":
        return "En cours de négociation" if lang == "fr" else "Yet to be agreed"
    
    if rule["status"] == "UNKNOWN":
        return rule["notes"]
    
    primary = rule.get("primary_rule", {})
    alt = rule.get("alternative_rule")
    regional = rule.get("regional_content", 40)
    
    if lang == "fr":
        summary = f"{primary.get('name', 'N/A')}"
        if alt:
            summary += f" OU {alt.get('name', '')}"
        if regional > 0 and regional < 100:
            summary += f" (min. {regional}% contenu régional)"
        return summary
    else:
        summary = f"{primary.get('name', 'N/A')}"
        if alt:
            summary += f" OR {alt.get('name', '')}"
        if regional > 0 and regional < 100:
            summary += f" (min. {regional}% regional content)"
        return summary


# Compatibility function for existing imports
def get_chapter_status_summary(chapter: str, lang: str = "fr") -> str:
    """Get a summary of the rule status for a chapter"""
    rule = get_chapter_rule(chapter, lang)
    if not rule:
        return "Non défini" if lang == "fr" else "Not defined"
    
    status = rule.get("status", "UNKNOWN")
    if status == "AGREED":
        return "Convenu" if lang == "fr" else "Agreed"
    elif status == "PARTIAL":
        return "Partiellement convenu" if lang == "fr" else "Partially agreed"
    elif status == "YTB":
        return "En négociation" if lang == "fr" else "Under negotiation"
    return status


# Statistics
def get_rules_statistics() -> dict:
    """Get statistics about the rules of origin database"""
    agreed_chapters = sum(1 for r in CHAPTER_RULES.values() if r.get("status") == "AGREED")
    partial_chapters = sum(1 for r in CHAPTER_RULES.values() if r.get("status") == "PARTIAL")
    ytb_chapters = sum(1 for r in CHAPTER_RULES.values() if r.get("status") == "YTB")
    
    return {
        "total_chapters": len(CHAPTER_RULES),
        "agreed_chapters": agreed_chapters,
        "partial_chapters": partial_chapters,
        "ytb_chapters": ytb_chapters,
        "heading_rules": len(HEADING_RULES),
        "ytb_headings": len(YTB_HEADINGS),
        "source": "AfCFTA Annex II, Appendix IV (COM-12, December 2023)",
        "last_updated": "2023-12"
    }
