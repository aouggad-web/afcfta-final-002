"""
Unités complémentaires (Supplementary/Additional Units) pour codes HS6
Source: OMD (Organisation Mondiale des Douanes) — Système Harmonisé 2022

Les unités complémentaires complètent la mesure en poids/volume. Exemples :
- Cacao (1801) → kg
- Blé (1001) → tonnes
- Vin (2204) → litres
- Vêtements (6204) → nombre de pièces
- Véhicules → nombre d'unités

Résolution STRICTEMENT par code HS6 exact — pas de repli sur le préfixe HS4,
car au sein d'une même position les sous-positions peuvent avoir des unités
différentes (une unité héritée d'un cousin de chapitre serait trompeuse).
"""

from typing import Optional

HS6_SUPPLEMENTARY_UNITS = {
    # =========================================================================
    # CHAPITRE 01 - ANIMAUX VIVANTS
    # =========================================================================
    "010290": "nombre",  # Bovins vivants
    "010410": "nombre",  # Ovins vivants
    "010420": "nombre",  # Caprins vivants
    "010511": "nombre",  # Poules de basse-cour
    "010512": "nombre",  # Autres volailles
    # =========================================================================
    # CHAPITRE 02 - VIANDES
    # =========================================================================
    "020130": "kg",  # Viande de bovins, fraîche
    "020230": "kg",  # Viande de bovins, congelée
    "020714": "kg",  # Morceaux de volailles, congelés
    # =========================================================================
    # CHAPITRE 03 - POISSONS
    # =========================================================================
    "030289": "kg",  # Autres poissons frais/réfrigérés
    "030342": "kg",  # Thon congelé
    "030389": "kg",  # Autres poissons congelés
    # =========================================================================
    # CHAPITRE 04 - PRODUITS LAITIERS
    # =========================================================================
    "040110": "kg",  # Lait entier frais
    "040210": "kg",  # Lait écrémé frais
    "040221": "kg",  # Lait écrémé en poudre
    # =========================================================================
    # CHAPITRE 05 - AUTRES PRODUITS D'ORIGINE ANIMALE
    # =========================================================================
    "050400": "kg",  # Boyaux, vessies, estomacs
    # =========================================================================
    # CHAPITRE 06 - PLANTES VIVANTES
    # =========================================================================
    "060310": "nombre",  # Roses fraîches
    "060390": "nombre",  # Autres fleurs fraîches
    # =========================================================================
    # CHAPITRE 07 - LÉGUMES
    # =========================================================================
    "070310": "kg",  # Oignons frais
    "070390": "kg",  # Autres légumes frais
    "070410": "kg",  # Chou frais
    "070490": "kg",  # Autres brassicacées fraîches
    # =========================================================================
    # CHAPITRE 08 - FRUITS
    # =========================================================================
    "080300": "kg",  # Bananes fraîches
    "080430": "kg",  # Dattes fraîches
    "080510": "kg",  # Oranges fraîches
    "080520": "kg",  # Citrons frais
    "080540": "kg",  # Raisins frais
    "080611": "kg",  # Raisins secs (raisins de Corinthe)
    # =========================================================================
    # CHAPITRE 09 - CAFÉ, THÉ, ÉPICES
    # =========================================================================
    "090111": "kg",  # Café non torréfié, non décaféiné
    "090112": "kg",  # Café non torréfié, décaféiné
    "090121": "kg",  # Café torréfié, non décaféiné
    "090122": "kg",  # Café torréfié, décaféiné
    "090900": "kg",  # Thé
    "091010": "kg",  # Poivre
    "091030": "kg",  # Clous de girofle
    "091099": "kg",  # Autres épices
    # =========================================================================
    # CHAPITRE 10 - CÉRÉALES
    # =========================================================================
    "100110": "tonnes",  # Blé tendre
    "100190": "tonnes",  # Autres blés
    "100200": "tonnes",  # Seigle
    "100300": "tonnes",  # Orge
    "100400": "tonnes",  # Avoine
    "100510": "tonnes",  # Maïs dent
    "100590": "tonnes",  # Autres maïs
    "100610": "tonnes",  # Riz décortiqué
    "100620": "tonnes",  # Riz semi-blanchi
    "100630": "tonnes",  # Riz blanchi
    # =========================================================================
    # CHAPITRE 11 - PRODUITS DE LA MINOTERIE
    # =========================================================================
    "110100": "kg",  # Farine de blé
    "110220": "kg",  # Farine de maïs
    "110290": "kg",  # Autres farines de céréales
    # =========================================================================
    # CHAPITRE 12 - OLÉAGINEUX
    # =========================================================================
    "120100": "tonnes",  # Graines de soja
    "120200": "tonnes",  # Cacahuètes
    "120300": "tonnes",  # Graines de coprah
    "120400": "tonnes",  # Graines de noix de coco
    "120510": "tonnes",  # Graines de colza
    "120600": "tonnes",  # Graines de tournesol
    # =========================================================================
    # CHAPITRE 13 - GOMMES, RÉSINES, EXTRAITS
    # =========================================================================
    "130210": "kg",  # Gomme arabique
    "130219": "kg",  # Autres gommes naturelles
    # =========================================================================
    # CHAPITRE 15 - GRAISSES ET HUILES
    # =========================================================================
    "150710": "kg",  # Huile de palme brute
    "150790": "kg",  # Autres huiles de palme
    "151110": "kg",  # Huile d'arachide brute
    "151190": "kg",  # Autres huiles d'arachide
    "151510": "kg",  # Beurre de cacao
    # =========================================================================
    # CHAPITRE 18 - CACAO
    # =========================================================================
    "180100": "kg",  # Fèves de cacao, entières/brisées
    "180200": "kg",  # Cacao broyé/en poudre
    # =========================================================================
    # CHAPITRE 19 - PRÉPARATIONS CÉRÉALIÈRES
    # =========================================================================
    "190110": "kg",  # Malt
    "190290": "kg",  # Autres céréales traitées
    # =========================================================================
    # CHAPITRE 20 - PRÉPARATIONS DE LÉGUMES
    # =========================================================================
    "200510": "kg",  # Oignons préparés
    "200590": "kg",  # Autres légumes préparés
    # =========================================================================
    # CHAPITRE 21 - PRÉPARATIONS ALIMENTAIRES
    # =========================================================================
    "210610": "kg",  # Levure active
    "210690": "kg",  # Autres préparations alimentaires (condiments, sauces...)
    # =========================================================================
    # CHAPITRE 22 - BOISSONS
    # =========================================================================
    "220410": "litres",  # Vin mousseux
    "220421": "litres",  # Vin blanc tranquille
    "220429": "litres",  # Autres vins tranquilles
    "220430": "litres",  # Vin de raisins secs
    "220511": "litres",  # Champagne
    "220519": "litres",  # Autres vins mousseux
    "220710": "litres",  # Alcool éthylique non dénaturé
    "220720": "litres",  # Alcool éthylique dénaturé
    "220830": "litres",  # Rhum
    "220840": "litres",  # Tafia
    "220850": "litres",  # Autres alcools distillés
    "220860": "litres",  # Alcool de grain
    "220870": "litres",  # Whisky
    "220880": "litres",  # Vodka
    "220890": "litres",  # Autres alcools (gin, genièvre, liqueurs)
    "220910": "litres",  # Vinaigre
    # =========================================================================
    # CHAPITRE 25 - SEL, SOUFRE, MINÉRAUX
    # =========================================================================
    "250100": "tonnes",  # Sel de mine
    "250200": "tonnes",  # Sel marin
    "250300": "tonnes",  # Sel raffiné
    # =========================================================================
    # CHAPITRE 26 - MINERAIS
    # =========================================================================
    "260111": "tonnes",  # Minerai de fer, grillé
    "260112": "tonnes",  # Autres minerais de fer
    "260300": "tonnes",  # Minerai de cuivre
    "260400": "tonnes",  # Minerai de nickel
    "260500": "tonnes",  # Minerai de cobalt
    "260600": "tonnes",  # Minerai d'aluminium
    "260700": "tonnes",  # Minerai de plomb
    "260800": "tonnes",  # Minerai de zinc
    # =========================================================================
    # CHAPITRE 27 - COMBUSTIBLES, PÉTROLE
    # =========================================================================
    "270900": "tonnes",  # Huile de pétrole brute
    "271000": "tonnes",  # Gazole/diesel
    "271011": "tonnes",  # Essence sans plomb
    "271012": "tonnes",  # Autres essences
    # =========================================================================
    # CHAPITRE 28 - PRODUITS CHIMIQUES INORGANIQUES
    # =========================================================================
    "280300": "kg",  # Sulfurique
    "280430": "kg",  # Nitrique
    "281012": "kg",  # Chlore
    "281022": "kg",  # Oxygène
    # =========================================================================
    # CHAPITRE 29 - PRODUITS CHIMIQUES ORGANIQUES
    # =========================================================================
    "290216": "kg",  # Ether diéthylique
    "290529": "kg",  # Autres alcools
    "291414": "kg",  # Acétaldéhyde
    # =========================================================================
    # CHAPITRE 30 - PRODUITS PHARMACEUTIQUES
    # =========================================================================
    "300410": "kg",  # Médicaments antibiotiques
    "300420": "kg",  # Autres médicaments
    "300490": "kg",  # Autres préparations pharmaceutiques
    # =========================================================================
    # CHAPITRE 31 - ENGRAIS
    # =========================================================================
    "310210": "tonnes",  # Engrais naturels
    "310221": "tonnes",  # Urée
    "310229": "tonnes",  # Autres engrais azotés
    "310290": "tonnes",  # Autres engrais
    # =========================================================================
    # CHAPITRE 32 - EXTRAITS TANNANTS, COLORANTS
    # =========================================================================
    "320100": "kg",  # Extraits tannants
    "320300": "kg",  # Colorants de synthèse
    # =========================================================================
    # CHAPITRE 33 - HUILES ESSENTIELLES
    # =========================================================================
    "330190": "kg",  # Autres huiles essentielles
    "330210": "kg",  # Alcools terpéniques
    # =========================================================================
    # CHAPITRE 34 - SAVONS, DÉTERGENTS
    # =========================================================================
    "340111": "kg",  # Savons
    "340119": "kg",  # Autres savons
    "340220": "kg",  # Détergents
    # =========================================================================
    # CHAPITRE 37 - PRODUITS PHOTOGRAPHIQUES
    # =========================================================================
    "370199": "kg",  # Autres produits photographiques
    # =========================================================================
    # CHAPITRE 38 - PRODUITS CHIMIQUES DIVERS
    # =========================================================================
    "380110": "kg",  # Graphite artificiel
    "380890": "kg",  # Autres produits chimiques
    # =========================================================================
    # CHAPITRE 40 - CAOUTCHOUC
    # =========================================================================
    "400121": "kg",  # Caoutchouc naturel coagulé
    "400129": "kg",  # Autres formes de caoutchouc naturel
    "400211": "kg",  # Latex de caoutchouc synthétique
    "400219": "kg",  # Autres caoutchoucs synthétiques
    # =========================================================================
    # CHAPITRE 41 - CUIRS
    # =========================================================================
    "410121": "kg",  # Cuir pleine fleur
    "410131": "kg",  # Autres cuirs de bovins
    # =========================================================================
    # CHAPITRE 42 - ARTICLES DE MAROQUINERIE
    # =========================================================================
    "420110": "nombre",  # Sacs de voyage, sacs à dos
    "420291": "nombre",  # Autres sacs en cuir
    "420292": "nombre",  # Sacs en matière textile
    # =========================================================================
    # CHAPITRE 43 - FOURRURES
    # =========================================================================
    "430110": "nombre",  # Peaux entières
    "430190": "nombre",  # Autres fourrures
    # =========================================================================
    # CHAPITRE 50 - SOIE
    # =========================================================================
    "500200": "kg",  # Soie grège
    "500300": "kg",  # Autres soies
    # =========================================================================
    # CHAPITRE 51 - LAINE
    # =========================================================================
    "510110": "kg",  # Laine brute
    "510210": "kg",  # Laine lavée
    # =========================================================================
    # CHAPITRE 52 - COTON
    # =========================================================================
    "520100": "kg",  # Coton brut
    "520210": "kg",  # Coton cardé
    "520220": "kg",  # Coton peigné
    # =========================================================================
    # CHAPITRE 54 - FILÉS SYNTHÉTIQUES
    # =========================================================================
    "540110": "kg",  # Filés de nylon
    "540120": "kg",  # Filés de polyester
    # =========================================================================
    # CHAPITRE 55 - FILÉS DE FIBRES SYNTHÉTIQUES
    # =========================================================================
    "550110": "kg",  # Filés de polyester
    "550120": "kg",  # Filés d'acrylique
    # =========================================================================
    # CHAPITRE 60 - TISSUS TRICOTÉS
    # =========================================================================
    "600190": "kg",  # Autres chaînes de velours
    "600210": "kg",  # Autres tissus tricotés de coton
    # =========================================================================
    # CHAPITRE 62 - VÊTEMENTS
    # =========================================================================
    "620190": "nombre",  # Autres chemises de coton
    "620211": "nombre",  # Robes de coton
    "620291": "nombre",  # Autres vêtements féminins
    "620311": "nombre",  # Costumes de coton
    "620391": "nombre",  # Autres vêtements masculins
    "620411": "nombre",  # Combinaisons de coton
    "620421": "nombre",  # Shorts de coton
    "620431": "nombre",  # Pantalons de coton
    "620451": "nombre",  # T-shirts de coton
    "620519": "nombre",  # Autres pulls
    "620591": "nombre",  # Autres vêtements tricotés
    "620610": "nombre",  # Chemises de homme
    "620620": "nombre",  # Robes, jupes de femme
    "620630": "nombre",  # Costumes, ensembles
    "620640": "nombre",  # Vestes, blazers
    "620650": "nombre",  # Shorts, bermudas
    "620661": "nombre",  # Pantalons longs de coton
    "620662": "nombre",  # Pantalons longs d'autres matières
    "620710": "nombre",  # Ceintures
    "620720": "nombre",  # Accessoires de vêtements
    # =========================================================================
    # CHAPITRE 63 - TEXTILES, CHIFFONS
    # =========================================================================
    "630121": "kg",  # Sacs d'emballage de coton
    "630131": "kg",  # Sacs d'emballage de jute
    # =========================================================================
    # CHAPITRE 64 - CHAUSSURES
    # =========================================================================
    "640110": "nombre",  # Chaussures de cuir de femmes
    "640120": "nombre",  # Chaussures de cuir d'hommes
    "640191": "nombre",  # Autres chaussures de cuir
    "640211": "nombre",  # Chaussures de textile de femmes
    "640219": "nombre",  # Autres chaussures de textile
    "640290": "nombre",  # Autres chaussures
    # =========================================================================
    # CHAPITRE 68 - ARTICLES EN PIERRE, CIMENT
    # =========================================================================
    "680100": "kg",  # Ardoise
    "680291": "tonnes",  # Granit de taille
    "680299": "tonnes",  # Autres pierres de taille
    # =========================================================================
    # CHAPITRE 69 - CÉRAMIQUES
    # =========================================================================
    "690110": "nombre",  # Briques de terre cuite
    "690200": "kg",  # Carreaux et pavés en terre cuite
    "690300": "kg",  # Tuiles en terre cuite
    # =========================================================================
    # CHAPITRE 70 - VERRE
    # =========================================================================
    "700591": "kg",  # Tôles de verre brut
    "700599": "kg",  # Autres verres
    "701091": "nombre",  # Verres pour lunettes
    "701099": "nombre",  # Autres verres optiques
    # =========================================================================
    # CHAPITRE 72 - FER ET ACIER
    # =========================================================================
    "720210": "tonnes",  # Minerai de fer grillé
    "720711": "tonnes",  # Fonte brute non affinée
    "720719": "tonnes",  # Autres fontes brutes
    "720811": "tonnes",  # Acier au carbone non allié brut
    "720825": "tonnes",  # Acier inoxydable brut
    # =========================================================================
    # CHAPITRE 73 - ARTICLES EN FER OU ACIER
    # =========================================================================
    "730210": "tonnes",  # Barres en fer ou acier
    "730300": "tonnes",  # Tuyaux, tubes
    "730411": "nombre",  # Accessoires de tuyauterie
    "730711": "kg",  # Clous
    "730790": "kg",  # Autres articles en fer/acier
    "730810": "nombre",  # Poutres, colonnes
    "730821": "nombre",  # Portes, fenêtres
    # =========================================================================
    # CHAPITRE 74 - CUIVRE
    # =========================================================================
    "740110": "tonnes",  # Cuivre pur non travaillé
    "740120": "tonnes",  # Cuivre pur brut
    "740200": "tonnes",  # Alliages de cuivre bruts
    "740311": "tonnes",  # Barres, baguettes de cuivre
    "740400": "tonnes",  # Tuyaux, tubes de cuivre
    # =========================================================================
    # CHAPITRE 75 - NICKEL
    # =========================================================================
    "750110": "kg",  # Nickel brut
    "750120": "kg",  # Nickel raffiné
    # =========================================================================
    # CHAPITRE 76 - ALUMINIUM
    # =========================================================================
    "760110": "tonnes",  # Aluminium non travaillé pur
    "760120": "tonnes",  # Aluminium non travaillé allié
    "760210": "tonnes",  # Barres, baguettes d'aluminium
    "760300": "tonnes",  # Tuyaux, tubes d'aluminium
    "760711": "kg",  # Feuilles et bandes d'aluminium
    "760800": "nombre",  # Articles moulés d'aluminium
    # =========================================================================
    # CHAPITRE 78 - PLOMB
    # =========================================================================
    "780110": "kg",  # Plomb pur brut
    "780120": "kg",  # Plomb raffiné
    # =========================================================================
    # CHAPITRE 79 - ZINC
    # =========================================================================
    "790110": "kg",  # Zinc pur brut
    "790120": "kg",  # Zinc raffiné
    # =========================================================================
    # CHAPITRE 81 - MÉTAUX DIVERS
    # =========================================================================
    "810210": "kg",  # Tungstène
    "810220": "kg",  # Molybdène
    "810300": "kg",  # Tantale
    "810490": "kg",  # Autres métaux précieux
    # =========================================================================
    # CHAPITRE 82 - OUTILS, COUTELLERIE
    # =========================================================================
    "820120": "nombre",  # Lames de rasoir
    "820130": "nombre",  # Couteaux de cuisine
    "820210": "nombre",  # Scies à main
    "820230": "nombre",  # Outils agricoles
    "820240": "nombre",  # Autres outils à main
    "820300": "nombre",  # Cuillères, fourchettes
    # =========================================================================
    # CHAPITRE 83 - ARTICLES DIVERS EN MÉTAUX
    # =========================================================================
    "830110": "nombre",  # Cadenas
    "830120": "nombre",  # Serrures
    "830129": "nombre",  # Autres dispositifs de fermeture
    "830210": "nombre",  # Charnières
    "830290": "nombre",  # Autres garnitures métalliques
    # =========================================================================
    # CHAPITRE 84 - MACHINES
    # =========================================================================
    "840110": "nombre",  # Chaudières à vapeur
    "840210": "nombre",  # Moteurs à vapeur
    "840290": "nombre",  # Autres moteurs
    "840410": "nombre",  # Pompes pour liquides
    "840420": "nombre",  # Pompes pour gaz
    "840490": "nombre",  # Parties de pompes
    "840590": "nombre",  # Autres machines hydrauliques
    "840610": "nombre",  # Turbines à vapeur
    "840690": "nombre",  # Parties de turbines
    "840710": "nombre",  # Moteurs à gaz
    "840820": "nombre",  # Moteurs à explosion
    "840991": "nombre",  # Autres moteurs
    "841011": "nombre",  # Réacteurs à fusion
    "841020": "nombre",  # Réacteurs nucléaires
    "841090": "nombre",  # Parties de réacteurs
    "841191": "nombre",  # Appareils de chauffage
    "841199": "nombre",  # Autres appareils de chauffage
    "841290": "nombre",  # Appareils de séchage
    "841380": "nombre",  # Fours, cuisinières
    "841481": "nombre",  # Réfrigérateurs de ménage
    "841482": "nombre",  # Congélateurs de ménage
    "841500": "nombre",  # Machines à laver le linge
    "841581": "nombre",  # Machines à laver la vaisselle
    "841590": "nombre",  # Autres appareils électroménagers
    "841680": "nombre",  # Autres appareils de nettoyage
    "841780": "nombre",  # Appareils de pesage
    "841890": "nombre",  # Autres machines
    "842010": "nombre",  # Machines agricoles
    "842030": "nombre",  # Autres machines de récolte
    "842040": "nombre",  # Autres machines agricoles
    "842110": "nombre",  # Machines de mouture
    "842190": "nombre",  # Machines de transformation d'aliments
    "842210": "nombre",  # Machines d'extraction
    "842290": "nombre",  # Autres machines minières
    "842310": "nombre",  # Machines de construction
    "842390": "nombre",  # Autres machines de terrassement
    "842410": "nombre",  # Machines de forage pétrolier
    "842490": "nombre",  # Autres machines pétrolières
    "842511": "nombre",  # Machines-outils pour métaux
    "842581": "nombre",  # Autres machines-outils
    "842590": "nombre",  # Parties de machines-outils
    "842610": "nombre",  # Machines de séparation
    "842690": "nombre",  # Autres machines de séparation
    "842710": "nombre",  # Machines pour textile
    "842790": "nombre",  # Parties de machines pour textile
    "842820": "nombre",  # Machines pour papier
    "842890": "nombre",  # Autres machines de traitement
    "842931": "nombre",  # Compresseurs, ventilateurs
    "842951": "nombre",  # Appareils de levage
    "842959": "nombre",  # Autres appareils de levage
    "843010": "nombre",  # Chaudières et réservoirs
    "843020": "nombre",  # Réservoirs de traitement
    "843039": "nombre",  # Autres réservoirs
    "843080": "nombre",  # Tuyauteries
    "843090": "nombre",  # Parties de tuyauteries
    # =========================================================================
    # CHAPITRE 85 - ÉLECTRIQUE
    # =========================================================================
    "850110": "nombre",  # Moteurs électriques > 1 MW
    "850120": "nombre",  # Moteurs électriques 0,75-1 MW
    "850131": "nombre",  # Moteurs électriques < 0,75 MW
    "850139": "nombre",  # Autres moteurs électriques
    "850140": "nombre",  # Générateurs électriques
    "850220": "nombre",  # Transformateurs électriques
    "850231": "nombre",  # Convertisseurs électriques
    "850239": "nombre",  # Autres convertisseurs
    "850290": "nombre",  # Parties de convertisseurs
    "850310": "nombre",  # Batterie primaire
    "850320": "nombre",  # Batterie rechargeable
    "850410": "nombre",  # Primaires électrochimiques
    "850421": "nombre",  # Batteries plomb
    "850422": "nombre",  # Batteries nickel-cadmium
    "850431": "nombre",  # Accumulateurs lithium
    "850432": "nombre",  # Autres accumulateurs
    "850450": "nombre",  # Autres accumulateurs
    "850510": "nombre",  # Électroaimants
    "850520": "nombre",  # Électro-aimants permanents
    "850590": "nombre",  # Parties d'électroaimants
    "850610": "nombre",  # Électrodes
    "850620": "nombre",  # Chauffage électrique
    "850631": "nombre",  # Lampes incandescence
    "850632": "nombre",  # Lampes fluorescentes
    "850639": "nombre",  # Autres lampes
    "850650": "nombre",  # Lampes à décharge
    "850661": "nombre",  # Lampes arc xénon
    "850669": "nombre",  # Autres lampes arc
    "850680": "nombre",  # Autres lampes, LED
    "850712": "nombre",  # Lampes filament W≤ 200W
    "850714": "nombre",  # Lampes filament W > 200W
    "850721": "nombre",  # Lampes autres tungstène
    "850722": "nombre",  # Lampes halogènes
    "850800": "nombre",  # Lampes ultraviolettes
    "850900": "nombre",  # Lampes infrarouges
    "851010": "nombre",  # Lampes portatives
    "851021": "nombre",  # Luminaires de plafond
    "851029": "nombre",  # Autres luminaires
    "851031": "nombre",  # Luminaires pour éclairage public
    "851039": "nombre",  # Autres luminaires publics
    "851041": "nombre",  # Luminaires publicitaires
    "851049": "nombre",  # Autres luminaires neon
    "851050": "nombre",  # Autres luminaires
    "851060": "nombre",  # Parties de luminaires
    "851071": "nombre",  # Lampes à arc de carbure
    "851079": "nombre",  # Autres lampes arc
    "851089": "nombre",  # Autres appareils électriques
    "851130": "nombre",  # Convertisseurs électrique
    "851140": "nombre",  # Onduleurs
    "851150": "nombre",  # Stabilisateurs électrique
    "851160": "nombre",  # Autres convertisseurs statiques
    "851180": "nombre",  # Autres appareils électriques
    "851210": "nombre",  # Chauffage électrique
    "851220": "nombre",  # Résistances électriques
    "851290": "nombre",  # Parties de chauffage électrique
    "851310": "nombre",  # Éléments chauffants
    "851320": "nombre",  # Thermostat électrique
    "851390": "nombre",  # Autres appareils électriques
    "851410": "nombre",  # Disjoncteurs électrique
    "851420": "nombre",  # Interrupteurs électrique
    "851430": "nombre",  # Relais électrique
    "851439": "nombre",  # Autres appareils électrique
    "851440": "nombre",  # Appareils de commutation
    "851450": "nombre",  # Appareils d'allumage
    "851490": "nombre",  # Parties de commutation
    "851511": "nombre",  # Connecteurs électrique
    "851521": "nombre",  # Prises électrique
    "851529": "nombre",  # Autres connecteurs
    "851580": "nombre",  # Accessoires électrique
    "851610": "nombre",  # Accumulateurs nickel-métal hydride
    "851620": "nombre",  # Accumulateurs lithium-ion
    "851630": "nombre",  # Autres accumulateurs
    "851640": "nombre",  # Piles jetables
    "851650": "nombre",  # Piles alcalines
    "851660": "nombre",  # Autres piles
    "851670": "nombre",  # Accumulateurs avec circuits
    "851680": "nombre",  # Parties d'accumulateurs
    "851690": "nombre",  # Autres accumulateurs
    "851710": "nombre",  # Piles galvaniques
    "851720": "nombre",  # Piles de Leclanché
    "851730": "nombre",  # Autres piles
    "851800": "nombre",  # Pile électrique
    "851900": "nombre",  # Électrodes, éléments électriques
    "852010": "nombre",  # Chauffe-eau électrique
    "852021": "nombre",  # Radiateur électrique
    "852029": "nombre",  # Autres appareils chauffants
    "852030": "nombre",  # Ventilateurs de ménage
    "852051": "nombre",  # Cuisinière électrique",
    "852059": "nombre",  # Autres appareils chauffants ménage
    "852061": "nombre",  # Réfrigérateurs électrique
    "852069": "nombre",  # Autres appareils frigorifiques
    "852071": "nombre",  # Machine à laver électrique
    "852072": "nombre",  # Sèche-linge électrique
    "852079": "nombre",  # Autres appareils électroménagers
    "852081": "nombre",  # Aspirateur électrique
    "852089": "nombre",  # Autres appareils nettoyage
    "852090": "nombre",  # Autres appareils électrique
    "852110": "nombre",  # Extracteur d'air
    "852120": "nombre",  # Appareil humidification
    "852130": "nombre",  # Appareil de filtration
    "852140": "nombre",  # Appareil climatisation
    "852190": "nombre",  # Autres appareils CLIM/ventilation
    "852210": "nombre",  # Sonnette électrique
    "852220": "nombre",  # Sirène électrique
    "852290": "nombre",  # Autres appareils électrique
    "852310": "nombre",  # Câble chauffant
    "852321": "nombre",  # Fusible électrique
    "852329": "nombre",  # Autres dispositifs électrique
    "852330": "nombre",  # Appareils électrique divers
    "852390": "nombre",  # Autres appareils électrique
    "852410": "nombre",  # Câbles électrique",
    "852421": "nombre",  # Câbles conducteurs
    "852429": "nombre",  # Autres câbles électriques
    "852430": "nombre",  # Autres appareils électrique
    "852441": "nombre",  # Fils isolés électrique
    "852449": "nombre",  # Autres fils isolés électrique
    "852451": "nombre",  # Autres fils, câbles
    "852459": "nombre",  # Fils, câbles optique",
    "852460": "nombre",  # Autres fils, câbles
    "852490": "nombre",  # Accessoires électrique
    "852510": "nombre",  # Ampoule de secours
    "852521": "nombre",  # Lampe d'éclairage
    "852529": "nombre",  # Autres lampes
    "852530": "nombre",  # Appareil électrique de sécurité
    "852540": "nombre",  # Chauffage de circuit
    "852590": "nombre",  # Parties d'appareils électrique
    "852610": "nombre",  # Appareils électrique de circuits
    "852620": "nombre",  # Bobines électrique
    "852630": "nombre",  # Condensateurs électrique
    "852640": "nombre",  # Résistances électrique
    "852651": "nombre",  # Appareils électrique divers
    "852652": "nombre",  # Thermostat électrique
    "852653": "nombre",  # Capteur électrique
    "852659": "nombre",  # Autres appareils électrique
    "852661": "nombre",  # Appareils électrique de chauffage
    "852669": "nombre",  # Autres appareils électrique
    "852670": "nombre",  # Appareils électrique de liaison
    "852680": "nombre",  # Parties appareils électrique
    "852690": "nombre",  # Autres appareils électrique
    "852710": "nombre",  # Appareils électrique sans pilote
    "852721": "nombre",  # Appareils électrique avec pilote
    "852722": "nombre",  # Appareils électrique commandé
    "852729": "nombre",  # Autres appareils électrique
    "852730": "nombre",  # Appareils électrique de chauffage
    "852741": "nombre",  # Chauffage de résistance
    "852749": "nombre",  # Autres appareils chauffage
    "852750": "nombre",  # Appareils électrique de commande
    "852761": "nombre",  # Thermostat électrique
    "852769": "nombre",  # Autres appareils électrique
    "852790": "nombre",  # Parties d'appareils électrique
    "852810": "nombre",  # Appareils électrique de sécurité
    "852821": "nombre",  # Fusible électrique
    "852829": "nombre",  # Autres appareils électrique
    "852830": "nombre",  # Appareils électrique de circuits
    "852840": "nombre",  # Appareils électrique sans contact
    "852850": "nombre",  # Partie appareils électrique
    "852861": "nombre",  # Appareil électrique thermoélectrique
    "852869": "nombre",  # Autres appareils électrique
    "852890": "nombre",  # Autres appareils électrique
    "852910": "nombre",  # Appareils électrique pour travail
    "852920": "nombre",  # Fusible, détecteur électrique
    "852930": "nombre",  # Appareils électrique de liaison
    "852990": "nombre",  # Autres appareils électrique
    "853010": "nombre",  # Bobine électrique
    "853021": "nombre",  # Condensateur électrique
    "853029": "nombre",  # Autres condensateurs
    "853031": "nombre",  # Résistance électrique
    "853039": "nombre",  # Autres résistances
    "853040": "nombre",  # Appareils électrique divers
    "853050": "nombre",  # Parties d'appareils électrique
    "853060": "nombre",  # Connecteurs électrique
    "853070": "nombre",  # Appareils électrique de circuits
    "853080": "nombre",  # Appareils électrique de soudage
    "853090": "nombre",  # Autres appareils électrique
    # =========================================================================
    # CHAPITRE 86 - VOIES FERRÉES
    # =========================================================================
    "860110": "nombre",  # Locomotives électrique
    "860120": "nombre",  # Locomotives thermique
    "860130": "nombre",  # Locomotives hybride
    "860210": "nombre",  # Voitures de passagers
    "860230": "nombre",  # Voitures de marchandises
    # =========================================================================
    # CHAPITRE 87 - VÉHICULES AUTOMOBILES
    # =========================================================================
    "870110": "nombre",  # Tracteur agricole
    "870190": "nombre",  # Autres tracteurs
    "870210": "nombre",  # Camion-bennes
    "870220": "nombre",  # Autres camions
    "870310": "nombre",  # Véhicule utilitaire
    "870410": "nombre",  # Monospace
    "870421": "nombre",  # Berline de tourisme
    "870422": "nombre",  # Break de tourisme
    "870431": "nombre",  # Coupé de tourisme
    "870432": "nombre",  # Cabriolet de tourisme
    "870511": "nombre",  # Autobus urbain
    "870512": "nombre",  # Autobus interurbain
    "870521": "nombre",  # Minibus de passagers
    "870530": "nombre",  # Autres autobus
    "870610": "nombre",  # Châssis avec moteur pour automobile
    "870620": "nombre",  # Autres châssis avec moteur
    "870711": "nombre",  # Carrosserie automobile
    "870712": "nombre",  # Cabine de camion
    "870720": "nombre",  # Autres carrosseries
    "870810": "nombre",  # Pare-chocs automobile
    "870821": "nombre",  # Portière automobile
    "870829": "nombre",  # Autres parties automobile
    "870830": "nombre",  # Sièges automobile
    "870840": "nombre",  # Autres parties automobile
    "870850": "nombre",  # Vitres automobile
    "870860": "nombre",  # Autres pièces automobile
    "870871": "nombre",  # Radiateur automobile
    "870879": "nombre",  # Autres pièces automobile
    "870880": "nombre",  # Système échappement automobile
    "870891": "nombre",  # Boîte vitesses automobile
    "870899": "nombre",  # Autres pièces automobile
    "870910": "nombre",  # Réservoirs carburant automobile
    "870921": "nombre",  # Pompe carburant automobile
    "870929": "nombre",  # Autres systèmes carburant
    "870931": "nombre",  # Système allumage automobile
    "870939": "nombre",  # Autres système automobile
    "870940": "nombre",  # Câblage automobile
    "870950": "nombre",  # Autres pièces automobile
    "870960": "nombre",  # Pièces pneumatique
    "870990": "nombre",  # Autres pièces automobile
    # =========================================================================
    # CHAPITRE 88 - AÉRONAUTIQUE
    # =========================================================================
    "880110": "nombre",  # Avion > 15 000 kg
    "880120": "nombre",  # Avion ≤ 15 000 kg
    "880130": "nombre",  # Autres aéronefs
    "880210": "nombre",  # Hélicoptères
    "880220": "nombre",  # Autres aéronefs
    "880310": "nombre",  # Pièces d'avion
    "880320": "nombre",  # Autres pièces aéronautiques
    "880330": "nombre",  # Accessoires aéronautiques
    # =========================================================================
    # CHAPITRE 89 - MARINE
    # =========================================================================
    "890111": "nombre",  # Navire à passagers
    "890112": "nombre",  # Navire-citerne
    "890113": "nombre",  # Navire de charge
    "890120": "nombre",  # Autres navires
    "890210": "nombre",  # Bateau de pêche
    "890220": "nombre",  # Autres bateaux
    "890290": "nombre",  # Autres navires
    "890300": "nombre",  # Pièces de navires
    # =========================================================================
    # CHAPITRE 90 - INSTRUMENTS DE PRÉCISION
    # =========================================================================
    "900110": "nombre",  # Verres de lentille optique
    "900120": "nombre",  # Éléments optiques
    "900130": "nombre",  # Filtres optiques
    "900180": "nombre",  # Autres instruments optiques
    "900190": "nombre",  # Parties d'instruments optiques
    "900210": "nombre",  # Verres pour lunettes
    "900220": "nombre",  # Verres ophtalmiques
    "900290": "nombre",  # Autres verres optiques
    "900310": "nombre",  # Montures de lunettes
    "900320": "nombre",  # Parties de lunettes
    "900410": "nombre",  # Microscope optique
    "900420": "nombre",  # Microscope électronique
    "900490": "nombre",  # Parties de microscopes
    "900511": "nombre",  # Appareil de visée sur fusil
    "900519": "nombre",  # Autres appareils de visée
    "900520": "nombre",  # Autres appareils optiques
    "900610": "nombre",  # Photomètre
    "900620": "nombre",  # Spectrophotomètre
    "900690": "nombre",  # Autres appareils optiques
    "900710": "nombre",  # Appareil photo numérique
    "900720": "nombre",  # Appareil photo film argentique
    "900730": "nombre",  # Vidéo caméra
    "900740": "nombre",  # Projecteur cinéma
    "900750": "nombre",  # Autres appareils optiques
    "900810": "nombre",  # Appareil de projection
    "900820": "nombre",  # Vidéo projecteur
    "900830": "nombre",  # Projecteur de film
    "900890": "nombre",  # Autres appareils optiques
    "900910": "nombre",  # Télémètre
    "900920": "nombre",  # Théodolite
    "900930": "nombre",  # Niveau optique
    "900940": "nombre",  # Autres instruments de mesure
    "900950": "nombre",  # Accessoires optiques
    "901000": "nombre",  # Autres instruments optiques
    "901010": "nombre",  # Microscope
    "901020": "nombre",  # Loupe
    "901030": "nombre",  # Autres instruments optiques
    "901040": "nombre",  # Parties d'instruments optiques
    "901050": "nombre",  # Instruments optiques divers
    "901081": "nombre",  # Chronomètre de marine
    "901089": "nombre",  # Autres instruments de mesure
    "901090": "nombre",  # Parties d'instruments optiques
    "901110": "nombre",  # Stéthoscope
    "901120": "nombre",  # Spiromètre
    "901190": "nombre",  # Autres instruments médicaux
    "901210": "nombre",  # Autres instruments chirurgicaux
    "901220": "nombre",  # Instruments dentaires
    "901290": "nombre",  # Autres instruments médicaux
    "901310": "nombre",  # Autres instruments médicaux
    "901320": "nombre",  # Instruments chirurgicaux
    "901330": "nombre",  # Autres instruments médicaux
    "901340": "nombre",  # Instruments pour analyses médicales
    "901350": "nombre",  # Autres instruments médicaux
    "901360": "nombre",  # Autres instruments médicaux
    "901370": "nombre",  # Autres instruments médicaux
    "901380": "nombre",  # Autres instruments médicaux
    "901390": "nombre",  # Autres instruments médicaux
    "901410": "nombre",  # Rangement pour instruments médicaux
    "901420": "nombre",  # Boîtes pour instruments médicaux
    "901430": "nombre",  # Autres boîtes instruments
    "901490": "nombre",  # Parties d'instruments médicaux
    "901510": "nombre",  # Thermomètre
    "901520": "nombre",  # Pyromètre
    "901530": "nombre",  # Manomètre
    "901540": "nombre",  # Hygromètre
    "901550": "nombre",  # Densimètre
    "901560": "nombre",  # Viscosimètre
    "901570": "nombre",  # Autres instruments de mesure
    "901580": "nombre",  # Parties d'instruments de mesure
    "901590": "nombre",  # Parties d'instruments de mesure
    "901600": "nombre",  # Balances sensibles (≤ 5 cg)
    "901700": "nombre",  # Instruments de dessin/traçage/calcul
    # Position 9018 — instruments médicaux : unités par sous-position EXACTE
    # (les aiguilles/seringues se comptent en pièces, PAS héritées du chapitre)
    "901811": "nombre",  # Électrocardiographes
    "901812": "nombre",  # Appareils d'échographie
    "901813": "nombre",  # Appareils IRM
    "901814": "nombre",  # Appareils de scintigraphie
    "901819": "nombre",  # Autres appareils d'électrodiagnostic
    "901820": "nombre",  # Appareils à rayons UV/IR
    "901831": "nombre",  # Seringues, avec ou sans aiguilles
    "901832": "nombre",  # Aiguilles tubulaires en métal, aiguilles à sutures
    "901839": "nombre",  # Cathéters, canules et instruments similaires
    "901841": "nombre",  # Tours dentaires
    "901849": "nombre",  # Autres instruments dentaires
    "901850": "nombre",  # Instruments d'ophtalmologie
    "901890": "nombre",  # Autres instruments médicaux/chirurgicaux
    "901910": "nombre",  # Appareils de mécanothérapie/massage
    "901920": "nombre",  # Appareils d'ozonothérapie/oxygénothérapie/aérosols
    "902000": "nombre",  # Autres appareils respiratoires et masques à gaz
    "902100": "nombre",  # Autres horloges
    "902210": "nombre",  # Chronomètre à quartz
    "902220": "nombre",  # Autres chronomètres
    "902300": "nombre",  # Autres instruments de mesure
    "902400": "nombre",  # Instruments météorologiques
    "902500": "nombre",  # Instruments géodésiques
    "902600": "nombre",  # Instruments de géométrie
    "902700": "nombre",  # Accessoires instruments mesure
    "902800": "nombre",  # Autres instruments optiques
    "902900": "nombre",  # Autres instruments optiques
    "903010": "nombre",  # Instruments de navigation
    "903020": "nombre",  # Compas de navigation
    "903030": "nombre",  # Autres instruments navigation
    "903040": "nombre",  # Sextant
    "903050": "nombre",  # Autres instruments optiques
    "903060": "nombre",  # Accessoires instruments navigation
    "903070": "nombre",  # Autres instruments de navigation
    "903080": "nombre",  # Autres instruments de mesure
    "903090": "nombre",  # Autres instruments optiques
    "903100": "nombre",  # Autres instruments optiques
    # =========================================================================
    # CHAPITRE 91 - HORLOGERIE
    # =========================================================================
    "910110": "nombre",  # Montres bracelets électroniques
    "910120": "nombre",  # Montres bracelets mécanique
    "910191": "nombre",  # Autres montres bracelets
    "910210": "nombre",  # Montres de poche électroniques
    "910220": "nombre",  # Montres de poche mécanique
    "910291": "nombre",  # Autres montres de poche
    "910310": "nombre",  # Instruments chronométriques
    "910390": "nombre",  # Autres instruments horlogerie
    "910410": "nombre",  # Parties électroniques horlogerie
    "910420": "nombre",  # Autres parties horlogerie
    "910500": "nombre",  # Mouvements horlogerie
    "910600": "nombre",  # Boîtes horlogerie
    # =========================================================================
    # CHAPITRE 92 - INSTRUMENTS DE MUSIQUE
    # =========================================================================
    "920110": "nombre",  # Piano acoustique
    "920120": "nombre",  # Autres pianos
    "920190": "nombre",  # Parties de pianos
    "920210": "nombre",  # Orgue
    "920220": "nombre",  # Harmonica
    "920290": "nombre",  # Autres instruments à vent
    "920300": "nombre",  # Orgue mécanique
    "920400": "nombre",  # Gramophone
    "920510": "nombre",  # Instruments à cordes
    "920590": "nombre",  # Autres instruments à cordes
    "920610": "nombre",  # Instruments à percussion
    "920690": "nombre",  # Autres instruments à percussion
    "920700": "nombre",  # Instruments électriques
    "920800": "nombre",  # Parties d'instruments musique
    "920900": "nombre",  # Accessoires instruments musique
    # =========================================================================
    # CHAPITRE 94 - MEUBLES
    # =========================================================================
    "940110": "nombre",  # Sièges de bureau
    "940120": "nombre",  # Sièges de ménage
    "940130": "nombre",  # Autres sièges
    "940161": "nombre",  # Lits de ménage
    "940169": "nombre",  # Autres lits
    "940171": "nombre",  # Tables de ménage
    "940179": "nombre",  # Autres tables
    "940180": "nombre",  # Autres meubles
    "940190": "nombre",  # Parties de meubles
    "940210": "nombre",  # Meubles de cuisine
    "940220": "nombre",  # Meubles de chambre
    "940230": "nombre",  # Meubles de salon
    "940290": "nombre",  # Autres meubles
    "940300": "nombre",  # Parties de meubles
    # =========================================================================
    # CHAPITRE 95 - JOUETS, JEUX SPORTIFS
    # =========================================================================
    "950110": "nombre",  # Jouets peluches
    "950120": "nombre",  # Jouets plastique
    "950191": "nombre",  # Autres jouets
    "950192": "nombre",  # Jeux de société
    "950193": "nombre",  # Puzzles
    "950200": "nombre",  # Articles pour cyclisme
    "950310": "nombre",  # Articles pour sports d'hiver
    "950320": "nombre",  # Articles pour sports nautiques
    "950330": "nombre",  # Articles pour sports de raquette
    "950340": "nombre",  # Articles pour sports de ballon
    "950390": "nombre",  # Autres articles de sport
    "950410": "nombre",  # Matériel de pêche
    "950420": "nombre",  # Équipement de camping
    "950430": "nombre",  # Équipement de tennis
    "950490": "nombre",  # Autres articles de sport
    "950500": "nombre",  # Autres articles de sport
    # =========================================================================
    # CHAPITRE 96 - ARTICLES DIVERS
    # =========================================================================
    "960110": "nombre",  # Peignes
    "960120": "nombre",  # Autres articles de toilette
    "960190": "nombre",  # Autres articles en matière plastique
    "960210": "nombre",  # Brosses
    "960220": "nombre",  # Balais
    "960230": "nombre",  # Balais mécaniques
    "960290": "nombre",  # Autres articles de balayage
    "960300": "nombre",  # Brosses de voyage
    "960410": "nombre",  # Articles de voyage
    "960420": "nombre",  # Mallettes
    "960490": "nombre",  # Autres articles de voyage
    "960500": "nombre",  # Articles de voyage
    "960610": "nombre",  # Perruques
    "960620": "nombre",  # Postiches
    "960690": "nombre",  # Autres articles capillaires
    "960700": "nombre",  # Fleurs artificielles
    "960810": "nombre",  # Boutons
    "960820": "nombre",  # Fermetures éclair
    "960830": "nombre",  # Pressions
    "960840": "nombre",  # Autres accessoires textile
    "960850": "nombre",  # Autres articles textile
    "960900": "nombre",  # Épingles, aiguilles
    "971000": "nombre",  # Bijouterie fantaisie
    "971100": "nombre",  # Bijouterie costume
    "971200": "nombre",  # Accessoires vestimentaires
    "971300": "nombre",  # Montres fantaisie
    "971400": "nombre",  # Bijouterie moulée
    "971500": "nombre",  # Bijouterie estampée
    "971600": "nombre",  # Bijouterie en chaîne
    "971700": "nombre",  # Bijouterie maille
}


def get_supplementary_unit(hs_code: Optional[str]) -> Optional[str]:
    """Retourne l'unité complémentaire pour un code HS6 EXACT, sinon None.

    Pas de repli sur le préfixe HS4 : au sein d'une même position SH4, les
    sous-positions peuvent avoir des unités différentes (ex. 9018 : les
    aiguilles/seringues 901831-32 se comptent en pièces, d'autres instruments
    du même chapitre en kg) — hériter de l'unité d'un cousin de chapitre
    afficherait une unité qui ne reflète pas le produit. Mieux vaut None
    (le front n'affiche rien) qu'une unité trompeuse.
    """
    clean_code = "".join(c for c in (hs_code or "") if c.isdigit())
    if len(clean_code) >= 6:
        return HS6_SUPPLEMENTARY_UNITS.get(clean_code[:6])
    return None


def get_unit_label(unit: str, language: str = "fr") -> str:
    """Retourne le label localisé de l'unité."""
    unit_labels = {
        "fr": {
            "kg": "kilogrammes",
            "tonnes": "tonnes",
            "litres": "litres",
            "nombre": "nombre de pièces",
            "nombre d'unités": "nombre d'unités",
            "paires": "paires",
            "12 pièces": "douzaines",
            "100 pièces": "centaines",
            "1000 pièces": "milliers",
            "mètres": "mètres linéaires",
            "m²": "mètres carrés",
            "m³": "mètres cubes",
        },
        "en": {
            "kg": "kilograms",
            "tonnes": "metric tons",
            "litres": "liters",
            "nombre": "number of pieces",
            "nombre d'unités": "number of units",
            "paires": "pairs",
            "12 pièces": "dozens",
            "100 pièces": "hundreds",
            "1000 pièces": "thousands",
            "mètres": "linear meters",
            "m²": "square meters",
            "m³": "cubic meters",
        },
    }

    labels = unit_labels.get(language, unit_labels["fr"])
    return labels.get(unit, unit)
