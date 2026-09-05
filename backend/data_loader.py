"""
Data loader for ZLECAf 2024 enhanced commerce and economic data
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# .resolve() normalise le chemin AVANT de remonter de deux niveaux : sans lui,
# un import via une entrée sys.path non normalisée (ex. certains tests font
# sys.path.insert(0, ".../backend/tests/..")) donne __file__ =
# ".../backend/tests/../data_loader.py", et Path(...).parent.parent se replie
# alors sur ".../backend/tests" (pathlib traite ".." comme un composant),
# repointant TOUTES les données du dépôt vers backend/tests pour le reste de la
# session de tests (500 sur /calculate-tariff, FileNotFoundError ailleurs).
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


# Load the corrections and enhanced statistics
def load_corrections_data():
    """Load the 2024 corrections JSON with tariffs and enhanced statistics"""
    corrections_path = ROOT_DIR / "data" / "json" / "zlecaf_corrections_2024.json"
    with open(corrections_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load the complete country economic data
def load_country_economic_data():
    """Load the complete economic data for 54 countries"""
    economic_path = ROOT_DIR / "data" / "csv" / "ZLECAF_54_PAYS_DONNEES_COMPLETES.csv"
    df = pd.read_csv(economic_path)
    return df


# Get enhanced statistics from corrections JSON
def get_enhanced_statistics() -> Dict:
    """Get enhanced statistics including projections and trade evolution"""
    corrections = load_corrections_data()
    return corrections.get("enhanced_statistics", {})


# Get tariff corrections
def get_tariff_corrections() -> Dict:
    """Get updated tariff rates for normal and zlecaf"""
    corrections = load_corrections_data()
    return corrections.get("tariff_corrections", {})


# Load customs data
def load_customs_data():
    """Load African customs administrations data"""
    customs_path = ROOT_DIR / "data" / "json" / "douanes_africaines.json"
    with open(customs_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load infrastructure ranking data
def load_infrastructure_ranking():
    """Load African infrastructure ranking (IPL & AIDI)"""
    ranking_path = ROOT_DIR / "data" / "json" / "classement_infrastructure_afrique.json"
    with open(ranking_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Get customs info for a country
def get_country_customs_info(country_name: str) -> Optional[Dict]:
    """Get customs administration info for a specific country"""
    customs_data = load_customs_data()

    # Match by country name (case-insensitive)
    for entry in customs_data:
        if entry["pays"].lower() == country_name.lower():
            return {
                "administration": entry["administration_douaniere"],
                "adresse": entry.get("adresse", ""),
                "website": entry["site_web"],
                "bureaux_portuaires": entry.get("bureaux_portuaires", ""),
                "bureaux_aeriens": entry.get("bureaux_aeriens", ""),
                "bureaux_terrestres": entry.get("bureaux_terrestres", ""),
            }
    return None


# Get infrastructure ranking for a country
def get_country_infrastructure_ranking(country_name: str) -> Optional[Dict]:
    """Get infrastructure ranking for a specific country"""
    ranking_data = load_infrastructure_ranking()

    # Normaliser le nom pour la comparaison
    import unicodedata

    def normalize(s):
        # Enlever les accents et convertir en minuscules
        return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode("ascii")

    search_name = normalize(country_name)

    # Match by country name (case-insensitive, accent-insensitive)
    for entry in ranking_data:
        entry_name = normalize(entry["pays"])
        if entry_name == search_name or search_name in entry_name or entry_name in search_name:
            return {
                "africa_rank": entry["rang_afrique"],
                "lpi_infrastructure_score": entry["score_infrastructure_ipl"],
                "lpi_world_rank": entry["rang_mondial_ipl"],
                "aidi_transport_score": entry.get(
                    "score_aidi_2024", entry.get("score_transport_aidi", 0)
                ),
            }
    return None
