"""Route contracts for the regulatory QA API (LOT 6, issue #361)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.regulatory_qa import router
from services.regulatory_master_registry_service import get_regulatory_registry

# Anchored to the master registry's own as_of rather than the wall clock so
# this test stays deterministic regardless of when CI happens to run.
_REGISTRY_AS_OF = get_regulatory_registry()["as_of"]


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_coverage_report_endpoint_covers_all_54_countries():
    response = _client().get("/regulatory-qa/coverage-report")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    report = payload["report"]
    assert report["total_tracked_countries"] == 54
    assert report["published_country_count"] == len(report["countries"])


def test_contradictions_endpoint_is_currently_empty():
    response = _client().get("/regulatory-qa/contradictions")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["total"] == 0
    assert payload["contradictions"] == []


def test_stale_countries_endpoint_is_currently_empty():
    response = _client().get(
        "/regulatory-qa/stale-countries", params={"reference_date": _REGISTRY_AS_OF}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["total"] == 0
    assert payload["stale_countries"] == []


def test_stale_countries_endpoint_accepts_no_reference_date():
    """Default behavior (no query param) still works — production monitoring
    uses the wall clock; only the regression test above is anchored."""

    response = _client().get("/regulatory-qa/stale-countries")
    assert response.status_code == 200
    assert response.json()["success"] is True
