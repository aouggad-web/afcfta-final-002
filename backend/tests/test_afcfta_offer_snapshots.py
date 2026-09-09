import gzip
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "official_preferential"
EXPECTED_MINIMUM_LINES = {
    "EAC": 4000,
    "ECOWAS": 4000,
    "CEMAC": 4000,
    "EGY": 8000,
    "TUN": 15000,
    "ETH": 4000,
    "ZMB": 4000,
}


def test_all_priority_offer_snapshots_are_complete_and_non_executable():
    for offer, minimum in EXPECTED_MINIMUM_LINES.items():
        path = DATA_DIR / f"{offer}_afcfta_etariff_2026-08-17.json.gz"
        payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        line_count = sum(payload["schedule_line_counts"].values())
        assert line_count >= minimum
        assert payload["legal_effect_status"] == "OFFER_ONLY"
        assert payload["execution_authorized"] is False
        assert payload["source_url"] == "https://etariff.au-afcfta.org/"
        assert payload["source_api_url"].startswith("https://prod-afcfta-api.azurewebsites.net/")


def test_snapshots_cover_every_requested_destination():
    destination_to_offer = {
        "KEN": "EAC",
        "RWA": "EAC",
        "GHA": "ECOWAS",
        "CIV": "ECOWAS",
        "NGA": "ECOWAS",
        "CMR": "CEMAC",
        "EGY": "EGY",
        "TUN": "TUN",
        "ETH": "ETH",
        "ZMB": "ZMB",
    }
    for offer in destination_to_offer.values():
        assert (DATA_DIR / f"{offer}_afcfta_etariff_2026-08-17.json.gz").exists()
