"""
Correspondance ISO3 → code numérique UN M49, pour les 54 pays africains.

DÉRIVÉE d'une source publiée, pas saisie à la main : le membre
``*_AreaCodes.csv`` du bulk FAOSTAT publie le code M49 en regard du nom de
pays, et ``scripts/build_production_faostat_usgs.py`` porte déjà la table
nom FAOSTAT → ISO3. La jointure des deux donne les 54 paires
ci-dessous ; les zones non africaines et les agrégats FAOSTAT (« Afrique »,
« Monde », « Pays les moins avancés »…) sont écartés par construction,
faute d'ISO3 dans cette table.

Sert aux API qui indexent les pays par M49 plutôt que par ISO3 — en premier
lieu la base ODD de l'UNSD (``scripts/fetch_unsd_manufacturing.py``).

Régénérer : voir la procédure en tête de ``scripts/fetch_unsd_manufacturing.py``.
"""

from __future__ import annotations

from typing import Dict

ISO3_TO_M49: Dict[str, str] = {
    "AGO": "24",  # Angola
    "BDI": "108",  # Burundi
    "BEN": "204",  # Benin
    "BFA": "854",  # Burkina Faso
    "BWA": "72",  # Botswana
    "CAF": "140",  # Central African Republic
    "CIV": "384",  # Côte d'Ivoire
    "CMR": "120",  # Cameroon
    "COD": "180",  # Democratic Republic of the Congo
    "COG": "178",  # Congo
    "COM": "174",  # Comoros
    "CPV": "132",  # Cabo Verde
    "DJI": "262",  # Djibouti
    "DZA": "12",  # Algeria
    "EGY": "818",  # Egypt
    "ERI": "232",  # Eritrea
    "ETH": "231",  # Ethiopia
    "GAB": "266",  # Gabon
    "GHA": "288",  # Ghana
    "GIN": "324",  # Guinea
    "GMB": "270",  # Gambia
    "GNB": "624",  # Guinea-Bissau
    "GNQ": "226",  # Equatorial Guinea
    "KEN": "404",  # Kenya
    "LBR": "430",  # Liberia
    "LBY": "434",  # Libya
    "LSO": "426",  # Lesotho
    "MAR": "504",  # Morocco
    "MDG": "450",  # Madagascar
    "MLI": "466",  # Mali
    "MOZ": "508",  # Mozambique
    "MRT": "478",  # Mauritania
    "MUS": "480",  # Mauritius
    "MWI": "454",  # Malawi
    "NAM": "516",  # Namibia
    "NER": "562",  # Niger
    "NGA": "566",  # Nigeria
    "RWA": "646",  # Rwanda
    "SDN": "736",  # Sudan (former)
    "SEN": "686",  # Senegal
    "SLE": "694",  # Sierra Leone
    "SOM": "706",  # Somalia
    "SSD": "728",  # South Sudan
    "STP": "678",  # Sao Tome and Principe
    "SWZ": "748",  # Eswatini
    "SYC": "690",  # Seychelles
    "TCD": "148",  # Chad
    "TGO": "768",  # Togo
    "TUN": "788",  # Tunisia
    "TZA": "834",  # United Republic of Tanzania
    "UGA": "800",  # Uganda
    "ZAF": "710",  # South Africa
    "ZMB": "894",  # Zambia
    "ZWE": "716",  # Zimbabwe
}
