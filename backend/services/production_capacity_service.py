"""
Production Capacity Service
===========================
Croise les opportunités commerciales (codes HS) du module Opportunités avec les
capacités de production réelles des organismes de premier plan :

  • FAO   (FAOSTAT)        — production agricole (tonnes)
  • USGS  (Mineral Commodity Summaries) — production minière & hydrocarbures (tonnes)
  • UNIDO (INDSTAT4)       — valeur ajoutée manufacturière (USD)
  • World Bank (WDI)       — valeur ajoutée sectorielle (% PIB)

Aucune donnée n'est extrapolée : les valeurs de production sont lues telles quelles
dans data/json/production_africaine.json (2021-2024, 54 pays). Les *scénarios*
d'intégration africaine sont des projections clairement étiquetées, calculées à
partir du CAGR réel observé et de l'écart au leader continental — jamais inventées.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

from production_data import load_production_data

# ── HS → commodité de production ────────────────────────────────────────────────
# Chaque entrée associe un préfixe HS (le plus spécifique l'emporte) au dataset et
# au libellé exact présent dans production_africaine.json. Le matching se fait par
# libellé (les codes commodité comportent des collisions dans la source).
#
# Format : (hs_prefix, dataset, commodity_label)
#   dataset ∈ {"agri", "mining", "manufacturing"}
HS_TO_COMMODITY: List[Tuple[str, str, str]] = [
    # ── Agriculture (FAO / FAOSTAT) ──
    ("0901", "agri", "Coffee"),
    ("0902", "agri", "Tea"),
    ("0905", "agri", "Vanilla"),
    ("0906", "agri", "Cinnamon"),
    ("0907", "agri", "Cloves"),
    ("1801", "agri", "Cocoa beans"),
    ("1802", "agri", "Cocoa beans"),
    ("1803", "agri", "Cocoa beans"),
    ("1804", "agri", "Cocoa beans"),
    ("1805", "agri", "Cocoa beans"),
    ("1806", "agri", "Cocoa beans"),
    ("1005", "agri", "Maize (corn)"),
    ("1006", "agri", "Rice"),
    ("1001", "agri", "Wheat"),
    ("1003", "agri", "Barley"),
    ("1007", "agri", "Sorghum"),
    ("1008", "agri", "Millet"),
    ("0714", "agri", "Cassava"),
    ("0803", "agri", "Plantain"),
    ("0801", "agri", "Cashew nuts"),
    ("0802", "agri", "Cashew nuts"),
    ("0805", "agri", "Citrus fruits"),
    ("0804", "agri", "Dates"),
    ("2401", "agri", "Tobacco"),
    ("0701", "agri", "Potatoes"),
    ("0713", "agri", "Cowpeas"),
    ("1202", "agri", "Groundnuts"),
    ("1207", "agri", "Sesame"),
    ("1212", "agri", "Sugarcane"),
    ("1701", "agri", "Sugarcane"),
    ("1511", "agri", "Oil palm"),
    ("1513", "agri", "Coconuts"),
    ("0709", "agri", "Olives"),
    ("1509", "agri", "Olives"),
    ("1510", "agri", "Olives"),
    ("4001", "agri", "Rubber"),
    ("3301", "agri", "Ylang-ylang"),
    # ── Agriculture : produits déjà présents dans les données FAOSTAT mais
    #    sans correspondance HS jusqu'ici (résolus désormais par le module
    #    Opportunités). Codes HS6 spécifiques d'abord (préfixe le plus long gagne).
    ("080390", "agri", "Bananas"),  # bananes (hors plantains 080310)
    ("080430", "agri", "Pineapples"),  # ananas (0804=dattes en repli)
    ("070310", "agri", "Onions"),  # oignons et échalotes
    ("0702", "agri", "Tomatoes"),  # tomates
    ("1201", "agri", "Soybeans"),  # fèves de soja
    ("1206", "agri", "Sunflower seed"),  # graines de tournesol
    ("071430", "agri", "Yam"),  # ignames
    ("071333", "agri", "Beans"),  # haricots (Phaseolus)
    ("5201", "agri", "Seed cotton"),  # coton (fibre) — proxy coton graine
    ("0603", "agri", "Cut flowers"),  # fleurs coupées
    ("130120", "agri", "Gum arabic"),  # gomme arabique
    ("0910", "agri", "Ginger"),  # gingembre/épices
    ("0708", "agri", "Beans"),  # légumineuses à cosse fraîches
    # ── Cultures ajoutées (importées au prochain build FAOSTAT ; HS spécifiques) ──
    ("080450", "agri", "Mangoes"),  # mangues, goyaves
    ("080440", "agri", "Avocados"),  # avocats
    ("0806", "agri", "Grapes"),  # raisins
    ("080711", "agri", "Watermelons"),  # pastèques
    ("080720", "agri", "Papayas"),  # papayes
    ("070320", "agri", "Garlic"),  # ail
    ("071420", "agri", "Sweet potatoes"),  # patates douces
    ("0704", "agri", "Cabbages"),  # choux
    ("070410", "agri", "Cauliflowers"),  # choux-fleurs et brocolis (12 pays)
    ("070610", "agri", "Carrots"),  # carottes
    ("070930", "agri", "Eggplants"),  # aubergines
    ("070960", "agri", "Chillies and peppers"),  # piments/poivrons frais (37 pays)
    ("070970", "agri", "Spinach"),  # épinards
    ("070999", "agri", "Okra"),  # gombo
    ("0707", "agri", "Cucumbers"),  # concombres
    ("0705", "agri", "Lettuce"),  # laitue
    ("080550", "agri", "Lemons and limes"),  # citrons et limes (sous-position de 0805)
    ("071340", "agri", "Lentils"),  # lentilles
    ("071320", "agri", "Chickpeas"),  # pois chiches
    ("071310", "agri", "Peas"),  # pois secs
    ("071360", "agri", "Pigeon peas"),  # pois d'Angole
    ("1205", "agri", "Rapeseed"),  # colza
    ("1204", "agri", "Linseed"),  # lin
    ("120799", "agri", "Shea nuts"),  # karité
    ("080270", "agri", "Kola nuts"),  # noix de kola
    ("0904", "agri", "Pepper"),  # poivre/piments
    ("080211", "agri", "Almonds"),  # amandes
    ("080810", "agri", "Apples"),  # pommes
    ("1004", "agri", "Oats"),  # avoine
    ("080510", "agri", "Oranges"),  # oranges (sous-position de 0805 Citrus)
    ("0401", "agri", "Cattle milk"),  # lait de vache
    ("0407", "agri", "Hen eggs"),  # œufs
    ("0201", "agri", "Cattle meat"),  # viande bovine
    ("0202", "agri", "Cattle meat"),
    ("0207", "agri", "Chicken meat"),  # viande de volaille
    # ── Industrie : positions HS4 spécifiques vers secteurs UNIDO ──
    ("2523", "manufacturing", "Manufacture of other non-metallic mineral products"),  # ciment
    ("3105", "manufacturing", "Manufacture of chemicals"),  # engrais composés
    ("3102", "manufacturing", "Manufacture of chemicals"),  # engrais azotés
    ("3103", "manufacturing", "Manufacture of chemicals"),  # engrais phosphatés
    # ── Industrie manufacturière : expansion des codes HS4 pour résolution fine ──
    # Plutôt que de tomber au niveau chapitre HS2 (qui retournerait le même besoin
    # pour tous les produits d'un chapitre), on capture maintenant des commodités
    # spécifiques à HS4. Cela améliore la résolution du mapping et prépare le terrain
    # pour des données de production plus granulaires. NOTE: Aujourd'hui, la plupart
    # des secteurs manufacturiers (pharma, chimie, électronique, etc.) ne disposent
    # que d'UNE seule valeur de production continentale par secteur UNIDO. L'amélioration
    # réelle du calcul L3 (suppression des doublons au sein d'un chapitre) nécessitera
    # une expansion des données production_africaine.json avec des commodity_label
    # distinctes par HS4, pas seulement une meilleure résolution du code.
    # Chimie & pharmaceutiques (HS28-34, 38)
    ("2801", "manufacturing", "Manufacture of chemicals"),  # éléments chimiques non métalliques
    ("2802", "manufacturing", "Manufacture of chemicals"),  # sulfure de carbone, phosphore blanc
    ("2804", "manufacturing", "Manufacture of chemicals"),  # hydrogène, gaz rares
    ("2807", "manufacturing", "Manufacture of chemicals"),  # acide sulfurique
    ("2808", "manufacturing", "Manufacture of chemicals"),  # acide nitrique
    ("2809", "manufacturing", "Manufacture of chemicals"),  # pentoxyde de phosphore
    ("2815", "manufacturing", "Manufacture of chemicals"),  # hydroxyde de sodium
    ("2825", "manufacturing", "Manufacture of chemicals"),  # chlore
    ("2901", "manufacturing", "Manufacture of chemicals"),  # hydrocarbures acycliques
    ("2902", "manufacturing", "Manufacture of chemicals"),  # hydrocarbures cycliques
    ("2905", "manufacturing", "Manufacture of chemicals"),  # alcools acycliques
    ("2915", "manufacturing", "Manufacture of chemicals"),  # acides gras
    ("2916", "manufacturing", "Manufacture of chemicals"),  # acides monocarboxyliques
    ("2930", "manufacturing", "Manufacture of chemicals"),  # composés organosulfurés
    ("3001", "manufacturing", "Produits pharmaceutiques"),  # principes pharmaceutiques
    ("3002", "manufacturing", "Produits pharmaceutiques"),  # antisérum et vaccins
    ("3003", "manufacturing", "Produits pharmaceutiques"),  # médicaments dosés
    ("3004", "manufacturing", "Produits pharmaceutiques"),  # médicaments non dosés
    ("3201", "manufacturing", "Manufacture of chemicals"),  # matières tannantes
    ("3301", "manufacturing", "Manufacture of chemicals"),  # huiles essentielles
    ("3401", "manufacturing", "Manufacture of chemicals"),  # savons et détergents
    # Caoutchouc & plastiques (HS39-40)
    ("3901", "manufacturing", "Caoutchouc et plastiques"),  # polymères linéaires d'éthylène
    ("3902", "manufacturing", "Caoutchouc et plastiques"),  # polymères de propylène
    ("3903", "manufacturing", "Caoutchouc et plastiques"),  # polystyrène
    ("3904", "manufacturing", "Caoutchouc et plastiques"),  # polychlorure de vinyle
    ("3907", "manufacturing", "Caoutchouc et plastiques"),  # polyéthers, polyesters
    ("4001", "manufacturing", "Caoutchouc et plastiques"),  # caoutchouc naturel
    ("4002", "manufacturing", "Caoutchouc et plastiques"),  # caoutchouc synthétique
    # Textiles (HS50-63)
    ("5001", "manufacturing", "Manufacture of textiles"),  # soies brutes
    ("5101", "manufacturing", "Manufacture of textiles"),  # laine brute
    ("5201", "manufacturing", "Manufacture of textiles"),  # coton brut
    ("5301", "manufacturing", "Manufacture of textiles"),  # lin brut
    ("5401", "manufacturing", "Manufacture of textiles"),  # fibres synthétiques filées
    ("5501", "manufacturing", "Manufacture of textiles"),  # fibrilles de polyester
    ("5601", "manufacturing", "Manufacture of textiles"),  # filés de filaments synthétiques
    ("5801", "manufacturing", "Manufacture of textiles"),  # tulles, dentelles
    ("5901", "manufacturing", "Manufacture of textiles"),  # textiles enduits
    ("6001", "manufacturing", "Manufacture of textiles"),  # velours
    ("6101", "manufacturing", "Articles d'habillement"),  # chandails, tricots
    ("6201", "manufacturing", "Articles d'habillement"),  # vêtements de laine/poil
    ("6301", "manufacturing", "Articles d'habillement"),  # tissus de ouate, linge
    # Métaux (HS72-79, 82-83)
    ("7201", "manufacturing", "Manufacture of basic metals"),  # fontes brutes
    ("7202", "manufacturing", "Manufacture of basic metals"),  # ferro-alliages
    ("7208", "manufacturing", "Manufacture of basic metals"),  # produits laminés fer
    ("7301", "manufacturing", "Manufacture of basic metals"),  # produits en fer
    ("7402", "manufacturing", "Manufacture of basic metals"),  # cuivre affiné
    ("7502", "manufacturing", "Manufacture of basic metals"),  # nickel affiné
    ("7601", "manufacturing", "Manufacture of basic metals"),  # aluminium non allié
    ("7801", "manufacturing", "Manufacture of basic metals"),  # plomb affiné
    ("7901", "manufacturing", "Manufacture of basic metals"),  # zinc affiné
    ("8101", "manufacturing", "Manufacture of basic metals"),  # tungstène
    ("8206", "manufacturing", "Manufacture of basic metals"),  # outils à main
    ("8307", "manufacturing", "Manufacture of basic metals"),  # tuyaux flexibles
    # Électronique — ISIC 26 (HS85 : téléphones, semiconducteurs, supports)
    ("8517", "manufacturing", "Produits électroniques"),  # téléphones
    ("8523", "manufacturing", "Produits électroniques"),  # supports d'enregistrement
    ("8528", "manufacturing", "Produits électroniques"),  # moniteurs, téléviseurs
    ("8541", "manufacturing", "Produits électroniques"),  # semiconducteurs
    ("8542", "manufacturing", "Produits électroniques"),  # circuits intégrés
    # Équipements électriques — ISIC 27 (HS85 : moteurs, groupes électrogènes,
    # transformateurs, piles, câblage) : secteur UNIDO distinct de l'électronique
    # (ISIC 26) — les deux libellés existent séparément dans production_africaine.json,
    # fusionner les deux sous "Produits électroniques" comme avant faussait le besoin
    # estimé pour les produits de ce sous-secteur.
    ("8501", "manufacturing", "Équipements électriques"),  # moteurs électriques
    ("8502", "manufacturing", "Équipements électriques"),  # groupes électrogènes
    ("8503", "manufacturing", "Équipements électriques"),  # pièces de moteurs/génératrices
    ("8504", "manufacturing", "Équipements électriques"),  # transformateurs électriques
    ("8506", "manufacturing", "Équipements électriques"),  # piles électriques
    ("8507", "manufacturing", "Équipements électriques"),  # accumulateurs électriques
    ("8535", "manufacturing", "Équipements électriques"),  # appareillage électrique >1kV
    ("8536", "manufacturing", "Équipements électriques"),  # appareillage électrique <=1kV
    ("8537", "manufacturing", "Équipements électriques"),  # tableaux de commande électrique
    ("8544", "manufacturing", "Équipements électriques"),  # fils et câbles isolés
    # Véhicules automobiles (HS87)
    ("8701", "manufacturing", "Manufacture of motor vehicles"),  # tracteurs
    ("8702", "manufacturing", "Manufacture of motor vehicles"),  # autobus/autocars
    ("8703", "manufacturing", "Manufacture of motor vehicles"),  # voitures particulières
    ("8704", "manufacturing", "Manufacture of motor vehicles"),  # véhicules de transport
    ("8705", "manufacturing", "Manufacture of motor vehicles"),  # véhicules à usage spécial
    ("8706", "manufacturing", "Manufacture of motor vehicles"),  # châssis de véhicules
    ("8708", "manufacturing", "Manufacture of motor vehicles"),  # pièces détachées
    ("8711", "manufacturing", "Manufacture of motor vehicles"),  # motocycles
    # Minéraux non métalliques (HS68-70)
    ("6801", "manufacturing", "Manufacture of other non-metallic mineral products"),  # ardoises
    ("6902", "manufacturing", "Manufacture of other non-metallic mineral products"),  # céramiques
    (
        "6903",
        "manufacturing",
        "Manufacture of other non-metallic mineral products",
    ),  # briques et tuiles
    ("7001", "manufacturing", "Manufacture of other non-metallic mineral products"),  # verres bruts
    (
        "7007",
        "manufacturing",
        "Manufacture of other non-metallic mineral products",
    ),  # verres de sécurité
    (
        "7008",
        "manufacturing",
        "Manufacture of other non-metallic mineral products",
    ),  # verres laminés
    # Agro-industrie : produits alimentaires (HS16, 19-21, 23)
    ("1601", "manufacturing", "Manufacture of food products"),  # saucisses et charcuterie
    ("1602", "manufacturing", "Manufacture of food products"),  # viande préparée
    ("1605", "manufacturing", "Manufacture of food products"),  # crustacés préparés
    ("1901", "manufacturing", "Manufacture of food products"),  # préparations de céréales
    ("1902", "manufacturing", "Manufacture of food products"),  # pâtes alimentaires
    ("1905", "manufacturing", "Manufacture of food products"),  # pain et biscuits
    ("2001", "manufacturing", "Manufacture of food products"),  # légumes préparés
    ("2005", "manufacturing", "Manufacture of food products"),  # légumes cuits
    ("2009", "manufacturing", "Manufacture of food products"),  # jus de fruits
    ("2106", "manufacturing", "Manufacture of food products"),  # préparations alimentaires
    ("2301", "manufacturing", "Manufacture of food products"),  # aliments pour animaux
    ("2207", "manufacturing", "Manufacture of beverages"),  # alcool éthylique
    ("2208", "manufacturing", "Manufacture of beverages"),  # alcools et spiritueux
    # Tabac transformé (cigarettes/cigares, ISIC 12) — distinct du tabac brut en
    # feuilles (chapitre 24 entier, repli agri "Tobacco" ci-dessous) : préfixe
    # 4 chiffres plus spécifique, prioritaire sur le repli de chapitre.
    ("2402", "manufacturing", "Manufacture of tobacco products"),  # cigarettes, cigares
    # ── Raffinage pétrolier (UNIDO) ──
    # 2710 = huiles de pétrole RAFFINÉES (essence, diesel, kérosène...), pas du brut :
    # rattaché à la valeur ajoutée UNIDO "Manufacture of coke and refined petroleum
    # products" (donnée réelle disponible), plutôt que confondu avec la production
    # minière de brut USGS ci-dessous — l'ancien mapping masquait cette distinction.
    ("2710", "manufacturing", "Manufacture of coke and refined petroleum products"),
    # ── Hydrocarbures & Mines (USGS) ──
    ("2709", "mining", "Crude oil"),  # pétrole brut
    ("2711", "mining", "Natural gas"),
    ("2701", "mining", "Coal"),
    ("2702", "mining", "Coal"),
    ("7108", "mining", "Gold"),
    ("7102", "mining", "Diamonds"),  # diamants bruts
    ("7103", "mining", "Diamonds"),  # pierres gemmes brutes
    # 7113 = joaillerie/bijouterie (diamants taillés, sertis) : valeur ajoutée de
    # transformation (taille, sertissage), pas de la production minière brute —
    # rattaché au libellé UNIDO "Autres industries (diamants)" plutôt qu'à "Diamonds"
    # (USGS, qui ne mesure que l'extraction).
    ("7113", "manufacturing", "Autres industries (diamants)"),  # bijouterie/joaillerie
    ("7110", "mining", "Platinum"),
    ("2510", "mining", "Phosphate"),
    ("2603", "mining", "Copper"),
    ("7402", "mining", "Copper"),
    ("7403", "mining", "Copper"),
    ("2606", "mining", "Bauxite"),
    ("2844", "mining", "Uranium"),
    ("8105", "mining", "Cobalt"),
    ("2605", "mining", "Cobalt"),
    ("2601", "mining", "Iron ore"),
    ("2501", "mining", "Salt"),
    ("2615", "mining", "Tantalum"),
    ("8103", "mining", "Tantalum"),
    ("2608", "mining", "Zinc"),
    ("7901", "mining", "Zinc"),
    ("2604", "mining", "Nickel"),
    ("7502", "mining", "Nickel"),
    ("2521", "mining", "Limestone"),
    ("2602", "mining", "Manganese"),
    ("2609", "mining", "Tin"),
    ("8001", "mining", "Tin"),
    ("2529", "mining", "Fluorspar"),
    ("2836", "mining", "Soda ash"),
    ("2516", "mining", "Granite"),
    ("2513", "mining", "Pumice"),
    ("2530", "mining", "Perlite"),
    ("2614", "mining", "Ilmenite"),
    # ── Minéraux ajoutés (enrichissement mining_extended) — codes HS spécifiques
    #    (préfixe le plus long prioritaire ; évite les collisions avec les
    #    positions génériques déjà mappées : 2615=Tantalum, 2530=Perlite…). ──
    ("2610", "mining", "Chromium"),  # minerais de chrome
    ("2504", "mining", "Graphite"),  # graphite naturel
    ("2520", "mining", "Gypsum"),  # gypse, anhydrite
    ("2607", "mining", "Lead"),  # minerais de plomb
    ("2617", "mining", "Antimony"),  # minerais d'antimoine
    ("253090", "mining", "Lithium"),  # spodumène / minéraux de lithium (HS6)
    ("261610", "mining", "Silver"),  # minerais d'argent (chap. 26 ; ≠ 7106 métal)
    ("711021", "mining", "Palladium"),  # palladium (groupe platine, HS6)
    ("261510", "mining", "Zircon"),  # minerais de zirconium (HS6)
    ("261590", "mining", "Vanadium"),  # minerais de vanadium/niobium (HS6)
    ("261400", "mining", "Titanium (ilmenite)"),  # minerais de titane (HS6)
]

# Repli par chapitre HS (2 chiffres) — moins précis mais utile pour couverture large.
# Couvre les grands secteurs manufacturiers (UNIDO, valeur ajoutée) et agro/mines.
HS_CHAPTER_FALLBACK: Dict[str, Tuple[str, str]] = {
    "09": ("agri", "Coffee"),
    "10": ("agri", "Maize (corn)"),
    "18": ("agri", "Cocoa beans"),
    "27": ("mining", "Crude oil"),
    "71": ("mining", "Gold"),
    # Métallurgie de base (UNIDO)
    "72": ("manufacturing", "Manufacture of basic metals"),
    "73": ("manufacturing", "Manufacture of basic metals"),
    "74": ("manufacturing", "Manufacture of basic metals"),
    "75": ("manufacturing", "Manufacture of basic metals"),
    "76": ("manufacturing", "Manufacture of basic metals"),
    "78": ("manufacturing", "Manufacture of basic metals"),
    "79": ("manufacturing", "Manufacture of basic metals"),
    # Agro-alimentaire (UNIDO)
    "16": ("manufacturing", "Manufacture of food products"),
    "19": ("manufacturing", "Manufacture of food products"),
    "20": ("manufacturing", "Manufacture of food products"),
    "21": ("manufacturing", "Manufacture of food products"),
    "22": ("manufacturing", "Manufacture of beverages"),
    # Chimie & pharmacie (UNIDO)
    "28": ("manufacturing", "Manufacture of chemicals"),
    "29": ("manufacturing", "Manufacture of chemicals"),
    "30": ("manufacturing", "Produits pharmaceutiques"),
    "31": ("manufacturing", "Manufacture of chemicals"),
    "32": ("manufacturing", "Manufacture of chemicals"),
    "33": ("manufacturing", "Manufacture of chemicals"),
    "34": ("manufacturing", "Manufacture of chemicals"),
    "38": ("manufacturing", "Manufacture of chemicals"),
    # Caoutchouc & plastiques (UNIDO)
    "39": ("manufacturing", "Caoutchouc et plastiques"),
    "40": ("manufacturing", "Caoutchouc et plastiques"),
    # Textiles & habillement (UNIDO)
    "50": ("manufacturing", "Manufacture of textiles"),
    "51": ("manufacturing", "Manufacture of textiles"),
    "52": ("manufacturing", "Manufacture of textiles"),
    "53": ("manufacturing", "Manufacture of textiles"),
    "54": ("manufacturing", "Manufacture of textiles"),
    "55": ("manufacturing", "Manufacture of textiles"),
    "56": ("manufacturing", "Manufacture of textiles"),
    "57": ("manufacturing", "Manufacture of textiles"),
    "58": ("manufacturing", "Manufacture of textiles"),
    "59": ("manufacturing", "Manufacture of textiles"),
    "60": ("manufacturing", "Manufacture of textiles"),
    "61": ("manufacturing", "Articles d'habillement"),
    "62": ("manufacturing", "Articles d'habillement"),
    "63": ("manufacturing", "Articles d'habillement"),
    # Électronique & équipements électriques (UNIDO)
    "85": ("manufacturing", "Produits électroniques"),
    # Véhicules automobiles (UNIDO)
    "87": ("manufacturing", "Manufacture of motor vehicles"),
    # Minéraux non métalliques : ciment, verre, céramique (UNIDO — 18 pays)
    "68": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    "69": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    "70": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    # Agro-industrie complémentaire : farines, huiles, aliments pour animaux
    "11": ("manufacturing", "Manufacture of food products"),
    "15": ("manufacturing", "Manufacture of food products"),
    "17": ("agri", "Sugarcane"),
    "23": ("manufacturing", "Manufacture of food products"),
    "24": ("agri", "Tobacco"),
    # Ouvrages en métaux (outillage, coutellerie)
    "82": ("manufacturing", "Manufacture of basic metals"),
    "83": ("manufacturing", "Manufacture of basic metals"),
    # Bois, papier (UNIDO ISIC 16-17)
    "44": ("manufacturing", "Manufacture of wood and wood products"),
    "48": ("manufacturing", "Manufacture of paper and paper products"),
}

DATASET_KEY = {
    "agri": "agri_faostat",
    "mining": "mining_usgs",
    "manufacturing": "manufacturing_unido",
}

# En-deçà de ce nombre de pays ayant une valeur pour l'année de classement,
# un "rang #1" / "part continentale" n'est PAS un signal de leadership réel —
# c'est un artefact de couverture incomplète de l'ingestion (ex. seule Maurice
# capturée pour "Produits pharmaceutiques" UNIDO alors que l'Égypte, le Maroc,
# l'Afrique du Sud et la Tunisie ont des industries pharmaceutiques réelles
# non encore ingérées). En dessous du seuil, `coverage_caveat` est renseigné
# et DOIT être affiché — jamais silencieusement masqué en aval.
_MIN_RELIABLE_COVERAGE_COUNTRIES = 3


def _coverage_caveat(dataset: str, label: str, n_countries: int) -> Optional[str]:
    if n_countries >= _MIN_RELIABLE_COVERAGE_COUNTRIES:
        return None
    institution = SOURCE_META[dataset]["institution"]
    return (
        f"Couverture {institution} limitée à {n_countries} pays africain(s) pour "
        f"« {label} » dans notre base actuelle — un rang ou une part continentale "
        "calculé sur si peu de pays NE reflète PAS un leadership réel : d'autres "
        "producteurs africains existent très probablement mais ne sont pas encore "
        "ingérés. À traiter comme une donnée partielle, pas comme un classement fiable."
    )


SOURCE_META = {
    "agri": {
        "institution": "FAO",
        "dataset": "FAOSTAT — Production",
        "url": "https://www.fao.org/faostat/",
        "measure": "Production",
        "unit": "tonnes",
    },
    "mining": {
        "institution": "USGS",
        "dataset": "Mineral Commodity Summaries",
        "url": "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        "measure": "Production minière",
        "unit": "tonnes",
    },
    "manufacturing": {
        "institution": "UNIDO",
        "dataset": "INDSTAT4 (ISIC Rev.4)",
        "url": "https://stat.unido.org/",
        "measure": "Valeur ajoutée manufacturière",
        "unit": "USD",
    },
}

# ── Proxy d'exportation (repli quand FAO/USGS/UNIDO ne couvrent pas le produit) ──
# Les exportations SH6/SH4 (OEC/BACI) servent d'INDICE de capacité productive
# UNIQUEMENT là où le référentiel production n'a rien. Ce n'est jamais une mesure
# de production : une exportation observée en est une BORNE BASSE (la part
# consommée sur le marché intérieur n'est pas exportée) et peut inclure des
# réexportations — lesquelles n'attestent d'AUCUNE production locale.
_EXPORT_PROXY_SOURCE = {
    "institution": "OEC / BACI (CEPII)",
    "dataset": "BACI — flux commerciaux bilatéraux (HS Rev. 2017)",
    "url": "https://oec.world/",
    "measure": "Exportations (proxy de capacité de production)",
    "unit": "USD",
}

_EXPORT_PROXY_CAVEAT = (
    "PROXY — les exportations ne mesurent PAS la production : elles en sont une "
    "BORNE BASSE (la production consommée sur le marché intérieur n'est pas "
    "exportée) et peuvent inclure des réexportations. À lire comme un indice de "
    "capacité productive en l'absence de données FAO/USGS/UNIDO, jamais comme un "
    "chiffre de production."
)

_EXPORT_PROXY_REEXPORT_CAVEAT = (
    "Ce pays est un hub de réexportation : une part des exportations peut être de "
    "la marchandise réexportée depuis une zone franche, qui n'atteste d'aucune "
    "production locale et n'acquiert pas l'origine ZLECAf. Le proxy peut donc "
    "surestimer nettement la capacité de production réelle."
)


def _normalize_hs(hs_code: Optional[str]) -> str:
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


def _match_commodity(hs_code: str) -> Optional[Tuple[str, str, str]]:
    """Retourne (dataset, commodity_label, match_level) ou None."""
    code = _normalize_hs(hs_code)
    if not code:
        return None
    # Match le plus spécifique d'abord (préfixe le plus long)
    for prefix, dataset, label in sorted(HS_TO_COMMODITY, key=lambda x: -len(x[0])):
        if code.startswith(prefix):
            return dataset, label, f"HS{len(prefix)}"
    # Repli par chapitre
    chapter = code[:2]
    if chapter in HS_CHAPTER_FALLBACK:
        dataset, label = HS_CHAPTER_FALLBACK[chapter]
        return dataset, label, "HS2 (chapitre)"
    return None


def _records_for(dataset: str, label: str) -> List[Dict]:
    data = load_production_data()
    key = DATASET_KEY[dataset]
    return [
        r
        for r in data.get(key, [])
        if r.get("commodity_label") == label
        or r.get("isic_label") == label
        or r.get("sector_detail") == label
    ]


def _cagr(first_val: float, last_val: float, years: int) -> Optional[float]:
    if not first_val or first_val <= 0 or years <= 0 or last_val <= 0:
        return None
    return ((last_val / first_val) ** (1.0 / years) - 1.0) * 100.0


def _build_scenarios(
    latest: float,
    cagr_pct: Optional[float],
    unit: str,
    country_share_pct: Optional[float],
    leader_value: Optional[float],
) -> Dict:
    """
    Projections d'intégration africaine — explicitement étiquetées comme scénarios.
    Calculées à partir du CAGR réel et de l'écart au leader continental ; aucun chiffre
    n'est inventé hors de ces fondations vérifiables.
    """
    if not latest or latest <= 0:
        return {}
    # CAGR de référence : observé, borné à [0%, 12%] pour rester réaliste
    base_cagr = cagr_pct if cagr_pct is not None else 2.0
    base_cagr = max(0.0, min(base_cagr, 12.0))

    def project(rate_pct: float, years: int) -> float:
        return round(latest * ((1.0 + rate_pct / 100.0) ** years), 1)

    scenarios = {
        "conservateur": {
            "label": "Conservateur — tendance actuelle",
            "annual_growth_pct": round(base_cagr, 2),
            "horizon_2030": project(base_cagr, 6),
            "hypothesis": "Maintien du CAGR observé 2021-2024, sans réforme additionnelle.",
        },
        "integration_zlecaf": {
            "label": "Intégration ZLECAf — accès marché élargi",
            "annual_growth_pct": round(base_cagr + 3.0, 2),
            "horizon_2030": project(base_cagr + 3.0, 6),
            "hypothesis": "Démantèlement tarifaire intra-africain (+3 pts de croissance via "
            "débouchés régionaux et réduction des barrières).",
        },
        "transformation_locale": {
            "label": "Transformation locale + ZLECAf",
            "annual_growth_pct": round(base_cagr + 6.0, 2),
            "horizon_2030": project(base_cagr + 6.0, 6),
            "hypothesis": "Montée en gamme industrielle (règles d'origine favorisant la "
            "valeur ajoutée locale) cumulée à l'accès marché ZLECAf.",
        },
    }
    # Écart au leader : potentiel de rattrapage tangible
    if leader_value and leader_value > latest:
        scenarios["potentiel_rattrapage"] = {
            "label": "Potentiel de rattrapage continental",
            "leader_production": round(leader_value, 1),
            "gap_pct": round((leader_value - latest) / leader_value * 100.0, 1),
            "hypothesis": f"Production additionnelle mobilisable si alignement sur le leader "
            f"continental ({unit}).",
        }
    return scenarios


def get_capacity(country_iso3: str, hs_code: str) -> Dict:
    """
    Capacité de production réelle d'un pays pour un produit (code HS), enrichie de
    son rang continental, de sa part africaine et de scénarios d'intégration.
    """
    iso3 = (country_iso3 or "").strip().upper()
    match = _match_commodity(hs_code)
    if not match:
        return {"available": False, "reason": "no_mapping", "hs_code": hs_code}

    dataset, label, match_level = match
    meta = SOURCE_META[dataset]
    all_recs = _records_for(dataset, label)
    if not all_recs:
        return {"available": False, "reason": "no_data", "commodity": label, "hs_code": hs_code}

    # Série temporelle du pays
    country_recs = sorted(
        [r for r in all_recs if r.get("country_iso3") == iso3],
        key=lambda r: r.get("year", 0),
    )
    timeseries = [
        {"year": r["year"], "value": r["value"], "unit": r.get("unit", meta["unit"])}
        for r in country_recs
    ]

    latest_rec = country_recs[-1] if country_recs else None
    latest_val = latest_rec["value"] if latest_rec else None
    latest_year = latest_rec["year"] if latest_rec else None

    cagr_pct = None
    if len(country_recs) >= 2:
        cagr_pct = _cagr(
            country_recs[0]["value"],
            country_recs[-1]["value"],
            country_recs[-1]["year"] - country_recs[0]["year"],
        )

    # Classement continental sur la dernière année commune
    ranking_year = latest_year
    year_recs = [r for r in all_recs if r.get("year") == ranking_year and r.get("value")]
    year_recs.sort(key=lambda r: r["value"], reverse=True)
    continental_total = sum(r["value"] for r in year_recs)
    rank = next((i + 1 for i, r in enumerate(year_recs) if r.get("country_iso3") == iso3), None)
    leader = year_recs[0] if year_recs else None
    country_share = (
        round(latest_val / continental_total * 100.0, 2)
        if latest_val and continental_total
        else None
    )

    top_producers = [
        {
            "country_iso3": r["country_iso3"],
            "country_name": r.get("country_name", r["country_iso3"]),
            "value": r["value"],
            "share_pct": (
                round(r["value"] / continental_total * 100.0, 1) if continental_total else None
            ),
        }
        for r in year_recs[:5]
    ]

    # Unité & source réelles de l'enregistrement (le pétrole/gaz ont leurs propres
    # unités/sources qui diffèrent du défaut du dataset).
    ref_rec = latest_rec or (year_recs[0] if year_recs else None)
    actual_unit = (ref_rec.get("unit") if ref_rec else None) or meta["unit"]
    actual_source = {
        "institution": (ref_rec.get("source_institution") if ref_rec else None)
        or meta["institution"],
        "dataset": (ref_rec.get("source_dataset") if ref_rec else None) or meta["dataset"],
        "url": (ref_rec.get("source_url") if ref_rec else None) or meta["url"],
    }

    # Sous le seuil de couverture fiable, un rang, une part ou un « leader »
    # continental est un artefact d'ingestion (ex. Maurice seule ingérée pour
    # « Produits pharmaceutiques » UNIDO → « 1/1, 100 % ») : on n'émet AUCUN de
    # ces champs — seuls la valeur réelle du pays et le garde-fou subsistent.
    coverage_caveat = _coverage_caveat(dataset, label, len(year_recs))
    if coverage_caveat:
        rank = None
        country_share = None
        leader = None
        continental_total = None
        top_producers = [{**p, "share_pct": None} for p in top_producers]

    scenarios = {}
    if latest_val:
        scenarios = _build_scenarios(
            latest_val,
            cagr_pct,
            actual_unit,
            country_share,
            leader["value"] if leader else None,
        )

    return {
        "available": bool(country_recs),
        "hs_code": hs_code,
        "match_level": match_level,
        "commodity": label,
        "dimension": dataset,
        "measure": meta["measure"],
        "unit": actual_unit,
        "source": actual_source,
        "country_iso3": iso3,
        "latest_value": latest_val,
        "latest_year": latest_year,
        "cagr_pct": round(cagr_pct, 2) if cagr_pct is not None else None,
        "timeseries": timeseries,
        "continental": {
            "ranking_year": ranking_year,
            "rank": rank,
            "total_countries": len(year_recs),
            "continental_total": round(continental_total, 1) if continental_total else None,
            "country_share_pct": country_share,
            "leader": (
                {
                    "country_iso3": leader["country_iso3"],
                    "country_name": leader.get("country_name"),
                    "value": leader["value"],
                }
                if leader
                else None
            ),
            "top_producers": top_producers,
            "coverage_caveat": coverage_caveat,
        },
        "integration_scenarios": scenarios,
    }


def list_tracked_products() -> List[Dict]:
    """
    Univers des produits traçables par le référentiel production (FAOSTAT /
    USGS / UNIDO) : un représentant HS par (dataset, commodity), uniquement
    ceux qui ont des enregistrements réels. Sert de liste de candidats au
    scénario S4 (opportunités d'importation par pays) du module Opportunités.
    """
    seen = set()
    products: List[Dict] = []
    for prefix, dataset, label in HS_TO_COMMODITY:
        key = (dataset, label)
        if key in seen:
            continue
        seen.add(key)
        if not _records_for(dataset, label):
            continue
        products.append({"hs_code": prefix, "dataset": dataset, "commodity": label})
    return products


def get_country_profile(country_iso3: str, top_n: int = 20) -> Dict:
    """
    Vue pays : ce que le pays produit RÉELLEMENT selon le référentiel
    production (FAOSTAT / USGS / UNIDO), avec rang continental et part
    africaine sur la dernière année disponible de chaque produit. Sert de
    bloc d'ancrage aux prompts IA du module Opportunités : le LLM choisit
    ses opportunités parmi ces produits vérifiés au lieu de sa mémoire.
    """
    iso3 = (country_iso3 or "").strip().upper()
    seen = set()
    products: List[Dict] = []
    for prefix, dataset, label in HS_TO_COMMODITY:
        key = (dataset, label)
        if key in seen:
            continue
        seen.add(key)
        all_recs = _records_for(dataset, label)
        if not all_recs:
            continue
        latest_year = max(r["year"] for r in all_recs)
        year_recs = sorted(
            [r for r in all_recs if r.get("year") == latest_year and r.get("value")],
            key=lambda r: r["value"],
            reverse=True,
        )
        rank, country_rec = next(
            ((i + 1, r) for i, r in enumerate(year_recs) if r.get("country_iso3") == iso3),
            (None, None),
        )
        if country_rec is None:
            continue
        total = sum(r["value"] for r in year_recs)
        meta = SOURCE_META[dataset]
        # Même règle que get_capacity : rang/part jamais émis sous le seuil de
        # couverture (ils alimenteraient les prompts avec un faux leadership).
        caveat = _coverage_caveat(dataset, label, len(year_recs))
        products.append(
            {
                "hs_code": prefix,
                "commodity": label,
                "dataset": dataset,
                "measure": meta["measure"],
                "unit": country_rec.get("unit") or meta["unit"],
                "institution": country_rec.get("source_institution") or meta["institution"],
                "year": latest_year,
                "value": country_rec["value"],
                "rank": None if caveat else rank,
                "total_countries": len(year_recs),
                "share_pct": (
                    round(country_rec["value"] / total * 100.0, 1) if total and not caveat else None
                ),
                "coverage_caveat": caveat,
            }
        )
    products.sort(key=lambda p: (p["share_pct"] or 0.0), reverse=True)
    return {
        "available": bool(products),
        "country_iso3": iso3,
        "products": products[:top_n],
        "total_tracked": len(products),
    }


def get_continental_producers(hs_code: str) -> Dict:
    """
    Vue continentale (sans pays) : top producteurs africains réels pour un code HS.
    Utilisé par la recherche HS6 du module Chaînes de Valeur.
    """
    match = _match_commodity(hs_code)
    if not match:
        return {"available": False, "reason": "no_mapping", "hs_code": hs_code}
    dataset, label, match_level = match
    meta = SOURCE_META[dataset]
    all_recs = _records_for(dataset, label)
    if not all_recs:
        return {"available": False, "reason": "no_data", "commodity": label, "hs_code": hs_code}

    latest_year = max(r["year"] for r in all_recs)
    year_recs = sorted(
        [r for r in all_recs if r.get("year") == latest_year and r.get("value")],
        key=lambda r: r["value"],
        reverse=True,
    )
    total = sum(r["value"] for r in year_recs)
    ref_rec = year_recs[0] if year_recs else None
    actual_unit = (ref_rec.get("unit") if ref_rec else None) or meta["unit"]
    actual_source = {
        "institution": (ref_rec.get("source_institution") if ref_rec else None)
        or meta["institution"],
        "dataset": (ref_rec.get("source_dataset") if ref_rec else None) or meta["dataset"],
        "url": (ref_rec.get("source_url") if ref_rec else None) or meta["url"],
    }
    # Sous le seuil de couverture, une « part africaine » calculée sur 1-2 pays
    # est un artefact (100 % pour l'unique pays ingéré) — jamais émise. Le
    # continental_total reste fourni (borne basse réelle, consommée par
    # l'estimation de demande qui relaie déjà le garde-fou).
    coverage_caveat = _coverage_caveat(dataset, label, len(year_recs))
    return {
        "available": True,
        "hs_code": hs_code,
        "match_level": match_level,
        "commodity": label,
        "dimension": dataset,
        "measure": meta["measure"],
        "unit": actual_unit,
        "source": actual_source,
        "year": latest_year,
        "continental_total": round(total, 1) if total else None,
        "top_producers": [
            {
                "country_iso3": r["country_iso3"],
                "country_name": r.get("country_name", r["country_iso3"]),
                "value": r["value"],
                "share_pct": (
                    round(r["value"] / total * 100.0, 1) if total and not coverage_caveat else None
                ),
            }
            for r in year_recs[:10]
        ],
        "coverage_caveat": coverage_caveat,
    }


def get_regional_producers(hs_code: str, iso3_set) -> Dict:
    """
    Vue SOUS-RÉGIONALE (Afrique du Nord / Ouest / Est / Centrale / Australe) :
    production réelle des pays de la région pour ce code HS, dernière année
    disponible. Sert de référence per-capita RÉGIONALE au module Opportunités
    (besoin national) : une moyenne CONTINENTALE mélange des régimes
    alimentaires très différents (blé/thé dominants en Afrique du Nord, riz/
    manioc en Afrique de l'Ouest...) — la référence régionale capte mieux le
    profil de consommation typique du pays évalué que la moyenne panafricaine.
    """
    match = _match_commodity(hs_code)
    if not match:
        return {"available": False, "reason": "no_mapping", "hs_code": hs_code}
    dataset, label, match_level = match
    all_recs = _records_for(dataset, label)
    if not all_recs:
        return {"available": False, "reason": "no_data", "commodity": label, "hs_code": hs_code}

    latest_year = max(r["year"] for r in all_recs)
    region_recs = sorted(
        (
            r
            for r in all_recs
            if r.get("year") == latest_year and r.get("value") and r.get("country_iso3") in iso3_set
        ),
        key=lambda r: r["value"],
        reverse=True,
    )
    total = sum(r["value"] for r in region_recs)
    return {
        "available": bool(region_recs),
        "hs_code": hs_code,
        "match_level": match_level,
        "commodity": label,
        "year": latest_year,
        "region_total": round(total, 1) if total else None,
        "producer_count": len(region_recs),
        "top_producers": [
            {
                "country_iso3": r["country_iso3"],
                "country_name": r.get("country_name", r["country_iso3"]),
                "value": r["value"],
            }
            for r in region_recs[:5]
        ],
    }


def _export_series_stats(
    exports: Optional[List[Dict]],
) -> Tuple[Optional[float], Optional[int], Optional[float], List[Dict]]:
    """
    (dernière_valeur, dernière_année, CAGR %, série) depuis la série
    d'exportations OEC. Ignore les années `no_data` et les valeurs nulles.
    """
    series = [
        {
            "year": e["year"],
            "value": e.get("trade_value") or 0.0,
            "quantity": e.get("quantity") or 0.0,
        }
        for e in (exports or [])
        if not e.get("no_data") and (e.get("trade_value") or 0) > 0
    ]
    series.sort(key=lambda r: r["year"])
    if not series:
        return None, None, None, []
    latest = series[-1]
    cagr = None
    if len(series) >= 2:
        cagr = _cagr(
            series[0]["value"], series[-1]["value"], series[-1]["year"] - series[0]["year"]
        )
    return latest["value"], latest["year"], cagr, series


def build_export_proxy_capacity(
    hs_code: str, oec_history: Optional[Dict], is_reexport_hub: bool = False
) -> Dict:
    """
    Construit un bloc « capacité » de REPLI à partir de l'historique
    d'EXPORTATIONS OEC/BACI (correspondance SH6 → SH4 → SH2), à utiliser
    lorsque FAO / USGS / UNIDO ne couvrent pas le produit.

    Fonction pure (aucune I/O) : reçoit la réponse déjà récupérée de
    `oec_service.get_country_hs6_history`. Étiquetage strict — `is_proxy=True`,
    `basis="exports_proxy"`, et un `proxy_caveat` obligatoire rappelant qu'une
    exportation est une borne basse de la production, jamais une mesure (avec un
    caveat réexport supplémentaire pour les hubs type Maurice/Togo/Djibouti).
    """
    if not oec_history or oec_history.get("error") or not oec_history.get("has_data"):
        return {"available": False, "reason": "no_export_data", "hs_code": hs_code}

    latest_val, latest_year, cagr_pct, series = _export_series_stats(oec_history.get("exports"))
    if latest_val is None:
        return {"available": False, "reason": "no_export_data", "hs_code": hs_code}

    level = str(oec_history.get("match_level") or oec_history.get("level") or "").lower()
    level_label = {"hs6": "HS6", "hs4": "HS4", "hs2": "HS2 (chapitre)"}.get(level, level or None)

    caveats = [_EXPORT_PROXY_CAVEAT]
    if is_reexport_hub:
        caveats.append(_EXPORT_PROXY_REEXPORT_CAVEAT)

    return {
        "available": True,
        "is_proxy": True,
        "basis": "exports_proxy",
        "hs_code": oec_history.get("hs_code") or hs_code,
        "hs4_code": oec_history.get("hs4_code"),
        "match_level": level_label,
        "measure": _EXPORT_PROXY_SOURCE["measure"],
        "unit": _EXPORT_PROXY_SOURCE["unit"],
        "source": {
            "institution": _EXPORT_PROXY_SOURCE["institution"],
            "dataset": _EXPORT_PROXY_SOURCE["dataset"],
            "url": _EXPORT_PROXY_SOURCE["url"],
        },
        "country_iso3": oec_history.get("country_iso3"),
        "latest_value": round(latest_val, 2),
        "latest_year": latest_year,
        "cagr_pct": round(cagr_pct, 2) if cagr_pct is not None else None,
        "timeseries": [
            {
                "year": s["year"],
                "value": round(s["value"], 2),
                "quantity": round(s["quantity"], 2),
                "unit": "USD",
            }
            for s in series
        ],
        "is_reexport_hub": is_reexport_hub,
        "proxy_caveat": " ".join(caveats),
        "currency": oec_history.get("currency", "USD"),
    }


def capacity_is_reliable(cap: Optional[Dict]) -> bool:
    """
    True si un bloc `production_capacity` mesuré peut être présenté tel quel :
    disponible ET couverture continentale fiable. Un bloc disponible mais sous
    le seuil de couverture (`coverage_caveat` renseigné — ex. Maurice seule
    ingérée pour les produits pharmaceutiques UNIDO) est trop mince pour ancrer
    seul l'affichage : le module Opportunités lui adjoint alors le proxy
    d'exportations OEC/BACI, plus spécifique au produit.
    """
    if not cap or not cap.get("available"):
        return False
    if cap.get("is_proxy"):
        return True
    return not (cap.get("continental") or {}).get("coverage_caveat")


def enrich_opportunities(opportunities: List[Dict], country_iso3: str) -> List[Dict]:
    """
    Attache `production_capacity` à chaque opportunité disposant d'un code HS,
    pour le pays analysé (producteur dans les modes export / industriel).
    """
    if not country_iso3:
        return opportunities
    for opp in opportunities:
        product = opp.get("product") or {}
        hs = (
            product.get("hs6Code")
            or product.get("hs_code")
            or opp.get("hs6Code")
            or opp.get("hs_code")
        )
        if not hs:
            continue
        cap = get_capacity(country_iso3, hs)
        if cap.get("available"):
            opp["production_capacity"] = cap
    return opportunities
