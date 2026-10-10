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


def test_utilitaire_usage_taxe_vehicules_et_enregistrement(positions):
    """Utilitaire usagé à 10 % : la FAQ DGD (38,01 %) ne porte pas la taxe sur les
    véhicules, que la loi 2025-17 étend à tous les véhicules importés (10 % sur
    base + DD + RS = 11,1 %, et TVA sur base + DD + RS + DA). Enregistrement 3 %
    lu dans le libellé « usagé »."""
    code = next(k for k in positions if k.startswith("870421") and "usagé" in positions[k]["designation"].lower()
                and any(d["code"] == "DD" and d["taux"] == 10.0 for d in positions[k]["droits"]))
    etat, lignes = _calcul(positions[code])
    assert lignes["DENR"]["taux_pct"] == 3.0 and lignes["DA"]["montant"] == 111.0
    assert lignes["TVA"]["base"] == 1221.0 and etat == COMPLET
    assert lignes["PCS"]["montant"] == 8.0 and lignes["PROMAD"]["montant"] == 20.0


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
    assert _calcul(positions["2402100000"])[1]["DA"]["taux_pct"] == 100.0
    assert _calcul(positions["2402200000"])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"
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


def test_revue_codex_5(positions):
    """Tracteur routier et véhicule spécial : enregistrement sans taux ;
    cigarettes : surtaxe sans taux et TVA indisponible ; vêtements non tissés exclus."""
    assert "DENR" in _calcul(positions["8701202000"])[1]
    assert "DENR" in _calcul(positions[next(k for k in positions if k.startswith("8705"))])[1]
    etat, lignes = _calcul(positions["2402200000"])
    assert lignes["STC"]["statut"] == "TAUX_INDISPONIBLE" and lignes["TVA"]["montant"] is None
    assert "DA" not in _calcul(positions["6210100000"])[1]


def test_revue_codex_6(positions):
    """Libellés nationaux : tracteur routier usagé 3 %, neuf 1 % ; eau gazéifiée
    5 %, eau plate sans taxe ; préformes et palme non alimentaire exclues ;
    cigares sans surtaxe ; tomates autres que concentrés sans TCI."""
    assert _calcul(positions["8701202000"])[1]["DENR"]["taux_pct"] == 3.0
    assert _calcul(positions["8701201000"])[1]["DENR"]["taux_pct"] == 1.0
    assert _calcul(positions["2201102000"])[1]["DA"]["taux_pct"] == 5.0
    for code in ("2201900000", "3923301000", "1511901000"):
        assert "DA" not in _calcul(positions[code])[1]
    assert "STC" not in _calcul(positions["2402100000"])[1]
    assert "TCI" not in _calcul(positions["2002909000"])[1]
    for code in ("5905000000", "3923900000"):
        assert _calcul(positions[code])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"


def test_revue_codex_7(positions):
    """« usages spéciaux » n'est pas « usagé » ; 59.06 et 8543.70 (cigarettes
    électroniques en SH 2017) sans taux."""
    assert _calcul(positions["8705900000"])[1]["DENR"]["statut"] == "TAUX_INDISPONIBLE"
    for code in ("5906910000", "8543700000"):
        assert _calcul(positions[code])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"


def test_revue_codex_8(positions):
    """Vin de palme exonéré (art. 412, 3°) ; moûts de raisin sans taux ; tapis tissés 5 %."""
    assert not {"DA", "TAA"} & set(_calcul(positions["2206009100"])[1])
    assert _calcul(positions["2204300000"])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"
    assert _calcul(positions["5702100000"])[1]["DA"]["taux_pct"] == 5.0
    assert _calcul(positions["5705000000"])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"


def test_revue_codex_9(positions):
    """Chariots automobiles (87.09.11/19) taxés comme véhicules ; 02.09 et
    2206.00.99 (cidres et poirés exonérés mêlés) sans taux ; DA en règle de pays."""
    assert _calcul(positions["8709110000"])[1]["DA"]["taux_pct"] == 10.0
    for code in ("0209100000", "2206009900"):
        assert _calcul(positions[code])[1]["DA"]["statut"] == "TAUX_INDISPONIBLE"
    assert all(d["assiette_origine"] == "regle_de_pays"
               for p in positions.values() for d in p["droits"] if d["code"] == "DA")
