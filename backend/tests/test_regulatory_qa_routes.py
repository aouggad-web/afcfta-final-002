"""Route contracts for the regulatory QA API (LOT 6, issue #361)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.regulatory_qa import router


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
    response = _client().get("/regulatory-qa/stale-countries")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["total"] == 0
    assert payload["stale_countries"] == []
