"""
Classification ISIC Rev.4 - Niveau 4 chiffres (classes)
=========================================================
Source officielle: Nations Unies - UNSD, International Standard Industrial
Classification of All Economic Activities, Rev.4 (2008)
https://unstats.un.org/unsd/classifications/Econ/Structure/RevList/detail/1

Couvre la Section C (Manufacturing, divisions 10-33), niveau "class" (4 chiffres),
rattaché à chaque division 2 chiffres déjà utilisée par le module Production.

Ce fichier fournit la table de référence (code -> libellé) utilisée pour :
- désagréger les statistiques UNIDO INDSTAT4 (disponibles au niveau division/2
  chiffres dans etl/unido_data.py) vers un niveau classe/4 chiffres indicatif,
  en attendant l'intégration directe du jeu de données UNIDO INDSTAT4 4 chiffres ;
- afficher/filtrer les statistiques de production par code ISIC 4 chiffres
  dans le sous-module Manufacturing du module Production.
"""

from typing import Dict, List

# =============================================================================
# TABLE ISIC REV.4 - CLASSES (4 CHIFFRES) PAR DIVISION (2 CHIFFRES)
# Source: UNSD ISIC Rev.4 structure (Section C - Manufacturing)
# =============================================================================

ISIC4_CLASSES: Dict[str, Dict[str, str]] = {
    "10": {
        "1010": "Transformation et conservation de viande",
        "1020": "Transformation et conservation de poisson, crustacés et mollusques",
        "1030": "Transformation et conservation de fruits et légumes",
        "1040": "Fabrication d'huiles et graisses végétales et animales",
        "1050": "Fabrication de produits laitiers",
        "1061": "Travail des grains",
        "1062": "Fabrication d'amidons et de produits amylacés",
        "1071": "Fabrication de produits de boulangerie",
        "1072": "Fabrication de sucre",
        "1073": "Fabrication de cacao, chocolat et confiserie",
        "1074": "Fabrication de pâtes alimentaires",
        "1075": "Fabrication de plats préparés",
        "1079": "Fabrication d'autres produits alimentaires n.c.a.",
        "1080": "Fabrication d'aliments pour animaux",
    },
    "11": {
        "1101": "Distillation, rectification et mélange de spiritueux",
        "1102": "Fabrication de vins",
        "1103": "Fabrication de boissons à base de malt et de malt",
        "1104": "Fabrication de boissons non alcoolisées, eaux minérales",
    },
    "12": {
        "1200": "Fabrication de produits à base de tabac",
    },
    "13": {
        "1311": "Préparation et filature de fibres textiles",
        "1312": "Tissage",
        "1313": "Achèvement (ennoblissement) des textiles",
        "1391": "Fabrication d'étoffes à mailles",
        "1392": "Fabrication d'articles textiles confectionnés (sauf habillement)",
        "1393": "Fabrication de tapis",
        "1394": "Fabrication de ficelles, cordes et filets",
        "1399": "Fabrication d'autres textiles n.c.a.",
    },
    "14": {
        "1410": "Fabrication de vêtements, autres qu'en fourrure",
        "1420": "Fabrication d'articles en fourrure",
        "1430": "Fabrication d'articles en bonneterie",
    },
    "15": {
        "1511": "Tannage et apprêt du cuir, préparation et teinture des fourrures",
        "1512": "Fabrication d'articles de voyage, de maroquinerie et de sellerie",
        "1520": "Fabrication de chaussures",
    },
    "16": {
        "1610": "Sciage et rabotage du bois",
        "1621": "Fabrication de placage et panneaux de bois",
        "1622": "Fabrication de charpentes et menuiseries",
        "1623": "Fabrication d'emballages en bois",
        "1629": "Fabrication d'autres ouvrages en bois",
    },
    "17": {
        "1701": "Fabrication de pâte à papier, papier et carton",
        "1702": "Fabrication de papier et carton ondulés, d'emballages",
        "1709": "Fabrication d'autres articles en papier et carton",
    },
    "18": {
        "1811": "Imprimerie",
        "1812": "Activités de soutien à l'imprimerie",
        "1820": "Reproduction d'enregistrements",
    },
    "19": {
        "1910": "Fabrication de produits de cokéfaction",
        "1920": "Raffinage de produits pétroliers",
    },
    "20": {
        "2011": "Fabrication de produits chimiques de base",
        "2012": "Fabrication d'engrais et de composés azotés",
        "2013": "Fabrication de matières plastiques et caoutchouc synthétique",
        "2021": "Fabrication de pesticides et autres produits agrochimiques",
        "2022": "Fabrication de peintures, vernis et encres",
        "2023": "Fabrication de savons, détergents et produits d'entretien",
        "2029": "Fabrication d'autres produits chimiques n.c.a.",
        "2030": "Fabrication de fibres synthétiques ou artificielles",
    },
    "21": {
        "2100": "Fabrication de produits pharmaceutiques de base et préparations",
    },
    "22": {
        "2211": "Fabrication de pneumatiques et chambres à air",
        "2219": "Fabrication d'autres articles en caoutchouc",
        "2220": "Fabrication d'articles en matières plastiques",
    },
    "23": {
        "2310": "Fabrication de verre et d'articles en verre",
        "2391": "Fabrication de produits céramiques réfractaires",
        "2392": "Fabrication de matériaux de construction en argile",
        "2393": "Fabrication d'autres produits en porcelaine et céramique",
        "2394": "Fabrication de ciment, chaux et plâtre",
        "2395": "Fabrication d'ouvrages en béton, ciment et plâtre",
        "2396": "Taille et façonnage de la pierre",
        "2399": "Fabrication d'autres produits minéraux non métalliques n.c.a.",
    },
    "24": {
        "2410": "Sidérurgie",
        "2420": "Métallurgie des métaux précieux et non ferreux",
        "2431": "Fonderie de fer et d'acier",
        "2432": "Fonderie de métaux non ferreux",
    },
    "25": {
        "2511": "Fabrication d'éléments de charpente en métal",
        "2512": "Fabrication de réservoirs et citernes métalliques",
        "2513": "Fabrication de générateurs de vapeur",
        "2520": "Fabrication d'armes et de munitions",
        "2591": "Forge, emboutissage et estampage des métaux",
        "2592": "Traitement et revêtement des métaux",
        "2593": "Fabrication d'outillage et de quincaillerie",
        "2599": "Fabrication d'autres ouvrages en métaux n.c.a.",
    },
    "26": {
        "2610": "Fabrication de composants électroniques et cartes",
        "2620": "Fabrication d'ordinateurs et de matériel périphérique",
        "2630": "Fabrication de matériel de communication",
        "2640": "Fabrication de produits électroniques grand public",
        "2651": "Fabrication d'instruments de mesure et de navigation",
        "2652": "Fabrication de montres et horloges",
        "2660": "Fabrication d'équipement d'irradiation et électromédical",
        "2670": "Fabrication de matériel optique et photographique",
        "2680": "Fabrication de supports magnétiques et optiques",
    },
    "27": {
        "2710": "Fabrication de moteurs, génératrices et transformateurs électriques",
        "2720": "Fabrication de piles et accumulateurs électriques",
        "2731": "Fabrication de câbles de fibres optiques",
        "2732": "Fabrication d'autres fils et câbles électroniques",
        "2733": "Fabrication de matériel d'installation électrique",
        "2740": "Fabrication d'appareils d'éclairage électrique",
        "2750": "Fabrication d'appareils ménagers",
        "2790": "Fabrication d'autres matériels électriques n.c.a.",
    },
    "28": {
        "2811": "Fabrication de moteurs et turbines (sauf véhicules)",
        "2812": "Fabrication de matériel hydraulique et pneumatique",
        "2813": "Fabrication d'autres pompes, compresseurs et vannes",
        "2814": "Fabrication de roulements, engrenages et organes mécaniques",
        "2815": "Fabrication de fours et brûleurs industriels",
        "2816": "Fabrication de matériel de levage et de manutention",
        "2817": "Fabrication de machines et matériel de bureau",
        "2818": "Fabrication d'outillage électrique portatif",
        "2819": "Fabrication d'autres machines à usage général",
        "2821": "Fabrication de machines agricoles et forestières",
        "2822": "Fabrication de machines de formage des métaux",
        "2823": "Fabrication de machines pour métallurgie",
        "2824": "Fabrication de machines pour mines et carrières",
        "2825": "Fabrication de machines pour l'industrie alimentaire",
        "2826": "Fabrication de machines pour le textile",
        "2829": "Fabrication d'autres machines à usage spécifique",
    },
    "29": {
        "2910": "Construction de véhicules automobiles",
        "2920": "Fabrication de carrosseries et remorques",
        "2930": "Fabrication de pièces et accessoires pour véhicules",
    },
    "30": {
        "3011": "Construction navale",
        "3012": "Construction de bateaux de plaisance",
        "3020": "Construction de matériel ferroviaire",
        "3030": "Construction aéronautique et spatiale",
        "3040": "Construction de véhicules militaires de combat",
        "3091": "Fabrication de motocycles",
        "3092": "Fabrication de bicyclettes et véhicules pour invalides",
        "3099": "Fabrication d'autres matériels de transport n.c.a.",
    },
    "31": {
        "3100": "Fabrication de meubles",
    },
    "32": {
        "3211": "Fabrication d'articles de bijouterie et joaillerie",
        "3212": "Fabrication de bijouterie fantaisie (imitation)",
        "3220": "Fabrication d'instruments de musique",
        "3230": "Fabrication d'articles de sport",
        "3240": "Fabrication de jeux et jouets",
        "3250": "Fabrication de matériel médical et dentaire",
        "3290": "Autres activités manufacturières n.c.a.",
    },
    "33": {
        "3311": "Réparation d'ouvrages en métaux",
        "3312": "Réparation de machines",
        "3313": "Réparation de matériel électronique et optique",
        "3314": "Réparation de matériel électrique",
        "3315": "Réparation et maintenance de matériel de transport (hors véhicules)",
        "3319": "Réparation d'autres équipements",
        "3320": "Installation de machines et équipements industriels",
    },
}


def get_isic4_for_division(division_code: str) -> Dict[str, str]:
    """Retourne les classes ISIC 4 chiffres (code -> libellé) d'une division 2 chiffres."""
    return ISIC4_CLASSES.get(division_code, {})


def list_isic4_flat() -> List[Dict[str, str]]:
    """Liste plate de toutes les classes ISIC 4 chiffres avec leur division parente."""
    flat = []
    for division, classes in ISIC4_CLASSES.items():
        for code, label in classes.items():
            flat.append({"isic4": code, "isic2": division, "label": label})
    return flat
