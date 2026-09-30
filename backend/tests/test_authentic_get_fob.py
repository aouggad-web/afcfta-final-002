"""
Variante GET de /authentic-tariffs/calculate — valeur FOB de la SACU.

Le frontend appelle cette variante GET. Elle n'acceptait pas `fob_value` et ne
le transmettait pas : le paramètre gardait alors son défaut FastAPI (un objet
`Query`, pas `None`), et toute position sud-africaine à droit non nul
répondait 500 (TypeError) au lieu de réclamer la valeur FOB.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.authentic_tariffs import router
from services.authentic_tariff_service import get_tariff_line

CODE = "020110"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _precondition():
    line = get_tariff_line("ZAF", CODE)
    assert line is not None and (line.get("dd_rate") or 0) > 0, (
        "précondition invalidée : besoin d'une ligne ZAF avec un droit de douane non nul"
    )


def test_sans_fob_le_chemin_historique_reclame_la_valeur_fob(client):
    r = client.get(f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000})

    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "VALEUR_FOB_REQUISE"
    assert detail["missing_or_non_ad_valorem_taxes"] == ["DD"]


def test_avec_fob_le_droit_est_liquide_sur_la_valeur_fob(client):
    r = client.get(
        f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000, "fob_value": 800}
    )

    assert r.status_code == 200, r.text
    etape_dd = next(s for s in r.json()["calculation_steps"] if s["code"] == "DD")
    assert etape_dd["base_formula"] == "FOB"
    assert etape_dd["base_value"] == 800


def test_fob_superieure_a_la_cif_reste_une_erreur_de_saisie(client):
    r = client.get(
        f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000, "fob_value": 1200}
    )

    assert r.status_code == 422, r.text
    assert "valeur_fob" in str(r.json()["detail"])
