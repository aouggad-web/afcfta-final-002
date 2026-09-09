"""
Service — Projections FMI (World Economic Outlook).

Sert les séries WEO du FMI (croissance du PIB réel + inflation, incluant les
PROJECTIONS pluriannuelles que la Banque mondiale ne publie pas), produites par
``etl/imf_weo_projections.py``. Alimente le bloc prospectif de la fiche pays.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "json" / "imf_weo_projections.json"


@lru_cache(maxsize=1)
def _load() -> Dict:
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"metadata": {}, "data": {}}


def get_projections(iso3: str) -> Optional[Dict]:
    """
    Retourne ``{"gdp_growth": {year: %}, "inflation": {year: %}}`` pour un pays,
    ou ``None`` si absent. Années en clés string, valeurs float.
    """
    return _load().get("data", {}).get((iso3 or "").upper())


def source_label() -> str:
    return _load().get("metadata", {}).get("source", "IMF World Economic Outlook (DataMapper API)")
