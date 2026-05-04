"""
Tests for the currencies module and exchange rate service.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend is on sys.path
_backend = Path(__file__).parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# ---------------------------------------------------------------------------
# Currency service tests
# ---------------------------------------------------------------------------

from currencies.service import (
    get_by_code,
    get_by_country,
    get_by_forex_regulation,
    get_by_monetary_union,
    get_unique_currencies,
    list_currencies,
)


class TestCurrencyService:
    """Tests for the currency data service."""

    def test_list_currencies_returns_54_countries(self):
        """All 54 African Union member states should be present."""
        currencies = list_currencies()
        assert len(currencies) == 54

    def test_all_entries_have_required_fields(self):
        """Every currency entry must have all required fields."""
        for c in list_currencies():
            assert c.country_code, f"Missing country_code for {c.country_name_en}"
            assert c.currency_code, f"Missing currency_code for {c.country_name_en}"
            assert c.currency_name_en, f"Missing currency_name_en for {c.country_code}"
            assert c.central_bank, f"Missing central_bank for {c.country_code}"
            assert c.subunit_factor > 0, f"Invalid subunit_factor for {c.country_code}"

    def test_get_by_country_nigeria(self):
        """Should return NGN for Nigeria."""
        info = get_by_country("NG")
        assert info is not None
        assert info.currency_code == "NGN"
        assert info.country_name_en == "Nigeria"

    def test_get_by_country_south_africa(self):
        """Should return ZAR for South Africa."""
        info = get_by_country("ZA")
        assert info is not None
        assert info.currency_code == "ZAR"

    def test_get_by_country_case_insensitive(self):
        """Country code lookup should be case-insensitive."""
        assert get_by_country("ng") == get_by_country("NG")

    def test_get_by_country_unknown_returns_none(self):
        """Unknown country code should return None."""
        assert get_by_country("XX") is None

    def test_get_by_code_usd_not_african(self):
        """USD is not an African currency; should return None."""
        assert get_by_code("USD") is None

    def test_get_by_code_xof_returns_entry(self):
        """XOF (West African CFA) should resolve to an entry."""
        info = get_by_code("XOF")
        assert info is not None
        assert info.monetary_union == "UEMOA"

    def test_get_by_monetary_union_uemoa(self):
        """UEMOA union should have exactly 8 members."""
        uemoa = get_by_monetary_union("UEMOA")
        assert len(uemoa) == 8

    def test_get_by_monetary_union_cemac(self):
        """CEMAC union should have exactly 6 members."""
        cemac = get_by_monetary_union("CEMAC")
        assert len(cemac) == 6

    def test_get_by_monetary_union_cma(self):
        """CMA (Common Monetary Area) should have exactly 4 members."""
        cma = get_by_monetary_union("CMA")
        assert len(cma) == 4

    def test_get_by_forex_regulation_strict(self):
        """Strict regulation countries should include Algeria and Nigeria."""
        strict = get_by_forex_regulation("strict")
        codes = {c.country_code for c in strict}
        assert "DZ" in codes
        assert "NG" in codes

    def test_get_unique_currencies_less_than_countries(self):
        """Unique currencies must be fewer than total countries (CFA zones share)."""
        unique = get_unique_currencies()
        all_c = list_currencies()
        assert len(unique) < len(all_c)

    def test_cfa_franc_countries_share_code(self):
        """UEMOA countries should all have XOF currency code."""
        uemoa = get_by_monetary_union("UEMOA")
        for country in uemoa:
            assert country.currency_code == "XOF", (
                f"{country.country_code} expected XOF, got {country.currency_code}"
            )

    def test_cemac_countries_share_xaf(self):
        """CEMAC countries should all have XAF currency code."""
        cemac = get_by_monetary_union("CEMAC")
        for country in cemac:
            assert country.currency_code == "XAF", (
                f"{country.country_code} expected XAF, got {country.currency_code}"
            )


# ---------------------------------------------------------------------------
# Exchange rate service tests
# ---------------------------------------------------------------------------

from exchange_rates.service import ExchangeRateService, AFRICAN_CURRENCY_CODES
from exchange_rates.models import RateBundle, ConversionRequest


class TestExchangeRateService:
    """Tests for the ExchangeRateService."""

    def _make_bundle(self, rates: dict, base: str = "USD") -> RateBundle:
        return RateBundle(
            base=base,
            timestamp=datetime.now(timezone.utc),
            source="test",
            rates=rates,
        )

    def test_convert_usd_to_ngn(self):
        """USD → NGN conversion with mocked rates."""
        svc = ExchangeRateService()
        fake_rates = {"NGN": 1500.0, "ZAR": 18.5, "KES": 130.0}
        svc._latest = self._make_bundle(fake_rates)

        result = svc.convert("USD", "NGN", 100.0)
        assert result is not None
        assert result.from_currency == "USD"
        assert result.to_currency == "NGN"
        assert result.amount == 100.0
        assert result.converted_amount == pytest.approx(150000.0, rel=1e-4)

    def test_convert_unknown_pair_returns_none(self):
        """Converting between an unknown pair should return None."""
        svc = ExchangeRateService()
        fake_rates = {"NGN": 1500.0}
        svc._latest = self._make_bundle(fake_rates, base="USD")

        result = svc.convert("USD", "UNKNOWN", 100.0)
        assert result is None

    def test_get_african_rates_filters_correctly(self):
        """get_african_rates() should only return African currency codes."""
        svc = ExchangeRateService()
        fake_rates = {"NGN": 1500.0, "ZAR": 18.5, "EUR": 0.92, "JPY": 150.0, "GBP": 0.79}
        svc._latest = self._make_bundle(fake_rates)

        african = svc.get_african_rates("USD")
        assert "NGN" in african
        assert "ZAR" in african
        assert "EUR" not in african
        assert "JPY" not in african
        assert "GBP" not in african

    def test_alert_triggered_on_large_move(self):
        """A rate change > 5% should produce a RateAlert."""
        svc = ExchangeRateService()
        old_rates = {"NGN": 1000.0}
        new_rates = {"NGN": 1100.0}  # +10% – exceeds threshold
        svc._latest = self._make_bundle(old_rates)
        new_bundle = self._make_bundle(new_rates)

        svc._detect_alerts(new_bundle)
        alerts = svc.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].currency_pair == "USD/NGN"
        assert alerts[0].change_percent == pytest.approx(10.0, rel=1e-2)
        assert alerts[0].direction == "up"

    def test_no_alert_on_small_move(self):
        """A rate change < 5% should not produce an alert."""
        svc = ExchangeRateService()
        old_rates = {"NGN": 1000.0}
        new_rates = {"NGN": 1020.0}  # +2% – below threshold
        svc._latest = self._make_bundle(old_rates)
        new_bundle = self._make_bundle(new_rates)

        svc._detect_alerts(new_bundle)
        assert svc.get_alerts() == []

    def test_alert_direction_down(self):
        """A rate drop > 5% should produce a 'down' direction alert."""
        svc = ExchangeRateService()
        svc._latest = self._make_bundle({"ZAR": 18.0})
        new_bundle = self._make_bundle({"ZAR": 17.0})  # -5.56%

        svc._detect_alerts(new_bundle)
        alerts = svc.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].direction == "down"

    def test_clear_alerts(self):
        """clear_alerts() should empty the alerts list."""
        svc = ExchangeRateService()
        svc._latest = self._make_bundle({"NGN": 1000.0})
        svc._detect_alerts(self._make_bundle({"NGN": 1100.0}))
        assert len(svc.get_alerts()) == 1

        svc.clear_alerts()
        assert svc.get_alerts() == []

    def test_cross_rate_calculation(self):
        """Cross-rate via USD should be computed when direct rate is missing."""
        svc = ExchangeRateService()
        # USD bundle with both currencies
        svc._latest = self._make_bundle({"NGN": 1500.0, "ZAR": 18.0})

        # Ask for NGN/ZAR (not in USD bundle directly)
        rate = svc._cross_rate("NGN", "ZAR")
        assert rate is not None
        expected = 18.0 / 1500.0
        assert rate == pytest.approx(expected, rel=1e-4)

    def test_provider_fallback_on_failure(self):
        """Service should fall back to Frankfurter when primary providers fail."""
        svc = ExchangeRateService()

        # Mock providers
        mock_primary = MagicMock()
        mock_primary.fetch_rates.return_value = None  # fails
        mock_primary.name = "mock_primary"

        mock_backup = MagicMock()
        mock_backup.fetch_rates.return_value = {"NGN": 1500.0}
        mock_backup.name = "mock_backup"

        svc._providers = [mock_primary, mock_backup]
        bundle = svc.update_rates("USD")

        assert bundle is not None
        assert bundle.source == "mock_backup"
        assert "NGN" in bundle.rates

    def test_all_providers_fail_returns_none(self):
        """When all providers fail, update_rates() returns None."""
        svc = ExchangeRateService()
        for provider in svc._providers:
            provider.fetch_rates = MagicMock(return_value=None)

        bundle = svc.update_rates("USD")
        assert bundle is None

    def test_african_currency_codes_set_completeness(self):
        """AFRICAN_CURRENCY_CODES set should cover key currencies."""
        assert "NGN" in AFRICAN_CURRENCY_CODES
        assert "ZAR" in AFRICAN_CURRENCY_CODES
        assert "KES" in AFRICAN_CURRENCY_CODES
        assert "EGP" in AFRICAN_CURRENCY_CODES
        assert "XOF" in AFRICAN_CURRENCY_CODES
        assert "XAF" in AFRICAN_CURRENCY_CODES
        assert "MAD" in AFRICAN_CURRENCY_CODES
        # Non-African currencies must NOT be in the set
        assert "USD" not in AFRICAN_CURRENCY_CODES
        assert "EUR" not in AFRICAN_CURRENCY_CODES


# ---------------------------------------------------------------------------
# Frankfurter provider tests (unit – mocked HTTP)
# ---------------------------------------------------------------------------

from exchange_rates.providers.frankfurter import FrankfurterProvider


class TestFrankfurterProvider:
    """Unit tests for the Frankfurter provider with mocked HTTP."""

    def test_fetch_rates_success(self):
        """Successful response should return a rates dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "date": "2024-01-15",
            "rates": {"EUR": 0.92, "GBP": 0.79, "ZAR": 18.5},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("exchange_rates.providers.frankfurter.requests.get", return_value=mock_response):
            provider = FrankfurterProvider()
            rates = provider.fetch_rates("USD")

        assert rates == {"EUR": 0.92, "GBP": 0.79, "ZAR": 18.5}

    def test_fetch_rates_network_error_returns_none(self):
        """Network errors should return None (not raise)."""
        import requests as _requests

        with patch(
            "exchange_rates.providers.frankfurter.requests.get",
            side_effect=_requests.RequestException("timeout"),
        ):
            provider = FrankfurterProvider()
            result = provider.fetch_rates("USD")

        assert result is None

    def test_fetch_historical_success(self):
        """Historical fetch should pass the date in the URL."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"ZAR": 17.5}}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "exchange_rates.providers.frankfurter.requests.get", return_value=mock_response
        ) as mock_get:
            provider = FrankfurterProvider()
            rates = provider.fetch_historical("2024-01-15", "USD")

        assert rates == {"ZAR": 17.5}
        call_url = mock_get.call_args[0][0]
        assert "2024-01-15" in call_url
