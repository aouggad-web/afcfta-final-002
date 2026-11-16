"""Paramètres bornés avant tout calcul ou appel externe (audit D4 et D5,
16/11/2026).

- OEC (onglet Statistiques) : niveau SH en liste fermée, années du cube
  HS Rev. 2017 (2018 à la dernière disponible), limites bornées, sens du flux
  en liste fermée. Sinon : 422, sans appel à l'OEC.
- Devis d'assurance en lot (module Finance) : au plus 10 types de produits,
  doublons retirés.
"""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes import insurance, oec  # noqa: E402


@pytest.fixture
def client_oec(monkeypatch):
    async def interdit(*_args, **_kwargs):
        raise AssertionError("appel OEC")

    for nom in (
        "get_exports_by_product", "get_imports_by_product", "get_trade_by_hs_code",
        "get_top_african_exporters", "get_bilateral_trade", "get_revealed_comparative_advantage",
        "get_trade_complementarity", "get_africa_totals", "get_country_hs6_history",
    ):
        monkeypatch.setattr(oec.oec_service, nom, interdit)
    app = FastAPI()
    app.include_router(oec.router, prefix="/api")
    return TestClient(app)


@pytest.mark.parametrize(
    "chemin",
    [
        "/api/oec/exports/DZA?hs_level=HS5",
        "/api/oec/imports/DZA?hs_level=hs4;x",
        "/api/oec/bilateral/DZA/TUN?hs_level=HS7",
        "/api/oec/rca/DZA?hs_level=HS8",
        "/api/oec/complementarity/DZA/TUN?hs_level=CHAPTER",
        "/api/oec/exports/DZA?year=1990",
        "/api/oec/rca/DZA?year=2099",
        "/api/oec/africa/totals?year=12345",
        "/api/oec/product/180100?year=2017",
        "/api/oec/country/DZA/hs6/180100/history?end_year=2030",
        "/api/oec/exports/DZA?limit=0",
        "/api/oec/exports/DZA?limit=100000",
        "/api/oec/product/180100?trade_flow=reexports",
    ],
)
def test_parametres_oec_hors_bornes_refuses_sans_appel(client_oec, chemin):
    assert client_oec.get(chemin).status_code == 422, chemin


def test_valeurs_de_l_interface_acceptees(client_oec, monkeypatch):
    """Ce qu'envoie l'onglet Statistiques (années 2018 à 2024, HS2/HS4/HS6,
    limites de 20 à 40) passe la validation."""
    vus = []

    async def faux(*args, **kwargs):
        vus.append((args, kwargs))
        return {"data": []}

    monkeypatch.setattr(oec.oec_service, "get_revealed_comparative_advantage", faux)
    monkeypatch.setattr(oec.oec_service, "get_bilateral_trade", faux)

    assert client_oec.get("/api/oec/rca/DZA?year=2024&hs_level=HS6&limit=25").status_code == 200
    assert client_oec.get("/api/oec/bilateral/DZA/TUN?year=2018&hs_level=HS2&limit=20").status_code == 200
    assert len(vus) == 2


@pytest.fixture
def client_assurance(monkeypatch):
    vus = []

    def calcul(country_code, contract_value_usd, product_types):
        vus.append(product_types)
        return {"quotes": []}

    monkeypatch.setattr(insurance, "batch_calculate_quotes", calcul)
    app = FastAPI()
    app.include_router(insurance.router, prefix="/api")
    return TestClient(app), vus


def test_lot_d_assurance_borne_a_dix_types(client_assurance):
    client, vus = client_assurance

    reponse = client.post(
        "/api/insurance/quotes/batch",
        json={"country_code": "DZ", "contract_value_usd": 1000, "product_types": ["export_credit"] * 11},
    )

    assert reponse.status_code == 422
    assert vus == []


def test_lot_d_assurance_doublons_retires(client_assurance):
    client, vus = client_assurance

    reponse = client.post(
        "/api/insurance/quotes/batch",
        json={"country_code": "DZ", "contract_value_usd": 1000,
              "product_types": ["export_credit", "export_credit", "political_risk"]},
    )

    assert reponse.status_code == 200
    assert [p.value for p in vus[0]] == ["export_credit", "political_risk"]


def test_lot_d_assurance_par_defaut_comme_l_interface(client_assurance):
    client, vus = client_assurance

    reponse = client.post("/api/insurance/quotes/batch", json={"country_code": "DZ", "contract_value_usd": 1000})

    assert reponse.status_code == 200 and vus == [None]
