import json
from pathlib import Path
from typing import Dict, List

# Determine data file path with fallback
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "json"
FREE_ZONES_FILE = DATA_DIR / "zones_franches_afrique.json"
if not FREE_ZONES_FILE.exists():
    FREE_ZONES_FILE = ROOT_DIR / "zones_franches_afrique.json"


def load_free_zones():
    """Charger les zones franches depuis le fichier JSON"""
    try:
        with open(
            ROOT_DIR / "data" / "json" / "zones_franches_afrique.json", "r", encoding="utf-8"
        ) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_free_zones_by_country(country_iso3: str = None) -> List[Dict]:
    """Récupérer les zones franches, filtre optionnel par pays"""
    zones = load_free_zones()
    if country_iso3:
        return [z for z in zones if z["country_iso"] == country_iso3]
    return zones
