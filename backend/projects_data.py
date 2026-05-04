
import json
from pathlib import Path
from typing import List, Dict

# Determine data file path with fallback
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "json"
PROJECTS_FILE = DATA_DIR / "projets_structurants_afrique.json"
if not PROJECTS_FILE.exists():
    PROJECTS_FILE = ROOT_DIR / "projets_structurants_afrique.json"

def load_ongoing_projects():
    """Charger les projets structurants depuis le fichier JSON"""
    try:
        with open(ROOT_DIR / 'data' / 'json' / 'projets_structurants_afrique.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_country_ongoing_projects(country_iso3: str) -> List[Dict]:
    """Récupérer les projets structurants pour un pays donné"""
    projects_data = load_ongoing_projects()
    return projects_data.get(country_iso3, [])
