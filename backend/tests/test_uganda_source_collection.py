"""
Vérifications d'intégrité de la collecte Ouganda (EAC) : TVA — taux standard
délibérément NON enregistré (délégué à un arrêté ministériel non archivé),
seul le mécanisme de taux zéro est vérifié — et accises vérifiées (5 lignes
représentatives du Schedule 2).

Cette collecte corrige une passe antérieure fusionnée avec des références
légales fictives ("Value Added Tax Act 1997, Act No. 106 of 1997" — cette loi
n'existe pas ; la loi réelle est le Cap. 349 de 1996) et des statuts non
conformes au schéma. Voir data/sources/uganda/README.md.

UGA n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "uganda"
_SOURCES_DIR = _ROOT / "data" / "sources" / "uganda"


def test_uga_vat_standard_rate_not_verified():
    """Garde-fou : aucune entrée VAT-RATE-STANDARD (taux délégué à un arrêté ministériel non archivé)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["vat_rates"] == []


def test_uga_vat_zero_rated_exports():
    """Taux zéro sur exportations (Section 24(4), Third Schedule)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = next(r for r in data["vat_zero_rated"])
    assert zero["rate"] == "0%"
    assert zero["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "24" in zero["legal_reference"]


def test_uga_excise_records_present_and_verified():
    """Au moins 5 lignes d'accise vérifiées sur texte primaire (Schedule 2)."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert len(data["excise_rates"]) >= 5
    for record in data["excise_rates"]:
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert "Schedule 2" in record["legal_reference"]


def test_uga_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés (TVA + accises) sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_zero_rated"]}
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    used_ids |= {r["source_id"] for r in excise["excise_rates"]}
    assert used_ids <= registered_ids


def test_uga_archived_vat_act_hash_matches_inventory():
    """La VAT Act Cap.349 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "UGA-ULII-VAT-ACT-CAP349")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "VAT Act Cap.349 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_uga_archived_excise_act_hash_matches_inventory():
    """L'Excise Duty Act Cap.336 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "UGA-URA-EXCISE-DUTY-ACT-2014")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Excise Duty Act Cap.336 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_uga_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "UGA"
    assert len(data["sources"]) >= 2
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_uga_inventory_csv_structure():
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


def test_uga_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "UGA"
    assert "vat_rates" in data
    assert "vat_zero_rated" in data


def test_uga_excise_measures_schema():
    """excise_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "UGA"
    assert "excise_rates" in data


def test_uga_readme_documents_delegated_rate_gap():
    """README.md documente explicitement pourquoi le taux standard n'est pas enregistré."""
    readme = (_SOURCES_DIR / "README.md").read_text(encoding="utf-8")
    assert "78(2)" in readme
    assert "arrêté ministériel" in readme.lower() or "statutory order" in readme.lower()


def test_uga_not_registered_as_supported_jurisdiction():
    """Garde-fou : UGA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "UGA" not in SUPPORTED_JURISDICTIONS


def test_uga_has_no_fabricated_afcfta_offer():
    """Garde-fou : UGA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "UGA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("UGA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
