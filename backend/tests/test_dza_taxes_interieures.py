"""Algérie : assiettes de la TIC, de la TCE, de la TEE, du DPPP et du droit sur
les piles (fiche DZA_assiettes_taxes_interieures_2026-10-27).

- TIC, TCE, TEE : les règles d'assiette de la TVA leur sont étendues (CTCA
  art. 26 ; LF 2017 art. 72) et elles entrent dans la base de la TVA (CTCA
  art. 27 ; LF 2017 art. 72). Allumettes et briquets : valeur en douane.
- DPPP : 30 % de la valeur en douane (CII art. 403 quater, LF 2026).
- DFP : 40 % de la valeur toutes taxes comprises (CII art. 485 bis, 3), hors
  base TVA, donc liquidé après elle.
- TEE : taux selon la classe énergétique, que le Tarif Web publie à 0 %.
- TICPV : assise sur le prix de vente hors taxes, non traduite.
"""

import json
import os

import pytest

from services.calcul import MANQUE_ASSIETTE, MANQUE_TAUX, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "DZA.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def positions():
    with open(os.path.join(SOCLE, "DZA.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(positions, code):
    r = calculer(positions[code], 10000, devise_cif="DZD")
    return r, {l["code"]: l for l in r["npf"]["lignes"]}


def test_la_tic_suit_l_assiette_de_la_tva_et_y_entre(positions):
    """Saumon keta 0302.13.10 : DD 30 %, TIC 30 %."""
    r, l = _lignes(positions, "0302131000")
    assert l["TIC"]["base"] == pytest.approx(13000.0)
    assert l["TVA"]["base"] == pytest.approx(13000.0 + 3900.0)
    assert r["npf"]["etat"] == "COMPLET"


def test_la_tic_des_allumettes_est_assise_sur_la_valeur_en_douane(positions):
    _, l = _lignes(positions, "3605001000")
    assert l["TIC"]["assiette"] == "CIF" and l["TIC"]["base"] == pytest.approx(10000.0)


def test_la_tce_entre_dans_la_base_de_la_tva(positions):
    _, l = _lignes(positions, "8403101910")
    assert l["TCE"]["montant"] == pytest.approx(3900.0)
    assert l["TVA"]["base"] == pytest.approx(16900.0)


def test_le_droit_sur_les_piles_porte_sur_la_valeur_ttc_apres_la_tva(positions):
    r, l = _lignes(positions, "8506101100")
    codes = [x["code"] for x in r["npf"]["lignes"]]
    assert codes.index("DFP") == codes.index("TVA") + 1
    assert l["DFP"]["base"] == pytest.approx(10000 + 3000 + 300 + l["TVA"]["montant"])
    assert l["TVA"]["base"] == pytest.approx(13000.0)


def test_le_droit_sur_les_pierres_precieuses_porte_sur_la_valeur_en_douane(positions):
    _, l = _lignes(positions, "7101101000")
    assert l["DPPP"]["assiette"] == "CIF" and l["DPPP"]["montant"] == pytest.approx(3000.0)


def test_la_tee_n_est_jamais_liquidee_a_zero(positions):
    """Le taux dépend de la classe énergétique (5 à 40 %) : la TEE et la TVA
    qui l'inclut restent indisponibles plutôt que servies à 0 %."""
    tee = [d for p in positions.values() for d in p["droits"] if d["code"] == "TEE"]
    assert tee and all(d.get("taux") is None and "classe énergétique" in d["note"] for d in tee)
    r, l = _lignes(positions, "8415109110")
    assert l["TEE"]["statut"] == MANQUE_TAUX
    assert l["TVA"]["montant"] is None and r["npf"]["etat"] == "PARTIEL"


def test_la_tic_proportionnelle_des_tabacs_reste_non_traduite(positions):
    _, l = _lignes(positions, "2402100000")
    assert l["TICPV"]["statut"] == MANQUE_ASSIETTE
    assert "prix de vente hors taxes" in l["TICPV"]["assiette_non_traduite"]
    assert l["TVA"]["montant"] is None
