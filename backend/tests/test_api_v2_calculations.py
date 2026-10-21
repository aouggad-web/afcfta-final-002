"""HTTP regressions: the mobile lookup never invents a tariff value."""

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
