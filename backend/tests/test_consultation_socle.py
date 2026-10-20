"""Consultation du tarif par le socle : les sous-positions proposées à l'écran
sont celles que POST /calcul sait liquider."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "EGY")),
    reason="socle absent : python3 scripts/build_socle.py",
)


def _route(nom):
    spec = importlib.util.spec_from_file_location(f"routes_{nom}_test", os.path.join(BACKEND, "routes", f"{nom}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"routes_{nom}_test"] = module
    spec.loader.exec_module(module)
    return module.router


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(_route("consultation"))
    app.include_router(_route("calcul"))
    return TestClient(app)


def test_sous_positions_lues_au_socle(client):
    reponse = client.get("/consultation/TUN/sous-positions/870323")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["source"] == "socle"
    assert corps["total"] == len(corps["sub_positions"]) > 1
    premiere = corps["sub_positions"][0]
    assert premiere["code"].startswith("870323") and premiere["digits"] == 10
    assert "cle_controle" in premiere
    assert isinstance(premiere["description_fr"], str) and premiere["description_fr"]


def test_le_droit_de_douane_est_celui_du_socle(client):
    ligne = client.get("/consultation/EGY/sous-positions/220830").json()["sub_positions"][0]
    assert ligne["code"] == "2208300000" and ligne["dd_rate"] == 3000.0


def test_memes_positions_que_le_calcul_en_reclame(client):
    """Un SH6 à plusieurs positions : la liste servie est exactement celle que
    POST /calcul nomme dans son refus POSITION_NATIONALE_REQUISE."""
    refus = client.post("/calcul", json={"destination": "TUN", "code_sh": "870323", "valeur_cif": 1000})
    assert refus.status_code == 422
    attendues = [p["code"] for p in refus.json()["detail"]["positions"]]
    servies = [p["code"] for p in client.get("/consultation/TUN/sous-positions/870323").json()["sub_positions"]]
    assert servies == attendues


def test_pays_hors_socle_et_code_invalide(client):
    assert client.get("/consultation/XXX/sous-positions/010121").status_code == 503
    assert client.get("/consultation/EGY/sous-positions/12").status_code == 422
