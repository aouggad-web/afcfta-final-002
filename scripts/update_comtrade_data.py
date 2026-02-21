#!/usr/bin/env python3
"""
UN COMTRADE Data Update Script

Fetches trade data for all 54 African countries from the UN COMTRADE API.
Uses numeric M49 codes (not ISO3 alpha codes) as required by the API.
Implements retry logic and graceful degradation on failures.
"""

import json
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# UN M49 numeric codes for all 54 AfCFTA member countries
# These numeric codes are required by the COMTRADE API (alpha-3 codes are NOT accepted)
AFRICAN_COUNTRY_CODES = {
    "DZA": 12,   # Algeria
    "AGO": 24,   # Angola
    "BEN": 204,  # Benin
    "BWA": 72,   # Botswana
    "BFA": 854,  # Burkina Faso
    "BDI": 108,  # Burundi
    "CMR": 120,  # Cameroon
    "CPV": 132,  # Cabo Verde
    "CAF": 140,  # Central African Republic
    "TCD": 148,  # Chad
    "COM": 174,  # Comoros
    "COG": 178,  # Congo
    "COD": 180,  # Democratic Republic of the Congo
    "CIV": 384,  # Côte d'Ivoire
    "DJI": 262,  # Djibouti
    "EGY": 818,  # Egypt
    "GNQ": 226,  # Equatorial Guinea
    "ERI": 232,  # Eritrea
    "ETH": 231,  # Ethiopia
    "GAB": 266,  # Gabon
    "GMB": 270,  # Gambia
    "GHA": 288,  # Ghana
    "GIN": 324,  # Guinea
    "GNB": 624,  # Guinea-Bissau
    "KEN": 404,  # Kenya
    "LSO": 426,  # Lesotho
    "LBR": 430,  # Liberia
    "LBY": 434,  # Libya
    "MDG": 450,  # Madagascar
    "MWI": 454,  # Malawi
    "MLI": 466,  # Mali
    "MRT": 478,  # Mauritania
    "MUS": 480,  # Mauritius
    "MAR": 504,  # Morocco
    "MOZ": 508,  # Mozambique
    "NAM": 516,  # Namibia
    "NER": 562,  # Niger
    "NGA": 566,  # Nigeria
    "RWA": 646,  # Rwanda
    "STP": 678,  # São Tomé and Príncipe
    "SEN": 686,  # Senegal
    "SYC": 690,  # Seychelles
    "SLE": 694,  # Sierra Leone
    "SOM": 706,  # Somalia
    "ZAF": 710,  # South Africa
    "SSD": 728,  # South Sudan
    "SDN": 729,  # Sudan
    "SWZ": 748,  # Eswatini
    "TZA": 834,  # Tanzania
    "TGO": 768,  # Togo
    "TUN": 788,  # Tunisia
    "UGA": 800,  # Uganda
    "ZMB": 894,  # Zambia
    "ZWE": 716,  # Zimbabwe
}

COMTRADE_BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
WTO_BASE_URL = "https://api.wto.org/timeseries/v1/data"

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 1.5  # seconds between requests


class ComtradeUpdater:
    def __init__(self):
        self.primary_key = os.environ.get("COMTRADE_API_KEY", "")
        self.secondary_key = os.environ.get("COMTRADE_API_KEY_SECONDARY", "")
        self.wto_key = os.environ.get("WTO_API_KEY", "")
        self.active_key = "primary"
        self.calls_made = 0
        self.calls_limit = 500
        self.results = {}
        self.errors = []
        self.start_time = datetime.now()

        print(f"Starting COMTRADE data update: {self.start_time.isoformat()}")
        print()
        self._print_status()

    def _print_status(self):
        print("=== COMTRADE Service Status ===")
        print(f"Primary key configured: {bool(self.primary_key)}")
        print(f"Secondary key configured: {bool(self.secondary_key)}")
        print(f"Current active key: {self.active_key}")
        remaining = max(0, self.calls_limit - self.calls_made)
        print(f"Calls remaining today: {remaining}/{self.calls_limit}")
        print("===================================")

    def _get_active_api_key(self):
        if self.active_key == "primary" and self.primary_key:
            return self.primary_key
        if self.secondary_key:
            self.active_key = "secondary"
            return self.secondary_key
        return None

    def _switch_to_secondary_key(self):
        if self.secondary_key and self.active_key != "secondary":
            print("⚠️ Switching to secondary API key")
            self.active_key = "secondary"
            return True
        return False

    def fetch_comtrade_data(self, iso3_code, reporter_code):
        """Fetch trade data from COMTRADE API with retry logic."""
        api_key = self._get_active_api_key()
        if not api_key:
            return None

        current_year = datetime.now().year
        # Try most recent years first; COMTRADE data is typically 1-2 years behind
        years_to_try = [current_year - 1, current_year - 2, current_year - 3]

        for year in years_to_try:
            for attempt in range(1, MAX_RETRIES + 1):
                params = {
                    "reporterCode": reporter_code,
                    "partnerCode": "0",  # World total
                    "period": str(year),
                    "subscription-key": api_key,
                }
                try:
                    response = requests.get(
                        COMTRADE_BASE_URL,
                        params=params,
                        timeout=30,
                    )
                    self.calls_made += 1

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("data"):
                            return {"year": year, "data": data["data"]}
                        # No data for this year, try next year
                        break

                    elif response.status_code == 429:
                        print(f"⚠️ Rate limit hit on {self.active_key} key (attempt {attempt}/{MAX_RETRIES})")
                        if attempt < MAX_RETRIES:
                            time.sleep(RETRY_DELAY * attempt)
                            if attempt == MAX_RETRIES - 1:
                                self._switch_to_secondary_key()
                                api_key = self._get_active_api_key()
                                if not api_key:
                                    return None
                        continue

                    elif response.status_code == 400:
                        error_detail = response.json() if response.content else {}
                        print(f"❌ Bad request for {iso3_code}: {response.status_code}")
                        print(f"   URL: {COMTRADE_BASE_URL}")
                        print(f"   Params: {{'reporterCode': {reporter_code}, 'partnerCode': '0', 'period': '{year}'}}")
                        print(f"   Error details: {error_detail}")
                        # 400 means bad parameters - no point retrying with same params
                        return None

                    elif response.status_code == 401:
                        print(f"⚠️ Unauthorized (401) for COMTRADE API. Check API credentials.")
                        if not self._switch_to_secondary_key():
                            return None
                        api_key = self._get_active_api_key()

                    else:
                        print(f"⚠️ HTTP {response.status_code} for {iso3_code} year {year} (attempt {attempt}/{MAX_RETRIES})")
                        if attempt < MAX_RETRIES:
                            time.sleep(RETRY_DELAY)

                except requests.exceptions.Timeout:
                    print(f"⚠️ Timeout for {iso3_code} year {year} (attempt {attempt}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Request error for {iso3_code}: {e} (attempt {attempt}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)

            time.sleep(RATE_LIMIT_DELAY)

        return None

    def fetch_wto_data(self, iso3_code):
        """Fetch trade data from WTO API as a fallback."""
        if not self.wto_key:
            return None

        params = {
            "i": "ITS_MTV_AX",
            "r": iso3_code,
            "p": "000",
            "ps": "2022,2023",
            "fmt": "json",
            "subscription-key": self.wto_key,
        }
        try:
            response = requests.get(WTO_BASE_URL, params=params, timeout=20)
            if response.status_code == 401:
                print(f"⚠️ Unauthorized (401) for URL: {WTO_BASE_URL}. Check API credentials. Skipping...")
                return None
            if response.status_code == 200:
                data = response.json()
                if data.get("Dataset"):
                    return data["Dataset"]
        except requests.exceptions.RequestException:
            pass
        return None

    def update_all_countries(self):
        """Fetch COMTRADE data for all 54 African countries."""
        mongodb_uri = os.environ.get("MONGODB_URI", "")
        if not mongodb_uri:
            print("ℹ No MongoDB URI configured - running without database storage")
        print()
        print(f"Fetching COMTRADE data for {len(AFRICAN_COUNTRY_CODES)} countries...")
        print()

        success_count = 0
        fail_count = 0

        for idx, (iso3, m49_code) in enumerate(AFRICAN_COUNTRY_CODES.items(), 1):
            print(f"[{idx}/{len(AFRICAN_COUNTRY_CODES)}] Processing {iso3}...")
            data = self.fetch_comtrade_data(iso3, m49_code)

            if data:
                self.results[iso3] = data
                print(f"✓ Successfully retrieved data for {iso3} (year {data['year']})")
                success_count += 1
            else:
                # Try WTO as fallback
                wto_data = self.fetch_wto_data(iso3)
                if wto_data:
                    self.results[iso3] = {"source": "wto", "data": wto_data}
                    print(f"✓ Retrieved WTO fallback data for {iso3}")
                    success_count += 1
                else:
                    print(f"✗ Error retrieving data for {iso3} - skipping")
                    self.errors.append(iso3)
                    fail_count += 1
            print()

        print(f"=== Results: {success_count} succeeded, {fail_count} failed ===")
        return success_count, fail_count

    def save_results(self):
        """Save fetched results to a JSON file."""
        if not self.results:
            print("ℹ No data to save")
            return False

        output_path = Path(__file__).parent.parent / "comtrade_data_latest.json"
        output = {
            "metadata": {
                "source": "UN COMTRADE API",
                "updated_at": datetime.now().isoformat(),
                "countries_updated": len(self.results),
                "countries_failed": len(self.errors),
                "failed_countries": self.errors,
            },
            "data": self.results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved COMTRADE data to {output_path}")
        return True

    def get_service_status(self):
        """Return current service status."""
        return {
            "current_key": self.active_key,
            "calls_today": self.calls_made,
            "calls_remaining": max(0, self.calls_limit - self.calls_made),
        }


def main():
    updater = ComtradeUpdater()

    if not updater.primary_key and not updater.secondary_key:
        print("⚠️ No COMTRADE API keys configured. Set COMTRADE_API_KEY environment variable.")
        print("ℹ Skipping COMTRADE data update.")
        sys.exit(0)

    success_count, fail_count = updater.update_all_countries()
    updater.save_results()

    total = success_count + fail_count
    print()
    print(f"COMTRADE update complete: {success_count}/{total} countries retrieved")

    # Exit with success even if some countries failed (graceful degradation)
    # Only fail if we couldn't retrieve ANY data at all
    if total > 0 and success_count == 0:
        print("❌ Failed to retrieve data for any country")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
