"""Route contracts for the 54-country regulatory-compliance master registry API
(LOT 5, issue #360) — exposes services.regulatory_master_registry_service over
HTTP without adding any new data or numeric rate."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.regulatory_master_registry import router


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_countries_endpoint_lists_all_54_and_the_published_subset():
    response = _client().get("/regulatory-master-registry/countries")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["total"] == 54
    assert len(payload["countries"]) == 54
    assert payload["published_total"] == len(payload["published_countries"])
    assert set(payload["published_countries"]) <= set(payload["countries"])
    for iso3 in ("CIV", "COD", "CMR", "GHA", "KEN", "NGA"):
        assert iso3 in payload["published_countries"]


def test_registry_endpoint_returns_all_54_entries_with_canonical_statuses():
    response = _client().get("/regulatory-master-registry/registry")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    registry = payload["registry"]
    assert registry["country_count"] == 54
    assert len(registry["countries"]) == 54
    civ = registry["countries"]["CIV"]
    assert civ["regulatory_coverage_status"] == "PARTIAL"
    assert civ["dataset_path"]


def test_registry_endpoint_never_exposes_numeric_rates_or_fees():
    payload = _client().get("/regulatory-master-registry/registry").json()
    forbidden = {"rate", "fee", "fees", "authorized_fees"}

    def inspect(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in forbidden
                assert not key.endswith(("_rate", "_amount"))
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    inspect(payload)


def test_country_endpoint_returns_a_single_entry():
    response = _client().get("/regulatory-master-registry/country/civ")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["country_iso3"] == "CIV"
    assert payload["entry"]["regulatory_coverage_status"] == "PARTIAL"


def test_country_endpoint_reports_not_available_for_unpublished_country():
    response = _client().get("/regulatory-master-registry/country/dza")
    assert response.status_code == 200
    payload = response.json()
    assert payload["entry"]["regulatory_coverage_status"] == "NOT_AVAILABLE"
    assert payload["entry"]["dataset_path"] is None


def test_country_endpoint_rejects_unknown_iso3():
    response = _client().get("/regulatory-master-registry/country/xxx")
    assert response.status_code == 404
