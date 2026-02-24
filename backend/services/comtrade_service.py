"""
UN COMTRADE API Service

Provides a reusable service for accessing the UN COMTRADE trade data API.
Handles API key rotation and rate limiting.
"""

import os
import time
import requests
from datetime import datetime, date


class ComtradeService:
    """Service for fetching data from the UN COMTRADE API."""

    BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
    CALLS_PER_DAY_LIMIT = 500

    def __init__(self):
        self.primary_key = os.environ.get("COMTRADE_API_KEY", "")
        self.secondary_key = os.environ.get("COMTRADE_API_KEY_SECONDARY", "")
        self.current_key = "primary"
        self.calls_today = 0
        self._last_reset_date = date.today()

    def _reset_daily_counter_if_needed(self):
        today = date.today()
        if today != self._last_reset_date:
            self.calls_today = 0
            self._last_reset_date = today

    def _get_api_key(self):
        self._reset_daily_counter_if_needed()
        if self.current_key == "primary" and self.primary_key:
            return self.primary_key
        if self.secondary_key:
            self.current_key = "secondary"
            return self.secondary_key
        return None

    def rotate_to_secondary(self):
        """Switch to the secondary API key if available."""
        if self.secondary_key and self.current_key != "secondary":
            self.current_key = "secondary"
            return True
        return False

    def fetch(self, reporter_code, partner_code="0", period=None, max_retries=3):
        """
        Fetch trade data from COMTRADE.

        Args:
            reporter_code: Numeric M49 country code (e.g. 504 for Morocco)
            partner_code: Partner country code, "0" for world total
            period: Year as string (e.g. "2023"), defaults to previous year
            max_retries: Number of retry attempts on transient errors

        Returns:
            List of trade data records, or None on failure
        """
        if period is None:
            period = str(datetime.now().year - 1)

        api_key = self._get_api_key()
        if not api_key:
            return None

        params = {
            "reporterCode": reporter_code,
            "partnerCode": partner_code,
            "period": period,
            "subscription-key": api_key,
        }

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                self.calls_today += 1

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data") or []

                if response.status_code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    if attempt == max_retries - 1:
                        self.rotate_to_secondary()
                        api_key = self._get_api_key()
                        if api_key:
                            params["subscription-key"] = api_key
                    continue

                if response.status_code in (401, 403):
                    if not self.rotate_to_secondary():
                        return None
                    api_key = self._get_api_key()
                    if api_key:
                        params["subscription-key"] = api_key
                    continue

                # Non-retryable error
                return None

            except requests.exceptions.RequestException:
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    return None

        return None

    def get_service_status(self):
        """Return the current service status as a dictionary."""
        self._reset_daily_counter_if_needed()
        calls_remaining = max(0, self.CALLS_PER_DAY_LIMIT - self.calls_today)
        return {
            "current_key": self.current_key,
            "primary_key_configured": bool(self.primary_key),
            "secondary_key_configured": bool(self.secondary_key),
            "calls_today": self.calls_today,
            "calls_remaining": calls_remaining,
        }


# Module-level singleton
comtrade_service = ComtradeService()
