"""Afrique du Sud : contrôles de la liste SARS des marchandises prohibées ou
réglementées d'octobre 2026, servis comme formalités, sans effet sur les droits.
Fiche : ZAF_controles_sars_2026-10-26.json."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(socle.SOCLE_DIR, "ZAF.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def client():
    spec = importlib.util.spec_from_file_location(
        "routes_consultation_zaf_test", os.path.join(BACKEND, "routes", "consultation.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_consultation_zaf_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _formalites(client, code):
    reponse = client.get(f"/consultation/ZAF/formalites/{code}")
    assert reponse.status_code == 200
    return reponse.json()


@pytest.mark.parametrize("code,attendus", [
    ("950590", ["PHYSICAL_INSPECTION_PORT_HEALTH"]),
    ("95030090", ["NRCS_LETTER_OF_AUTHORITY", "PHYSICAL_INSPECTION_PORT_HEALTH"]),
    ("290220", ["PHYSICAL_INSPECTION_PORT_HEALTH"]),
    ("290230", ["ITAC_IMPORT_PERMIT", "PHYSICAL_INSPECTION_PORT_HEALTH"]),
])
def test_retenue_port_health_a_l_importation(client, code, attendus):
    reponse = _formalites(client, code)
    assert reponse["statut"] == "DOCUMENTEES"
    assert [f["code"] for f in reponse["formalities"]] == attendus
    assert all("SARS" in f["source"] for f in reponse["formalities"])


def test_9505_10_sortie_du_controle_le_22_octobre(client):
    reponse = _formalites(client, "950510")
    assert reponse["formalities"] == [] and reponse["statut"] == "NON_ETABLIES"


def test_controle_export_2530_90_sauf_pyrophyllite(client):
    reponse = _formalites(client, "253090")
    assert reponse["formalities"] == []
    (controle,) = reponse["formalities_export"]
    assert controle["code"] == "ITAC_EXPORT_PERMIT"
    assert controle["exclusion_produit"]["produit"] == "Pyrophyllite"


def test_aucun_effet_sur_les_droits():
    position = socle.position("ZAF", "950590")[0]
    assert not [d for d in position["droits"] if "SARS" in (d.get("source") or "")]
