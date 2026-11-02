"""Congo : droit de douane et TVA des lois de finances hors du gabarit TEC CEMAC,
contribution d'intégration africaine et taxe statistique.
Fiche : COG_tarif_national_2026-11-02.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "COG.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _taux(position):
    return {d["code"]: d.get("taux") for d in position["droits"]}


def _lignes(position, origine=None):
    position, _ = exoneration_origine.appliquer(position, origine)
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


@pytest.mark.parametrize(
    "code",
    ["04070010", "31021000", "31051010", "84248110", "84321000", "84323000", "84329000", "84335100", "84369900",
     "87162000", "87168010", "89020000"],
)
def test_liste_de_l_article_22_sans_droit_de_douane_ni_tva(positions, code):
    taux = _taux(positions[code])
    assert (taux["DD"], taux["TVA"]) == (0.0, 0.0)
    assert taux["RI"] == 2.0 and taux["TCI"] == 1.0


@pytest.mark.parametrize(
    "code, dd",
    [("31023000", 5.0),  # nitrate d'ammonium, absent de la liste
     ("31052000", 5.0),  # engrais NPK, absent de la liste
     ("84331100", 30.0),  # tondeuses à gazon
     ("84342000", 10.0),  # machines de laiterie
     ("87011000", 10.0),  # motoculteurs
     ("10051000", 5.0),  # maïs de semence
     ("56081100", 10.0)],  # filets de pêche
)
def test_hors_de_la_liste_le_tec_demeure(positions, code, dd):
    assert _taux(positions[code])["DD"] == dd


def test_tracteurs_agricoles_sans_taux(positions):
    taux = _taux(positions["87019011"])
    assert taux["DD"] is None and taux["TVA"] is None


def test_farine_de_froment_a_trente_pour_cent(positions):
    taux = _taux(positions["11010010"])
    assert (taux["DD"], taux["TVA"]) == (30.0, 5.0)


def test_gaz_butane(positions):
    taux = _taux(positions["27111300"])
    assert (taux["DD"], taux["TVA"], taux["RI"]) == (5.0, 5.0, 2.0)


def test_logiciels_sans_taux(positions):
    assert _taux(positions["85238000"])["DD"] is None


def test_cia_sur_la_valeur_en_douane_hors_de_l_assiette_de_la_tva(positions):
    """Farine de froment, CIF 1 000 : DD 30 % = 300 ; CIA 0,2 % = 2 ; TVA sur CIF + DD."""
    etat, lignes = _lignes(positions["11010010"])
    assert (lignes["CIA"]["base"], lignes["CIA"]["montant"]) == (1000.0, 2.0)
    assert lignes["TS"]["montant"] == 2.0
    assert lignes["TVA"]["base"] == 1300.0
    assert etat == COMPLET


@pytest.mark.parametrize(
    "origine, retires",
    [("GAB", {"CIA", "CCI", "OHADA", "TCI"}), ("NGA", {"CIA"}), ("SEN", {"CIA", "OHADA"}), ("FRA", set()),
     ("CHN", set())],
)
def test_la_cia_n_est_due_que_hors_union_africaine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["84321000"], origine)
    assert {e["code"] for e in exonerations} == retires


def test_chaque_position_porte_cia_et_ts_sourcees(positions):
    for code, position in positions.items():
        par_code = {d["code"]: d for d in position["droits"]}
        assert par_code["CIA"]["taux"] == 0.2 and par_code["CIA"]["exoneration_origine"] == "UA", code
        assert "Ngakosso" in par_code["TS"]["source"], code
