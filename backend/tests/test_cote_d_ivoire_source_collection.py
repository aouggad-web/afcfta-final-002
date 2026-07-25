"""
Vérifications d'intégrité de la collecte Côte d'Ivoire (UEMOA) : TVA — taux
standard 18%, confirmé via l'annexe fiscale à la loi de Finances 2026 (pas
l'article de base du CGI, qui n'a pas été lu directement) — vérifiée sur
texte primaire, archivée et hachée.

Corrige une passe antérieure (bulk UEMOA) fusionnée avec un statut
PENDING_OFFICIAL_CONSOLIDATION, un sha256 "pending_collection", et une
affirmation non vérifiée que le CGI couvrait aussi les accises et
prélèvements. Voir data/sources/cote-d-ivoire/README.md.

CIV n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "cote-d-ivoire"
_SOURCES_DIR = _ROOT / "data" / "sources" / "cote-d-ivoire"


def test_civ_vat_standard_rate():
    """Côte d'Ivoire : taux TVA standard 18% (Annexe fiscale 2026, Article 6)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Article 6" in standard["legal_reference"]


def test_civ_no_excise_or_levy_data_in_this_cycle():
    """Collecte délibérément incomplète : pas d'accises, pas de prélèvements."""
    assert not (_DATA_DIR / "excise_measures.json").exists()
    assert not (_DATA_DIR / "import_levies.json").exists()


def test_civ_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_civ_archived_excerpt_hash_matches_inventory():
    """L'extrait de l'annexe fiscale 2026 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "CIV-DGBF-ANNEXE-FISCALE-2026")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Extrait de l'annexe fiscale 2026 manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_civ_inventory_csv_structure():
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


def test_civ_readme_documents_base_article_gap():
    """README.md documente explicitement que l'article de base du CGI n'a pas été lu directement."""
    readme = (_SOURCES_DIR / "README.md").read_text(encoding="utf-8")
    assert "359" in readme
    assert "pas" in readme.lower() and "directement" in readme.lower()


def test_civ_not_registered_as_supported_jurisdiction():
    """Garde-fou : CIV n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "CIV" not in SUPPORTED_JURISDICTIONS


def test_civ_has_no_fabricated_afcfta_offer():
    """Garde-fou : CIV n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "CIV" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("CIV")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
