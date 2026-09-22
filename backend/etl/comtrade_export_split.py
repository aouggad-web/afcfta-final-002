"""
Exportations domestiques / réexportations, dérivées d'UN Comtrade.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/build_comtrade_export_split.py`` — NE PAS
ÉDITER À LA MAIN. Régénérer plutôt que corriger.

Source : endpoint PUBLIC ``comtradeapi.un.org/public/v1/preview`` (sans clé),
flux ``X`` (exportations totales), ``DX`` (domestiques), ``RX``
(réexportations), partenaire Monde, tous produits.

Généré le 2026-09-22T13:17:00.907976+00:00.

RÈGLE D'ADMISSION
------------------
Un pays ne figure ici que si ``DX + RX`` réconcilie avec ``X``. La présence
des trois flux ne suffit pas : neuf pays africains les publient sans qu'ils
se recomposent, et les servir ferait passer une incohérence pour une mesure.

Écartés faute de réconciliation :
#   BWA 2023 — écart de -1,744,507 USD (5.4 % du total)
#   GHA 2022 — écart de -7,109,746,881 USD (37,111.1 % du total)
#   MDG 2023 — écart de 122,361,541 USD (72.3 % du total)
#   MWI 2021 — écart de 931,718,279 USD (92.3 % du total)
#   MUS 2024 — écart de -683,801,545 USD (74,455,743.2 % du total)
#   STP 2022 — écart de -21,429,760 USD (3,612.3 % du total)
#   SYC 2022 — écart de -575,240,233 USD (1,913.8 % du total)
#   ZAF 2024 — écart de -252,032,948 USD (18.9 % du total)
#   ZMB 2023 — écart de -1,033,429,111 USD (13,140,548.6 % du total)

Publient un total sans ventilation : DZA, CPV, CMR, CAF, COM, COG, CIV, DJI, EGY, GAB, GNB, LBR, LBY, MLI, MRT, MAR, MOZ, NER, NGA, SEN, SLE, TUN, UGA

Ne reportent aucune année 2018-2024 : TCD, GNQ, ERI, ETH, GIN, SOM, SSD, SDN

CE QUE CES CHIFFRES NE DISENT PAS
-----------------------------------
Ils portent sur le TOTAL des marchandises, partenaire Monde. Ils ne
ventilent ni par produit ni par client — pour cela il faut la statistique de
l'office national (voir ``services/national_official_stats.py``), qui couvre
moins de pays mais descend plus bas.

Une part de réexportation élevée ne dit pas qu'un pays produit peu : elle dit
que ses exportations ENREGISTRÉES incluent des marchandises d'origine
étrangère, qui n'acquièrent pas l'origine locale au sens de la ZLECAf.
"""

from typing import Dict, List

#: Valeurs en USD, telles que publiées par l'ONU. Aucune conversion.
COMTRADE_EXPORT_SPLIT: List[Dict] = [
    {
        'country_iso3': 'AGO',
        'year': 2020,
        'total_exports_usd': 22004317640.278,
        'domestic_exports_usd': 21051986606.938,
        'reexports_usd': 952331033.34,
        'reexport_share_pct': 4.3,
    },
    {
        'country_iso3': 'BDI',
        'year': 2022,
        'total_exports_usd': 207868668.533,
        'domestic_exports_usd': 195495224.799,
        'reexports_usd': 12373443.735,
        'reexport_share_pct': 6.0,
    },
    {
        'country_iso3': 'BEN',
        'year': 2019,
        'total_exports_usd': 850663257.893,
        'domestic_exports_usd': 756000882.926,
        'reexports_usd': 94662374.967,
        'reexport_share_pct': 11.1,
    },
    {
        'country_iso3': 'BFA',
        'year': 2024,
        'total_exports_usd': 5642319696.589,
        'domestic_exports_usd': 5533522132.385,
        'reexports_usd': 108797564.205,
        'reexport_share_pct': 1.9,
    },
    {
        'country_iso3': 'COD',
        'year': 2023,
        'total_exports_usd': 27726829372.841,
        'domestic_exports_usd': 27533562692.316,
        'reexports_usd': 193266680.525,
        'reexport_share_pct': 0.7,
    },
    {
        'country_iso3': 'GMB',
        'year': 2024,
        'total_exports_usd': 49641899.473,
        'domestic_exports_usd': 22899587.82,
        'reexports_usd': 26742311.654,
        'reexport_share_pct': 53.9,
    },
    {
        'country_iso3': 'KEN',
        'year': 2024,
        'total_exports_usd': 8255797029.967,
        'domestic_exports_usd': 6920553939.227,
        'reexports_usd': 1335243090.739,
        'reexport_share_pct': 16.2,
    },
    {
        'country_iso3': 'LSO',
        'year': 2024,
        'total_exports_usd': 1004752519.401,
        'domestic_exports_usd': 992366435.923,
        'reexports_usd': 12386083.477,
        'reexport_share_pct': 1.2,
    },
    {
        'country_iso3': 'NAM',
        'year': 2018,
        'total_exports_usd': 7488296000.257,
        'domestic_exports_usd': 4097476622.878,
        'reexports_usd': 3390819377.38,
        'reexport_share_pct': 45.3,
    },
    {
        'country_iso3': 'RWA',
        'year': 2022,
        'total_exports_usd': 2019269801.94,
        'domestic_exports_usd': 1368491291.97,
        'reexports_usd': 650778509.97,
        'reexport_share_pct': 32.2,
    },
    {
        'country_iso3': 'SWZ',
        'year': 2021,
        'total_exports_usd': 2068468810.41,
        'domestic_exports_usd': 2061289420.26,
        'reexports_usd': 7179390.15,
        'reexport_share_pct': 0.3,
    },
    {
        'country_iso3': 'TGO',
        'year': 2024,
        'total_exports_usd': 1372307203.735,
        'domestic_exports_usd': 1067407049.023,
        'reexports_usd': 304900154.712,
        'reexport_share_pct': 22.2,
    },
    {
        'country_iso3': 'TZA',
        'year': 2023,
        'total_exports_usd': 7274328787.87,
        'domestic_exports_usd': 7139086837.91,
        'reexports_usd': 135241949.96,
        'reexport_share_pct': 1.9,
    },
    {
        'country_iso3': 'ZWE',
        'year': 2024,
        'total_exports_usd': 7434439006.215,
        'domestic_exports_usd': 7418902003.985,
        'reexports_usd': 15537002.23,
        'reexport_share_pct': 0.2,
    },
]

#: Pays dont la ventilation a été REFUSÉE faute de réconciliation. Exposé pour
#: qu'un appelant puisse dire « la source publie une ventilation, nous la
#: jugeons incohérente » plutôt que « nous n'avons rien ».
COMTRADE_SPLIT_REJECTED: List[str] = ['BWA', 'GHA', 'MDG', 'MUS', 'MWI', 'STP', 'SYC', 'ZAF', 'ZMB']
