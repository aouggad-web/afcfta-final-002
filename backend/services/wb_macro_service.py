"""
Indicateurs macro Banque Mondiale (API officielle) — lecture du dataset
auto-actualisé ``data/json/worldbank_data_latest.json`` produit par
``backend/update_data_automated.py``.

Pourquoi : le module Profils Pays affiche des indicateurs complets, mais les
vues de comparaison (multi-pays, /ai/compare) laissaient des champs à null ou
générés de mémoire par le LLM. Ce service est la source UNIQUE, réelle et
rafraîchissable de ces indicateurs : PIB, PIB/habitant, population, croissance
— et inflation/chômage dès que l'ETL les aura collectés (indicateurs ajoutés à
``update_data_automated.py`` ; en attendant ils restent null, jamais inventés).

Chaque valeur est renvoyée avec son année réelle (dernière année disponible,
2024 puis repli) — jamais d'année affichée sans donnée correspondante.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

_log = logging.getLogger(__name__)

_DATASET_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "json" / "worldbank_data_latest.json"
)

# indicateur du dataset -> clé de sortie
_FIELDS = {
    "GDP": "gdp_usd",
    "GDP_per_capita": "gdp_per_capita_usd",
    "Population": "population",
    "GDP_growth": "gdp_growth_percent",
    "Inflation": "inflation_percent",
    "Unemployment": "unemployment_percent",
}

_cache: Optional[Dict] = None


def _load() -> Dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(_DATASET_PATH, encoding="utf-8") as fh:
            _cache = json.load(fh) or {}
    except (OSError, ValueError) as exc:
        _log.warning("worldbank_data_latest.json unreadable: %s", exc)
        _cache = {}
    return _cache


def reset_cache() -> None:
    """Pour les tests et après un run de l'ETL."""
    global _cache
    _cache = None


def _latest(years: Dict) -> Optional[tuple]:
    """(valeur, année) de la dernière année renseignée, None sinon."""
    if not isinstance(years, dict):
        return None
    usable = [(int(y), v) for y, v in years.items() if v is not None and str(y).isdigit()]
    if not usable:
        return None
    year, value = max(usable, key=lambda t: t[0])
    return value, year


def get_macro(country_iso3: str) -> Dict:
    """
    Indicateurs macro réels d'un pays, chacun avec son année :
    {available, source, updated_at, indicators: {clé: {value, year}}}.
    Un indicateur absent du dataset vaut None — jamais une valeur inventée.
    """
    data = _load()
    rec = (data.get("data") or {}).get((country_iso3 or "").strip().upper())
    meta = data.get("metadata") or {}
    if not rec:
        return {"available": False, "indicators": {}}
    out = {}
    for src_key, out_key in _FIELDS.items():
        latest = _latest((rec.get("indicators") or {}).get(src_key) or {})
        out[out_key] = {"value": latest[0], "year": latest[1]} if latest else None
    return {
        "available": any(v is not None for v in out.values()),
        "source": meta.get("source", "World Bank API"),
        "updated_at": meta.get("updated_at"),
        "indicators": out,
    }


def value_of(country_iso3: str, out_key: str) -> Optional[float]:
    """Raccourci : valeur seule (dernière année) d'un indicateur, ou None."""
    ind = get_macro(country_iso3).get("indicators", {}).get(out_key)
    return ind["value"] if ind else None


def get_series(country_iso3: str, out_key: str) -> Dict[int, float]:
    """
    Série pluriannuelle complète {année: valeur} d'un indicateur (ex.
    "gdp_usd") pour un pays — alimente les graphiques d'historique (module
    Statistiques). Dict vide si le pays ou l'indicateur est absent.
    """
    src_key = next((k for k, v in _FIELDS.items() if v == out_key), None)
    if not src_key:
        return {}
    data = _load()
    rec = (data.get("data") or {}).get((country_iso3 or "").strip().upper())
    if not rec:
        return {}
    years = (rec.get("indicators") or {}).get(src_key) or {}
    return {int(y): v for y, v in years.items() if v is not None and str(y).isdigit()}


def all_countries_iso3() -> list:
    """Codes ISO3 présents dans le dataset BM auto-actualisé."""
    return sorted((_load().get("data") or {}).keys())
