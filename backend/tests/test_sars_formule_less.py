"""SACU : « 110c/kg less 80% with a maximum of 37% » et « 10% or 55c/kg less 90% ».

Le socle gardait la part spécifique (110c/kg) et le plafond (37 %), et perdait
la déduction « less 80% ». Le moteur liquidait donc 110c/kg × quantité, borné à
37 % : un droit SURESTIMÉ de 80 % de la valeur en douane.

Lecture établie (fiche SACU_formule_less_2026-10-25.json) : dans la colonne
des taux, « % » signifie « per cent AD VALOREM » (General Notes, G.53), sur la
« value for duty purposes » (C.) — la valeur FOB des pays SACU. Le taux est
donc « Yc/kg moins N % de la valeur », borné à M % de cette même valeur ;
séparé par « or », il est un taux complet que la note B.3 compare à l'autre.

Cinq positions par pays SACU : 1901.90.10, 2002.10.90, 2006.00.30, 2401.10,
2401.20 — au NPF et dans les colonnes EFTA, MERCOSUR et AfCFTA.
"""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle
from services.calcul import MANQUE_FOB, MANQUE_REGLE_COMPOSEE, calculer
from services.preference import taux_preferentiels

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)


def _constructeur():
    spec = importlib.util.spec_from_file_location(
        "build_socle_less_test", os.path.join(RACINE, "scripts", "build_socle.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_less_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_less_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _rangee(brut, rate_pct, specifique, source="sars.gov.za"):
    rangee = {"code": "GENERAL", "name": "General Customs Duty", "rate_pct": rate_pct,
              "raw_value": brut, "compound": True, "specific_component": specifique}
    return _constructeur().droits_depuis_liste([rangee], source)[0]


# ── Lecture de la ligne SARS ─────────────────────────────────────────────────
def test_la_deduction_de_la_forme_plafonnee_est_conservee():
    """Le crawl range 80,0 (la déduction) dans `rate_pct` : ni taux, ni perdue."""
    droit = _rangee("110c/kg less 80% with a maximum of 37%", 80.0, "110c/kg")
    assert droit["taux"] is None
    assert droit["specifique"] == "110c/kg"
    assert droit["plafond_ad_valorem_pct"] == 37.0
    assert droit["deduction_ad_valorem_pct"] == 80.0


def test_la_forme_or_suit_la_note_b3_avec_sa_deduction():
    droit = _rangee("10% or 55c/kg less 90%", 10.0, "55c/kg")
    assert droit["taux"] == 10.0
    assert droit["regle_composee"] == "LE_PLUS_ELEVE"
    assert droit["deduction_ad_valorem_pct"] == 90.0


def test_la_virgule_decimale_de_la_colonne_afcfta_est_lue():
    droit = _rangee("344c/kg less 34% with a maximum of 17,6%", 34.0, "344c/kg")
    assert (droit["deduction_ad_valorem_pct"], droit["plafond_ad_valorem_pct"]) == (34.0, 17.6)


def test_hors_tarif_sars_la_formule_n_est_pas_liquidable():
    """La lecture « % = ad valorem » est celle des General Notes SARS : ailleurs,
    ni le spécifique seul ni aucun montant."""
    droit = _rangee("110c/kg less 80% with a maximum of 37%", 80.0, "110c/kg", source="autre.example")
    assert droit["taux"] is None and droit.get("specifique") is None
    assert "less" in droit["note"]


# ── Liquidation ──────────────────────────────────────────────────────────────
#
# 1 000 kg de tomates (2002.10.90), FOB 1 000 R, CIF 1 200 R. Dû :
# 1,10 × 1 000 − 80 % × 1 000 = 300 R, sous le plafond de 37 % × 1 000 = 370 R.
# Servi avant correction : 1 100 R bornés à 37 % du CIF, soit 444 R.

PLAFONNE = {
    "designation": "Other",
    "hs6": "200210",
    "unite": "kg",
    "droits": [
        {
            "code": "DD",
            "famille": "droit",
            "specifique": {"montant": 1.1, "unite_monetaire": "unite_principale",
                           "unite_quantite": "kg", "brut": "110c/kg"},
            "assiette": "xQTE",
            "assiette_valeur": "FOB",
            "plafond_ad_valorem_pct": 37.0,
            "deduction_ad_valorem_pct": 80.0,
            "expression_brute": "110c/kg less 80% with a maximum of 37%",
            "source": "sars.gov.za",
        }
    ],
}


def _dd(position, cif, fob, quantite=1000.0, **kw):
    resultat = calculer(position, cif, valeur_fob=fob, quantite=quantite, **kw)
    return next(l for l in resultat["npf"]["lignes"] if l["code"] == "DD")


def test_la_deduction_est_retranchee_du_specifique():
    """Le défaut mesuré : 444 R servis pour 300 R dus."""
    ligne = _dd(PLAFONNE, 1200.0, 1000.0)
    assert ligne["statut"] == "CALCULE"
    assert ligne["montant"] == 300.0
    assert ligne["deduction_ad_valorem_montant"] == 800.0
    assert ligne.get("plafond_applique") is not True


def test_le_plafond_porte_sur_la_meme_valeur_que_la_deduction():
    """0,50 R/kg : 1 100 − 400 = 700, borné à 37 % de la valeur FOB (185), pas du CIF."""
    ligne = _dd(PLAFONNE, 600.0, 500.0)
    assert ligne["montant"] == 185.0
    assert ligne["plafond_applique"] is True


def test_une_formule_negative_ne_produit_aucun_droit():
    """2 R/kg : 1 100 − 1 600 < 0. Un droit négatif n'existe pas : rien n'est dû."""
    ligne = _dd(PLAFONNE, 2200.0, 2000.0)
    assert ligne["statut"] == "CALCULE"
    assert ligne["montant"] == 0.0
    assert ligne["formule_negative"] is True


def test_sans_valeur_fob_la_ligne_reste_indisponible():
    """La déduction porte sur la valeur en douane SACU : sans elle, jamais 110c/kg seul."""
    ligne = _dd(PLAFONNE, 1200.0, None)
    assert ligne["statut"] == MANQUE_FOB
    assert ligne["montant"] is None


OU = {
    "designation": "Corn flour",
    "hs6": "190190",
    "unite": "kg",
    "droits": [
        {
            "code": "DD",
            "famille": "droit",
            "taux": 10.0,
            "specifique": {"montant": 0.55, "unite_monetaire": "unite_principale",
                           "unite_quantite": "kg", "brut": "55c/kg"},
            "assiette": "FOB",
            "assiette_valeur": "FOB",
            "compose": True,
            "regle_composee": "LE_PLUS_ELEVE",
            "deduction_ad_valorem_pct": 90.0,
            "expression_brute": "10% or 55c/kg less 90%",
            "source": "sars.gov.za",
        }
    ],
}


def test_la_forme_or_compare_le_specifique_net_de_sa_deduction():
    """0,30 R/kg : 10 % → 30 R ; 550 − 270 → 280 R. La part spécifique l'emporte, nette."""
    ligne = _dd(OU, 300.0, 300.0)
    assert ligne["composantes"]["specifique_montant"] == 280.0
    assert ligne["composante_retenue"] == "specifique"
    assert ligne["montant"] == 280.0


def test_la_forme_or_retient_l_ad_valorem_quand_la_formule_s_annule():
    ligne = _dd(OU, 1000.0, 1000.0)
    assert ligne["montant"] == 100.0
    assert ligne["composante_retenue"] == "ad_valorem"


# ── Bout en bout sur le socle ────────────────────────────────────────────────
@besoin_socle
@pytest.mark.parametrize("pays", ["ZAF", "BWA", "LSO", "NAM", "SWZ"])
def test_le_socle_sacu_porte_la_deduction(pays):
    position = socle.position(pays, "20021090")[0]
    dd = next(d for d in position["droits"] if d["code"] == "DD")
    assert dd["deduction_ad_valorem_pct"] == 80.0
    assert dd["assiette_valeur"] == "FOB"
    assert position["preferentiels"]["AFCFTA"]["deduction_ad_valorem_pct"] == 80.0


@besoin_socle
def test_la_route_liquide_2002_10_90_net_de_sa_deduction(client):
    reponse = client.post(
        "/calcul",
        json={"destination": "ZAF", "code_sh": "20021090", "valeur_cif": 1200,
              "valeur_fob": 1000, "quantite": 1000},
    )
    ligne = next(l for l in reponse.json()["npf"]["lignes"] if l["code"] == "DD")
    assert (ligne["statut"], ligne["montant"]) == ("CALCULE", 300.0)


@besoin_socle
def test_la_colonne_afcfta_de_2401_10_garde_sa_deduction():
    """« 344c/kg less 34% with a maximum of 17,6% » (Égypte, 1 000 kg, FOB 5 000) :
    3 440 − 1 700 = 1 740, borné à 17,6 % × 5 000 = 880."""
    position, _ = socle.position("ZAF", "240110")
    table = taux_preferentiels(position, "ZAF", "EGY", "240110")
    assert table["taux"]["DD"]["deduction_ad_valorem_pct"] == 34.0
    resultat = calculer(position, 6000.0, quantite=1000.0, valeur_fob=5000.0,
                        taux_preferentiels=table["taux"])
    ligne = next(l for l in resultat["preference"]["lignes"] if l["code"] == "DD")
    assert ligne["montant"] == 880.0
    assert ligne["montant_avant_plafond"] == 1740.0


@besoin_socle
def test_la_colonne_afcfta_de_2401_10_sans_plafond_mordant():
    """FOB 9 000 : 3 440 − 3 060 = 380, sous 17,6 % × 9 000 = 1 584."""
    position, _ = socle.position("ZAF", "240110")
    table = taux_preferentiels(position, "ZAF", "EGY", "240110")
    resultat = calculer(position, 9500.0, quantite=1000.0, valeur_fob=9000.0,
                        taux_preferentiels=table["taux"])
    ligne = next(l for l in resultat["preference"]["lignes"] if l["code"] == "DD")
    assert ligne["montant"] == 380.0


@besoin_socle
def test_la_forme_or_du_socle_se_liquide(client):
    """1901.90.10, 1 000 kg, FOB 300 : max(30 ; 550 − 270) = 280."""
    reponse = client.post(
        "/calcul",
        json={"destination": "ZAF", "code_sh": "19019010", "valeur_cif": 350,
              "valeur_fob": 300, "quantite": 1000},
    )
    ligne = next(l for l in reponse.json()["npf"]["lignes"] if l["code"] == "DD")
    assert ligne["statut"] != MANQUE_REGLE_COMPOSEE
    assert ligne["montant"] == 280.0
