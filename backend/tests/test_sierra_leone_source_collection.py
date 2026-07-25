"""
Vérifications d'intégrité de la collecte Sierra Leone (UEMOA, lot 3) :
GST (Goods and Services Tax, équivalent TVA) seule, vérifiée sur le Goods
and Services Tax Act 2009 (Act No. 6 of 2009), publié au Sierra Leone
Gazette, archivé et haché. Pas d'accises collectées dans ce cycle (régime
fragmenté entre Customs Act 2011 et Finance Acts successifs — voir
data/sources/sierra-leone/README.md).

SLE n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "sierra-leone"
_SOURCES_DIR = _ROOT / "data" / "sources" / "sierra-leone"


def test_sle_vat_standard_rate():
    """Sierra Leone : taux standard GST 15% (Section 14(3))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "15%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "14" in standard["legal_reference"]


def test_sle_vat_zero_rated_exports():
    """Sierra Leone : exportations taux zéro (First Schedule, item 1), minéraux exclus."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    exports = next(r for r in data["vat_zero_rated"] if "EXPORTS" in r["record_id"])
    assert exports["rate"] == "0%"
    assert "rutile" in exports["legal_product_description"].lower()
    assert exports["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_sle_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_sle_archived_gst_act_hash_matches_inventory():
    """Le GST Act 2009 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "SLE-GOV-GST-ACT-2009")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "GST Act 2009 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_sle_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "SLE"
    assert len(data["sources"]) >= 1


def test_sle_inventory_csv_structure():
    """inventory.csv possède les colonnes requises."""
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id",
        "institution",
        "title",
        "legal_date",
        "accessed_at",
        "url",
        "local_file",
        "sha256",
        "coverage",
        "status",
        "notes",
    }
    assert required_columns <= set(rows[0].keys())


def test_sle_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "SLE"
    assert "vat_rates" in data


def test_sle_not_registered_as_supported_jurisdiction():
    """Garde-fou : SLE n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "SLE" not in SUPPORTED_JURISDICTIONS


def test_sle_has_no_fabricated_afcfta_offer():
    """Garde-fou : SLE n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "SLE" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("SLE")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
