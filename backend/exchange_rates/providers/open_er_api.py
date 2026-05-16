"""
OpenERApi provider – free, no API key required.
Covers ~160+ currencies including most African currencies
(DZD, MAD, TND, EGP, GHS, NGN, KES, ZAR, XOF, XAF, ETB, TZS, UGX, …).

Endpoint: https://open.er-api.com/v6/latest/{base}
Documentation: https://www.exchangerate-api.com/docs/free
"""
import logging
from typing import Dict, Optional

import requests

from .base import BaseRateProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://open.er-api.com/v6/latest"
_TIMEOUT = 12  # seconds


class OpenERApiProvider(BaseRateProvider):
    """Fetch exchange rates from the Open Exchange Rates API (free tier, no key)."""

    name = "open_er_api"

    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """Return rates from open.er-api.com relative to *base*."""
        try:
            url = f"{_BASE_URL}/{base.upper()}"
            resp = requests.get(url, timeout=_TIMEOUT, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            if data.get("result") != "success":
                logger.warning("OpenERApi returned non-success result: %s", data.get("result"))
                return None
            rates = data.get("rates", {})
            if not rates:
                return None
            logger.debug("OpenERApi: fetched %d rates (base=%s)", len(rates), base.upper())
            return {k: float(v) for k, v in rates.items()}
        except requests.RequestException as exc:
            logger.warning("OpenERApi request failed: %s", exc)
            return None
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("OpenERApi parse error: %s", exc)
            return None
