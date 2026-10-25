"""Mali : tarif de la DGD (TEC CEDEAO, édition du Mali, 28/12/2023) ; ISCP sur la
valeur en douane majorée des droits et taxes dus à l'entrée (CGI art. 243) ;
TVA sur la valeur CAF et tous les droits et taxes autres que la TVA (CGI
art. 198 et 199). Fiche : MLI_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "MLI.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_prelevements_du_tarif_et_tva(positions):
    """0101.21 : DD 5 % : 50 ; RS 10 ; PC-AES 5 ; PCS 0,8 % : 8 ; TVA 18 % sur 1 073."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PC-AES", "PCS")] == [50.0, 10.0, 5.0, 8.0]
    assert lignes["TVA"]["base"] == 1073.0


def test_iscp_sur_valeur_et_droits_d_entree(positions):
    """Bière 2203.00.10 : ISCP 50 % sur 1 000 + 200 + 10 + 5 + 8 ; TVA sur cette base + ISCP."""
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["ISCP"]["base"] == 1223.0 and lignes["ISCP"]["montant"] == 611.5
    assert lignes["TVA"]["base"] == 1834.5


def test_tai_droit_d_entree(positions):
    """0101.29 : TAI 5 % sur la valeur CAF, comprise dans la base de la TVA."""
    etat, lignes = _calcul(positions["0101290000"])
    assert lignes["TAI"]["montant"] == 50.0
    assert lignes["TVA"]["base"] == 1173.0


def test_tci_sans_assiette_rend_la_tva_indisponible(positions):
    etat, lignes = _calcul(positions["1701120000"])
    assert lignes["TCI"]["montant"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"


def test_tva_du_tarif_officiel(positions):
    taux = {d["code"]: d["taux"] for d in positions["0101210000"]["droits"]}
    assert taux["PCS"] == 0.8 and "PCC" not in taux


def test_tva_vide_du_tarif_prend_le_taux_de_droit_commun(positions):
    """9508.21 : case de TVA vide au tarif, position absente des listes du CGI
    (art. 195 IV, point D) : 18 % (art. 229), pas TVA non due."""
    etat, lignes = _calcul(positions["9508210000"])
    assert lignes["TVA"]["taux_pct"] == 18.0 and etat == "COMPLET"


def test_intention_d_importation_et_pvi_au_bloc_reglementaire():
    """Hors des droits et taxes : intention d'importation 1 500 F, PVI 0,75 % de la FOB (guide CCIM)."""
    from services.regulatory_fee_service import build_regulatory_blocks

    cout = build_regulatory_blocks("MLI", None, fob_value=5_000_000, cif_value=5_500_000)["regulatory_cost"]
    montants = {l["measure_name"]: (l["fee_status"], l["calculated_amount"]) for l in cout["line_items"]}
    assert montants["Intention d'importation (II)"] == ("DOCUMENTED_FIXED_AMOUNT", 1_500.0)
    assert montants["PVI — Programme de vérification des importations (vérification avant embarquement)"] == (
        "CALCULABLE", 37_500.0,
    )
    pvi = next(l for l in cout["line_items"] if l["measure_name"].startswith("PVI"))
    assert pvi["stage"] == "export"  # vérification avant embarquement, payée par l'importateur
    # 1 500 XOF et 37 500 dans l'unité de la FOB saisie ne s'additionnent pas.
    assert cout["regulatory_cost_total"] is None
