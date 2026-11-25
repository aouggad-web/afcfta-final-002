"""
Uranium africain dérivé de la WNA — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===================================================================
Produit par ``backend/scripts/build_uranium_from_wna.py`` depuis le tableau
de production par pays de la World Nuclear Association :
https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production

Production des mines, en tonnes d'uranium (tU), années 2022-2024.

Régénérer :
    python3 backend/scripts/build_uranium_from_wna.py
"""

from __future__ import annotations

from typing import Dict

WNA_DATASET = "World Nuclear Association — World Uranium Mining Production"
WNA_SOURCE_URL = 'https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production'
WNA_MEASURE = "Production from mines, tonnes U"
#: Empreinte SHA-256 du tableau HTML dont ces chiffres sont issus.
WNA_SHA256 = 'c32fd126e46d9229e089513d56e1bc3288c14bef6d8c9c56cff2d11286337a51'

#: iso3 -> {année: tonnes d'uranium}
WNA_URANIUM: Dict[str, Dict[int, float]] = {
    'NAM': {2022: 5611.0, 2023: 6986.0, 2024: 7333.0},
    'NER': {2022: 2020.0, 2023: 1130.0, 2024: 962.0},
}
