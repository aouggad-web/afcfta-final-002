"""
Minerais africains dérivés du fichier USGS — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===========================================================================
Produit par ``backend/scripts/build_mining_from_usgs_mcs.py`` depuis le membre
``MCS2025_World_Data.csv`` de la publication ScienceBase du *Mineral Commodity Summaries 2025 Data Release*.
https://www.sciencebase.gov/catalog/item/677eaf95d34e760b392c4970

24 commodités, 21 pays, 96 points (2023 publié, 2024 estimé).

CHAQUE COMMODITÉ PORTE SA MESURE
----------------------------------
``measure`` reprend la colonne ``TYPE`` du fichier. Elle n'est pas
décorative : « Mine production » et « Refinery production » ne se comparent
pas. Le générateur ne retient qu'une mesure par commodité, précisément pour
qu'un classement ne mêle jamais les deux — mais un consommateur qui agrège
plusieurs commodités doit continuer à la lire.

Régénérer :
    python3 backend/scripts/build_mining_from_usgs_mcs.py
"""

from __future__ import annotations

from typing import Dict

USGS_MCS_EDITION = 'Mineral Commodity Summaries 2025'
USGS_MCS_MEMBER = 'MCS2025_World_Data.csv'
#: Empreinte du membre CSV dont ces chiffres sont issus. Une régénération qui
#: la change signale une nouvelle édition — donc une relecture, pas un simple
#: rafraîchissement.
USGS_MCS_SHA256 = '4cf9adcc5add0f2271b073569635e49adc51392326ac5225bb9d644b1bb11e28'
USGS_MCS_SOURCE_URL = 'https://www.sciencebase.gov/catalog/item/677eaf95d34e760b392c4970'

#: commodité -> {unit, measure, by_country: {iso3: {année: valeur}}}
MCS_DERIVED: Dict[str, dict] = {
    'Arsenic': {
        'unit': 'metric tons',
        'measure': 'Plant production, arsenic trioxide or calculated equivalent.',
        'by_country': {
            'MAR': {2023: 6000.0, 2024: 6000.0},
        },
    },
    'Barite': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, barite, estimated',
        'by_country': {
            'MAR': {2023: 1000.0, 2024: 1000.0},
        },
    },
    'Beryllium': {
        'unit': 'metric tons',
        'measure': 'Mine production, beryllium content',
        'by_country': {
            'MDG': {2023: 1.0, 2024: 1.0},
            'MOZ': {2023: 23.0, 2024: 24.0},
            'RWA': {2023: 1.0, 2024: 1.0},
            'UGA': {2023: 1.0, 2024: 1.0},
        },
    },
    'Cement': {
        'unit': 'thousand metric tons',
        'measure': 'Cement production, estimated',
        'by_country': {
            'EGY': {2023: 52000.0, 2024: 50000.0},
        },
    },
    'Diatomite': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'MOZ': {2023: 50.0, 2024: 50.0},
        },
    },
    'Feldspar': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'MAR': {2023: 590.0, 2024: 590.0},
        },
    },
    'Garnet (industrial)': {
        'unit': 'metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2023: 180000.0, 2024: 180000.0},
        },
    },
    'Gemstones': {
        'unit': 'thousand carats',
        'measure': 'Mine production, thousand carats of gem-quality diamond',
        'by_country': {
            'AGO': {2023: 8780.0, 2024: 8800.0},
            'BWA': {2023: 17600.0, 2024: 18000.0},
            'COD': {2023: 1670.0, 2024: 1700.0},
            'GHA': {2023: 203.0, 2024: 200.0},
            'GIN': {2023: 96.0, 2024: 96.0},
            'NAM': {2023: 2390.0, 2024: 2400.0},
            'SLE': {2023: 420.0, 2024: 420.0},
            'TZA': {2023: 162.0, 2024: 160.0},
            'ZAF': {2023: 2360.0, 2024: 2400.0},
            'ZWE': {2023: 491.0, 2024: 490.0},
        },
    },
    'Helium': {
        'unit': 'million cubic meters',
        'measure': 'Production, helium gas content',
        'by_country': {
            'DZA': {2023: 9.0, 2024: 11.0},
        },
    },
    'Lime': {
        'unit': 'thousand metric tons',
        'measure': 'Plant production, lime',
        'by_country': {
            'ZAF': {2023: 1100.0, 2024: 1100.0},
        },
    },
    'Mercury': {
        'unit': 'metric tons',
        'measure': 'Mine production, mercury content',
        'by_country': {
            'MAR': {2023: 2.0, 2024: 2.0},
        },
    },
    'Mica (Natural)': {
        'unit': 'metric tons',
        'measure': 'Mine production, mica scrap and flake',
        'by_country': {
            'MDG': {2023: 35000.0, 2024: 50000.0},
        },
    },
    'Niobium': {
        'unit': 'metric tons',
        'measure': 'Mine production, niobium content',
        'by_country': {
            'COD': {2023: 740.0, 2024: 700.0},
            'RWA': {2023: 210.0, 2024: 200.0},
        },
    },
    'Nitrogen(fixed) - Ammonia': {
        'unit': 'thousand metric tons',
        'measure': 'Plant production, nitrogen content',
        'by_country': {
            'DZA': {2023: 2000.0, 2024: 2000.0},
            'EGY': {2023: 4500.0, 2024: 5000.0},
            'NGA': {2023: 1700.0, 2024: 1700.0},
        },
    },
    'Perlite': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2023: 11.0, 2024: 10.0},
        },
    },
    'Pumice & Pumicite': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'CMR': {2023: 280.0, 2024: 280.0},
            'DZA': {2023: 900.0, 2024: 900.0},
            'ETH': {2023: 510.0, 2024: 510.0},
            'TZA': {2023: 230.0, 2024: 230.0},
            'UGA': {2023: 830.0, 2024: 830.0},
        },
    },
    'Rare earths': {
        'unit': 'metric tons',
        'measure': 'Mine production, rare-earth-oxide equivalent',
        'by_country': {
            'MDG': {2023: 2100.0, 2024: 2000.0},
            'NGA': {2023: 7200.0, 2024: 13000.0},
        },
    },
    'Selenium': {
        'unit': 'metric tons',
        'measure': 'Refinery production, selenium content',
        'by_country': {
            'ZAF': {2023: 9.0, 2024: 9.0},
        },
    },
    'Silicon': {
        'unit': 'thousand metric tons',
        'measure': 'Plant production, Ferosilicon, silicon content',
        'by_country': {
            'ZAF': {2023: 37.0, 2024: 40.0},
        },
    },
    'Soda ash': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, natural',
        'by_country': {
            'BWA': {2023: 262.0, 2024: 270.0},
            'ETH': {2023: 18.0, 2024: 20.0},
            'KEN': {2023: 300.0, 2024: 300.0},
        },
    },
    'Talc, crude': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2023: 200.0, 2024: 320.0},
        },
    },
    'Tellurium': {
        'unit': 'metric tons',
        'measure': 'Refinery production, tellurium content',
        'by_country': {
            'ZAF': {2023: 4.0, 2024: 4.0},
        },
    },
    'Tungsten': {
        'unit': 'metric tons',
        'measure': 'Mine production, tungsten content',
        'by_country': {
            'RWA': {2023: 1200.0, 2024: 1200.0},
        },
    },
    'Vermiculite': {
        'unit': 'thousand metric tons',
        'measure': 'Mine production',
        'by_country': {
            'UGA': {2023: 23.0, 2024: 20.0},
            'ZAF': {2023: 170.0, 2024: 170.0},
            'ZWE': {2023: 28.0, 2024: 30.0},
        },
    },
}
