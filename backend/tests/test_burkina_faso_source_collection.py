"""
Vérifications d'intégrité de la collecte Burkina Faso (UEMOA, lot 2) :
TVA seule, vérifiée sur le Code Général des Impôts 2023 (édition consolidée),
archivé et haché. Pas d'accises, pas de prélèvements collectés dans ce cycle.

Collecte délibérément incomplète : taux réduit est listé mais non extrait.
BFA n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/burkina-faso/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "burkina-faso"
_SOURCES_DIR = _ROOT / "data" / "sources" / "burkina-faso"


def test_bfa_vat_standard_rate():
    """Burkina Faso : taux standard 18% (CGI, Article 352 et seq)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next((r for r in data["vat_rates"] if "STANDARD" in r["record_id"]), None)
    assert standard is not None, "Taux standard 18% manquant"
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_bfa_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_bfa_archived_cgi_hash_matches_inventory():
    """Le CGI 2023 archivé correspond au SHA-256 déclaré dans legal_sources.json et inventory.csv."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "BFA-DGI-CGI-2023")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2023 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "BFA-DGI-CGI-2023")
    assert inventory_row["sha256"] == primary["sha256"]
    assert inventory_row["local_file"] == primary["local_file"]


def test_bfa_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "BFA"
    assert len(data["sources"]) >= 1


def test_bfa_inventory_csv_structure():
    """inventory.csv possède les colonnes requises."""
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 1
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


def test_bfa_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "BFA"
    assert "vat_rates" in data


def test_bfa_not_registered_as_supported_jurisdiction():
    """Garde-fou : BFA n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "BFA" not in SUPPORTED_JURISDICTIONS


def test_bfa_has_no_fabricated_afcfta_offer():
    """Garde-fou : BFA n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "BFA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("BFA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
