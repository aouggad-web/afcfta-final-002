"""
Gold reserves and Global Attractiveness Index data
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def load_gold_reserves_gai():
    """Load gold reserves and Global Attractiveness Index 2025 data"""
    try:
        with open(
            ROOT_DIR / "../data/json/gold_reserves_gai_2025.json", "r", encoding="utf-8"
        ) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Warning: Could not load gold_reserves_gai_2025.json: {e}")
        return {"gold_reserves": {}, "global_attractiveness_index_2025": {}}


GOLD_RESERVES_GAI_DATA = load_gold_reserves_gai()
