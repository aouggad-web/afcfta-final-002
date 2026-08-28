import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from exchange_rates.models import ConversionResult, RateBundle


def _load_banking_module():
    banking_path = backend_path / "routes" / "banking.py"
    spec = importlib.util.spec_from_file_location("backend.routes.banking", banking_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_bundle(rates: dict[str, float], base: str = "USD", source: str = "stub") -> RateBundle:
    return RateBundle(
        base=base,
        timestamp=datetime.now(timezone.utc),
        source=source,
        rates=rates,
    )


def _make_conversion(
    from_currency: str,
    to_currency: str,
    amount: float,
    converted_amount: float,
    rate: float,
    source: str = "stub",
) -> ConversionResult:
    return ConversionResult(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        converted_amount=converted_amount,
        rate=rate,
        timestamp=datetime.now(timezone.utc),
        source=source,
    )


class StubRateService:
    def __init__(
        self,
        *,
        usd_rate: float | None = None,
        eur_rate: float | None = None,
        latest_bundle: RateBundle | None = None,
        conversion_result: ConversionResult | None = None,
        error: Exception | None = None,
    ):
        self.usd_rate = usd_rate
        self.eur_rate = eur_rate
        self.latest_bundle = latest_bundle
        self.conversion_result = conversion_result
        self.error = error

    def get_rate(self, base: str, _: str):
        if self.error:
            raise self.error
        rate_value = {"USD": self.usd_rate, "EUR": self.eur_rate}.get(base.upper())
        if rate_value is None:
            return None
        return type(
            "Rate",
            (),
            {
                "rate": rate_value,
                "source": "stub",
                "timestamp": datetime.now(timezone.utc),
            },
        )()

    def get_latest(self, _: str):
        if self.error:
            raise self.error
        return self.latest_bundle

    def convert(self, _: str, __: str, ___: float):
        if self.error:
            raise self.error
        return self.conversion_result


@pytest.fixture
def banking_module():
    return _load_banking_module()


@pytest.fixture
def client(banking_module):
    app = FastAPI()
    app.include_router(banking_module.router)
    return TestClient(app)


class TestBankingRoutes:
    def test_get_banks_by_country_success(self, client):
        response = client.get("/banking/countries/MA/banks")
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "MA"
        assert payload["central_bank"]["name"] == "Bank Al-Maghrib"

    def test_get_banks_by_country_unknown_returns_404(self, client):
        response = client.get("/banking/countries/XX/banks")
        assert response.status_code == 404

    def test_regional_banks_endpoint_supports_filter(self, client):
        response = client.get("/banking/regional-banks?region=West Africa")
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_list_banking_countries_returns_registry_entries(self, client):
        response = client.get("/banking/countries")
        assert response.status_code == 200
        countries = response.json()
        assert any(country["country_code"] == "MA" for country in countries)

    def test_get_forex_regulations_enriches_live_rates(self, client, banking_module, monkeypatch):
        stub_service = StubRateService(usd_rate=10.1, eur_rate=10.9)
        monkeypatch.setattr(banking_module, "get_rate_service", lambda: stub_service)

        response = client.get("/banking/countries/MA/regulations")
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "MA"
        assert payload["exchange_rate_info"]["currency_code"] == "MAD"
        assert payload["exchange_rate_info"]["rate_usd"] == pytest.approx(10.1)
        assert payload["exchange_rate_info"]["rate_source"] == "stub"

    def test_get_forex_regulations_unknown_country_uses_default_currency(self, client):
        response = client.get("/banking/countries/XX/regulations")
        assert response.status_code == 200
        payload = response.json()
        assert payload["exchange_rate_info"]["currency_code"] == "USD"
        assert payload["exchange_rate_info"]["rate_usd"] == 1.0
        assert payload["exchange_rate_info"]["rate_source"] == "N/A"

    def test_get_forex_regulations_handles_rate_service_errors(
        self, client, banking_module, monkeypatch
    ):
        monkeypatch.setattr(
            banking_module,
            "get_rate_service",
            lambda: StubRateService(error=RuntimeError("boom")),
        )

        response = client.get("/banking/countries/MA/regulations")
        assert response.status_code == 200
        payload = response.json()
        assert payload["exchange_rate_info"]["rate_source"] == "unavailable"
        assert payload["exchange_rate_info"]["rate_usd"] is None

    def test_get_all_domiciliation_rules_returns_country_rows(self, client):
        response = client.get("/banking/forex/domiciliation-rules")
        assert response.status_code == 200
        rows = response.json()
        assert any(row["country_code"] == "MA" for row in rows)

    def test_get_african_forex_rates_returns_filtered_rates(
        self, client, banking_module, monkeypatch
    ):
        stub_service = StubRateService(
            latest_bundle=_make_bundle({"MAD": 10.0, "NGN": 1500.0, "EUR": 0.92})
        )
        monkeypatch.setattr(banking_module, "get_rate_service", lambda: stub_service)

        response = client.get("/banking/forex/rates?base=usd")
        assert response.status_code == 200
        payload = response.json()
        codes = {row["currency_code"] for row in payload["rates"]}
        assert payload["base_currency"] == "USD"
        assert {"MAD", "NGN"}.issubset(codes)
        assert "EUR" not in codes

    def test_get_african_forex_rates_returns_503_when_service_is_unavailable(
        self, client, banking_module, monkeypatch
    ):
        monkeypatch.setattr(
            banking_module,
            "get_rate_service",
            lambda: StubRateService(latest_bundle=None),
        )

        response = client.get("/banking/forex/rates")
        assert response.status_code == 503

    def test_get_african_forex_rates_handles_unexpected_errors(
        self, client, banking_module, monkeypatch
    ):
        monkeypatch.setattr(
            banking_module,
            "get_rate_service",
            lambda: StubRateService(error=RuntimeError("provider error")),
        )

        response = client.get("/banking/forex/rates")
        assert response.status_code == 503
        assert "provider error" in response.json()["detail"]

    def test_convert_to_local_currency_returns_conversion_payload(
        self, client, banking_module, monkeypatch
    ):
        stub_service = StubRateService(
            conversion_result=_make_conversion("EUR", "MAD", 50.0, 545.0, 10.9)
        )
        monkeypatch.setattr(banking_module, "get_rate_service", lambda: stub_service)

        response = client.get("/banking/forex/convert?country_code=ma&amount=50&from_currency=eur")
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "MA"
        assert payload["to_currency"] == "MAD"
        assert payload["converted_amount"] == pytest.approx(545.0)

    def test_convert_to_local_currency_returns_503_when_rate_is_missing(
        self, client, banking_module, monkeypatch
    ):
        monkeypatch.setattr(
            banking_module,
            "get_rate_service",
            lambda: StubRateService(conversion_result=None),
        )

        response = client.get("/banking/forex/convert?country_code=MA&amount=50")
        assert response.status_code == 503

    def test_convert_to_local_currency_handles_unexpected_errors(
        self, client, banking_module, monkeypatch
    ):
        monkeypatch.setattr(
            banking_module,
            "get_rate_service",
            lambda: StubRateService(error=RuntimeError("convert error")),
        )

        response = client.get("/banking/forex/convert?country_code=MA&amount=50")
        assert response.status_code == 503
        assert "convert error" in response.json()["detail"]

    def test_trade_finance_instruments_endpoint_returns_catalogue(self, client):
        response = client.get("/banking/trade-finance/instruments")
        assert response.status_code == 200
        assert any(item["code"] == "LC_IRREVOCABLE" for item in response.json())

    def test_trade_finance_recommend_endpoint_returns_recommendations(self, client):
        response = client.get(
            "/banking/trade-finance/recommend?country_code=NG&transaction_type=export&amount_usd=100000"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "NG"
        assert len(payload["recommended_instruments"]) > 0

    def test_regional_payment_systems_endpoint_returns_regional_rows(self, client):
        response = client.get("/banking/payment-systems/regional")
        assert response.status_code == 200
        systems = response.json()
        assert len(systems) > 0
        assert all(system["type"] == "regional" for system in systems)

    def test_payment_systems_endpoint_returns_full_catalogue(self, client):
        response = client.get("/banking/payment-systems")
        assert response.status_code == 200
        systems = response.json()
        assert any(system["code"] == "SWIFT" for system in systems)

    def test_risk_assessment_endpoint_returns_alert_metadata(self, client):
        response = client.get(
            "/banking/countries/MA/risk-assessment?amount_usd=50000&transaction_type=export"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "MA"
        assert payload["alert_level"] == "orange"

    def test_compliance_endpoint_returns_country_requirements(self, client):
        response = client.get("/banking/compliance/MA")
        assert response.status_code == 200
        payload = response.json()
        assert payload["country_code"] == "MA"
        assert "aml_framework" in payload

    def test_register_endpoint_supports_filters(self, client):
        response = client.get(
            "/banking/register?country_code=MA&bank_type=central&search=Al-Maghrib"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["results"][0]["type"] == "central"

    def test_regulations_summary_endpoint_filters_levels(self, client):
        response = client.get("/banking/regulations/summary?regulation_level=strict")
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] > 0
        assert all(row["regulation_level"] == "strict" for row in payload["results"])

    def test_regulations_summary_exposes_structured_thresholds_and_deadlines(self, client):
        response = client.get("/banking/regulations/summary")
        assert response.status_code == 200
        rows = {row["country_code"]: row for row in response.json()["results"]}

        assert rows["CI"]["threshold_local_amount"] == 20_000_000
        assert rows["CI"]["threshold_currency"] == "XOF"
        assert rows["CI"]["export_payment_due_days"] == 120
        assert rows["CI"]["repatriation_after_due_months"] == 1

        assert rows["DZ"]["repatriation_days"] == 120
        assert rows["DZ"]["conditional_repatriation_days"] == 180
        assert "assurance-crédit" in rows["DZ"]["conditional_repatriation_condition"]

    def test_validate_transaction_combines_banking_checks(self, client):
        response = client.post(
            "/banking/transaction/validate",
            json={
                "origin_country": "DZ",
                "destination_country": "MA",
                "amount_usd": 50000,
                "transaction_type": "export",
                "sector": "agroalimentaire",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["transaction"]["destination_country"] == "MA"
        assert payload["domiciliation_alert"]["required"] is True
        assert payload["domiciliation_alert"]["country_code"] == "DZ"
        assert payload["domiciliation_alert"]["flow"] == "export"
        assert payload["summary"]["domiciliation_country"] == "DZ"
        assert payload["summary"]["domiciliation_flow"] == "export"
        assert payload["summary"]["top_instrument"] is not None

    def test_validate_transaction_does_not_compare_local_threshold_with_usd(self, client):
        for transaction_type, origin, destination, amount, currency in (
            ("export", "CI", "MA", 20_000_000, "XOF"),
            ("export", "CM", "MA", 5_000_000, "XAF"),
            ("import", "MA", "CI", 20_000_000, "XOF"),
            ("import", "MA", "CM", 5_000_000, "XAF"),
        ):
            response = client.post(
                "/banking/transaction/validate",
                json={
                    "origin_country": origin,
                    "destination_country": destination,
                    "amount_usd": 50_000,
                    "transaction_type": transaction_type,
                    "sector": "agroalimentaire",
                },
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["summary"]["domiciliation_required"] is None
            assert payload["domiciliation_alert"]["required"] is None
            regulatory_country = origin if transaction_type == "export" else destination
            assert payload["domiciliation_alert"]["country_code"] == regulatory_country
            assert payload["domiciliation_alert"]["flow"] == transaction_type
            assert payload["domiciliation_alert"]["threshold_local_amount"] == amount
            assert payload["domiciliation_alert"]["threshold_currency"] == currency

    def test_validate_transaction_rejects_unknown_flow(self, client):
        response = client.post(
            "/banking/transaction/validate",
            json={
                "origin_country": "DZ",
                "destination_country": "MA",
                "amount_usd": 50_000,
                "transaction_type": "transit",
            },
        )
        assert response.status_code == 422
