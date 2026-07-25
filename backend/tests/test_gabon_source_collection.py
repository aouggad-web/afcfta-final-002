"""
Vérifications d'intégrité de la collecte Gabon (quatrième pays CEMAC) :
TVA partielle, vérifiée sur la Loi de Finances 2025 (Journal Officiel du Gabon,
n°51 Bis Spécial du 20 janvier 2025), archivée et hachée.

Collecte délibérément incomplète : le taux normal de la TVA n'a pas pu être
vérifié sur texte primaire (la loi de finances modifie seulement les articles
210/221 nouveaux, pas l'article du taux normal). Seuls les articles 210 nouveau
(exonération pêche artisanale) et 221 nouveau (taux réduit 5%) sont vérifiés.
GAB n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/gabon/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "gabon"
_SOURCES_DIR = _ROOT / "data" / "sources" / "gabon"


def test_gab_vat_reduced_rate():
    """Gabon : taux réduit 5% (Loi de Finances 2025, Article 221 nouveau)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    reduced = next(
        (r for r in data["vat_rates"] if "REDUCED" in r["record_id"]), None
    )
    assert reduced is not None, "Taux réduit 5% manquant"
    assert reduced["rate"] == "5%"
    assert reduced["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "221" in reduced["legal_reference"]


def test_gab_vat_exemption_artisanal_fishing():
    """Exonération TVA sur pétrole pour pêche artisanale (Article 210 nouveau)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    exemption = next(
        (r for r in data["vat_exemptions"] if "PECHE" in r["record_id"]), None
    )
    assert exemption is not None, "Exonération pêche artisanale manquante"
    assert exemption["rate"] == "0%"
    assert exemption["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "210" in exemption["legal_reference"]


def test_gab_vat_standard_rate_not_verified():
    """Garde-fou : aucune entrée VAT-RATE-STANDARD (non vérifiée sur texte primaire)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(
        (r for r in data["vat_rates"] if "STANDARD" in r["record_id"]), None
    )
    assert standard is None, "Taux normal ne doit pas être enregistré sans source primaire"


def test_gab_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_exemptions"]}
    assert used_ids <= registered_ids


def test_gab_archived_loi_finances_hash_matches_inventory():
    """La Loi de Finances 2025 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "GAB-JO-LOI-FINANCES-2025")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Loi de Finances 2025 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_gab_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "GAB"
    assert len(data["sources"]) >= 1
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_gab_inventory_csv_structure():
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


def test_gab_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "GAB"
    assert "vat_rates" in data
    assert "vat_exemptions" in data


def test_gab_not_registered_as_supported_jurisdiction():
    """Garde-fou : GAB n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "GAB" not in SUPPORTED_JURISDICTIONS


def test_gab_has_no_fabricated_afcfta_offer():
    """Garde-fou : GAB n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "GAB" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("GAB")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
