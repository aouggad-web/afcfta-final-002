"""
Base exchange rate provider interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BaseRateProvider(ABC):
    """Abstract base class for exchange rate data providers."""

    name: str = "base"

    @abstractmethod
    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """Fetch exchange rates from the provider.

        Args:
            base: Base currency code (ISO 4217).

        Returns:
            Dictionary mapping target currency codes to their exchange rates,
            or ``None`` if the request fails.
        """
        ...

    def is_available(self) -> bool:
        """Return True if the provider is reachable and configured."""
        try:
            result = self.fetch_rates("USD")
            return result is not None and len(result) > 0
        except Exception:
            return False
