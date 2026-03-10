"""
CurrencyFreaks provider – broad African currency coverage.
Requires CURRENCYFREAKS_API_KEY environment variable.
"""
import logging
import os
from typing import Dict, Optional

import requests

from .base import BaseRateProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.currencyfreaks.com/v2.0"
_TIMEOUT = 10


class CurrencyFreaksProvider(BaseRateProvider):
    """Fetch exchange rates from CurrencyFreaks (primary provider)."""

    name = "currencyfreaks"

    def __init__(self) -> None:
        self._api_key = os.environ.get("CURRENCYFREAKS_API_KEY", "")

    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        if not self._api_key:
            logger.debug("CURRENCYFREAKS_API_KEY not set; skipping provider")
            return None
        try:
            url = f"{_BASE_URL}/rates/latest"
            resp = requests.get(
                url,
                params={"apikey": self._api_key, "base": base.upper()},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("rates", {})
            return {k: float(v) for k, v in raw.items()}
        except requests.RequestException as exc:
            logger.warning("CurrencyFreaks request failed: %s", exc)
            return None
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("CurrencyFreaks parse error: %s", exc)
            return None
