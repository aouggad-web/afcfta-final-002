"""
Fetch World Bank WDI robuste, partagé par les ETL (``fetch_wb_gdp``,
``fetch_wb_reserves``).

Leçon du run GitHub Actions 28660846789 : une requête unique 54 pays ×
15 ans peut dépasser le read-timeout de l'API WDI. Ici :

  - pays interrogés par LOTS (payloads bornés) ;
  - 4 tentatives par lot avec backoff exponentiel (2/4/8/16 s) ;
  - timeout de lecture long (120 s).

Aucune valeur n'est jamais synthétisée : un lot définitivement injoignable
lève, l'appelant décide (les scripts sortent en erreur, comme avant).
"""

import json
import time
import urllib.request
from typing import Dict, List

WB_BASE = "https://api.worldbank.org/v2"
_CHUNK_SIZE = 18
_RETRIES = 4
_TIMEOUT_S = 120


def _get_json(url: str) -> list:
    delay = 2.0
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # timeout / réseau / HTTP
            last_exc = exc
            if attempt < _RETRIES - 1:
                print(f"⚠ WB fetch tentative {attempt + 1}/{_RETRIES} échouée ({exc}) — retry")
                time.sleep(delay)
                delay *= 2
    raise last_exc


def fetch_indicator(indicator: str, iso3_list: List[str]) -> Dict[str, Dict]:
    """{iso3: {"value": float, "year": int}} — dernière observation non nulle,
    récupérée par lots de pays avec retries."""
    latest: Dict[str, Dict] = {}
    for i in range(0, len(iso3_list), _CHUNK_SIZE):
        chunk = iso3_list[i : i + _CHUNK_SIZE]
        url = (
            f"{WB_BASE}/country/{';'.join(chunk)}/indicator/{indicator}"
            f"?format=json&per_page=20000&date=2010:2025"
        )
        payload = _get_json(url)
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            continue
        for row in payload[1]:
            iso3 = (row.get("countryiso3code") or "").upper()
            value = row.get("value")
            year = row.get("date")
            if not iso3 or value is None or year is None:
                continue
            year = int(year)
            if iso3 not in latest or year > latest[iso3]["year"]:
                latest[iso3] = {"value": float(value), "year": year}
    return latest
