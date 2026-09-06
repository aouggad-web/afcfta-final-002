"""Intégrité des fichiers de juridictions nationales (9 partenaires ZLECAf).

Niveau DONNÉES uniquement : collecte, vérification, documentation.
Aucun test du calculateur (côté Emergent, hors périmètre de cette PR).
"""

import json
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from services.national_legal_calculation_service import (  # noqa: E402
    SUPPORTED_JURISDICTIONS,
)

_ROOT = BACKEND_ROOT.parent

CURRENCIES = {"ZAF": "ZAR", "CMR": "XAF", "GHA": "GHS", "MUS": "MUR", "RWA": "RWF", "TZA": "TZS", "TUN": "TND"}


@pytest.mark.parametrize("iso3", ["ZAF", "CMR", "GHA", "MUS", "RWA", "TZA", "TUN"])
def test_jurisdiction_files_integrity(iso3):
    if iso3 not in SUPPORTED_JURISDICTIONS:
        pytest.skip(
            f"{iso3}: juridiction non présente sur cette branche (1 PR par pays)"
        )
    slug = SUPPORTED_JURISDICTIONS[iso3].fiscal_data_dir.name
    d = _ROOT / "data" / slug
    for f in ("vat_measures.json", "excise_measures.json", "import_levies.json",
              "legal_overrides.json", "jurisdiction_config.json"):
        assert (d / f).is_file(), f"{iso3}: {f} manquant"
    reg = json.loads(
        next(d.glob("*gazette_register.json")).read_text(encoding="utf-8")
    )
    assert reg["coverage_complete"] is True
    base = reg["base_tariff_documentation"]
    assert base["sha256"], iso3
    canon_sha = __import__("hashlib").sha256(
        (_ROOT / "backend" / "data" / f"{iso3}_tariffs.json").read_bytes()
    ).hexdigest()
    assert base["sha256"] == canon_sha
    overrides = json.loads((d / "legal_overrides.json").read_text(encoding="utf-8"))
    for m in overrides["measures"]:
        assert m["mapping_status"] == "DIRECT_HS" and m["source_hash"]
