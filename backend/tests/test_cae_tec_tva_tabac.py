"""CAE : quatre positions du TEC absentes de la collecte, TVA sur tous les droits
au Rwanda et en Tanzanie, accise sur le tabac importé (Rwanda, Tanzanie,
Ouganda). Fiche : CAE_TEC_TVA_tabac_2026-10-13.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "TZA.json")), reason="socle absent (gitignoré)"
)


def _positions(iso):
    with open(os.path.join(SOCLE, f"{iso}.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(iso, code, quantite=None):
    r = calculer(_positions(iso)[code], 1_000_000, quantite=quantite)["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


@pytest.mark.parametrize("iso", ["KEN", "RWA", "TZA", "UGA", "BDI", "SSD"])
def test_quatre_positions_du_tec(iso):
    positions = _positions(iso)
    attendus = {"53021000": 0.0, "58110000": 25.0, "92099200": 10.0, "92099400": 10.0}
    for code, taux in attendus.items():
        assert next(d for d in positions[code]["droits"] if d["code"] == "DD")["taux"] == taux


def test_tva_tanzanienne_sur_l_accise():
    """Cigarettes, 10 milliers : la TVA porte sur la valeur, le droit et l'accise."""
    etat, lignes = _calcul("TZA", "24022010", quantite=10)
    assert etat == "COMPLET"
    assert lignes["TVA"]["base"] == pytest.approx(1_000_000 + lignes["DD"]["montant"] + lignes["EXC"]["montant"])


def test_cigarettes_tanzanie_au_millier():
    """Finance Act 2026 : 72 462,19 TZS par millier."""
    etat, _ = _calcul("TZA", "24022010")
    assert etat != "COMPLET"
    etat, lignes = _calcul("TZA", "24022010", quantite=10)
    assert etat == "COMPLET" and lignes["EXC"]["montant"] == pytest.approx(724_621.9)


@pytest.mark.parametrize("code", ["24031900", "24039100", "24039900"])
def test_tabacs_tanzanie_au_kilo(code):
    """Finance Act 2026 : « Other/Imported » 36 609,19 TZS par kg."""
    etat, lignes = _calcul("TZA", code, quantite=2)
    assert etat == "COMPLET" and lignes["EXC"]["montant"] == pytest.approx(73_218.38)
    assert lignes["EXC"]["unite_quantite"] == "kg"


def test_reserve_d_assiette_de_la_tva():
    tva = next(d for d in _positions("TZA")["24029000"]["droits"] if d["code"] == "TVA")
    assert "Railway Development Levy" in tva["note"]


@pytest.mark.parametrize("code", ["24021000", "24029000", "24031100"])
def test_tanzanie_positions_hors_du_fourth_schedule(code):
    assert not any(d["code"] == "EXC" for d in _positions("TZA")[code]["droits"])


def test_tabac_ouganda_200_pour_cent():
    etat, lignes = _calcul("UGA", "24031100")
    assert etat == "COMPLET" and lignes["EXC"]["taux_pct"] == 200.0
    assert lignes["EXC"]["base"] == 1_350_000.0


@pytest.mark.parametrize("iso,code", [("UGA", "24022010"), ("RWA", "24022010"), ("RWA", "24029000")])
def test_cigarettes_sans_donnee_du_taux(iso, code):
    """Conditionnement (UGA) ou prix de détail (RWA) absents : total incomplet."""
    etat, lignes = _calcul(iso, code)
    assert etat != "COMPLET" and lignes["EXC"]["taux_pct"] is None


def test_cigares_rwanda_et_tva_sur_tous_les_droits():
    etat, lignes = _calcul("RWA", "24021000")
    assert lignes["EXC"]["taux_pct"] == 160.0
    assert lignes["TVA"]["base"] == pytest.approx(1_350_000.0 + 2_160_000.0)
