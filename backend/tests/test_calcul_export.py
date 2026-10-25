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
    # La RPD s'assoit sur la taxe manquante : elle est incomplète, pas nulle.
    assert sans["etat"] == "INDISPONIBLE"
    assert _ligne(sans, "TAXE/FERRAILLES.EXP")["statut"] == "QUANTITE_REQUISE"
    assert _ligne(sans, "RPD/EXPOR")["statut"] == "ASSIETTE_INCOMPLETE"

    avec = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="TND", quantite=5000)
    assert avec["etat"] == "COMPLET"
    assert avec["total_droits"] == pytest.approx(1500.0)


def test_tun_rpd_liquidee_apres_les_droits_quelle_somme(client):
    """La RPD s'assoit sur la somme des autres droits : servie avant eux, sa
    base serait nulle (le moteur liquide dans l'ordre servi)."""
    export = _export(client, pays="TUN", code_sh="8549122000", valeur=1000, devise="TND", quantite=500)
    assert [ligne["code"] for ligne in export["lignes"]][-1] == "RPD/EXPOR"
    assert _ligne(export, "RPD/EXPOR")["base"] == pytest.approx(_ligne(export, "TAXE/FERRAILLES.EXP")["montant"])


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


def test_taux_de_change_en_devise_pour_un_dinar(client):
    """Comme pour POST /calcul : unités de `devise` pour UN dinar. 0,3 TND/kg
    × 5 000 kg = 1 500 TND, soit 483,87 USD à 3,1 TND pour 1 USD."""
    export = _export(
        client, pays="TUN", code_sh="2620110000", valeur=10000, devise="USD", quantite=5000, taux_de_change=1 / 3.1
    )
    assert _ligne(export, "TAXE/FERRAILLES.EXP")["montant"] == pytest.approx(1500 / 3.1, rel=1e-6)


def test_civ_chicoree_hors_regle_du_cafe(client):
    """La liste DGD nomme le café, pas la chicorée (2101.30) : la note du
    café ne s'y attache pas."""
    export = _export(client, pays="CIV", code_sh="2101300000", valeur=1000, devise="XOF")
    assert "CAFE" not in _ligne(export, "DUS")["note"]
    assert "CAFE" in _ligne(_export(client, pays="CIV", code_sh="2101110000", valeur=1000), "DUS")["note"]
