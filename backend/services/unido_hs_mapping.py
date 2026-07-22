"""
UNIDO ISIC (Rev.4) -> HS product mapping
========================================

Ce module matérialise la correspondance entre les **divisions manufacturières
ISIC Rev.4** (celles portées par les données UNIDO INDSTAT4 du module
production) et les **produits SH (positions SH4, sous-positions SH6)
susceptibles d'être produits** dans chaque division.

Pourquoi ce module existe
-------------------------
Les données UNIDO ne donnent qu'une *valeur ajoutée par division ISIC* (ex.
« 23 — Manufacture of other non-metallic mineral products : 2,68 Md$ »). Cette
capacité manufacturière avérée doit être traduite en **produits échangeables**
(ciment 2523, carreaux/faïence 6907/6908, verre 7010…) pour pouvoir :
  1) croiser la capacité de production d'un pays avec la demande d'import
     africaine (index OEC) et
  2) faire émerger des opportunités d'export « pilotées par la capacité »
     — même quand le flux d'export actuel est encore modeste.

Aucune correspondance ISIC->SH n'existait dans le code : seules deux tables
inverses (SH->libellé) vivaient dans ``production_capacity_service``. Ce module
fournit la correspondance *directe* manquante, à la maille SH4 (précise et
lisible), alignée sur la table officielle des Nations Unies « Correspondence
between commodity codes (HS) and ISIC Rev.4 ».

Source de la correspondance
---------------------------
UNSD — ISIC Rev.4 structure & « Correspondence between commodity codes and
HS 2002/2007 and ISIC Rev.4 » (https://unstats.un.org/unsd/classifications).
Les positions retenues sont les principaux extrants *exportables* de chaque
division (biens finis/intermédiaires échangeables), pas l'exhaustivité de la
nomenclature.

Structure
---------
``ISIC_HS`` : ``Dict[str, Dict]`` indexé par code ISIC Rev.4 à 2 chiffres ::

    {
      "23": {
        "isic_label_en": "Manufacture of other non-metallic mineral products",
        "isic_label_fr": "Autres produits minéraux non métalliques",
        "input": "minéraux non métalliques (calcaire, argile, silice, feldspath)",
        "process": "cuisson / calcination / fusion verrière",
        "hs4": {
          "2523": "Ciment (y compris clinker)",
          "6907": "Carreaux céramiques",
          "6908": "Carreaux céramiques vernissés (faïence)",
          ...
        },
      },
      ...
    }

Seules les divisions manufacturières (section ISIC « C ») sont couvertes.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional


def _norm(hs_code: Optional[str]) -> str:
    """Ne conserver que les chiffres d'un code SH."""
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


# --------------------------------------------------------------------------- #
# Correspondance ISIC Rev.4 (division) -> produits SH4 exportables.
#
# `input`/`process` décrivent la chaîne de transformation type de la division,
# réutilisés pour narrer la « stratégie de transformation industrielle » d'une
# opportunité découverte (intrant -> procédé -> extrant).
# --------------------------------------------------------------------------- #
ISIC_HS: Dict[str, Dict] = {
    "10": {
        "isic_label_en": "Manufacture of food products",
        "isic_label_fr": "Produits alimentaires",
        "input": "matières premières agricoles (céréales, oléagineux, lait, viande, poisson, sucre brut)",
        "process": "transformation agroalimentaire (mouture, raffinage, conserverie, trituration)",
        "hs4": {
            "0402": "Lait concentré / en poudre",
            "0406": "Fromages",
            "1101": "Farine de froment",
            "1507": "Huile de soja",
            "1511": "Huile de palme",
            "1512": "Huile de tournesol",
            "1517": "Margarine & matières grasses préparées",
            "1601": "Saucisses & préparations de viande",
            "1604": "Préparations & conserves de poisson",
            "1701": "Sucre de canne ou de betterave",
            "1704": "Sucreries sans cacao",
            "1806": "Chocolat & préparations au cacao",
            "1902": "Pâtes alimentaires",
            "1905": "Produits de boulangerie & biscuiterie",
            "2005": "Légumes préparés/conservés",
            "2009": "Jus de fruits & légumes",
            "2101": "Extraits de café/thé",
            "2103": "Sauces & condiments",
            "2106": "Préparations alimentaires diverses",
            "2304": "Tourteaux de soja (alimentation animale)",
            "2309": "Préparations pour animaux",
        },
    },
    "11": {
        "isic_label_en": "Manufacture of beverages",
        "isic_label_fr": "Boissons",
        "input": "eau, concentrés, malt, sucre, fruits",
        "process": "embouteillage, brassage, fermentation, distillation",
        "hs4": {
            "2201": "Eaux minérales",
            "2202": "Boissons non alcoolisées (sodas, jus)",
            "2203": "Bières de malt",
            "2204": "Vins",
            "2208": "Spiritueux & liqueurs",
        },
    },
    "12": {
        "isic_label_en": "Manufacture of tobacco products",
        "isic_label_fr": "Produits du tabac",
        "input": "tabac brut",
        "process": "séchage, mélange, confection",
        "hs4": {
            "2402": "Cigares & cigarettes",
            "2403": "Autres tabacs manufacturés",
        },
    },
    "13": {
        "isic_label_en": "Manufacture of textiles",
        "isic_label_fr": "Textiles",
        "input": "coton, laine, fibres synthétiques",
        "process": "filature, tissage, ennoblissement",
        "hs4": {
            "5205": "Fils de coton",
            "5208": "Tissus de coton",
            "5209": "Tissus de coton (lourds)",
            "5407": "Tissus de filaments synthétiques",
            "5513": "Tissus de fibres synthétiques",
            "5701": "Tapis à points noués",
            "5703": "Tapis touffetés",
            "6302": "Linge de lit/table/toilette",
            "6305": "Sacs d'emballage",
        },
    },
    "14": {
        "isic_label_en": "Manufacture of wearing apparel",
        "isic_label_fr": "Articles d'habillement",
        "input": "tissus & fils (chapitres 50-60)",
        "process": "confection (coupe, assemblage, finition)",
        "hs4": {
            "6109": "T-shirts & maillots en bonneterie",
            "6110": "Chandails & pull-overs",
            "6203": "Costumes/ensembles homme",
            "6204": "Costumes/ensembles femme",
            "6205": "Chemises homme",
            "6206": "Chemisiers femme",
            "6211": "Survêtements & vêtements de sport",
            "6212": "Soutiens-gorge & corsetterie",
        },
    },
    "16": {
        "isic_label_en": "Manufacture of wood and wood products",
        "isic_label_fr": "Bois & articles en bois",
        "input": "grumes & bois brut",
        "process": "sciage, tranchage, panneautage, menuiserie",
        "hs4": {
            "4407": "Bois sciés",
            "4408": "Feuilles de placage",
            "4410": "Panneaux de particules",
            "4411": "Panneaux de fibres (MDF)",
            "4412": "Contreplaqués",
            "4418": "Ouvrages de menuiserie",
        },
    },
    "17": {
        "isic_label_en": "Manufacture of paper and paper products",
        "isic_label_fr": "Papier & articles en papier",
        "input": "pâte à papier, papier de récupération",
        "process": "formage, couchage, transformation",
        "hs4": {
            "4802": "Papiers d'écriture/impression",
            "4804": "Papiers kraft",
            "4810": "Papiers couchés",
            "4818": "Papiers domestiques (hygiénique, mouchoirs)",
            "4819": "Cartonnages & boîtes",
        },
    },
    "19": {
        "isic_label_en": "Manufacture of coke and refined petroleum products",
        "isic_label_fr": "Cokéfaction & raffinage pétrolier",
        "input": "pétrole brut, gaz de champ",
        "process": "raffinage (distillation, craquage, reformage)",
        "hs4": {
            "2710": "Produits pétroliers raffinés (essence, gazole, kérosène)",
            "2711": "Gaz de pétrole (GPL) & hydrocarbures gazeux",
            "2713": "Coke de pétrole & bitume de pétrole",
            "2715": "Mélanges bitumineux",
        },
    },
    "20": {
        "isic_label_en": "Manufacture of chemicals and chemical products",
        "isic_label_fr": "Produits chimiques",
        "input": "gaz naturel, phosphates, sel, intermédiaires chimiques",
        "process": "synthèse & formulation chimique",
        "hs4": {
            "2814": "Ammoniac",
            "2815": "Soude caustique",
            "3102": "Engrais azotés (urée, nitrate d'ammonium)",
            "3103": "Engrais phosphatés",
            "3105": "Engrais composés (NPK)",
            "3204": "Colorants & pigments de synthèse",
            "3208": "Peintures & vernis (base non aqueuse)",
            "3209": "Peintures & vernis (base aqueuse)",
            "3401": "Savons",
            "3402": "Agents de surface & détergents",
            "3808": "Insecticides & pesticides",
            "3814": "Solvants & diluants",
            "3901": "Polymères d'éthylène (PE)",
            "3902": "Polymères de propylène (PP)",
        },
    },
    "21": {
        "isic_label_en": "Manufacture of pharmaceuticals",
        "isic_label_fr": "Produits pharmaceutiques",
        "input": "principes actifs (API), excipients",
        "process": "formulation & conditionnement pharmaceutique",
        "hs4": {
            "3002": "Vaccins, sang & produits immunologiques",
            "3003": "Médicaments (en vrac)",
            "3004": "Médicaments (conditionnés pour la vente)",
            "3006": "Préparations pharmaceutiques diverses",
        },
    },
    "22": {
        "isic_label_en": "Manufacture of rubber and plastics products",
        "isic_label_fr": "Caoutchouc & plastiques",
        "input": "polymères de base, caoutchouc naturel/synthétique",
        "process": "extrusion, moulage, injection, vulcanisation",
        "hs4": {
            "3917": "Tubes & tuyaux plastiques",
            "3920": "Plaques & films plastiques",
            "3923": "Emballages plastiques",
            "3924": "Articles ménagers plastiques",
            "3926": "Ouvrages divers en plastique",
            "4011": "Pneumatiques neufs",
            "4016": "Ouvrages en caoutchouc vulcanisé",
        },
    },
    "23": {
        "isic_label_en": "Manufacture of other non-metallic mineral products",
        "isic_label_fr": "Autres produits minéraux non métalliques",
        "input": "minéraux non métalliques (calcaire, argile, silice, feldspath)",
        "process": "cuisson / calcination / fusion verrière",
        "hs4": {
            "2523": "Ciment (y compris clinker)",
            "6802": "Pierres de taille travaillées (marbre, granit)",
            "6810": "Ouvrages en ciment/béton",
            "6907": "Carreaux céramiques",
            "6908": "Carreaux céramiques vernissés (faïence)",
            "6910": "Appareils sanitaires en céramique",
            "6911": "Vaisselle en porcelaine",
            "7010": "Bouteilles & bocaux en verre",
            "7013": "Verrerie de table & de ménage",
            "7019": "Fibres de verre",
        },
    },
    "24": {
        "isic_label_en": "Manufacture of basic metals",
        "isic_label_fr": "Métallurgie de base",
        "input": "minerais, ferrailles, demi-produits métalliques",
        "process": "réduction, fusion, laminage, tréfilage",
        "hs4": {
            "7201": "Fontes brutes",
            "7202": "Ferro-alliages",
            "7207": "Demi-produits en fer/acier",
            "7208": "Produits plats laminés (à chaud)",
            "7210": "Produits plats revêtus",
            "7213": "Fil machine en fer/acier",
            "7214": "Barres en fer/acier",
            "7216": "Profilés en fer/acier",
            "7217": "Fils en fer/acier",
            "7402": "Cuivre non affiné",
            "7403": "Cuivre affiné",
            "7601": "Aluminium brut",
            "7604": "Profilés en aluminium",
            "7606": "Tôles & bandes en aluminium",
        },
    },
    "25": {
        "isic_label_en": "Manufacture of fabricated metal products",
        "isic_label_fr": "Produits métalliques fabriqués",
        "input": "produits sidérurgiques (tôles, barres, profilés)",
        "process": "façonnage, soudure, traitement de surface",
        "hs4": {
            "7301": "Palplanches & profilés soudés",
            "7304": "Tubes sans soudure",
            "7306": "Autres tubes en fer/acier",
            "7308": "Constructions métalliques",
            "7310": "Réservoirs & fûts métalliques",
            "7318": "Boulonnerie & visserie",
            "8207": "Outils interchangeables",
            "8215": "Coutellerie de table",
        },
    },
    "26": {
        "isic_label_en": "Manufacture of computer, electronic and optical products",
        "isic_label_fr": "Produits informatiques, électroniques & optiques",
        "input": "composants électroniques, cartes (PCBA), kits SKD/CKD",
        "process": "assemblage électronique (CMS, intégration, test)",
        "hs4": {
            "8471": "Machines de traitement de l'information (ordinateurs)",
            "8517": "Téléphones & appareils de télécommunication",
            "8528": "Récepteurs de télévision & moniteurs",
            "8541": "Semi-conducteurs & cellules photovoltaïques",
            "8542": "Circuits intégrés",
            "9018": "Instruments médicaux",
            "9027": "Instruments d'analyse",
        },
    },
    "27": {
        "isic_label_en": "Manufacture of electrical equipment",
        "isic_label_fr": "Équipements électriques",
        "input": "cuivre, aluminium, composants électriques, kits",
        "process": "bobinage, assemblage électrotechnique",
        "hs4": {
            "8501": "Moteurs & génératrices électriques",
            "8504": "Transformateurs & convertisseurs",
            "8506": "Piles & batteries primaires",
            "8507": "Accumulateurs électriques",
            "8536": "Appareillage de connexion (< 1000 V)",
            "8539": "Lampes & tubes électriques",
            "8544": "Fils & câbles isolés",
        },
    },
    "28": {
        "isic_label_en": "Manufacture of machinery and equipment n.e.c.",
        "isic_label_fr": "Machines & équipements n.c.a.",
        "input": "aciers, composants mécaniques, moteurs",
        "process": "usinage & assemblage mécanique",
        "hs4": {
            "8413": "Pompes pour liquides",
            "8418": "Réfrigérateurs & congélateurs",
            "8419": "Appareils à traitement thermique",
            "8422": "Machines à laver/emballer",
            "8450": "Machines à laver le linge",
            "8481": "Robinetterie & vannes",
        },
    },
    "29": {
        "isic_label_en": "Manufacture of motor vehicles, trailers and semi-trailers",
        "isic_label_fr": "Véhicules automobiles & remorques",
        "input": "kits CKD/SKD, tôles, composants automobiles",
        "process": "assemblage automobile (emboutissage, montage)",
        "hs4": {
            "8702": "Véhicules de transport en commun (bus)",
            "8703": "Voitures particulières",
            "8704": "Véhicules de transport de marchandises",
            "8708": "Pièces & accessoires automobiles",
            "8716": "Remorques & semi-remorques",
        },
    },
    "30": {
        "isic_label_en": "Manufacture of other transport equipment",
        "isic_label_fr": "Autres matériels de transport",
        "input": "aciers, aluminium, composants",
        "process": "assemblage de matériels de transport",
        "hs4": {
            "8711": "Motocycles",
            "8712": "Bicyclettes",
            "8901": "Navires de transport",
            "8904": "Remorqueurs",
        },
    },
    "31": {
        "isic_label_en": "Manufacture of furniture",
        "isic_label_fr": "Meubles",
        "input": "bois, panneaux, métal, mousse",
        "process": "menuiserie & assemblage d'ameublement",
        "hs4": {
            "9401": "Sièges",
            "9403": "Autres meubles",
        },
    },
    "32": {
        "isic_label_en": "Other manufacturing",
        "isic_label_fr": "Autres industries manufacturières",
        "input": "métaux précieux, pierres, matériaux divers",
        "process": "taille, sertissage, façonnage",
        "hs4": {
            "7102": "Diamants",
            "7103": "Pierres gemmes",
            "7113": "Articles de bijouterie",
            "9403": "Meubles",
        },
    },
}


# --------------------------------------------------------------------------- #
# Intrant PRÉCIS par produit final (SH4).
#
# Le champ ``input`` de ``ISIC_HS`` décrit l'intrant type de TOUTE la division
# ISIC — trop générique pour une carte de flux (« matières premières agricoles
# (céréales, oléagineux, lait, viande, poisson, sucre brut) » s'affichait à
# l'identique pour le sucre, la farine, le lait…). Cette table nomme, produit
# final par produit final, la matière première réellement en amont — ce que
# l'utilisateur doit lire sur la carte (« Sucre raffiné ← sucre brut de canne/
# betterave », « Farine ← blé », « Acier plat ← brames/ferrailles »).
#
# Repli : un SH4 absent de cette table retombe sur l'intrant de division.
# --------------------------------------------------------------------------- #
HS4_INPUT: Dict[str, str] = {
    # 10 — Produits alimentaires
    "0402": "lait cru",
    "0406": "lait cru",
    "1101": "blé (froment)",
    "1507": "graines de soja",
    "1511": "régimes de palmier à huile",
    "1512": "graines de tournesol",
    "1517": "huiles végétales brutes",
    "1601": "viande fraîche",
    "1604": "poisson frais",
    "1701": "sucre brut de canne / betterave",
    "1704": "sucre raffiné, sirop de glucose",
    "1806": "pâte & beurre de cacao, sucre",
    "1902": "semoule de blé dur",
    "1905": "farine de blé, sucre",
    "2005": "légumes frais",
    "2009": "fruits & concentrés",
    "2101": "café vert, thé",
    "2103": "tomates, épices, vinaigre",
    "2106": "ingrédients alimentaires transformés",
    "2304": "graines de soja",
    "2309": "céréales, tourteaux, additifs",
    # 11 — Boissons
    "2201": "eau de source, gaz carbonique",
    "2202": "eau, sucre, concentrés",
    "2203": "malt d'orge, houblon",
    "2204": "raisin / moût",
    "2208": "alcool, plantes aromatiques",
    # 12 — Tabac
    "2402": "tabac brut",
    "2403": "tabac brut",
    # 13 — Textiles
    "5205": "coton fibre",
    "5208": "fils de coton",
    "5209": "fils de coton",
    "5407": "filaments synthétiques",
    "5513": "fibres synthétiques",
    "5701": "laine, fils",
    "5703": "fils synthétiques",
    "6302": "tissus de coton",
    "6305": "polypropylène tissé / jute",
    # 14 — Habillement
    "6109": "bonneterie de coton",
    "6110": "fils de laine / coton",
    "6203": "tissus",
    "6204": "tissus",
    "6205": "tissus de coton",
    "6206": "tissus",
    "6211": "bonneterie",
    "6212": "tissus élastiques",
    # 16 — Bois
    "4407": "grumes",
    "4408": "grumes",
    "4410": "copeaux / bois de trituration",
    "4411": "fibres de bois",
    "4412": "grumes / placages",
    "4418": "bois sciés",
    # 17 — Papier
    "4802": "pâte à papier",
    "4804": "pâte kraft",
    "4810": "pâte à papier, pigments",
    "4818": "pâte / papier recyclé",
    "4819": "carton / papier recyclé",
    # 19 — Raffinage pétrolier
    "2710": "pétrole brut",
    "2711": "gaz de champ / pétrole brut",
    "2713": "résidus de raffinage",
    "2715": "résidus de distillation",
    # 20 — Chimie
    "2814": "gaz naturel",
    "2815": "sel, électricité",
    "3102": "ammoniac, gaz naturel",
    "3103": "phosphates, acide sulfurique",
    "3105": "azote, phosphate, potasse",
    "3204": "intermédiaires chimiques",
    "3208": "résines, solvants, pigments",
    "3209": "résines, pigments, eau",
    "3401": "corps gras, soude",
    "3402": "agents de surface, alcalins",
    "3808": "matières actives, solvants",
    "3814": "hydrocarbures, alcools",
    "3901": "éthylène",
    "3902": "propylène",
    # 21 — Pharmacie
    "3002": "antigènes, milieux biologiques",
    "3003": "principes actifs (API)",
    "3004": "principes actifs (API), excipients",
    "3006": "principes actifs, dispositifs",
    # 22 — Caoutchouc & plastiques
    "3917": "polymères (PE/PP/PVC)",
    "3920": "polymères",
    "3923": "polymères",
    "3924": "polymères",
    "3926": "polymères",
    "4011": "caoutchouc, noir de carbone, câblés",
    "4016": "caoutchouc vulcanisé",
    # 23 — Minéraux non métalliques
    "2523": "calcaire, argile, gypse",
    "6802": "blocs de marbre / granit",
    "6810": "ciment, granulats",
    "6907": "argile, feldspath, kaolin",
    "6908": "argile, feldspath, émaux",
    "6910": "argile, kaolin",
    "6911": "kaolin, feldspath",
    "7010": "sable siliceux, soude, calcaire",
    "7013": "sable siliceux, soude",
    "7019": "sable siliceux, résines",
    # 24 — Métallurgie de base
    "7201": "minerai de fer, coke",
    "7202": "minerais métalliques, réducteurs",
    "7207": "fonte / ferrailles",
    "7208": "brames d'acier / ferrailles",
    "7210": "tôles laminées, zinc",
    "7213": "billettes d'acier",
    "7214": "billettes d'acier",
    "7216": "billettes d'acier",
    "7217": "fil machine",
    "7402": "concentrés de cuivre",
    "7403": "cuivre blister / cathodes",
    "7601": "alumine, électricité",
    "7604": "billettes d'aluminium",
    "7606": "plaques d'aluminium",
    # 25 — Produits métalliques fabriqués
    "7301": "profilés d'acier",
    "7304": "ronds / billettes d'acier",
    "7306": "bandes / tôles d'acier",
    "7308": "profilés, tôles",
    "7310": "tôles d'acier",
    "7318": "fil / barres d'acier",
    "8207": "aciers spéciaux, carbures",
    "8215": "acier inoxydable",
    # 26 — Électronique
    "8471": "composants, cartes (PCBA)",
    "8517": "composants, cartes, kits SKD/CKD",
    "8528": "dalles, cartes, kits SKD/CKD",
    "8541": "wafers de silicium",
    "8542": "wafers de silicium",
    "9018": "composants électroniques, plastiques",
    "9027": "composants, optiques",
    # 27 — Équipements électriques
    "8501": "cuivre, acier électrique",
    "8504": "cuivre, tôles magnétiques",
    "8506": "zinc, manganèse, lithium",
    "8507": "plomb / lithium, électrolytes",
    "8536": "cuivre, plastiques",
    "8539": "verre, filaments, gaz",
    "8544": "cuivre / aluminium, isolants",
    # 28 — Machines & équipements
    "8413": "acier, fonte, composants",
    "8418": "acier, compresseurs, plastiques",
    "8419": "acier, composants",
    "8422": "acier, moteurs, composants",
    "8450": "acier, moteurs, plastiques",
    "8481": "laiton, acier, fonte",
    # 29 — Véhicules automobiles
    "8702": "kits CKD/SKD, tôles, moteurs",
    "8703": "kits CKD/SKD, tôles, moteurs",
    "8704": "kits CKD/SKD, châssis, moteurs",
    "8708": "aciers, plastiques, composants",
    "8716": "profilés d'acier, essieux",
    # 30 — Autres matériels de transport
    "8711": "kits, moteurs, cadres",
    "8712": "tubes d'acier / aluminium, composants",
    "8901": "tôles d'acier, moteurs",
    "8904": "tôles d'acier, moteurs",
    # 31 — Meubles
    "9401": "bois, mousse, textile, métal",
    "9403": "bois, panneaux, métal",
    # 32 — Autres industries manufacturières
    "7102": "diamants bruts",
    "7103": "pierres brutes",
    "7113": "métaux précieux, pierres",
}


def input_for_hs4(hs_code: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Matière première PRÉCISE d'un produit SH4 (ex. 1701 -> « sucre brut »),
    avec repli sur l'intrant de division (``fallback``) si le SH4 n'est pas
    nommément couvert.
    """
    code = _norm(hs_code)
    if len(code) >= 4 and code[:4] in HS4_INPUT:
        return HS4_INPUT[code[:4]]
    return fallback


# --------------------------------------------------------------------------- #
# Index dérivés (mémoïsés) — construits une fois depuis ``ISIC_HS``.
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _hs4_to_isic() -> Dict[str, List[str]]:
    """SH4 -> liste des codes ISIC qui le produisent (souvent un seul)."""
    out: Dict[str, List[str]] = {}
    for isic, block in ISIC_HS.items():
        for hs4 in block.get("hs4", {}):
            out.setdefault(hs4, []).append(isic)
    return out


@lru_cache(maxsize=1)
def _hs2_to_isic() -> Dict[str, List[str]]:
    """Chapitre SH2 -> liste des codes ISIC (repli plus grossier que le SH4)."""
    out: Dict[str, List[str]] = {}
    for isic, block in ISIC_HS.items():
        seen = set()
        for hs4 in block.get("hs4", {}):
            ch = hs4[:2]
            if ch not in seen:
                seen.add(ch)
                out.setdefault(ch, []).append(isic)
    return out


def isic_codes() -> List[str]:
    """Liste des codes ISIC couverts par le mapping."""
    return list(ISIC_HS.keys())


def products_for_isic(isic_code: str) -> Dict[str, str]:
    """Produits SH4 (code -> libellé) susceptibles d'être produits par la division."""
    return dict(ISIC_HS.get(str(isic_code), {}).get("hs4", {}))


def hs4_codes_for_isic(isic_code: str) -> List[str]:
    """Positions SH4 exportables d'une division ISIC."""
    return list(ISIC_HS.get(str(isic_code), {}).get("hs4", {}).keys())


def transformation_for_isic(isic_code: str) -> Dict[str, Optional[str]]:
    """Chaîne de transformation type (intrant, procédé, libellés) d'une division."""
    block = ISIC_HS.get(str(isic_code), {})
    return {
        "input": block.get("input"),
        "process": block.get("process"),
        "isic_label_fr": block.get("isic_label_fr"),
        "isic_label_en": block.get("isic_label_en"),
    }


def isic_for_hs(hs_code: str) -> List[str]:
    """
    Codes ISIC susceptibles de produire un code SH donné.

    Match par SH4 exact d'abord (précis), repli par chapitre SH2 (plus large).
    Retourne ``[]`` si aucune division manufacturière ne couvre ce produit
    (ex. produit purement agricole/minier extractif).
    """
    code = _norm(hs_code)
    if len(code) >= 4:
        hit = _hs4_to_isic().get(code[:4])
        if hit:
            return list(hit)
    if len(code) >= 2:
        return list(_hs2_to_isic().get(code[:2], []))
    return []


def product_label(hs_code: str) -> Optional[str]:
    """Libellé SH4 du produit dans le mapping (ou None si non couvert)."""
    code = _norm(hs_code)
    if len(code) < 4:
        return None
    hs4 = code[:4]
    for block in ISIC_HS.values():
        label = block.get("hs4", {}).get(hs4)
        if label:
            return label
    return None
