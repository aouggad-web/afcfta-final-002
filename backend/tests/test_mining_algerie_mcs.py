"""
Algérie, onglet Mines : les chiffres servis sont ceux que l'USGS publie.

Relevé dans les fiches « Mineral Commodity Summaries » 2024, 2025 et 2026
(pubs.usgs.gov/periodicals/mcs2024, mcs2025, mcs2026) :

- phosphate : 1 800 kt en 2022 (MCS 2024), 2 000 kt en 2023 (MCS 2025),
  2024 et 2025 (MCS 2026) ;
- gypse : 2 500 kt chaque année de 2022 à 2025 (estimations USGS) ;
- zinc, plomb, argent : l'Algérie ne figure dans aucun des tableaux de
  production minière de ces deux éditions.

L'écran affichait 1,2 à 1,4 Mt de phosphate, 1,8 à 1,9 Mt de gypse, et des
séries zinc, plomb et argent attribuées à MCS 2025 sans y figurer.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from production_data import get_mining_by_country  # noqa: E402


def _series(par_minerai, minerai):
    return {r["year"]: (r["value"], r["source_dataset"]) for r in par_minerai.get(minerai, [])}


def test_algerie_phosphate_et_gypse_conformes_a_mcs():
    par_minerai = get_mining_by_country("DZA")["data_by_commodity"]

    assert _series(par_minerai, "Phosphate") == {
        2022: (1_800_000.0, "Mineral Commodity Summaries 2024"),
        2023: (2_000_000.0, "Mineral Commodity Summaries 2025"),
        2024: (2_000_000.0, "Mineral Commodity Summaries 2026"),
        2025: (2_000_000.0, "Mineral Commodity Summaries 2026"),
    }
    assert _series(par_minerai, "Gypsum") == {
        2022: (2_500_000.0, "Mineral Commodity Summaries 2024"),
        2023: (2_500_000.0, "Mineral Commodity Summaries 2025"),
        2024: (2_500_000.0, "Mineral Commodity Summaries 2026"),
        2025: (2_500_000.0, "Mineral Commodity Summaries 2026"),
    }


def test_algerie_sans_serie_que_l_usgs_ne_publie_pas():
    par_minerai = get_mining_by_country("DZA")["data_by_commodity"]

    assert not {"Zinc", "Lead", "Silver", "Diamonds", "Gemstones"} & set(par_minerai)
