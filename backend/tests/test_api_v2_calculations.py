"""HTTP regressions: client-provided tariffs must not become verified calculations."""

import pytest
from api.v2.endpoints import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("data_status", ["SYNTHETIC", "PARTIAL", "VERIFIED"])
@pytest.mark.parametrize("regime", ["NPF", "ZLECAF"])
def test_client_supplied_provenance_cannot_authorize_calculation(
    client, data_status, regime
):
    # Contract sentinel only: no customs dataset or invented official rate.
    response = client.post(
        "/api/v2/calculations",
        json={
            "line": {
                "commodity": {
                    "country_iso3": "ZZZ",
                    "national_code": "00000000",
                    "hs6": "000000",
                    "digits": 8,
                    "chapter": "00",
                    "description_fr": "Contract test sentinel",
                },
                "measures": [],
                "provenance": {"data_status": data_status},
            },
            "cif_value": 100,
            "regime": regime,
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["data_status"] == "NOT_AVAILABLE"
    assert response.json()["detail"]["code"] == "VERIFIED_TARIFF_PROVIDER_REQUIRED"
    assert "result" not in response.json()


def test_bulk_endpoint_cannot_return_chapter_estimates(client):
    response = client.post(
        "/api/v2/bulk/tariff-calculations",
        json={
            "products": [
                {"hs_code": "870000", "description": "Contract test sentinel"}
            ],
            "routes": [{"origin": "ZZZ", "destination": "ZZZ"}],
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["data_status"] == "NOT_AVAILABLE"
    assert "results" not in response.json()


@pytest.mark.parametrize("hs_code", ["010000", "870000", "999999"])
def test_mobile_lookup_preserves_unknown_tariff_values(client, hs_code):
    response = client.get("/api/v2/mobile/quick-lookup", params={"hs_code": hs_code})
    assert response.status_code == 200
    summary = response.json()["tariff_summary"]
    assert summary["mfn_rate_pct"] is None
    assert summary["afcfta_rate_pct"] is None
    assert summary["data_status"] == "NOT_AVAILABLE"


def test_mobile_empty_query_still_rejected(client):
    assert client.get("/api/v2/mobile/quick-lookup").status_code == 400
