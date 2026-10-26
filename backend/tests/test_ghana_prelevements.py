"""Ghana : ECOWAS Levy, AU Import Levy, EXIM Levy et Special Import Levy sur la
valeur c.a.f. (MoFEP/IFS 2026, tableau 3.9 ; Act 911 s. 29) ; TVA, NHIL et
GETFund sur une même base, valeur en douane + droits et taxes à l'importation
autres que la TVA (VAT Act 2025, Act 1151, s. 45). Fiche : GHA_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GHA.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="GHS")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_prelevements_et_base_commune_de_la_tva(positions):
    """0101.21 : DD 5 % : 50 ; ECOWAS 5 ; AU 2 ; EXIM 7,5 ; SIL 20 ; base 1 084,5."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "CEDEAO", "PUA", "EXIM", "SIL")] == [50.0, 5.0, 2.0, 7.5, 20.0]
    for c in ("TVA", "NHIL", "GETFUND"):
        assert lignes[c]["base"] == 1084.5
    assert lignes["TVA"]["montant"] == pytest.approx(162.675)


def test_produits_petroliers_hors_exim_et_sil(positions):
    code = next(k for k in positions if k.startswith("2710"))
    codes = {d["code"] for d in positions[code]["droits"]}
    assert "EXIM" not in codes and "SIL" not in codes and "CEDEAO" in codes


def test_engrais_hors_sil(positions):
    code = next(k for k in positions if k.startswith("31"))
    codes = {d["code"] for d in positions[code]["droits"]}
    assert "SIL" not in codes and "EXIM" in codes


def test_machines_hors_du_sil(positions):
    """Act 861, Second Schedule substituée par l'Act 944 : « Machinery and Equipment
    listed under Chapters 84 and 85 » hors du SIL ; la TVA se calcule."""
    for prefixe in ("847130", "8501"):
        code = next(k for k in positions if k.startswith(prefixe))
        etat, lignes = _calcul(positions[code])
        assert "SIL" not in lignes
        assert lignes["TVA"]["montant"] is not None and etat == "COMPLET"


def test_biere_accise_sur_valeur_et_droits_d_entree(positions):
    """Act 878, s. 5(2)(a) et tariff 3(a) : 47,5 % sur 1 000 + DD 200 + 5 + 2 + 7,5 + 20 ;
    TVA, NHIL et GETFund sur cette base + l'accise."""
    etat, lignes = _calcul(positions["2203001000"])
    assert etat == "COMPLET"
    assert lignes["DA"]["base"] == 1234.5 and lignes["DA"]["taux_pct"] == 47.5
    for c in ("TVA", "NHIL", "GETFUND"):
        assert lignes[c]["base"] == pytest.approx(1234.5 + 586.3875)


def test_taux_d_accises_du_first_schedule(positions):
    taux = {
        code: next(d["taux"] for d in positions[code]["droits"] if d["code"] == "DA")
        for code in ("2009111000", "2202991000", "2204100000", "2208300000", "2207101000", "2207200000", "3923210000")
    }
    assert taux == {
        "2009111000": 20.0, "2202991000": 20.0, "2204100000": 45.0, "2208300000": 50.0,
        "2207101000": 0.0, "2207200000": 10.0, "3923210000": 5.0,
    }


def test_cigarettes_accise_mixte_non_liquidee(positions):
    """Tariff 7(a) : 50 % plus GH¢ 0,28 par bâtonnet ; la TVA ne se calcule pas sans l'accise."""
    etat, lignes = _calcul(positions["2402200000"])
    assert lignes["DA"]["montant"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"


def test_produit_non_accisable_sans_droit_d_accises(positions):
    assert not any(d["code"] == "DA" for d in positions["0101210000"]["droits"])
