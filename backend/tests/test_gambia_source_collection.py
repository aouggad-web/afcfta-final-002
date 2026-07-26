"""
Vérifications d'intégrité de la collecte Gambie (CEDEAO) : TVA vérifiée sur
la brochure officielle GRA (guide d'agence, pas le texte de loi brut).
Corrige une collecte initiale fabriquée (voir data/sources/gambia/README.md).
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "gambia"
_SOURCES_DIR = _ROOT / "data" / "sources" / "gambia"


def test_gmb_vat_standard_rate():
    """Gambie : taux standard 15% (brochure GRA)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "15%"
    assert standard["verification_status"] == "VERIFIED_OFFICIAL_GUIDE"


def test_gmb_zero_rated_exports():
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = data["vat_zero_rated"]
    assert zero
    assert zero[0]["rate"] == "0%"


def test_gmb_effective_date_honestly_flagged_as_unconfirmed():
    """Garde-fou de sincérité : la date d'entrée en vigueur, absente de la
    brochure GRA elle-même, doit être signalée comme non re-vérifiée."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert "not re-verified" in standard["legal_reference"] or "NOT stated" in standard[
        "legal_reference"
    ].replace("NOT", "NOT stated")


def test_gmb_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_gmb_archived_brochure_hash_matches_inventory():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "GMB-GRA-VAT-BROCHURE")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Brochure GRA archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "GMB-GRA-VAT-BROCHURE")
    assert inventory_row["sha256"] == primary["sha256"]


def test_gmb_no_fabricated_domain_remains():
    for path in (_DATA_DIR / "legal_sources.json", _SOURCES_DIR / "inventory.csv"):
        text = path.read_text(encoding="utf-8")
        assert "impots.gmb" not in text


def test_gmb_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "GMB" not in SUPPORTED_JURISDICTIONS


def test_gmb_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "GMB" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("GMB")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
