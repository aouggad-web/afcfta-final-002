"""Mauritius coverage must remain partial while evidence is incomplete."""
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS  # noqa: E402


def test_mauritius_is_registered_as_partial_usd_coverage():
    cfg = SUPPORTED_JURISDICTIONS["MUS"]
    assert cfg.default_currency == "USD"
    register = json.loads((cfg.fiscal_data_dir / "mus_gazette_register.json").read_text())
    assert register["coverage_complete"] is False
    assert register["preference_and_origin_status"] == "NOT_AVAILABLE"
    assert register["verification_nationale"]["status"] == "REVIEW_REQUIRED"


def test_mauritius_artifact_hash_matches_canonical():
    import hashlib
    cfg = SUPPORTED_JURISDICTIONS["MUS"]
    register = json.loads((cfg.fiscal_data_dir / "mus_gazette_register.json").read_text())
    digest = hashlib.sha256((BACKEND / "data/MUS_tariffs.json").read_bytes()).hexdigest()
    assert register["base_tariff_documentation"]["sha256"] == digest
