"""Tests des juridictions nationales générées (9 partenaires ZLECAf de l'Algérie)."""

import hashlib
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

CURRENCIES = {"ZAF": "ZAR", "CMR": "XAF", "GHA": "GHS", "MUS": "MUR", "RWA": "RWF", "TZA": "TZS", "TUN": "TND"}


def _dossier(iso3):
    """Le dossier data/<slug>/ dont le jurisdiction_config.json déclare ce pays."""
    for config in sorted((_ROOT / "data").glob("*/jurisdiction_config.json")):
        declaration = json.loads(config.read_text(encoding="utf-8"))
        if str(declaration.get("iso3", "")).upper() == iso3:
            return config.parent, declaration
    raise AssertionError(f"{iso3} : aucun data/*/jurisdiction_config.json")


@pytest.mark.parametrize("iso3", sorted(CURRENCIES))
def test_jurisdiction_files_integrity(iso3):
    d, declaration = _dossier(iso3)
    assert declaration.get("currency", "USD") == CURRENCIES[iso3]
    for f in ("vat_measures.json", "excise_measures.json", "import_levies.json",
              "legal_overrides.json", "jurisdiction_config.json"):
        assert (d / f).is_file(), f"{iso3}: {f} manquant"
    reg = json.loads(
        (d / declaration.get("gazette_register", f"{iso3.lower()}_gazette_register.json")).read_text(
            encoding="utf-8"
        )
    )
    assert reg["coverage_complete"] is True
    base = reg["base_tariff_documentation"]
    assert base["sha256"], iso3
    canon_sha = hashlib.sha256(
        (_ROOT / "backend" / "data" / f"{iso3}_tariffs.json").read_bytes()
    ).hexdigest()
    assert base["sha256"] == canon_sha
    overrides = json.loads((d / "legal_overrides.json").read_text(encoding="utf-8"))
    for m in overrides["measures"]:
        assert m["mapping_status"] == "DIRECT_HS" and m["source_hash"]
