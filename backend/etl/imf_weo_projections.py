"""
ETL — Projections FMI (World Economic Outlook) -> JSON.

Récupère, via l'API publique IMF DataMapper, les séries WEO de croissance du PIB
réel et d'inflation (prix à la consommation) pour les 54 pays africains, incluant
les PROJECTIONS pluriannuelles (année courante + suivantes) que la Banque mondiale
ne publie pas. Complète ``worldbank_data_latest.json`` (réalisé) par la vision
prospective du FMI, pour une fiche pays plus complète.

Indicateurs :
  * ``NGDP_RPCH``  — croissance du PIB réel (variation annuelle, %)
  * ``PCPIPCH``    — inflation, prix moyens à la consommation (variation, %)

Sortie : ``data/json/imf_weo_projections.json`` ::

    {
      "metadata": {"source": "IMF World Economic Outlook (DataMapper API)",
                   "updated_at": "...", "indicators": {...}},
      "data": {
        "DZA": {"gdp_growth": {"2024": 3.7, "2025": 3.8, "2026": 3.8, ...},
                 "inflation":  {"2024": 4.0, "2025": 1.4, "2026": 2.9, ...}},
        ...
      }
    }

Deux appels réseau seulement (un par indicateur, tous pays). Dégradation
silencieuse : en cas d'échec, le fichier existant est conservé (jamais écrasé
par du vide).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "json"
_OUT = _DATA_DIR / "imf_weo_projections.json"

_API = "https://www.imf.org/external/datamapper/api/v1/{indicator}"
_INDICATORS = {
    "gdp_growth": "NGDP_RPCH",  # croissance PIB réel (%)
    "inflation": "PCPIPCH",  # inflation prix conso (%)
}

# 54 pays membres de la ZLECAf (ISO3).
_AFRICAN_ISO3 = [
    "DZA",
    "AGO",
    "BEN",
    "BWA",
    "BFA",
    "BDI",
    "CMR",
    "CPV",
    "CAF",
    "TCD",
    "COM",
    "COG",
    "COD",
    "CIV",
    "DJI",
    "EGY",
    "GNQ",
    "ERI",
    "ETH",
    "GAB",
    "GMB",
    "GHA",
    "GIN",
    "GNB",
    "KEN",
    "LSO",
    "LBR",
    "LBY",
    "MDG",
    "MWI",
    "MLI",
    "MRT",
    "MUS",
    "MAR",
    "MOZ",
    "NAM",
    "NER",
    "NGA",
    "RWA",
    "STP",
    "SEN",
    "SYC",
    "SLE",
    "SOM",
    "ZAF",
    "SSD",
    "SDN",
    "SWZ",
    "TZA",
    "TGO",
    "TUN",
    "UGA",
    "ZMB",
    "ZWE",
]


def _fetch_indicator(imf_code: str) -> Dict[str, Dict[str, float]]:
    """Retourne ``{iso3: {year: value}}`` pour un indicateur WEO, tous pays."""
    resp = requests.get(_API.format(indicator=imf_code), timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    by_country = payload.get("values", {}).get(imf_code, {})
    out: Dict[str, Dict[str, float]] = {}
    for iso3 in _AFRICAN_ISO3:
        series = by_country.get(iso3)
        if not series:
            continue
        clean: Dict[str, float] = {}
        for year, value in series.items():
            if value is None:
                continue
            try:
                clean[str(year)] = round(float(value), 2)
            except (TypeError, ValueError):
                continue
        if clean:
            out[iso3] = clean
    return out


def build() -> Dict:
    """Construit le fichier de projections FMI ; conserve l'existant si échec."""
    if requests is None:  # pragma: no cover
        raise RuntimeError("requests indisponible")

    fetched: Dict[str, Dict[str, Dict[str, float]]] = {}
    for field, imf_code in _INDICATORS.items():
        fetched[field] = _fetch_indicator(imf_code)

    data: Dict[str, Dict] = {}
    for iso3 in _AFRICAN_ISO3:
        growth = fetched["gdp_growth"].get(iso3)
        inflation = fetched["inflation"].get(iso3)
        if growth or inflation:
            data[iso3] = {"gdp_growth": growth or {}, "inflation": inflation or {}}

    if not data:  # collecte totalement vide -> on NE remplace PAS l'existant
        raise RuntimeError("collecte FMI vide — fichier existant conservé")

    payload = {
        "metadata": {
            "source": "IMF World Economic Outlook (DataMapper API)",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "indicators": {
                "gdp_growth": "NGDP_RPCH — croissance PIB réel (%)",
                "inflation": "PCPIPCH — inflation prix à la consommation (%)",
            },
            "country_count": len(data),
        },
        "data": data,
    }
    _OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = build()
    print(f"FMI WEO écrit : {result['metadata']['country_count']} pays -> {_OUT}")
