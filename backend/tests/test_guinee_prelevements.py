"""Guinée : tarif de la DGD (TEC CEDEAO SH 2022) ; DD, RTL, PC et CA sur la valeur
CAF ; accises (colonne AC) sur la valeur CAF et les droits perçus au cordon
douanier (CGI art. 436) ; TVA sur la valeur et tous les droits et taxes liquidés
(arrêté du 31/03/2017, art. 12). Fiche : GIN_prelevements_TVA_2026-10-11.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GIN.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1_000_000, devise_cif="GNF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_droits_d_entree_et_tva(positions):
    """0101.29 : DD 10 % ; PC 0,5 % ; RTL 2 % ; CA 0,25 % ; TVA 18 % sur 1 127 500."""
    etat, lignes = _calcul(positions["0101290000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "PCC", "RTL", "CA")] == [100_000.0, 5_000.0, 20_000.0, 2_500.0]
    assert lignes["TVA"]["base"] == 1_127_500.0


def test_tva_exoneree_au_tarif(positions):
    """0101.21 : TVA « ex » au tarif."""
    assert _calcul(positions["0101210000"])[1]["TVA"]["montant"] == 0.0


def test_accise_sur_la_valeur_et_les_droits_d_entree(positions):
    """Bière 2203.00.10 : AC 47 % sur 1 000 000 + 200 000 + 5 000 + 20 000 + 2 500 ; TVA sur cette base + l'accise."""
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["DA"]["taux_pct"] == 47.0 and lignes["DA"]["base"] == 1_227_500.0
    assert lignes["TVA"]["base"] == pytest.approx(1_227_500.0 + 576_925.0)


def test_accise_specifique_des_produits_petroliers_sans_taux(positions):
    etat, lignes = _calcul(positions["2710124000"])
    assert lignes["DA"]["taux_pct"] is None and etat != "COMPLET"


def test_frais_existants_sans_montant_au_bloc_reglementaire():
    """Redevance informatique, GUCEG, port de Conakry : cités, montant non publié, jamais à zéro."""
    from services.regulatory_fee_service import build_regulatory_blocks

    cout = build_regulatory_blocks("GIN", None, fob_value=1000, cif_value=1000)["regulatory_cost"]
    lignes = {l["measure_name"]: l for l in cout["line_items"]}
    for nom in ("Redevance informatique (SYDONIA World)", "Prestations du guichet unique (GUCEG)",
                "Port autonome de Conakry (escales, acconage, magasinage)"):
        assert lignes[nom]["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
        assert lignes[nom]["calculated_amount"] is None and lignes[nom]["tier"] == "EXISTENCE_ONLY"
    assert cout["has_unpriced_fees"] is True and cout["regulatory_cost_total"] is None


def test_port_de_conakry_ecarte_pour_une_importation_par_route():
    from services.regulatory_fee_service import build_regulatory_blocks, transport_declare

    def frais(mode):
        cout = build_regulatory_blocks(
            "GIN", None, fob_value=1000, cif_value=1000, transport=transport_declare(None, None, mode)
        )["regulatory_cost"]
        return {l["measure_name"] for l in cout["line_items"]}

    port = "Port autonome de Conakry (escales, acconage, magasinage)"
    assert port in frais("MER") and port in frais(None)
    assert port not in frais("ROUTE") and port not in frais("AIR")
    assert "Prestations du guichet unique (GUCEG)" in frais("ROUTE")
