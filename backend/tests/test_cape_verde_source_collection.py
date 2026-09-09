"""
Vérifications d'intégrité de la collecte Cabo Verde (CEDEAO, lot 3) :
IVA seule, vérifiée sur le Regulamento do IVA (Lei nº 21/VI/2003 de 14 de
Julho), archivé et haché. L'ICE (Imposto sobre Consumos Especiais,
équivalent accises, Lei nº 22/VI/2003) n'a pas pu être collecté : le seul
lien officiel identifié (igae.cv) est hors de la liste blanche réseau de
cet environnement de collecte.

CPV n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/cape-verde/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "cape-verde"
_SOURCES_DIR = _ROOT / "data" / "sources" / "cape-verde"


def test_cpv_vat_standard_rate():
    """Cabo Verde : taux standard IVA 15% (Regulamento do IVA, Artigo 17º)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "15%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "17" in standard["legal_reference"]


def test_cpv_vat_zero_rated_exports():
    """Cabo Verde : exportações isentas com direito a dedução (Artigo 13º)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    exports = next(r for r in data["vat_zero_rated"] if "EXPORTS" in r["record_id"])
    assert exports["rate"] == "0%"
    assert exports["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_cpv_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés dans vat_measures sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_cpv_archived_iva_law_hash_matches_inventory():
    """La loi IVA archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "CPV-MF-IVA-LEI-21-VI-2003")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Loi IVA archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_cpv_ice_source_documented_as_blocked():
    """La loi ICE (accises) est déclarée bloquée, pas silencieusement omise."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    ice = next(s for s in sources if s["source_id"] == "CPV-IGAE-ICE-LEI-22-VI-2003")
    assert ice["status"] == "source_blocked"
    assert ice["verification_status"] == "PENDING_COLLECTION"
    assert ice["sha256"] is None
    assert ice["local_file"] is None


def test_cpv_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "CPV"
    assert len(data["sources"]) == 2


def test_cpv_inventory_csv_structure():
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
    assert len(rows) == 2


def test_cpv_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "CPV"
    assert "vat_rates" in data


def test_cpv_not_registered_as_supported_jurisdiction():
    """Garde-fou : CPV n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "CPV" not in SUPPORTED_JURISDICTIONS


def test_cpv_has_no_fabricated_afcfta_offer():
    """Garde-fou : CPV n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "CPV" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("CPV")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
