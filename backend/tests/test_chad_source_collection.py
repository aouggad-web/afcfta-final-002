"""
Vérifications d'intégrité de la collecte Tchad (second pays CEMAC, EAC adjacent) :
TVA seule, vérifiée sur le Code Général des Impôts 2016 (Article 238(1)),
archivé et haché. Pas d'accises, pas de prélèvements collectés dans ce cycle.

Collecte délibérément incomplète : aucune base_cet_rate calculable sans le TEC
CEMAC, et les prélèvements/ristournes ne sont pas archivés. TCD n'est donc pas
enregistrée dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY.
Voir data/sources/chad/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "chad"
_SOURCES_DIR = _ROOT / "data" / "sources" / "chad"


def test_tcd_vat_standard_rate():
    """Tchad : taux TVA général 18% (CGI 2016, Article 238(1))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "238" in standard["legal_reference"]


def test_tcd_vat_zero_rated_exports():
    """Taux zéro sur exportations (Art. 238(1)2), soumis à conditions douanières."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = next(r for r in data["vat_zero_rated"])
    assert zero["rate"] == "0%"
    assert zero["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "238" in zero["legal_reference"]
    assert zero["hs_codes_explicit"] == []


def test_tcd_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    assert used_ids <= registered_ids


def test_tcd_archived_cgi_hash_matches_inventory():
    """Le CGI 2016 archivé correspond au SHA-256 déclaré dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "TCD-AFRICALAWS-CGI-2016")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2016 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_tcd_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "TCD"
    assert len(data["sources"]) >= 1
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_tcd_inventory_csv_structure():
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


def test_tcd_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "TCD"
    assert "vat_rates" in data
    assert "vat_zero_rated" in data


def test_tcd_not_registered_as_supported_jurisdiction():
    """Garde-fou : TCD n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "TCD" not in SUPPORTED_JURISDICTIONS


def test_tcd_has_no_fabricated_afcfta_offer():
    """Garde-fou : TCD n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "TCD" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("TCD")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_tcd_no_excise_or_levy_data_in_this_cycle():
    """Collecte délibérément incomplète : pas d'accises, pas de prélèvements."""
    assert not (_DATA_DIR / "excise_measures.json").exists()
    assert not (_DATA_DIR / "import_levies.json").exists()


def test_tcd_readme_documents_incomplete_status():
    """README.md documente le statut de collecte incomplète."""
    readme = (_SOURCES_DIR / "README.md").read_text(encoding="utf-8")
    assert "TEC CEMAC" in readme or "tec cemac" in readme.lower()
    assert "non confirmé" in readme or "not confirmed" in readme.lower()
