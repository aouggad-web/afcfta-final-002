"""Défense commerciale (sauvegarde, antidumping) selon l'origine et le
producteur : services/defense_commerciale.py et sa place dans POST /calcul.

Fiche : ZAF_amendements_octobre_2026_2026-10-31.json (R.7991, R.8119)."""

import os
import sys
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import defense_commerciale, socle

besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)

ANTIDUMPING = {
    "code": "AD", "taux": None, "assiette": None, "note": "",
    "defense_commerciale": {
        "id": "AD_TEST", "type": "antidumping", "debut": "2026-03-19", "assiette": "FOB",
        "par_origine": {
            "CHN": {"producteurs": [{"noms": ["Baoshan Iron and Steel"], "taux": 40.77}], "autres": 47.92},
            "JPN": {"producteurs": [{"noms": ["Nippon Steel Corporation"], "taux": 44.95}]},
            "TWN": {"taux": 24.2},
        },
    },
}
SAUVEGARDE = {
    "code": "SAUV", "taux": None, "assiette": None, "note": "",
    "defense_commerciale": {
        "id": "SG_TEST", "type": "sauvegarde", "debut": "2026-10-16", "fin": "2027-05-03", "assiette": "FOB",
        "origines": "TOUTES", "exemptees": ["MUS"], "taux": 21.0,
    },
}
DD = {"code": "DD", "taux": 10.0, "assiette": "FOB"}


def _ligne(position, code):
    return next((d for d in position["droits"] if d["code"] == code), None)


def test_antidumping_selon_l_origine_et_le_producteur():
    position = {"droits": [DD, ANTIDUMPING]}
    le = date(2026, 10, 31)
    taiwan, _ = defense_commerciale.appliquer(position, "TWN", le=le)
    assert _ligne(taiwan, "AD")["taux"] == 24.2
    baoshan, _ = defense_commerciale.appliquer(position, "CHN", "BAOSHAN IRON AND STEEL CO. LTD", le=le)
    assert _ligne(baoshan, "AD")["taux"] == 40.77
    autre, _ = defense_commerciale.appliquer(position, "CHN", "Un autre aciériste", le=le)
    assert _ligne(autre, "AD")["taux"] == 47.92
    sans_producteur, rendu = defense_commerciale.appliquer(position, "CHN", le=le)
    assert _ligne(sans_producteur, "AD")["taux"] is None and rendu[0]["statut"] == "PRODUCTEUR_NON_FOURNI"
    # Un fragment ou une ponctuation n'obtient pas le taux d'un producteur nommé.
    fragment, _ = defense_commerciale.appliquer(position, "CHN", "Steel", le=le)
    assert _ligne(fragment, "AD")["taux"] == 47.92
    vide, _ = defense_commerciale.appliquer(position, "CHN", "!!! Co. Ltd", le=le)
    assert _ligne(vide, "AD")["taux"] is None
    # Producteur japonais non nommé, sans taux « autres » dans la donnée : à établir.
    japon, _ = defense_commerciale.appliquer(position, "JPN", "Autre", le=le)
    assert _ligne(japon, "AD")["taux"] is None


def test_antidumping_retire_pour_une_origine_non_visee_et_a_etablir_sans_origine():
    position = {"droits": [DD, ANTIDUMPING]}
    kenya, rendu = defense_commerciale.appliquer(position, "KEN", le=date(2026, 10, 31))
    assert _ligne(kenya, "AD") is None and rendu[0]["statut"] == "ORIGINE_NON_VISEE"
    sans_origine, rendu = defense_commerciale.appliquer(position, None, le=date(2026, 10, 31))
    assert _ligne(sans_origine, "AD")["taux"] is None and rendu[0]["statut"] == "ORIGINE_NON_FOURNIE"


def test_sauvegarde_selon_l_exemption_et_la_periode():
    position = {"droits": [DD, SAUVEGARDE]}
    visee, _ = defense_commerciale.appliquer(position, "KEN", le=date(2026, 11, 1))
    assert _ligne(visee, "SAUV")["taux"] == 21.0
    exemptee, rendu = defense_commerciale.appliquer(position, "MUS", le=date(2026, 11, 1))
    assert _ligne(exemptee, "SAUV") is None and rendu[0]["statut"] == "ORIGINE_EXEMPTEE"
    echue, rendu = defense_commerciale.appliquer(position, "KEN", le=date(2027, 5, 4))
    assert _ligne(echue, "SAUV") is None and rendu[0]["statut"] == "HORS_PERIODE"
    sans_origine, _ = defense_commerciale.appliquer(position, None, le=date(2026, 11, 1))
    assert _ligne(sans_origine, "SAUV")["taux"] == 21.0


def test_sauvegarde_a_etablir_quand_la_position_couvre_d_autres_produits():
    regle = {**SAUVEGARDE["defense_commerciale"], "condition_produit": "feuilles A4"}
    position = {"droits": [DD, {**SAUVEGARDE, "defense_commerciale": regle}]}
    rendu_position, rendu = defense_commerciale.appliquer(position, "KEN", le=date(2026, 11, 1))
    ligne = _ligne(rendu_position, "SAUV")
    assert ligne["taux"] is None and "feuilles A4" in ligne["note"] and rendu[0]["statut"] == "CONDITION_PRODUIT"


def test_position_sans_mesure_inchangee():
    position = {"droits": [DD]}
    assert defense_commerciale.appliquer(position, "CHN") == (position, [])


@pytest.fixture
def client():
    import importlib.util

    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_defense", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_defense"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _npf(client, **corps):
    reponse = client.post("/calcul", json={"destination": "ZAF", "valeur_cif": 100_000, "valeur_fob": 100_000,
                                            **corps})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    return {ligne["code"]: ligne for ligne in corps["npf"]["lignes"]}, corps


@besoin_socle
def test_route_antidumping_acier_sud_africain(client):
    """R.7991 : Taipei chinois 24,2 % ; Japon, Nippon Steel 44,95 % ; Kenya non visé."""
    lignes, corps = _npf(client, code_sh="72081000", origine="TWN")
    assert lignes["AD"]["montant"] == pytest.approx(24_200)
    lignes, _ = _npf(client, code_sh="72081000", origine="JPN", producteur="NIPPON STEEL CORP.")
    assert lignes["AD"]["montant"] == pytest.approx(44_950)
    # Le droit antidumping entre dans la base de la TVA (VAT Act s.13(2)(a)).
    tva_sans = 100_000 * 1.10 + 10_000
    assert lignes["TVA"]["base"] == pytest.approx(tva_sans + 44_950)
    # Producteur chinois non déclaré : droit à établir, et la TVA qui l'inclut aussi.
    lignes, corps = _npf(client, code_sh="72081000", origine="CHN")
    assert lignes["AD"]["montant"] is None and lignes["TVA"]["montant"] is None
    assert corps["npf"]["etat"] != "COMPLET"
    lignes, corps = _npf(client, code_sh="72081000", origine="KEN")
    assert "AD" not in lignes and corps["defense_commerciale"][0]["statut"] == "ORIGINE_NON_VISEE"


@besoin_socle
def test_route_sauvegarde_papier_de_bureau_et_papier_journal(client):
    """R.8119 : la sauvegarde vise toutes les origines, mais seulement les feuilles A4 : à établir ; R.8025 :
    papier journal à 5 %."""
    lignes, _ = _npf(client, code_sh="48025690", origine="KEN")
    assert lignes["SAUV"]["montant"] is None
    lignes, _ = _npf(client, code_sh="48010000")
    assert lignes["DD"]["montant"] == pytest.approx(5_000)
