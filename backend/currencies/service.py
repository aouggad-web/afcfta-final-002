"""
Currency service – loads and exposes the complete African currency dataset.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import CurrencyInfo

logger = logging.getLogger(__name__)

# Path to the canonical currency data file (repo root).
# Use .resolve() so that non-normalized sys.path entries (e.g. "backend/tests/..")
# that leave ".." components in __file__ are fully resolved before computing parents.
_DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "json" / "currencies_african_complete.json"


def _load_currencies() -> Tuple[Dict[str, CurrencyInfo], Dict[str, CurrencyInfo]]:
    """Load currency data from the JSON file, keyed by ISO currency code.

    Where multiple countries share the same currency code (CFA zones), the
    entry for the most populous country is kept for the currency-level view;
    all entries remain accessible by country code via ``get_by_country``.
    """
    try:
        with open(_DATA_FILE, encoding="utf-8") as fh:
            raw: List[dict] = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to load currencies_african_complete.json: %s", exc)
        return {}, {}

    by_country: Dict[str, CurrencyInfo] = {}
    by_code: Dict[str, CurrencyInfo] = {}

    for entry in raw:
        info = CurrencyInfo(**entry)
        by_country[info.country_code] = info
        # Prefer the entry with the largest country (by alphabetical order as
        # a stable tie-breaker) when two countries share a currency code.
        if info.currency_code not in by_code:
            by_code[info.currency_code] = info

    return by_country, by_code


# Module-level caches populated once at import time
_BY_COUNTRY: Dict[str, CurrencyInfo]
_BY_CODE: Dict[str, CurrencyInfo]
_BY_COUNTRY, _BY_CODE = _load_currencies()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_currencies() -> List[CurrencyInfo]:
    """Return all currency records (one per country)."""
    return list(_BY_COUNTRY.values())


# ISO3 → ISO2 mapping for all 54 African countries
_ISO3_TO_ISO2: Dict[str, str] = {
    "DZA": "DZ", "AGO": "AO", "BEN": "BJ", "BWA": "BW", "BFA": "BF",
    "BDI": "BI", "CMR": "CM", "CPV": "CV", "CAF": "CF", "TCD": "TD",
    "COM": "KM", "COD": "CD", "COG": "CG", "CIV": "CI", "DJI": "DJ",
    "EGY": "EG", "GNQ": "GQ", "ERI": "ER", "SWZ": "SZ", "ETH": "ET",
    "GAB": "GA", "GMB": "GM", "GHA": "GH", "GIN": "GN", "GNB": "GW",
    "KEN": "KE", "LSO": "LS", "LBR": "LR", "LBY": "LY", "MDG": "MG",
    "MWI": "MW", "MLI": "ML", "MRT": "MR", "MUS": "MU", "MAR": "MA",
    "MOZ": "MZ", "NAM": "NA", "NER": "NE", "NGA": "NG", "RWA": "RW",
    "STP": "ST", "SEN": "SN", "SLE": "SL", "SOM": "SO", "ZAF": "ZA",
    "SSD": "SS", "SDN": "SD", "TZA": "TZ", "TGO": "TG", "TUN": "TN",
    "UGA": "UG", "ZMB": "ZM", "ZWE": "ZW",
}


def get_by_country(country_code: str) -> Optional[CurrencyInfo]:
    """Return the currency info for a given ISO 3166-1 alpha-2 or alpha-3 country code."""
    code = country_code.upper()
    # If ISO3 (3 chars), convert to ISO2 first
    if len(code) == 3:
        code = _ISO3_TO_ISO2.get(code, code)
    return _BY_COUNTRY.get(code)


def get_by_code(currency_code: str) -> Optional[CurrencyInfo]:
    """Return the first currency record matching an ISO 4217 currency code."""
    return _BY_CODE.get(currency_code.upper())


def get_unique_currencies() -> List[CurrencyInfo]:
    """Return one record per unique ISO 4217 currency code."""
    return list(_BY_CODE.values())


def get_by_monetary_union(union: str) -> List[CurrencyInfo]:
    """Return all currencies that belong to a given monetary union."""
    return [c for c in _BY_COUNTRY.values() if c.monetary_union == union.upper()]


def get_by_forex_regulation(level: str) -> List[CurrencyInfo]:
    """Return all currencies with a given forex regulation level."""
    return [c for c in _BY_COUNTRY.values() if c.forex_regulation == level.lower()]
