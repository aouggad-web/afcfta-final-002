"""
Fixer.io provider – enterprise reliability backup.
Requires FIXER_API_KEY environment variable.
Note: The free Fixer plan uses EUR as base only.
"""
import logging
import os
from typing import Dict, Optional

import requests

from .base import BaseRateProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://data.fixer.io/api"
_TIMEOUT = 10


class FixerProvider(BaseRateProvider):
    """Fetch exchange rates from Fixer.io (secondary provider)."""

    name = "fixer"

    def __init__(self) -> None:
        self._api_key = os.environ.get("FIXER_API_KEY", "")

    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        if not self._api_key:
            logger.debug("FIXER_API_KEY not set; skipping provider")
            return None
        try:
            resp = requests.get(
                f"{_BASE_URL}/latest",
                params={"access_key": self._api_key, "base": base.upper()},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success", False):
                logger.warning("Fixer API error: %s", data.get("error"))
                return None
            return {k: float(v) for k, v in data.get("rates", {}).items()}
        except requests.RequestException as exc:
            logger.warning("Fixer request failed: %s", exc)
            return None
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Fixer parse error: %s", exc)
            return None
