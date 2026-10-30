"""Congo : fin de la circulaire n° 0138 au 31/12/2026 et taxe sur les nouveaux
terminaux à carte SIM. Fiche : COG_echeances_terminaux_2026-10-30.json."""

import json
import os

import pytest

from services.calcul import PARTIEL, calculer, droits_a_la_date

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "COG.json")


def test_une_mesure_datee_reprend_son_taux_passe_son_terme():
    droits = [{"code": "TVA", "taux": 5.0, "note": "circulaire", "jusqu_au": "2026-12-31", "taux_apres": 18.0,
               "note_apres": "taux normal"}, {"code": "DD", "taux": 10.0}]
    assert droits_a_la_date(droits, "2026-12-31")[0]["taux"] == 5.0  # le terme est compris
    apres = droits_a_la_date(droits, "2027-01-01")
    assert (apres[0]["taux"], apres[0]["note"], apres[1]["taux"]) == (18.0, "taux normal", 10.0)
    assert droits[0]["taux"] == 5.0  # la position n'est pas modifiée


@pytest.fixture(scope="module")
def positions():
    if not os.path.exists(SOCLE):
        pytest.skip("socle absent (gitignoré)")
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _taux(droits, code):
    return next(d for d in droits if d["code"] == code)["taux"]


def test_le_riz_conditionne_revient_au_taux_normal_en_2027(positions):
    droits = positions["10063010"]["droits"]
    assert (_taux(droits, "DD"), _taux(droits, "TVA")) == (5.0, 5.0)
    apres = droits_a_la_date(droits, "2027-01-01")
    assert _taux(apres, "TVA") == 18.0  # hors annexe 5 (seule la 10.06.30.90 y figure)


def test_la_viande_reste_exoneree_par_l_annexe_3_apres_la_circulaire(positions):
    apres = droits_a_la_date(positions["02071400"]["droits"], "2027-01-01")
    assert _taux(apres, "TVA") == 0.0


def test_les_telephones_portent_la_taxe_rtn_sans_montant(positions):
    droits = positions["85171200"]["droits"]
    rtn = next(d for d in droits if d["code"] == "RTN")
    assert rtn["taux"] is None and "1 300 FCFA (2G)" in rtn["note"]
    r = calculer(positions["85171200"], 1000, devise_position="XAF", devise_cif="XAF")
    assert r["npf"]["etat"] == PARTIEL
