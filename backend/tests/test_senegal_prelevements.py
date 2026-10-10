"""Sénégal : prélèvements d'entrée et taxes spécifiques selon le CGI (édition
DGID 2025) et les FAQ de la DGD (2026). Fiche : SEN_taxes_specifiques_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "SEN.json")
COMPLET = "COMPLET"

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_utilitaire_reproduit_le_taux_cumule_de_la_dgd(positions):
    """FAQ véhicules, utilitaire usagé à 10 % : 38,01 %, dont enregistrement
    3,33 % non liquidé : 34,68 % ; plus le PUA de 0,2 % maintenu : 34,88 %."""
    code = next(k for k in positions if k.startswith("870421") and
                any(d["code"] == "DD" and d["taux"] == 10.0 for d in positions[k]["droits"]))
    etat, lignes = _calcul(positions[code])
    assert "DA" not in lignes
    # Enregistrement (1 % neuf, 3 % d'occasion) : état absent de la position, sans taux.
    assert lignes["DENR"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    assert round(sum(l["montant"] for l in lignes.values() if l["montant"]) / 10, 2) == 34.88
    assert lignes["PCS"]["montant"] == 8.0 and lignes["PROMAD"]["montant"] == 20.0
    assert lignes["TVA"]["base"] == 1110.0


def test_vehicule_de_tourisme_taxe_specifique_10_pour_cent(positions):
    """FAQ véhicules : droit d'accises « (base + DD + RS) × 10 % » = 12,1 % ;
    TVA sur base + DD + RS + DA."""
    etat, lignes = _calcul(positions["8703100000"])
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1210.0, 121.0)
    assert lignes["TVA"]["base"] == 1331.0 and etat != COMPLET  # enregistrement sans taux


def test_pcs_a_0_8_pour_cent_promad_et_cosec_sur_toutes_les_positions(positions):
    droits = [d for p in positions.values() for d in p["droits"]]
    assert sum(1 for d in droits if d["code"] == "COSEC") == len(positions)
    assert {d["taux"] for d in droits if d["code"] == "PCS"} == {0.8}
    assert sum(1 for d in droits if d["code"] == "PROMAD") == len(positions)


def test_alcools_et_tabacs_aux_taux_de_la_loi_2025_17(positions):
    """Tableau de la DGID : alcools importés 65 %, tabac 100 % ; la taxe
    additionnelle par litre d'alcool reste sans taux (degré et volume absents)."""
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["DA"]["taux_pct"] == 65.0
    assert lignes["TAA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    assert _calcul(positions["2402200000"])[1]["DA"]["taux_pct"] == 100.0
    assert _calcul(positions["9614000000"])[1]["DA"]["taux_pct"] == 100.0


def test_cosmetique_et_tissu_taxes_cereale_non(positions):
    assert _calcul(positions["3304990000"])[1]["DA"]["montant"] == 121.0
    assert _calcul(positions["5208110000"])[1]["DA"]["taux_pct"] == 5.0
    etat, lignes = _calcul(positions["1006301000"])
    assert "DA" not in lignes and etat == COMPLET


def test_positions_mixtes_sans_taux(positions):
    """Maté (2101.20), soupes et bouillons (2104.10), pipes : sans taux ;
    carburéacteur hors des quatre carburants de l'art. 443 : pas de taxe."""
    for code in ("2101200000", "2104101000", "2710124000", "2202100000", "1517909000", "0401400000", "1506000000", "1517100000", "5801100000", "5903100000", "0210110000", "3923210000"):
        etat, lignes = _calcul(positions[code])
        assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    assert "DA" not in _calcul(positions["2710191100"])[1]
