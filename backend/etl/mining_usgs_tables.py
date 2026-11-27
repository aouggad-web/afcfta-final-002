"""
Minerais africains dérivés des fiches USGS MCS — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===============================================================================
Produit par ``backend/scripts/build_mining_from_usgs_pdfs.py`` depuis les
fiches par minerai des Mineral Commodity Summaries 2024 et 2025
(https://pubs.usgs.gov/periodicals/mcs2024/, https://pubs.usgs.gov/periodicals/mcs2025/).

22 commodités, 186 points : 2022 d'après MCS 2024 ; 2023 (révisé) et
2024 (estimé) d'après MCS 2025.

Sans aucun pays africain au tableau de production : Lead, Nickel, Antimony, Silver.
Ces commodités n'ont pas de série : l'USGS range leurs producteurs africains
dans « Other countries ».

Régénérer :
    python3 backend/scripts/build_mining_from_usgs_pdfs.py
"""

from __future__ import annotations

from typing import Dict

#: Année -> édition MCS qui la publie.
EDITION_PAR_ANNEE = {2022: 2024, 2023: 2025, 2024: 2025}
URL_FICHE = 'https://pubs.usgs.gov/periodicals/mcs{edition}/mcs{edition}-{slug}.pdf'

#: Empreinte SHA-256 de chaque fiche lue. Une régénération qui en change une
#: signale une révision de l'USGS — donc une relecture, pas un simple rafraîchissement.
USGS_PDF_SHA256: Dict[str, str] = {
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-antimony.pdf': '7b154b1e40ed371a06736e74014b434b35dfc38d567a84ace63df29584d0fc42',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-bauxite-alumina.pdf': '7311769aa95c70026d5739cd8856f1b4314063d78c352e7cf32375fb23da9134',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-chromium.pdf': '8b35f9b4cadb59b61527414944a5d04a68771834c224a5e3d502eb4258a9dd35',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-cobalt.pdf': '7cea74b82fdf6f3228a6111ac5b33e9d0d23364b491b976a44e6fa828f366e33',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-copper.pdf': '582f9135384885ccb004a724787fd55f751c057b616312f43a6078aaa6f52f69',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-diamond.pdf': 'ddff850584a5df5b763e521967c760bdc82e58d07eedae6012a6dac154902403',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-fluorspar.pdf': '4500d4b002fac46ee755ce8ed6fa3ba0ac0a948b5e897ad97792b8eea4d020e2',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-gold.pdf': '3b551dcc4dbc7e21b3b1789c4552dab12d370e7a839288744196105e4767946c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-graphite.pdf': '00ab8511468509f87a1b9b5d9393d5c172b3877cd3f7036304e122025c1b9742',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-gypsum.pdf': '1f3837071199a6a054ee2f7b7502491a1ad85602a9e07cb7710f0732bca93f53',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-iron-ore.pdf': '8e3671f58e95f090050fa33eac7ccc4c1ae1764a3d8863659f8a982ddd9e65ac',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-lead.pdf': '2ed2d41936e7e9953a2cc20597b2485ef763aeef57d7c5e3966b893678a243e5',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-lithium.pdf': '14f43f30f8905f7cd3e6284a843fa007d74d0bf74f8ad186c7ae1219c115eb8b',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-manganese.pdf': 'c5b90e373a0e61b86176a337f8db8beac74683af8acc138437bd49c5da78748c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-nickel.pdf': '39f5aa8333e52385861dab8e184d36be57b276246f343848ec46ea2e06a9f5cf',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-phosphate.pdf': '65eac9e41af333fa72ce8de8147442de6b3fc31732aa7b9cc74380402e2fa26a',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-platinum-group.pdf': 'f05241d70dab46d401fdf58c5a60331e37ebed8ef51b2070d506c5403723de17',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-salt.pdf': 'abe3e445614c59a2dd4a019a9af542690dd83d5149541fc75bf12b30e2eb38d2',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-silver.pdf': '7c74bb6f756c5b801882a487aac1053d1791af2d91a20c4fbc260ca678d72336',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tantalum.pdf': 'c1a582c8467fb6a607c933e0ba7ddec2fae894b6a4f0183f86d3add5d5acee4c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tin.pdf': '81ea9ab53ca494719f59993db111f718d8401fa9f66acb04606c45a7b947b979',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-titanium-minerals.pdf': 'a93112fd1dc3101607995a1fc637a151d3de2c2ccae2a245dc84d329c7c64b3d',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-vanadium.pdf': '3a2d8f5e742646f82e8ef35816ebdd036374357c1cd551329faead800f6df5fc',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-zinc.pdf': 'cc889d5f180bf905564f678dae3d25d3018b9a67ca5de436d874b913ab68a841',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-zirconium-hafnium.pdf': '6ee6c0c2ab7ce998f007ee9429368b5b8fdab27486c54e2fca27687b8d48e2c1',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-antimony.pdf': '9e79e0d2e45be3d9322ac77b48849420090c1ef90e07534419e45f531ff60c76',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-bauxite-alumina.pdf': 'f37ce33c9b54976deb3ed22571fd2dfaa1f7c19dff174ff62b73105b0d81f189',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-chromium.pdf': '650dc3db07128f7233a0d730c31b67d782e78e6276ce7ec2e95fb2e13630b3b7',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-cobalt.pdf': '2d736a1d4f76a38b067c0b530d2db9121cdfe1d2b9c5b7d5c2343b7e6abc0d92',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-copper.pdf': '348b1e224d830a51e6d35cf81343eead26a0cb2a4e74c474d699b7faed1b10e6',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-diamond.pdf': '29ac1f6c9d4bcb640f3047e32690f9ffcb4efbbf84d094b302de9bebbeadc02c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-fluorspar.pdf': '35384613f8fa6bc77ed69ae05688bdea3f61ddf98ea5571a65ff029f3a4f04d0',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gold.pdf': 'd4ec1750249005b4ad91dd59aaa7978932ecb7b7a410d8f6a135e6f8f8cc136f',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-graphite.pdf': '96f088e1346022462def556b9b470e0b14c290be496d4580ec0e1f93f2b88d88',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gypsum.pdf': '0f3eac0c44547e9d10d98d717663facf62876a649a1f236e312f83520e736798',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-iron-ore.pdf': '5338c109340fd9d0edbde03c7fe17d2ab1632e7b47638850a705f5fca342d9c8',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lead.pdf': '2c02af206d1efab6f44d6f2d404df7c48936e30344830e18706ffcfedd8992ed',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lithium.pdf': '7ec5654133aa5ef64fcfd6d4d23ac64a58f06f51bf1231576ebd8f595ad9257b',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-manganese.pdf': '5868e111d64cc6a771883efd27332511ad407db64eddbe7c5f70a2256ecd2052',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-nickel.pdf': 'ad0eabdf50cd4d63a5c110ab1445697127c9c33e42eb4dca64135e4183d7d410',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-phosphate.pdf': '1680ad2ff3c481b5413a9ae686eed9c6a7ac72662373370ffa7f8ce311c36631',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-platinum-group.pdf': 'e2a443b26d93fc71431a26e094bc1630b220059f81c469db510266011aa4f376',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-salt.pdf': '2c5bbbdd435f1fd29f1acbc2806bcf2b2f80eb1490a72f4f08af3583f0b8cd0d',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-silver.pdf': '1aa6e68c9700f88e97d4cbf31fc039d45d4b1b738a09f6bfece8edac0ec59b24',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tantalum.pdf': 'd6f3e9e79fc10e5f4a20b277be4488c5e98484a830ef19c1888f37dc2d3a359c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tin.pdf': 'dee3fdd3dff310c5e609e2ae069da2a5141dac471b0523b0c33217d1ac6b0e8d',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-titanium-minerals.pdf': '96a5d6922275b3a50f7515ae8e7283ca41477d9c0536dd62c6400ad04cc3df4c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-vanadium.pdf': 'e9412dbb57fbead5d3bc410170517d794567bb20626717a7ac2184a1f3c9760b',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-zinc.pdf': 'e99d72f809ed9ee8a2aa2b78339e13f91577ea36efb1a73a9df715df6aa0b9bc',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-zirconium-hafnium.pdf': 'b7615a849825bb8947b71037e9fd634b288c4abadd188091f774b96078fb174c',
}

#: commodité -> {slug, unit, measure, by_country: {iso3: {année: valeur}}}
MCS_TABLES: Dict[str, dict] = {
    'Gold': {
        'slug': 'gold',
        'unit': 'tonnes',
        'measure': 'Mine production, gold content',
        'by_country': {
            'BFA': {2022: 58.0, 2023: 57.0, 2024: 60.0},
            'GHA': {2022: 88.0, 2023: 126.0, 2024: 130.0},
            'MLI': {2022: 64.0, 2023: 67.0, 2024: 70.0},
            'TZA': {2022: 57.0, 2023: 55.0, 2024: 60.0},
            'ZAF': {2022: 89.0, 2023: 104.0, 2024: 100.0},
        },
    },
    'Copper': {
        'slug': 'copper',
        'unit': 'tonnes',
        'measure': 'Mine production, copper content',
        'by_country': {
            'COD': {2022: 2350000.0, 2023: 2930000.0, 2024: 3300000.0},
            'ZMB': {2022: 797000.0, 2023: 712000.0, 2024: 680000.0},
        },
    },
    'Cobalt': {
        'slug': 'cobalt',
        'unit': 'tonnes',
        'measure': 'Mine production, cobalt content',
        'by_country': {
            'COD': {2022: 144000.0, 2023: 175000.0, 2024: 220000.0},
            'MDG': {2022: 3500.0, 2023: 4000.0, 2024: 2600.0},
        },
    },
    'Diamonds': {
        'slug': 'diamond',
        'unit': 'carats',
        'measure': 'Mine production, natural industrial diamond',
        'by_country': {
            'AGO': {2022: 1000000.0, 2023: 1000000.0, 2024: 1000000.0},
            'BWA': {2022: 7000000.0, 2023: 8000000.0, 2024: 8000000.0},
            'COD': {2022: 8000000.0, 2023: 7000000.0, 2024: 7000000.0},
            'ZAF': {2022: 6000000.0, 2023: 4000000.0, 2024: 4000000.0},
            'ZWE': {2022: 4000000.0, 2023: 4000000.0, 2024: 4000000.0},
        },
    },
    'Phosphate': {
        'slug': 'phosphate',
        'unit': 'tonnes',
        'measure': 'Mine production, marketable phosphate rock',
        'by_country': {
            'DZA': {2022: 1800000.0, 2023: 2000000.0, 2024: 2000000.0},
            'EGY': {2022: 5000000.0, 2023: 5000000.0, 2024: 5000000.0},
            'MAR': {2022: 39000000.0, 2023: 33000000.0, 2024: 30000000.0},
            'SEN': {2022: 2600000.0, 2023: 2400000.0, 2024: 2500000.0},
            'TGO': {2022: 1500000.0, 2023: 1610000.0, 2024: 1500000.0},
            'TUN': {2022: 3560000.0, 2023: 3600000.0, 2024: 3300000.0},
            'ZAF': {2022: 1990000.0, 2023: 1720000.0, 2024: 2200000.0},
        },
    },
    'Bauxite': {
        'slug': 'bauxite-alumina',
        'unit': 'tonnes',
        'measure': 'Mine production, bauxite, dry tons',
        'by_country': {
            'GIN': {2022: 100000000.0, 2023: 123000000.0, 2024: 130000000.0},
        },
    },
    'Iron ore': {
        'slug': 'iron-ore',
        'unit': 'tonnes',
        'measure': 'Mine production, usable ore',
        'by_country': {
            'MRT': {2022: 12700000.0, 2023: 14100000.0, 2024: 15000000.0},
            'ZAF': {2022: 63700000.0, 2023: 63200000.0, 2024: 66000000.0},
        },
    },
    'Manganese': {
        'slug': 'manganese',
        'unit': 'tonnes',
        'measure': 'Mine production, manganese content',
        'by_country': {
            'CIV': {2022: 394000.0, 2023: 357000.0, 2024: 360000.0},
            'GAB': {2022: 4670000.0, 2023: 4490000.0, 2024: 4600000.0},
            'GHA': {2022: 844000.0, 2023: 818000.0, 2024: 820000.0},
            'ZAF': {2022: 7300000.0, 2023: 7300000.0, 2024: 7400000.0},
        },
    },
    'Platinum': {
        'slug': 'platinum-group',
        'unit': 'tonnes',
        'measure': 'Mine production, platinum',
        'by_country': {
            'ZAF': {2022: 124.0, 2023: 125.0, 2024: 120.0},
            'ZWE': {2022: 17.0, 2023: 19.2, 2024: 19.0},
        },
    },
    'Palladium': {
        'slug': 'platinum-group',
        'unit': 'tonnes',
        'measure': 'Mine production, palladium',
        'by_country': {
            'ZAF': {2022: 73.1, 2023: 74.9, 2024: 72.0},
            'ZWE': {2022: 14.3, 2023: 15.9, 2024: 15.0},
        },
    },
    'Zinc': {
        'slug': 'zinc',
        'unit': 'tonnes',
        'measure': 'Mine production, zinc content',
        'by_country': {
            'ZAF': {2022: 238000.0, 2023: 198000.0, 2024: 120000.0},
        },
    },
    'Tin': {
        'slug': 'tin',
        'unit': 'tonnes',
        'measure': 'Mine production, tin content',
        'by_country': {
            'COD': {2022: 18600.0, 2023: 20000.0, 2024: 25000.0},
            'NGA': {2022: 7000.0, 2023: 7000.0, 2024: 7000.0},
            'RWA': {2022: 3300.0, 2023: 3600.0, 2024: 3600.0},
        },
    },
    'Chromium': {
        'slug': 'chromium',
        'unit': 'tonnes',
        'measure': 'Mine production, marketable chromite ore',
        'by_country': {
            'ZAF': {2022: 19100000.0, 2023: 19700000.0, 2024: 21000000.0},
            'ZWE': {2023: 1070000.0, 2024: 1100000.0},
        },
    },
    'Lithium': {
        'slug': 'lithium',
        'unit': 'tonnes',
        'measure': 'Mine production, lithium content',
        'by_country': {
            'NAM': {2023: 2700.0, 2024: 2700.0},
            'ZWE': {2022: 1030.0, 2023: 14900.0, 2024: 22000.0},
        },
    },
    'Graphite': {
        'slug': 'graphite',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'MDG': {2022: 130000.0, 2023: 63000.0, 2024: 89000.0},
            'MOZ': {2022: 166000.0, 2023: 98000.0, 2024: 75000.0},
            'TZA': {2022: 6120.0, 2023: 13200.0, 2024: 25000.0},
        },
    },
    'Tantalum': {
        'slug': 'tantalum',
        'unit': 'tonnes',
        'measure': 'Mine production, tantalum content',
        'by_country': {
            'BDI': {2022: 59.0, 2023: 1.0, 2024: 2.0},
            'COD': {2022: 890.0, 2023: 920.0, 2024: 880.0},
            'ETH': {2023: 40.0, 2024: 40.0},
            'MOZ': {2023: 51.0, 2024: 55.0},
            'NGA': {2022: 110.0, 2023: 390.0, 2024: 390.0},
            'RWA': {2022: 347.0, 2023: 350.0, 2024: 350.0},
        },
    },
    'Vanadium': {
        'slug': 'vanadium',
        'unit': 'tonnes',
        'measure': 'Mine production, vanadium content',
        'by_country': {
            'ZAF': {2022: 8870.0, 2023: 8670.0, 2024: 8000.0},
        },
    },
    'Titanium (ilmenite)': {
        'slug': 'titanium-minerals',
        'unit': 'tonnes',
        'measure': 'Mine production, ilmenite, TiO2 content',
        'by_country': {
            'KEN': {2022: 190000.0},
            'MDG': {2022: 320000.0, 2023: 300000.0, 2024: 240000.0},
            'MOZ': {2022: 1400000.0, 2023: 1860000.0, 2024: 1900000.0},
            'SEN': {2022: 410000.0, 2023: 260000.0, 2024: 300000.0},
            'ZAF': {2022: 1100000.0, 2023: 1260000.0, 2024: 1300000.0},
        },
    },
    'Zircon': {
        'slug': 'zirconium-hafnium',
        'unit': 'tonnes',
        'measure': 'Mine production, zirconium mineral concentrates',
        'by_country': {
            'KEN': {2022: 27000.0, 2023: 20000.0, 2024: 20000.0},
            'MDG': {2022: 27000.0, 2023: 34000.0, 2024: 30000.0},
            'MOZ': {2022: 104000.0, 2023: 144000.0, 2024: 160000.0},
            'SEN': {2022: 57000.0, 2023: 48000.0, 2024: 60000.0},
            'SLE': {2022: 34000.0, 2023: 28000.0, 2024: 20000.0},
            'ZAF': {2022: 300000.0, 2023: 289000.0, 2024: 300000.0},
        },
    },
    'Fluorspar': {
        'slug': 'fluorspar',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'ZAF': {2022: 406000.0, 2023: 345000.0, 2024: 380000.0},
        },
    },
    'Salt': {
        'slug': 'salt',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'EGY': {2022: 2300000.0, 2023: 2300000.0, 2024: 2300000.0},
        },
    },
    'Gypsum': {
        'slug': 'gypsum',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'DZA': {2022: 2500000.0, 2023: 2500000.0, 2024: 2500000.0},
        },
    },
}
