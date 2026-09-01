"""
Vérifications d'intégrité de la collecte Mali (UEMOA) : TVA — taux standard
18% et taux réduit 5% — vérifiée sur texte primaire (portail officiel DGI
Mali), archivée et hachée.

Corrige une passe antérieure (bulk UEMOA) fusionnée avec un statut
PENDING_OFFICIAL_CONSOLIDATION, un sha256 "pending_collection" et une URL
fictive (armp.mali.org/documents/legislation). Voir
data/sources/mali/README.md.

MLI n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "mali"
_SOURCES_DIR = _ROOT / "data" / "sources" / "mali"


def test_mli_vat_standard_rate():
    """Mali : taux TVA standard 18% (CGI, Article 229)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "229" in standard["legal_reference"]


def test_mli_vat_reduced_rate():
    """Taux réduit 5% pour les produits du point D (Article 229)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    reduced = next(r for r in data["vat_rates"] if "REDUCED" in r["record_id"])
    assert reduced["rate"] == "5%"
    assert reduced["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_mli_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_mli_archived_cgi_hash_matches_inventory():
    """Le CGI Mali archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "MLI-DGI-CGI")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI Mali archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_mli_inventory_csv_structure():
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
    assert len(rows) >= 2


def test_mli_not_registered_as_supported_jurisdiction():
    """Garde-fou : MLI n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "MLI" not in SUPPORTED_JURISDICTIONS


def test_mli_has_no_fabricated_afcfta_offer():
    """Garde-fou : MLI n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "MLI" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("MLI")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
