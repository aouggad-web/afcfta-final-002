"""Congo : TVA à l'importation, annexes 3 et 5 de la loi TVA (loi de finances
2026) et véhicules neufs de tourisme. Fiche : COG_tva_2026-10-30.json."""

import json
import os

import pytest

from services.calcul import COMPLET, PARTIEL, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "COG.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _taux(position, code):
    return next(d for d in position["droits"] if d["code"] == code)["taux"]


@pytest.mark.parametrize(
    "code, taux",
    [
        ("30049000", 0.0),  # produits pharmaceutiques (annexe 3)
        ("90189000", 0.0),  # appareils médicaux, plage 90.18.11.00 à 90.22.90
        ("23099090", 0.0),  # aliments du bétail
        ("25010019", 0.0),  # sel (annexe 3)
        ("17019910", 5.0),  # sucre (annexe 5)
        ("07020000", 5.0),  # tomate
        ("11010010", 5.0),  # farine de froment
        ("10063010", 5.0),  # riz conditionné : circulaire n° 0138
        ("23091000", 18.0),  # aliments pour chiens et chats, exclus
        ("01011010", 18.0),
    ],
)
def test_taux_de_tva_par_position(positions, code, taux):
    assert _taux(positions[code], "TVA") == taux


@pytest.mark.parametrize("code", ["29392000", "34042000", "40151100", "40151900"])
def test_numero_et_libelle_discordants_sans_taux(positions, code):
    assert _taux(positions[code], "TVA") is None


@pytest.mark.parametrize("code", ["87033110", "87033210", "87033290"])
def test_vehicules_neufs_droit_et_tva_sans_taux(positions, code):
    position = positions[code]
    assert _taux(position, "DD") is None and _taux(position, "TVA") is None
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF")
    assert r["npf"]["etat"] == PARTIEL


def test_le_sucre_paie_5_pct_et_ses_centimes(positions):
    r = calculer(positions["17019910"], 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert lignes["TVA"]["montant"] == pytest.approx(lignes["TVA"]["base"] * 0.05)
    assert lignes["CATVA"]["montant"] == pytest.approx(lignes["TVA"]["montant"] * 0.05)
    assert r["npf"]["etat"] == COMPLET
