"""
Vérifications d'intégrité de la collecte Tanzanie (EAC) : TVA (taux standard +
taux zéro exports) et accises partielles (6 lignes représentatives du Fourth
Schedule), vérifiées sur texte primaire, archivées et hachées.

Cette collecte corrige une passe antérieure fusionnée avec des références
légales incorrectes et des statuts VERIFIED_PARTIAL non conformes au schéma
(sha256 "pending_collection", verification_status "PENDING_OFFICIAL_
CONSOLIDATION"). Voir data/sources/tanzania/README.md.

Collecte délibérément incomplète : accises non exhaustives (Fourth Schedule
couvre des dizaines de positions SH), pas de Finance Act 2026, pas de TEC EAC
relié. TZA n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "tanzania"
_SOURCES_DIR = _ROOT / "data" / "sources" / "tanzania"


def test_tza_vat_standard_rate():
    """Tanzanie : taux TVA standard 18% (VAT Act 2014, Section 5(1))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "5" in standard["legal_reference"]


def test_tza_vat_zero_rated_exports():
    """Taux zéro sur exportations (Section 5(2) et Section 55)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = next(r for r in data["vat_zero_rated"])
    assert zero["rate"] == "0%"
    assert zero["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "55" in zero["legal_reference"]


def test_tza_excise_records_present_and_verified():
    """Au moins une ligne d'accise vérifiée sur texte primaire (Fourth Schedule)."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert len(data["excise_rates"]) >= 5
    for record in data["excise_rates"]:
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert "Fourth Schedule" in record["legal_reference"]


def test_tza_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés (TVA + accises) sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    used_ids |= {r["source_id"] for r in excise["excise_rates"]}
    assert used_ids <= registered_ids


def test_tza_archived_vat_act_hash_matches_inventory():
    """La VAT Act 2014 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "TZA-TANZLII-VAT-ACT-2014")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "VAT Act 2014 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_tza_archived_excise_act_hash_matches_inventory():
    """L'Excise Act Cap.147 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "TZA-MOF-EXCISE-ACT-CAP147")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Excise Act Cap.147 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_tza_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "TZA"
    assert len(data["sources"]) >= 2
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_tza_inventory_csv_structure():
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


def test_tza_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "TZA"
    assert "vat_rates" in data
    assert "vat_zero_rated" in data


def test_tza_excise_measures_schema():
    """excise_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "TZA"
    assert "excise_rates" in data


def test_tza_not_registered_as_supported_jurisdiction():
    """Garde-fou : TZA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "TZA" not in SUPPORTED_JURISDICTIONS


def test_tza_has_no_fabricated_afcfta_offer():
    """Garde-fou : TZA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "TZA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("TZA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
