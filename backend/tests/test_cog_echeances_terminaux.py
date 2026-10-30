"""Congo : fin de la circulaire n° 0138 au 31/12/2026 et taxe sur les nouveaux
terminaux à carte SIM. Fiche : COG_echeances_terminaux_2026-10-30.json."""

import csv
import json
import os
import sys
from datetime import date

import pytest

from services.calcul import PARTIEL, calculer, droits_a_la_date

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "COG.json")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))


def test_une_mesure_datee_reprend_son_taux_passe_son_terme():
    droits = [{"code": "TVA", "taux": 5.0, "note": "circulaire", "jusqu_au": "2026-12-31", "taux_apres": 18.0,
               "note_apres": "taux normal"}, {"code": "DD", "taux": 10.0}]
    assert droits_a_la_date(droits, "2026-12-31")[0]["taux"] == 5.0  # le terme est compris
    apres = droits_a_la_date(droits, "2027-01-01")
    assert (apres[0]["taux"], apres[0]["note"], apres[1]["taux"]) == (18.0, "taux normal", 10.0)
    assert droits[0]["taux"] == 5.0  # la position n'est pas modifiée
    assert "jusqu_au" not in apres[0] and droits_a_la_date(apres, "2026-06-01")[0]["taux"] == 18.0


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


def test_l_export_lit_la_mesure_a_sa_date_de_reference(tmp_path, monkeypatch):
    """Cellule et total de l'export suivent le même taux, avant comme après le terme."""
    import exporter_tarifs_socle as exp

    monkeypatch.setattr(exp, "EXPORT_DIR", str(tmp_path))
    with open(os.path.join(exp.SOCLE_DIR, "MANIFESTE.json"), encoding="utf-8") as f:
        manifeste = json.load(f)
    for jour, tva in ((date(2026, 12, 31), "5"), (date(2027, 1, 1), "18")):
        exp.exporter("COG", manifeste, le=jour)
        with open(tmp_path / "COG_NPF.csv", encoding="utf-8-sig") as f:
            lignes = list(csv.reader(f, delimiter=";"))
        entete = lignes[0]
        riz = next(l for l in lignes if l[0] == "10063010")
        cellule = riz[next(i for i, c in enumerate(entete) if c.startswith("TVA "))]
        assert cellule.replace(",", ".").rstrip("0").rstrip(".") == tva, (jour, cellule)


def test_les_telephones_portent_la_taxe_rtn_sans_montant(positions):
    droits = positions["85171200"]["droits"]
    rtn = next(d for d in droits if d["code"] == "RTN")
    assert rtn["taux"] is None and "1 300 FCFA (2G)" in rtn["note"]
    r = calculer(positions["85171200"], 1000, devise_position="XAF", devise_cif="XAF")
    assert r["npf"]["etat"] == PARTIEL


def test_la_consultation_affiche_le_droit_a_la_date_du_jour():
    from routes.consultation import _droit_de_douane

    echu = {"droits": [{"code": "DD", "taux": 0.0, "jusqu_au": "2000-01-01", "taux_apres": 10.0}]}
    assert _droit_de_douane(echu)["dd_rate"] == 10.0


def test_les_lectures_du_socle_rendent_la_mesure_a_la_date_du_jour(monkeypatch):
    from services import benchmarking_service, socle

    echu = {"droits": [{"code": "DD", "taux": 0.0, "jusqu_au": "2000-01-01", "taux_apres": 20.0}]}
    monkeypatch.setattr(socle, "charger", lambda iso3: {"positions": {"02011000": echu}})
    assert socle.position("COG", "02011000")[0]["droits"][0]["taux"] == 20.0
    assert benchmarking_service._positions_socle("COG", "0201")["02011000"]["droits"][0]["taux"] == 20.0
    assert echu["droits"][0]["taux"] == 0.0  # le socle chargé n'est pas modifié
