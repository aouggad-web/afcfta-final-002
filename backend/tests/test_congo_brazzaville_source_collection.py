"""
Vérifications d'intégrité de la collecte Congo-Brazzaville (troisième pays CEMAC) :
TVA seule, vérifiée sur le Code Général des Impôts Tome I (Article 17),
archivé et haché. Pas d'accises, pas de prélèvements collectés dans ce cycle.

Collecte délibérément incomplète : le taux réduit est listé (Annexe 5) mais son
pourcentage n'a pas pu être extrait de ce Tome. Aucune base_cet_rate sans le TEC
CEMAC. COG n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/congo-brazzaville/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "congo-brazzaville"
_SOURCES_DIR = _ROOT / "data" / "sources" / "congo-brazzaville"


def test_cog_vat_standard_rate():
    """Congo-Brazzaville : taux TVA général 18% (CGI Tome I, Article 17)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "17" in standard["legal_reference"] or "Article 17" in standard["legal_reference"]


def test_cog_vat_zero_rated_exports():
    """Taux zéro sur exportations et accessoires (Article 17, CGI Tome I)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = next(r for r in data["vat_zero_rated"])
    assert zero["rate"] == "0%"
    assert zero["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "17" in zero["legal_reference"] or "Article 17" in zero["legal_reference"]
    assert zero["hs_codes_explicit"] == []


def test_cog_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    assert used_ids <= registered_ids


def test_cog_archived_cgi_hash_matches_inventory():
    """Le CGI Tome I archivé correspond au SHA-256 déclaré dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "COG-MINFIN-CGI-TOME1")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI Tome I archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_cog_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "COG"
    assert len(data["sources"]) >= 1
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_cog_inventory_csv_structure():
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


def test_cog_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "COG"
    assert "vat_rates" in data
    assert "vat_zero_rated" in data


def test_cog_not_registered_as_supported_jurisdiction():
    """Garde-fou : COG n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "COG" not in SUPPORTED_JURISDICTIONS


def test_cog_has_no_fabricated_afcfta_offer():
    """Garde-fou : COG n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "COG" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("COG")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_cog_reduced_rate_pending_percentage():
    """Annexe 5 (liste de biens à taux réduit) est documentée comme incomplète."""
    readme = (_DATA_DIR.parent / "sources" / "congo-brazzaville" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "Annexe 5" in readme
    assert "pourcentage" in readme.lower() or "taux réduit" in readme.lower()
    assert "n'a pas pu être extrait" in readme or "pending" in readme.lower()


def test_cog_no_excise_or_levy_data_in_this_cycle():
    """Collecte délibérément incomplète : pas d'accises, pas de prélèvements."""
    assert not (_DATA_DIR / "excise_measures.json").exists()
    assert not (_DATA_DIR / "import_levies.json").exists()
