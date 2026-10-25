"""Angola : Imposto Especial de Consumo à l'importation (Lei n.º 16/21,
Anexo I ; Lei n.º 14/25, art. 34.º et Anexo IV pour 2026). Fiche :
AGO_IEC_2026-10-25.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "AGO.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_ago_iec_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_ago_iec_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code):
    demande = {"destination": "AGO", "code_sh": code, "valeur_cif": 10000, "valeur_fob": 9000,
               "devise_cif": "AOA", "origine": "CHN"}
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("code,taux", [
    ("22021010", 3.0),   # eaux sucrées
    ("22030000", 4.0),   # bière de malt
    ("22042100", 8.0),   # vins
    ("22071000", 15.0),  # alcool éthylique
    ("22083000", 25.0),  # whisky, Anexo IV de l'OGE 2026
    ("24022000", 50.0),  # cigarettes, Anexo IV de l'OGE 2026
    ("39232110", 2.0),   # sacs d'emballage
    ("40122000", 19.0),  # pneumatiques usagés
    ("87032449", 5.0),   # voitures essence > 3 000 cm³, neuves
    ("87042113", 5.0),   # pickups
    ("89033200", 20.0),  # bateaux à moteur in-bord
    ("97012100", 5.0),   # tableaux
])
def test_iec_sur_le_valor_aduaneiro_et_dans_l_iva(client, code, taux):
    """Art. 7.º n.º 1 b) : valor aduaneiro ; CIVA art. 18.º a) : l'IVA comprend l'IEC."""
    etat, lignes = _calcul(client, code)
    assert etat == "COMPLET"
    assert lignes["EXC"]["base"] == pytest.approx(10_000)
    assert lignes["EXC"]["montant"] == pytest.approx(100 * taux)
    autres = sum(lignes[c]["montant"] for c in lignes if c != "TVA")
    assert lignes["TVA"]["base"] == pytest.approx(10_000 + autres)


def test_hors_du_perimetre():
    """Ambulances, pétrole (Anexo II, exigible à la mise à disposition), 24.04,
    3926.90.50 et 8903.99 : pas d'IEC."""
    with open(os.path.join(RACINE, "backend", "socle", "AGO.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code in ("87032441", "27101212", "24041100", "39269050", "89039900", "22043000"):
        assert not any(d["code"] == "EXC" for d in positions[code]["droits"])
