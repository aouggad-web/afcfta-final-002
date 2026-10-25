"""Droits et taxes à l'exportation (`POST /calcul/export`) : lus au socle et
liquidés par le moteur de `POST /calcul`, avec les mêmes refus — une assiette
non collectée, une quantité ou un taux de change manquant rendent la ligne
indisponible et la nomment, jamais un zéro."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "CIV")),
    reason="socle absent : python3 scripts/build_socle.py",
)


@pytest.fixture(scope="module")
def client():
    nom = "routes_calcul_export_test"
    spec = importlib.util.spec_from_file_location(nom, os.path.join(BACKEND, "routes", "calcul_export.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    app.include_router(module.router_couverture)
    return TestClient(app)


def _export(client, **demande):
    reponse = client.post("/calcul/export", json=demande)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["export"]


def _ligne(export, code):
    return next(ligne for ligne in export["lignes"] if ligne["code"] == code)


def test_pays_couverts(client):
    pays = client.get("/calcul/export/pays").json()["pays"]
    assert set(pays) == {"TUN", "CIV"}


def test_tun_dattes_un_pour_cent_de_la_valeur(client):
    export = _export(client, pays="TUN", code_sh="0804100001", valeur=10000, devise="TND")
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DROIT.EXP.DATTES")["montant"] == pytest.approx(100.0)
    assert "total_a_payer" not in export


def test_tun_ferrailles_droit_specifique_exige_la_quantite(client):
    sans = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="TND")
    assert sans["etat"] == "PARTIEL"
    assert [m["code"] for m in sans["manques"]] == ["TAXE/FERRAILLES.EXP"]
    assert _ligne(sans, "TAXE/FERRAILLES.EXP")["statut"] == "QUANTITE_REQUISE"

    avec = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="TND", quantite=5000)
    assert avec["etat"] == "COMPLET"
    assert avec["total_droits"] == pytest.approx(1500.0)


def test_tun_droit_en_dinars_et_valeur_en_dollars_exige_le_change(client):
    export = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="USD", quantite=5000)
    assert _ligne(export, "TAXE/FERRAILLES.EXP")["statut"] == "TAUX_DE_CHANGE_REQUIS"


def test_civ_karite_dix_francs_le_kilo(client):
    export = _export(client, pays="CIV", code_sh="1207991000", valeur=1000000, devise="XOF", quantite=20000)
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DUS")["montant"] == pytest.approx(200000.0)


def test_civ_cacao_prix_de_reference_non_collecte(client):
    export = _export(client, pays="CIV", code_sh="1801001100", valeur=1000000, devise="XOF")
    ligne = _ligne(export, "DUS")
    assert ligne["statut"] == "ASSIETTE_INDISPONIBLE"
    assert ligne["montant"] is None
    assert "PRIX CAF DE REFERENCE" in ligne["note"]


def test_position_sans_droit_de_sortie(client):
    reponse = client.post("/calcul/export", json={"pays": "CIV", "code_sh": "0101210000", "valeur": 1000})
    corps = reponse.json()
    assert corps["droits_export_publies"] is False
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"
    assert corps["export"]["lignes"] == []


def test_pays_sans_droit_export_au_socle(client):
    reponse = client.post("/calcul/export", json={"pays": "KEN", "code_sh": "0901110000", "valeur": 1000})
    assert reponse.status_code == 404


def test_sh6_exige_la_position_nationale(client):
    reponse = client.post("/calcul/export", json={"pays": "TUN", "code_sh": "080410", "valeur": 1000})
    assert reponse.status_code == 422
    assert reponse.json()["detail"]["code"] == "POSITION_NATIONALE_REQUISE"
