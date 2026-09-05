import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


def _load_insurance_module():
    insurance_path = backend_path / "routes" / "insurance.py"
    spec = importlib.util.spec_from_file_location("backend.routes.insurance", insurance_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def insurance_module():
    return _load_insurance_module()


@pytest.fixture
def client(insurance_module):
    app = FastAPI()
    app.include_router(insurance_module.router)
    return TestClient(app)


class TestInsuranceRoutes:
    def test_list_countries_returns_code_and_full_name(self, client):
        response = client.get("/insurance/countries")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["total"] > 0
        assert len(payload["countries"]) == payload["total"]
        dz = next((c for c in payload["countries"] if c["country_code"] == "DZ"), None)
        assert dz is not None
        assert dz["country_name"] == "Algérie"
        # sorted alphabetically by full name
        names = [c["country_name"] for c in payload["countries"]]
        assert names == sorted(names)

    def test_list_insurers_returns_full_directory(self, client):
        response = client.get("/insurance/insurers")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["total"] > 0
        assert len(payload["insurers"]) == payload["total"]

    def test_list_insurers_filters_by_country(self, client):
        response = client.get("/insurance/insurers?country_code=dz")
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] > 0
        for insurer in payload["insurers"]:
            assert "DZ" in insurer["active_countries"]

    def test_get_country_profile_success(self, client):
        response = client.get("/insurance/countries/DZ/profile")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["profile"]["country_code"] == "DZ"
        assert len(payload["profile"]["available_products"]) > 0

    def test_get_country_profile_unknown_country_returns_404(self, client):
        response = client.get("/insurance/countries/XX/profile")
        assert response.status_code == 404

    def test_premium_adjustments_success(self, client):
        response = client.get("/insurance/countries/DZ/premium-adjustments")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["country_code"] == "DZ"
        assert "total_premium_adjustment_percent" in payload

    def test_premium_adjustments_unknown_country_returns_404(self, client):
        response = client.get("/insurance/countries/XX/premium-adjustments")
        assert response.status_code == 404

    def test_get_quote_success(self, client):
        response = client.post(
            "/insurance/quote",
            json={
                "country_code": "DZ",
                "product_type": "export_credit",
                "contract_value_usd": 500000,
                "sector": "manufacturing",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["quote"]["final_premium_usd"] > 0

    def test_get_quote_invalid_product_type_returns_400(self, client):
        response = client.post(
            "/insurance/quote",
            json={
                "country_code": "DZ",
                "product_type": "bogus_type",
                "contract_value_usd": 500000,
            },
        )
        assert response.status_code == 400

    def test_get_quote_unknown_country_returns_404(self, client):
        response = client.post(
            "/insurance/quote",
            json={
                "country_code": "XX",
                "product_type": "export_credit",
                "contract_value_usd": 500000,
            },
        )
        assert response.status_code == 404

    def test_get_quote_zero_amount_rejected_by_validation(self, client):
        response = client.post(
            "/insurance/quote",
            json={
                "country_code": "DZ",
                "product_type": "export_credit",
                "contract_value_usd": 0,
            },
        )
        assert response.status_code == 422

    def test_batch_quotes_success(self, client):
        response = client.post(
            "/insurance/quotes/batch",
            json={"country_code": "DZ", "contract_value_usd": 500000},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert "export_credit" in payload["quotes"]

    def test_batch_quotes_invalid_product_types_returns_400(self, client):
        response = client.post(
            "/insurance/quotes/batch",
            json={
                "country_code": "DZ",
                "contract_value_usd": 500000,
                "product_types": ["bogus_type"],
            },
        )
        assert response.status_code == 400
