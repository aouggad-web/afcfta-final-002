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

Généré le : 2026-09-22T09:13:04.869245+00:00
Bilan de génération :
#   SH revendiqués par plusieurs items     224
#   agrégats écartés                       21
#   déjà couverts par la table curée       10
#   précisent un repli plus large          255
#   résolus (exact)                        213
#   résolus (groupe)                       20
#   codes SH ajoutés                       201
#   libellés distincts atteints            126
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
    ("020711", "agri", "Chicken meat"),
    ("020713", "agri", "Chicken meat"),
    ("020724", "agri", "Meat of turkeys, fresh or chilled"),
    ("020726", "agri", "Meat of turkeys, fresh or chilled"),
    ("020741", "agri", "Meat of ducks, fresh or chilled"),
    ("020744", "agri", "Meat of ducks, fresh or chilled"),
    ("020751", "agri", "Meat of geese, fresh or chilled"),
    ("020754", "agri", "Meat of geese, fresh or chilled"),
    ("020910", "agri", "Fat of pigs"),
    ("020990", "agri", "Fat of pigs"),
    ("030760", "agri", "Snails, fresh, chilled, frozen, dried, salted or in brine, except sea snails"),
    ("040110", "agri", "Skim milk of cows"),
    ("040210", "agri", "Skim milk and whey powder"),
    ("040221", "agri", "Whole milk powder"),
    ("040229", "agri", "Whole milk powder"),
    ("040299", "agri", "Whole milk, condensed"),
    ("040410", "agri", "Whey, dry"),
    ("040711", "agri", "Hen eggs"),
    ("040719", "agri", "Eggs from other birds in shell, fresh, n.e.c."),
    ("040721", "agri", "Hen eggs"),
    ("040729", "agri", "Eggs from other birds in shell, fresh, n.e.c."),
    ("040900", "agri", "Natural honey"),
    ("070110", "agri", "Potatoes"),
    ("070190", "agri", "Potatoes"),
    ("070200", "agri", "Tomatoes"),
    ("070390", "agri", "Leeks and other alliaceous vegetables"),
    ("070420", "agri", "Cabbages"),
    ("070490", "agri", "Cabbages"),
    ("070511", "agri", "Lettuce"),
    ("070519", "agri", "Lettuce"),
    ("070521", "agri", "Lettuce"),
    ("070529", "agri", "Lettuce"),
    ("070700", "agri", "Cucumbers"),
    ("070810", "agri", "Peas, green"),
    ("070890", "agri", "Broad beans and horse beans, green"),
    ("070920", "agri", "Asparagus"),
    ("070951", "agri", "Mushrooms and truffles"),
    ("070959", "agri", "Mushrooms and truffles"),
    ("070991", "agri", "Artichokes"),
    ("070992", "agri", "Olives"),
    ("070993", "agri", "Pumpkins, squash and gourds"),
    ("071331", "agri", "Beans"),
    ("071332", "agri", "Beans"),
    ("071334", "agri", "Bambara beans, dry"),
    ("071335", "agri", "Cowpeas"),
    ("071339", "agri", "Beans"),
    ("071350", "agri", "Broad beans and horse beans, dry"),
    ("071410", "agri", "Cassava"),
    ("071440", "agri", "Taro"),
    ("071490", "agri", "Edible roots and tubers with high starch or inulin content, n.e.c., fresh"),
    ("080112", "agri", "Coconuts"),
    ("080119", "agri", "Coconuts"),
    ("080121", "agri", "Brazil nuts, in shell"),
    ("080131", "agri", "Cashew nuts"),
    ("080221", "agri", "Hazelnuts, in shell"),
    ("080231", "agri", "Walnuts, in shell"),
    ("080241", "agri", "Chestnuts, in shell"),
    ("080251", "agri", "Pistachios, in shell"),
    ("080310", "agri", "Plantain"),
    ("080410", "agri", "Dates"),
    ("080420", "agri", "Figs"),
    ("080521", "agri", "Tangerines, mandarins, clementines"),
    ("080522", "agri", "Tangerines, mandarins, clementines"),
    ("080529", "agri", "Tangerines, mandarins, clementines"),
    ("080540", "agri", "Pomelos and grapefruits"),
    ("080590", "agri", "Other citrus fruit, n.e.c."),
    ("080610", "agri", "Grapes"),
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
    ("090111", "agri", "Coffee"),
    ("090210", "agri", "Green tea (not fermented), black tea (fermented) and partly fermented tea, in immediate packings of a content not exceeding 3 kg"),
    ("090220", "agri", "Tea"),
    ("090230", "agri", "Green tea (not fermented), black tea (fermented) and partly fermented tea, in immediate packings of a content not exceeding 3 kg"),
    ("090240", "agri", "Tea"),
    ("090411", "agri", "Pepper"),
    ("090421", "agri", "Chillies and peppers"),
    ("090510", "agri", "Vanilla"),
    ("090611", "agri", "Cinnamon"),
    ("090619", "agri", "Cinnamon"),
    ("090710", "agri", "Cloves"),
    ("090811", "agri", "Nutmeg, mace, cardamoms, raw"),
    ("090821", "agri", "Nutmeg, mace, cardamoms, raw"),
    ("090831", "agri", "Nutmeg, mace, cardamoms, raw"),
    ("090921", "agri", "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw"),
    ("090931", "agri", "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw"),
    ("090961", "agri", "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw"),
    ("091011", "agri", "Ginger"),
    ("091020", "agri", "Other stimulant, spice and aromatic crops, n.e.c."),
    ("091030", "agri", "Other stimulant, spice and aromatic crops, n.e.c."),
    ("091091", "agri", "Other stimulant, spice and aromatic crops, n.e.c."),
    ("091099", "agri", "Other stimulant, spice and aromatic crops, n.e.c."),
    ("100111", "agri", "Wheat"),
    ("100119", "agri", "Wheat"),
    ("100191", "agri", "Wheat"),
    ("100199", "agri", "Wheat"),
    ("100210", "agri", "Rye"),
    ("100290", "agri", "Rye"),
    ("100310", "agri", "Barley"),
    ("100390", "agri", "Barley"),
    ("100410", "agri", "Oats"),
    ("100490", "agri", "Oats"),
    ("100510", "agri", "Maize (corn)"),
    ("100590", "agri", "Maize (corn)"),
    ("100610", "agri", "Rice"),
    ("100710", "agri", "Sorghum"),
    ("100790", "agri", "Sorghum"),
    ("100810", "agri", "Buckwheat"),
    ("100821", "agri", "Millet"),
    ("100829", "agri", "Millet"),
    ("100830", "agri", "Canary seed"),
    ("100840", "agri", "Fonio"),
    ("100860", "agri", "Triticale"),
    ("100890", "agri", "Cereals n.e.c."),
    ("120110", "agri", "Soybeans"),
    ("120190", "agri", "Soybeans"),
    ("120230", "agri", "Groundnuts"),
    ("120241", "agri", "Groundnuts"),
    ("120400", "agri", "Linseed"),
    ("120510", "agri", "Rapeseed"),
    ("120590", "agri", "Rapeseed"),
    ("120600", "agri", "Sunflower seed"),
    ("120721", "agri", "Cotton seed"),
    ("120729", "agri", "Cotton seed"),
    ("120730", "agri", "Castor oil seeds"),
    ("120740", "agri", "Sesame"),
    ("120750", "agri", "Mustard seed"),
    ("120760", "agri", "Safflower seed"),
    ("121010", "agri", "Hop cones"),
    ("121020", "agri", "Hop cones"),
    ("121291", "agri", "Sugar beet"),
    ("121292", "agri", "Locust beans (carobs)"),
    ("121293", "agri", "Sugarcane"),
    ("121294", "agri", "Chicory roots"),
    ("121299", "agri", "Other stimulant, spice and aromatic crops, n.e.c."),
    ("150110", "agri", "Pig fat, rendered"),
    ("150120", "agri", "Pig fat, rendered"),
    ("150210", "agri", "Tallow"),
    ("150500", "agri", "Fat of camels"),
    ("150600", "agri", "Fat of camels"),
    ("150710", "agri", "Soya bean oil"),
    ("150790", "agri", "Soya bean oil"),
    ("150810", "agri", "Groundnut oil"),
    ("150890", "agri", "Groundnut oil"),
    ("150910", "agri", "Olive oil"),
    ("150990", "agri", "Olive oil"),
    ("151000", "agri", "Olive oil"),
    ("151110", "agri", "Oil palm"),
    ("151190", "agri", "Oil palm"),
    ("151221", "agri", "Cottonseed oil"),
    ("151229", "agri", "Cottonseed oil"),
    ("151311", "agri", "Coconut oil"),
    ("151319", "agri", "Coconut oil"),
    ("151411", "agri", "Rapeseed or canola oil, crude"),
    ("151491", "agri", "Rapeseed or canola oil, crude"),
    ("151710", "agri", "Margarine and shortening"),
    ("151790", "agri", "Margarine and shortening"),
    ("152190", "agri", "Beeswax"),
    ("160558", "agri", "Snails, fresh, chilled, frozen, dried, salted or in brine, except sea snails"),
    ("170112", "agri", "Raw cane or beet sugar (centrifugal only)"),
    ("170113", "agri", "Raw cane or beet sugar (centrifugal only)"),
    ("170114", "agri", "Raw cane or beet sugar (centrifugal only)"),
    ("170310", "agri", "Molasses"),
    ("170390", "agri", "Molasses"),
    ("180100", "agri", "Cocoa beans"),
    ("220300", "agri", "Beer of barley, malted"),
    ("220421", "agri", "Wine"),
    ("220422", "agri", "Wine"),
    ("220429", "agri", "Wine"),
    ("220430", "agri", "Wine"),
    ("240110", "agri", "Tobacco"),
    ("400110", "agri", "Rubber"),
    ("400121", "agri", "Rubber"),
    ("400122", "agri", "Rubber"),
    ("400129", "agri", "Rubber"),
    ("410210", "agri", "Raw hides and skins of sheep or lambs"),
    ("410221", "agri", "Raw hides and skins of sheep or lambs"),
    ("410229", "agri", "Raw hides and skins of sheep or lambs"),
    ("410390", "agri", "Raw hides and skins of goats or kids"),
    ("500100", "agri", "Silk-worm cocoons suitable for reeling"),
    ("500200", "agri", "Raw silk (not thrown)"),
    ("510111", "agri", "Shorn wool, greasy, including fleece-washed shorn wool"),
]

#: Commodités FAOSTAT qu'AU MOINS un code SH atteint — soit par une entrée
#: ci-dessus, soit parce que la table curée y pointait déjà.
#:
#: L'ingestion s'en sert comme FILTRE : une commodité absente de cet ensemble
#: n'entre pas dans ``production_africaine.json``. L'invariant du dépôt
#: (tests/test_hs_commodity_mapping.py) est ainsi tenu par construction, et non
#: par vigilance — toute commodité ingérée est joignable par un code SH, donc
#: exploitable par le module Opportunités.
FAOSTAT_REACHABLE_COMMODITIES: FrozenSet[str] = frozenset({
    "Almonds",
    "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw",
    "Apples",
    "Apricots",
    "Artichokes",
    "Asparagus",
    "Avocados",
    "Bambara beans, dry",
    "Bananas",
    "Barley",
    "Beans",
    "Beer of barley, malted",
    "Beeswax",
    "Brazil nuts, in shell",
    "Broad beans and horse beans, dry",
    "Broad beans and horse beans, green",
    "Buckwheat",
    "Cabbages",
    "Canary seed",
    "Cantaloupes and other melons",
    "Carrots",
    "Cashew nuts",
    "Cassava",
    "Castor oil seeds",
    "Cattle meat",
    "Cattle milk",
    "Cauliflowers",
    "Cereals n.e.c.",
    "Cherries",
    "Chestnuts, in shell",
    "Chicken meat",
    "Chickpeas",
    "Chicory roots",
    "Chillies and peppers",
    "Cinnamon",
    "Cloves",
    "Cocoa beans",
    "Coconut oil",
    "Coconuts",
    "Coffee",
    "Cotton seed",
    "Cottonseed oil",
    "Cowpeas",
    "Cucumbers",
    "Currants",
    "Dates",
    "Edible offal of pigs, fresh, chilled or frozen",
    "Edible roots and tubers with high starch or inulin content, n.e.c., fresh",
    "Eggplants",
    "Eggs from other birds in shell, fresh, n.e.c.",
    "Fat of camels",
    "Fat of pigs",
    "Figs",
    "Fonio",
    "Ginger",
    "Grapes",
    "Green tea (not fermented), black tea (fermented) and partly fermented tea, in immediate packings of a content not exceeding 3 kg",
    "Groundnut oil",
    "Groundnuts",
    "Hazelnuts, in shell",
    "Hen eggs",
    "Hop cones",
    "Kiwi fruit",
    "Kola nuts",
    "Leeks and other alliaceous vegetables",
    "Lemons and limes",
    "Lentils",
    "Lettuce",
    "Linseed",
    "Locust beans (carobs)",
    "Maize (corn)",
    "Mangoes",
    "Margarine and shortening",
    "Meat of ducks, fresh or chilled",
    "Meat of geese, fresh or chilled",
    "Meat of goat, fresh or chilled",
    "Meat of pig with the bone, fresh or chilled",
    "Meat of sheep, fresh or chilled",
    "Meat of turkeys, fresh or chilled",
    "Millet",
    "Molasses",
    "Mushrooms and truffles",
    "Mustard seed",
    "Natural honey",
    "Nutmeg, mace, cardamoms, raw",
    "Oats",
    "Oil palm",
    "Okra",
    "Olive oil",
    "Olives",
    "Onions",
    "Oranges",
    "Other citrus fruit, n.e.c.",
    "Other stimulant, spice and aromatic crops, n.e.c.",
    "Other tropical fruits, n.e.c.",
    "Papayas",
    "Peaches and nectarines",
    "Peas",
    "Peas, green",
    "Pepper",
    "Pig fat, rendered",
    "Pigeon peas",
    "Pineapples",
    "Pistachios, in shell",
    "Plantain",
    "Plums and sloes",
    "Pomelos and grapefruits",
    "Potatoes",
    "Pumpkins, squash and gourds",
    "Rapeseed",
    "Rapeseed or canola oil, crude",
    "Raspberries",
    "Raw cane or beet sugar (centrifugal only)",
    "Raw hides and skins of goats or kids",
    "Raw hides and skins of sheep or lambs",
    "Raw silk (not thrown)",
    "Rice",
    "Rubber",
    "Rye",
    "Safflower seed",
    "Seed cotton",
    "Sesame",
    "Shea nuts",
    "Shorn wool, greasy, including fleece-washed shorn wool",
    "Silk-worm cocoons suitable for reeling",
    "Skim milk and whey powder",
    "Skim milk of cows",
    "Snails, fresh, chilled, frozen, dried, salted or in brine, except sea snails",
    "Sorghum",
    "Soya bean oil",
    "Soybeans",
    "Spinach",
    "Strawberries",
    "Sugar beet",
    "Sugarcane",
    "Sunflower seed",
    "Sweet potatoes",
    "Tallow",
    "Tangerines, mandarins, clementines",
    "Taro",
    "Tea",
    "Tobacco",
    "Tomatoes",
    "Triticale",
    "Vanilla",
    "Walnuts, in shell",
    "Watermelons",
    "Wheat",
    "Whey, dry",
    "Whole milk powder",
    "Whole milk, condensed",
    "Wine",
    "Yam",
})

# Commodités écartées faute de code SH qui leur soit propre. La cause n'est pas
# une lacune de la correspondance : ce sont des cas où UN code SH recouvre
# PLUSIEURS commodités FAOSTAT — le SH 0201 « viande de bovins » vaut pour les
# bovins et les buffles, le SH 0205 pour les chevaux et les ânes. Le pont
# n'associe qu'un libellé par préfixe ; trancher reviendrait à attribuer une
# production au mauvais produit. Elles restent donc hors ingestion, en
# attendant que le pont sache exprimer une relation un-à-plusieurs.
#
#   Abaca, manila hemp, raw
#   Areca nuts
#   Blueberries
#   Buffalo fat, unrendered
#   Butter and ghee of sheep milk
#   Butter of buffalo milk
#   Butter of cow milk
#   Buttermilk, dry
#   Cashewapple
#   Cassava leaves
#   Cattle fat, unrendered
#   Cheese from milk of buffalo, fresh or processed
#   Cheese from milk of goats, fresh or processed
#   Cheese from milk of sheep, fresh or processed
#   Cheese from skimmed cow milk
#   Cheese from whole cow milk
#   Coir, raw
#   Cotton lint, ginned
#   Cranberries
#   Cream, fresh
#   Edible offal of buffalo, fresh, chilled or frozen
#   Edible offal of cattle, fresh, chilled or frozen
#   Edible offal of goat, fresh, chilled or frozen
#   Edible offal of sheep, fresh, chilled or frozen
#   Edible offals of camels and other camelids, fresh, chilled or frozen
#   Edible offals of horses and other equines, fresh, chilled or frozen
#   Flax, raw or retted
#   Game meat, fresh, chilled or frozen
#   Ghee from cow milk
#   Goat fat, unrendered
#   Green corn (maize)
#   Green garlic
#   Horse meat, fresh or chilled
#   Jute, raw or retted
#   Kenaf, and other textile bast fibres, raw or retted
#   Lupins
#   Meat of asses, fresh or chilled
#   Meat of buffalo, fresh or chilled
#   Meat of camels, fresh or chilled
#   Meat of pigeons and other birds n.e.c., fresh, chilled or frozen
#   Meat of rabbits and hares, fresh or chilled
#   Melonseed
#   Oil of linseed
#   Oil of maize
#   Oil of palm kernel
#   Oil of sesame seed
#   Onions and shallots, green
#   Other beans, green
#   Other berries and fruits of the genus vaccinium n.e.c.
#   Other fibre crops, raw, n.e.c.
#   Other fruits, n.e.c.
#   Other meat of mammals, fresh or chilled
#   Other nuts (excluding wild edible nuts and groundnuts), in shell, n.e.c.
#   Other oil seeds, n.e.c.
#   Other pulses n.e.c.
#   Other stone fruits
#   Other vegetables, fresh n.e.c.
#   Palm kernels
#   Pears
#   Peppermint, spearmint
#   Pyrethrum, dried flowers
#   Quinces
#   Raw hides and skins of buffaloes
#   Raw hides and skins of cattle
#   Raw milk of buffalo
#   Raw milk of camel
#   Raw milk of goats
#   Raw milk of sheep
#   Safflower-seed oil, crude
#   Sheep fat, unrendered
#   Sisal, raw
#   Skim milk, evaporated
#   String beans
#   Sunflower-seed oil, crude
#   Tung nuts
#   Vetches
#   Whole milk, evaporated
#   Yoghurt

# Items FAOSTAT qui sont des AGRÉGATS (préfixe CPC « F1 ») : ils totalisent des
# productions déjà portées ligne à ligne. « Meat, Total » recouvre la volaille,
# le bœuf et le mouton ; « Cereals, primary » recouvre blé, maïs et riz. Les
# ingérer à côté de leurs composants ferait compter deux fois la même récolte,
# et les ferait remonter en tête de tout classement par volume. Ils sont donc
# écartés à l'ingestion — non pour une lacune de correspondance, mais parce
# qu'ils ne sont pas une production supplémentaire.
FAOSTAT_AGGREGATE_ITEMS: FrozenSet[str] = frozenset({
    "Beef and Buffalo Meat, primary",
    "Butter and Ghee",
    "Cereals, primary",
    "Cheese (All Kinds)",
    "Citrus Fruit, Total",
    "Eggs Primary",
    "Evaporated & Condensed Milk",
    "Fibre Crops, Fibre Equivalent",
    "Fruit Primary",
    "Meat, Poultry",
    "Meat, Total",
    "Milk, Total",
    "Oilcrops, Cake Equivalent",
    "Oilcrops, Oil Equivalent",
    "Pulses, Total",
    "Roots and Tubers, Total",
    "Sheep and Goat Meat",
    "Skim Milk & Buttermilk, Dry",
    "Sugar Crops Primary",
    "Treenuts, Total",
    "Vegetables Primary",
})
