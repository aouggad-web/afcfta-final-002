"""
Frankfurter provider – free ECB-based rates, no API key required.
Endpoint: https://api.frankfurter.app/latest?from=USD
"""
import logging
from typing import Dict, Optional

import requests

from .base import BaseRateProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.frankfurter.app"
_TIMEOUT = 10  # seconds


class FrankfurterProvider(BaseRateProvider):
    """Fetch exchange rates from the Frankfurter API (European Central Bank)."""

    name = "frankfurter"

    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """Return rates relative to *base* from Frankfurter."""
        try:
            url = f"{_BASE_URL}/latest"
            resp = requests.get(url, params={"from": base.upper()}, timeout=_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("rates", {})
        except requests.RequestException as exc:
            logger.warning("Frankfurter request failed: %s", exc)
            return None
        except (KeyError, ValueError) as exc:
            logger.warning("Frankfurter response parse error: %s", exc)
            return None

    def fetch_historical(self, date: str, base: str = "USD") -> Optional[Dict[str, float]]:
        """Return rates for a specific date (YYYY-MM-DD format)."""
        try:
            url = f"{_BASE_URL}/{date}"
            resp = requests.get(url, params={"from": base.upper()}, timeout=_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("rates", {})
        except requests.RequestException as exc:
            logger.warning("Frankfurter historical request failed for %s: %s", date, exc)
            return None
        except (KeyError, ValueError) as exc:
            logger.warning("Frankfurter historical parse error for %s: %s", date, exc)
            return None
