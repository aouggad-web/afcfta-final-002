"""
Exchange rate service.

Manages rate retrieval through a provider chain (CurrencyFreaks →
Fixer.io → Frankfurter), in-memory caching, cross-rate calculations,
historical snapshots (rolling 30-day in-memory buffer), and rate-change
alert generation.
"""
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import ConversionResult, ExchangeRate, RateAlert, RateBundle
from .providers import CurrencyFreaksProvider, FixerProvider, FrankfurterProvider

logger = logging.getLogger(__name__)

# African currency codes (ISO 4217)
AFRICAN_CURRENCY_CODES = {
    "AOA", "BWP", "BIF", "CVE", "XAF", "KMF", "CDF", "DJF",
    "DZD", "EGP", "ERN", "ETB", "GMD", "GHS", "GNF", "KES",
    "LSL", "LRD", "LYD", "MAD", "MGA", "MWK", "MRU", "MUR",
    "MZN", "NAD", "NGN", "RWF", "STN", "SCR", "SLE", "SOS",
    "SSP", "SDG", "SZL", "TZS", "TND", "UGX", "XOF", "ZAR",
    "ZMW", "ZWL",
}

# Rate change alert threshold (percent)
_ALERT_THRESHOLD_PERCENT = 5.0

# History rolling buffer: keep up to 30 snapshots (one per day)
_MAX_HISTORY = 30


class ExchangeRateService:
    """Multi-provider exchange rate service with caching and alerting."""

    def __init__(self) -> None:
        self._providers = [
            CurrencyFreaksProvider(),
            FixerProvider(),
            FrankfurterProvider(),
        ]
        # Latest rates bundle (base=USD)
        self._latest: Optional[RateBundle] = None
        # Rolling history: deque of RateBundle objects
        self._history: deque = deque(maxlen=_MAX_HISTORY)
        # Pending rate alerts
        self._alerts: List[RateAlert] = []

    # ------------------------------------------------------------------
    # Rate fetching
    # ------------------------------------------------------------------

    def update_rates(self, base: str = "USD") -> Optional[RateBundle]:
        """Fetch fresh rates using the provider chain and cache them.

        Returns the new ``RateBundle`` or ``None`` if all providers fail.
        """
        base = base.upper()
        for provider in self._providers:
            rates = provider.fetch_rates(base)
            if rates:
                now = datetime.now(timezone.utc)
                bundle = RateBundle(
                    base=base, timestamp=now, source=provider.name, rates=rates
                )
                self._detect_alerts(bundle)
                self._latest = bundle
                self._history.append(bundle)
                logger.info(
                    "Rates updated via %s at %s (%d pairs)",
                    provider.name,
                    now.isoformat(),
                    len(rates),
                )
                return bundle
        logger.error("All exchange rate providers failed; rates not updated")
        return None

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def get_latest(self, base: str = "USD") -> Optional[RateBundle]:
        """Return the cached rates, refreshing if no data is available."""
        if self._latest is None or self._latest.base != base.upper():
            return self.update_rates(base)
        return self._latest

    def get_rate(self, base: str, target: str) -> Optional[ExchangeRate]:
        """Return the exchange rate for a specific pair."""
        bundle = self.get_latest(base)
        if bundle is None:
            return None
        rate_value = bundle.rates.get(target.upper())
        if rate_value is None:
            # Try cross-rate via USD
            rate_value = self._cross_rate(base, target)
            if rate_value is None:
                return None
        return ExchangeRate(
            base_currency=base.upper(),
            target_currency=target.upper(),
            rate=rate_value,
            timestamp=bundle.timestamp,
            source=bundle.source,
        )

    def convert(self, from_currency: str, to_currency: str, amount: float) -> Optional[ConversionResult]:
        """Convert an amount from one currency to another."""
        rate_obj = self.get_rate(from_currency, to_currency)
        if rate_obj is None:
            return None
        converted = amount * rate_obj.rate
        return ConversionResult(
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            amount=amount,
            converted_amount=round(converted, 6),
            rate=rate_obj.rate,
            timestamp=rate_obj.timestamp,
            source=rate_obj.source,
        )

    def get_african_rates(self, base: str = "USD") -> Dict[str, float]:
        """Return only the African currency rates from the latest bundle."""
        bundle = self.get_latest(base)
        if bundle is None:
            return {}
        return {
            code: rate
            for code, rate in bundle.rates.items()
            if code in AFRICAN_CURRENCY_CODES
        }

    def get_historical(self, date_str: str, base: str = "USD") -> Optional[RateBundle]:
        """Return historical rates for a date (YYYY-MM-DD) from in-memory buffer.

        If the exact date is not in the buffer the Frankfurter provider is
        used as a fallback (it provides free historical data from the ECB).
        """
        for bundle in self._history:
            if bundle.timestamp.strftime("%Y-%m-%d") == date_str and bundle.base == base.upper():
                return bundle
        # Fallback: fetch from Frankfurter
        ff = FrankfurterProvider()
        rates = ff.fetch_historical(date_str, base)
        if rates:
            ts = datetime.fromisoformat(f"{date_str}T00:00:00+00:00")
            return RateBundle(base=base.upper(), timestamp=ts, source="frankfurter", rates=rates)
        return None

    def get_alerts(self) -> List[RateAlert]:
        """Return all pending rate alerts."""
        return list(self._alerts)

    def clear_alerts(self) -> None:
        """Clear all pending rate alerts."""
        self._alerts.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cross_rate(self, base: str, target: str) -> Optional[float]:
        """Compute a cross rate via USD when a direct rate is not available."""
        usd_bundle = self.get_latest("USD")
        if usd_bundle is None:
            return None
        base_to_usd = usd_bundle.rates.get(base.upper())
        target_to_usd = usd_bundle.rates.get(target.upper())
        if base_to_usd and target_to_usd and base_to_usd != 0:
            return target_to_usd / base_to_usd
        return None

    def _detect_alerts(self, new_bundle: RateBundle) -> None:
        """Compare new rates against the previous snapshot and emit alerts."""
        if self._latest is None or self._latest.base != new_bundle.base:
            return
        for code, new_rate in new_bundle.rates.items():
            old_rate = self._latest.rates.get(code)
            if old_rate is None or old_rate == 0:
                continue
            change_pct = ((new_rate - old_rate) / old_rate) * 100
            if abs(change_pct) >= _ALERT_THRESHOLD_PERCENT:
                alert = RateAlert(
                    currency_pair=f"{new_bundle.base}/{code}",
                    previous_rate=old_rate,
                    current_rate=new_rate,
                    change_percent=round(change_pct, 4),
                    direction="up" if change_pct > 0 else "down",
                    timestamp=new_bundle.timestamp,
                )
                self._alerts.append(alert)
                logger.warning(
                    "Rate alert: %s changed %.2f%% (%s → %s)",
                    alert.currency_pair,
                    change_pct,
                    old_rate,
                    new_rate,
                )


# Module-level singleton
_service: Optional[ExchangeRateService] = None


def get_service() -> ExchangeRateService:
    """Return the module-level ExchangeRateService singleton."""
    global _service
    if _service is None:
        _service = ExchangeRateService()
    return _service
