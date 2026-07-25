"""
Vérifications d'intégrité de la collecte Bénin (UEMOA, lot 2) :
TVA seule, vérifiée sur le Code Général des Impôts 2025 (édition consolidée),
archivé et haché. Pas d'accises, pas de prélèvements collectés dans ce cycle.

Collecte délibérément incomplète : taux réduit est listé mais non extrait.
BEN n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/benin/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "benin"
_SOURCES_DIR = _ROOT / "data" / "sources" / "benin"


def test_ben_vat_standard_rate():
    """Bénin : taux standard 18% (CGI, Article 241)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next((r for r in data["vat_rates"] if "STANDARD" in r["record_id"]), None)
    assert standard is not None, "Taux standard 18% manquant"
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "241" in standard["legal_reference"]


def test_ben_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_exemptions", [])}
    assert used_ids <= registered_ids


def test_ben_archived_cgi_hash_matches_inventory():
    """Le CGI 2025 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "BEN-DGI-CGI-2025")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2025 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_ben_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "BEN"
    assert len(data["sources"]) >= 1
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_ben_inventory_csv_structure():
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
    assert len(rows) >= 1


def test_ben_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "BEN"
    assert "vat_rates" in data


def test_ben_not_registered_as_supported_jurisdiction():
    """Garde-fou : BEN n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "BEN" not in SUPPORTED_JURISDICTIONS


def test_ben_has_no_fabricated_afcfta_offer():
    """Garde-fou : BEN n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "BEN" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("BEN")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
