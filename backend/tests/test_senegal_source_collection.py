"""
Vérifications d'intégrité de la collecte Sénégal (UEMOA) : TVA — taux
standard, taux réduit tourisme, exportations — vérifiée sur texte primaire
(Code Général des Impôts, édition 2019), archivée et hachée.

Corrige une passe antérieure (bulk UEMOA) fusionnée avec un statut
PENDING_OFFICIAL_CONSOLIDATION, un sha256 "pending_collection" et une URL
fictive (armp.sn/textes-legaux/code-general-impots). Voir
data/sources/senegal/README.md.

SEN n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "senegal"
_SOURCES_DIR = _ROOT / "data" / "sources" / "senegal"


def test_sen_vat_standard_rate():
    """Sénégal : taux TVA standard 18% (CGI, Article 369)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "369" in standard["legal_reference"]


def test_sen_vat_reduced_rate_tourism():
    """Taux réduit 10% pour l'hébergement touristique agréé (Article 369)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    reduced = next(r for r in data["vat_rates"] if "REDUCED" in r["record_id"])
    assert reduced["rate"] == "10%"
    assert reduced["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_sen_vat_zero_rated_exports():
    """Exportations : droit à déduction équivalent au taux zéro (Article 380)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = next(r for r in data["vat_zero_rated"])
    assert zero["rate"] == "0%"
    assert zero["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "380" in zero["legal_reference"]


def test_sen_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    assert used_ids <= registered_ids


def test_sen_archived_cgi_hash_matches_inventory():
    """Le CGI 2019 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "SEN-CGI-2019")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2019 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_sen_inventory_csv_structure():
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


def test_sen_not_registered_as_supported_jurisdiction():
    """Garde-fou : SEN n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "SEN" not in SUPPORTED_JURISDICTIONS


def test_sen_has_no_fabricated_afcfta_offer():
    """Garde-fou : SEN n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "SEN" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("SEN")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
