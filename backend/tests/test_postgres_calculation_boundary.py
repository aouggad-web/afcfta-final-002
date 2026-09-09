"""The compatibility URL must not bypass the authentic calculation boundary.

Tariff assertions use repository data; quota accounting and optional currency
enrichment are isolated without injecting any tariff or exchange rate.
"""

import currencies.service as currency_service
import entitlement_guard
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes import authentic_tariffs, postgres_tariffs


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(authentic_tariffs.router)
    app.include_router(postgres_tariffs.router)
    return app


@pytest.mark.parametrize("country,code", [("DZA", "010121"), ("DZA", "0101219999")])
def test_selection_errors_match_authentic_route(app, country, code):
    with TestClient(app) as client:
        legacy = client.post(
            "/postgres-tariffs/calculate",
            params={"country_iso3": country, "hs6": code, "value": 1000},
        )
        authentic = client.post(
            "/authentic-tariffs/calculate",
            params={"country_iso3": country, "hs_code": code, "cif_value": 1000},
        )
    assert legacy.status_code == authentic.status_code == 422
    assert legacy.json() == authentic.json()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf"])
@pytest.mark.parametrize("compatibility", [True, False])
def test_invalid_value_rejected(app, value, compatibility):
    path = "/postgres-tariffs/calculate" if compatibility else "/authentic-tariffs/calculate"
    params = {"country_iso3": "DZA"}
    params.update(
        {"hs6": "0101211100", "value": value}
        if compatibility
        else {"hs_code": "0101211100", "cif_value": value}
    )
    with TestClient(app) as client:
        response = client.post(path, params=params)
    assert response.status_code == 422


def test_country_doctrine_rejection_is_not_a_success(app):
    with TestClient(app) as client:
        response = client.post(
            "/postgres-tariffs/calculate",
            params={"country_iso3": "ZZZ", "hs6": "010121", "value": 1000},
        )
    assert response.status_code == 404


def test_real_national_calculation_matches_authentic_boundary(app, monkeypatch):
    # Exchange-rate refresh timing is unrelated to route equivalence. Mark
    # optional currency enrichment unavailable; never inject a fictional rate.
    monkeypatch.setattr(currency_service, "get_by_country", lambda country: None)
    with TestClient(app) as client:
        legacy = client.post(
            "/postgres-tariffs/calculate",
            params={"country_iso3": "GHA", "hs6": "010121", "value": 1000},
        )
        authentic = client.post(
            "/authentic-tariffs/calculate",
            params={"country_iso3": "GHA", "hs_code": "010121", "cif_value": 1000},
        )
    assert legacy.status_code == authentic.status_code == 200
    for key in ("rates", "taxes_breakdown", "overall_status", "quality_dimensions", "disclaimer"):
        assert legacy.json()[key] == authentic.json()[key]


def test_quota_exhaustion_blocks_compatibility_url(app, monkeypatch):
    calls = []

    async def subscriber():
        return {"_id": "quota-contract-test"}

    async def exhausted(user, module, access):
        calls.append(module)
        return False

    async def must_not_calculate(**kwargs):
        pytest.fail("quota rejection must happen before calculation")

    app.dependency_overrides[entitlement_guard.get_optional_subscriber] = subscriber
    monkeypatch.setattr(entitlement_guard, "check_and_increment_usage", exhausted)
    monkeypatch.setattr(postgres_tariffs, "calculate_taxes_endpoint", must_not_calculate)
    with TestClient(app) as client:
        response = client.post(
            "/postgres-tariffs/calculate",
            params={"country_iso3": "GHA", "hs6": "010121", "value": 1000},
        )
    assert response.status_code == 429
    assert calls == ["calculator"]
