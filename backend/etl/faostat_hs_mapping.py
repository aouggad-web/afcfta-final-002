"""
Pont SH → commodités FAOSTAT, dérivé de correspondances publiées.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/build_faostat_hs_mapping.py`` — NE PAS
ÉDITER À LA MAIN.

Chaîne de dérivation, deux maillons publiés :
  1. item FAOSTAT → CPC v2.1  (membre ``*_ItemCodes.csv`` du bulk FAOSTAT)
  2. CPC v2.1 → SH 2017       (table officielle UNSD ``CPC21-HS2017.csv``,
     https://unstats.un.org/unsd/classifications/Econ)

Aucune attribution au jugé : rattacher une production au mauvais produit
échangé tromperait le module Opportunités plus sûrement qu'une absence.

Cette liste est ADDITIVE. Les codes SH que la table curée de
``services/production_capacity_service.py`` résout déjà n'y figurent pas :
le pont existant garde son comportement, tests compris.

Généré le : 2026-09-21T19:42:42.932851+00:00
Bilan de génération :
#   SH revendiqués par plusieurs items     119
#   agrégats écartés                       21
#   déjà couverts par la table curée       208
#   résolus (exact)                        213
#   résolus (groupe)                       20
#   codes SH ajoutés                       38
#   libellés distincts atteints            25
"""

from __future__ import annotations

from typing import FrozenSet, List, Tuple

#: (préfixe SH, dataset, libellé de commodité) — même format que
#: ``production_capacity_service.HS_TO_COMMODITY``, dont cette liste est
#: l'extension générée.
FAOSTAT_HS_TO_COMMODITY: List[Tuple[str, str, str]] = [
    ("020311", "agri", "Meat of pig with the bone, fresh or chilled"),
    ("020312", "agri", "Meat of pig with the bone, fresh or chilled"),
    ("020319", "agri", "Meat of pig with the bone, fresh or chilled"),
    ("020410", "agri", "Meat of sheep, fresh or chilled"),
    ("020421", "agri", "Meat of sheep, fresh or chilled"),
    ("020422", "agri", "Meat of sheep, fresh or chilled"),
    ("020423", "agri", "Meat of sheep, fresh or chilled"),
    ("020450", "agri", "Meat of goat, fresh or chilled"),
    ("020630", "agri", "Edible offal of pigs, fresh, chilled or frozen"),
    ("020641", "agri", "Edible offal of pigs, fresh, chilled or frozen"),
    ("020649", "agri", "Edible offal of pigs, fresh, chilled or frozen"),
    ("020910", "agri", "Fat of pigs"),
    ("020990", "agri", "Fat of pigs"),
    (
        "030760",
        "agri",
        "Snails, fresh, chilled, frozen, dried, salted or in brine, except sea snails",
    ),
    ("040210", "agri", "Skim milk and whey powder"),
    ("040221", "agri", "Whole milk powder"),
    ("040229", "agri", "Whole milk powder"),
    ("040299", "agri", "Whole milk, condensed"),
    ("040410", "agri", "Whey, dry"),
    ("040900", "agri", "Natural honey"),
    ("070390", "agri", "Leeks and other alliaceous vegetables"),
    ("080719", "agri", "Cantaloupes and other melons"),
    ("080910", "agri", "Apricots"),
    ("080921", "agri", "Cherries"),
    ("080929", "agri", "Cherries"),
    ("080930", "agri", "Peaches and nectarines"),
    ("080940", "agri", "Plums and sloes"),
    ("081010", "agri", "Strawberries"),
    ("081020", "agri", "Raspberries"),
    ("081030", "agri", "Currants"),
    ("081050", "agri", "Kiwi fruit"),
    ("081060", "agri", "Other tropical fruits, n.e.c."),
    ("121010", "agri", "Hop cones"),
    ("121020", "agri", "Hop cones"),
    ("410210", "agri", "Raw hides and skins of sheep or lambs"),
    ("410221", "agri", "Raw hides and skins of sheep or lambs"),
    ("410229", "agri", "Raw hides and skins of sheep or lambs"),
    ("410390", "agri", "Raw hides and skins of goats or kids"),
]

#: Commodités FAOSTAT qu'AU MOINS un code SH atteint — soit par une entrée
#: ci-dessus, soit parce que la table curée y pointait déjà.
#:
#: L'ingestion s'en sert comme FILTRE : une commodité absente de cet ensemble
#: n'entre pas dans ``production_africaine.json``. L'invariant du dépôt
#: (tests/test_hs_commodity_mapping.py) est ainsi tenu par construction, et non
#: par vigilance — toute commodité ingérée est joignable par un code SH, donc
#: exploitable par le module Opportunités.
FAOSTAT_REACHABLE_COMMODITIES: FrozenSet[str] = frozenset(
    {
        "Almonds",
        "Apples",
        "Apricots",
        "Avocados",
        "Bananas",
        "Barley",
        "Beans",
        "Cabbages",
        "Cantaloupes and other melons",
        "Carrots",
        "Cashew nuts",
        "Cassava",
        "Cattle meat",
        "Cattle milk",
        "Cauliflowers",
        "Cherries",
        "Chicken meat",
        "Chickpeas",
        "Chillies and peppers",
        "Cinnamon",
        "Cloves",
        "Cocoa beans",
        "Coffee",
        "Cowpeas",
        "Cucumbers",
        "Currants",
        "Dates",
        "Edible offal of pigs, fresh, chilled or frozen",
        "Eggplants",
        "Fat of pigs",
        "Ginger",
        "Grapes",
        "Groundnuts",
        "Hen eggs",
        "Hop cones",
        "Kiwi fruit",
        "Kola nuts",
        "Leeks and other alliaceous vegetables",
        "Lemons and limes",
        "Lentils",
        "Lettuce",
        "Linseed",
        "Maize (corn)",
        "Mangoes",
        "Meat of goat, fresh or chilled",
        "Meat of pig with the bone, fresh or chilled",
        "Meat of sheep, fresh or chilled",
        "Millet",
        "Natural honey",
        "Oats",
        "Oil palm",
        "Okra",
        "Olives",
        "Onions",
        "Oranges",
        "Other tropical fruits, n.e.c.",
        "Papayas",
        "Peaches and nectarines",
        "Peas",
        "Pepper",
        "Pigeon peas",
        "Pineapples",
        "Plantain",
        "Plums and sloes",
        "Potatoes",
        "Rapeseed",
        "Raspberries",
        "Raw hides and skins of goats or kids",
        "Raw hides and skins of sheep or lambs",
        "Rice",
        "Rubber",
        "Seed cotton",
        "Sesame",
        "Shea nuts",
        "Skim milk and whey powder",
        "Snails, fresh, chilled, frozen, dried, salted or in brine, except sea snails",
        "Sorghum",
        "Soybeans",
        "Spinach",
        "Strawberries",
        "Sugarcane",
        "Sunflower seed",
        "Sweet potatoes",
        "Tea",
        "Tobacco",
        "Tomatoes",
        "Vanilla",
        "Watermelons",
        "Wheat",
        "Whey, dry",
        "Whole milk powder",
        "Whole milk, condensed",
        "Yam",
    }
)

# Commodités écartées faute de code SH qui leur soit propre. La cause n'est pas
# une lacune de la correspondance : ce sont des cas où UN code SH recouvre
# PLUSIEURS commodités FAOSTAT — le SH 0201 « viande de bovins » vaut pour les
# bovins et les buffles, le SH 0205 pour les chevaux et les ânes. Le pont
# n'associe qu'un libellé par préfixe ; trancher reviendrait à attribuer une
# production au mauvais produit. Elles restent donc hors ingestion, en
# attendant que le pont sache exprimer une relation un-à-plusieurs.
#
#   Abaca, manila hemp, raw
#   Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw
#   Areca nuts
#   Artichokes
#   Asparagus
#   Bambara beans, dry
#   Beer of barley, malted
#   Beeswax
#   Blueberries
#   Brazil nuts, in shell
#   Broad beans and horse beans, dry
#   Broad beans and horse beans, green
#   Buckwheat
#   Buffalo fat, unrendered
#   Butter and ghee of sheep milk
#   Butter of buffalo milk
#   Butter of cow milk
#   Buttermilk, dry
#   Canary seed
#   Cashewapple
#   Cassava leaves
#   Castor oil seeds
#   Cattle fat, unrendered
#   Cereals n.e.c.
#   Cheese from milk of buffalo, fresh or processed
#   Cheese from milk of goats, fresh or processed
#   Cheese from milk of sheep, fresh or processed
#   Cheese from skimmed cow milk
#   Cheese from whole cow milk
#   Chestnuts, in shell
#   Chicory roots
#   Coconut oil
#   Coconuts
#   Coir, raw
#   Cotton lint, ginned
#   Cotton seed
#   Cottonseed oil
#   Cranberries
#   Cream, fresh
#   Edible offal of buffalo, fresh, chilled or frozen
#   Edible offal of cattle, fresh, chilled or frozen
#   Edible offal of goat, fresh, chilled or frozen
#   Edible offal of sheep, fresh, chilled or frozen
#   Edible offals of camels and other camelids, fresh, chilled or frozen
#   Edible offals of horses and other equines, fresh, chilled or frozen
#   Edible roots and tubers with high starch or inulin content, n.e.c., fresh
#   Eggs from other birds in shell, fresh, n.e.c.
#   Fat of camels
#   Figs
#   Flax, raw or retted
#   Fonio
#   Game meat, fresh, chilled or frozen
#   Ghee from cow milk
#   Goat fat, unrendered
#   Green corn (maize)
#   Green garlic
#   Green tea (not fermented), black tea (fermented) and partly fermented tea, in immediate packings of a content not exceeding 3 kg
#   Groundnut oil
#   Hazelnuts, in shell
#   Horse meat, fresh or chilled
#   Jute, raw or retted
#   Kenaf, and other textile bast fibres, raw or retted
#   Locust beans (carobs)
#   Lupins
#   Margarine and shortening
#   Meat of asses, fresh or chilled
#   Meat of buffalo, fresh or chilled
#   Meat of camels, fresh or chilled
#   Meat of ducks, fresh or chilled
#   Meat of geese, fresh or chilled
#   Meat of pigeons and other birds n.e.c., fresh, chilled or frozen
#   Meat of rabbits and hares, fresh or chilled
#   Meat of turkeys, fresh or chilled
#   Melonseed
#   Molasses
#   Mushrooms and truffles
#   Mustard seed
#   Nutmeg, mace, cardamoms, raw
#   Oil of linseed
#   Oil of maize
#   Oil of palm kernel
#   Oil of sesame seed
#   Olive oil
#   Onions and shallots, green
#   Other beans, green
#   Other berries and fruits of the genus vaccinium n.e.c.
#   Other citrus fruit, n.e.c.
#   Other fibre crops, raw, n.e.c.
#   Other fruits, n.e.c.
#   Other meat of mammals, fresh or chilled
#   Other nuts (excluding wild edible nuts and groundnuts), in shell, n.e.c.
#   Other oil seeds, n.e.c.
#   Other pulses n.e.c.
#   Other stimulant, spice and aromatic crops, n.e.c.
#   Other stone fruits
#   Other vegetables, fresh n.e.c.
#   Palm kernels
#   Pears
#   Peas, green
#   Peppermint, spearmint
#   Pig fat, rendered
#   Pistachios, in shell
#   Pomelos and grapefruits
#   Pumpkins, squash and gourds
#   Pyrethrum, dried flowers
#   Quinces
#   Rapeseed or canola oil, crude
#   Raw cane or beet sugar (centrifugal only)
#   Raw hides and skins of buffaloes
#   Raw hides and skins of cattle
#   Raw milk of buffalo
#   Raw milk of camel
#   Raw milk of goats
#   Raw milk of sheep
#   Raw silk (not thrown)
#   Rye
#   Safflower seed
#   Safflower-seed oil, crude
#   Sheep fat, unrendered
#   Shorn wool, greasy, including fleece-washed shorn wool
#   Silk-worm cocoons suitable for reeling
#   Sisal, raw
#   Skim milk of cows
#   Skim milk, evaporated
#   Soya bean oil
#   String beans
#   Sugar beet
#   Sunflower-seed oil, crude
#   Tallow
#   Tangerines, mandarins, clementines
#   Taro
#   Triticale
#   Tung nuts
#   Vetches
#   Walnuts, in shell
#   Whole milk, evaporated
#   Wine
#   Yoghurt
