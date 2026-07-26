"""
Vérifications d'intégrité de la collecte Ghana (CEDEAO) : TVA seule,
vérifiée sur la Value Added Tax Act 2013 (Act 870), archivée et hachée.
Corrige une collecte initiale fabriquée (voir data/sources/ghana/README.md).
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "ghana"
_SOURCES_DIR = _ROOT / "data" / "sources" / "ghana"


def test_gha_vat_standard_rate():
    """Ghana : taux standard 15% (Act 870, Section 3)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "15%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Section 3" in standard["legal_reference"]


def test_gha_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_exemptions", [])}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_gha_archived_act_hash_matches_inventory():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "GHA-GRA-VAT-ACT-870-2013")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Act 870 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "GHA-GRA-VAT-ACT-870-2013")
    assert inventory_row["sha256"] == primary["sha256"]


def test_gha_no_fabricated_domain_in_urls():
    """Garde-fou : le domaine fabriqué impots.gha ne doit plus apparaître
    comme URL de source (peut être mentionné en prose dans les notes
    historiques expliquant la correction)."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    for s in sources:
        assert "impots.gha" not in (s.get("url") or "")
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert "impots.gha" not in (row.get("url") or "")


def test_gha_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "GHA" not in SUPPORTED_JURISDICTIONS


def test_gha_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "GHA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("GHA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
