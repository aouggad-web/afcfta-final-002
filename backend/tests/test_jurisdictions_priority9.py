"""Tests des juridictions nationales générées (9 partenaires ZLECAf de l'Algérie)."""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from services.national_legal_calculation_service import (  # noqa: E402
    SUPPORTED_JURISDICTIONS,
    calculate_national_legal_layer,
)

_ROOT = BACKEND_ROOT.parent
ON_DATE = date(2026, 9, 6)

CURRENCIES = {"ZAF": "ZAR", "CMR": "XAF", "GHA": "GHS", "MUS": "MUR", "RWA": "RWF", "TZA": "TZS", "TUN": "TND"}


def _first_position(iso3):
    canon = json.loads((_ROOT / "backend" / "data" / f"{iso3}_tariffs.json").read_text(encoding="utf-8"))
    for l in canon["tariff_lines"]:
        sps = l.get("sub_positions") or []
        if sps and l.get("taxes_detail"):
            return sps[0]["code"]
    return None


@pytest.mark.parametrize("iso3", ["ZAF", "CMR", "GHA", "MUS", "RWA", "TZA", "TUN"])
def test_jurisdiction_registered_and_documented(iso3):
    cfg = SUPPORTED_JURISDICTIONS[iso3]
    assert cfg.default_currency == CURRENCIES[iso3]
    hs = _first_position(iso3)
    assert hs, iso3
    r = calculate_national_legal_layer(
        jurisdiction=iso3, hs_code=hs, on_date=ON_DATE,
        customs_value=10000.0, base_cet_rate=15.0,
    )
    q = r["quality_dimensions"]
    assert q["source"] == "DOCUMENTED", (iso3, q)
    assert q["temporal_validity"] == "DOCUMENTED", (iso3, q)
    assert q["taxes_and_levies"] == "DOCUMENTED", (iso3, q)
    assert r["overall_status"] == "INFORMATIVE_COMPLETE", (iso3, q, r.get("known_data_gaps"))
    gaps = " ".join(r.get("known_data_gaps", []) + r.get("missing_elements", []))
    assert "gazette coverage" not in gaps and "national-measure coverage" not in gaps
    assert r["currency_code"] == CURRENCIES[iso3]


@pytest.mark.parametrize("iso3", ["ZAF", "CMR", "GHA", "MUS", "RWA", "TZA", "TUN"])
def test_jurisdiction_files_integrity(iso3):
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
