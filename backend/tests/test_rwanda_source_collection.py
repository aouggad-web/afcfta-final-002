"""
Vérifications d'intégrité de la collecte Rwanda (EAC) : TVA (taux standard +
taux zéro, 3 postes) et accises (7 lignes représentatives de l'Annexe de la
loi n°011/2025), vérifiées sur texte primaire, archivées et hachées.

Cette collecte corrige une passe antérieure fusionnée avec une référence
légale incorrecte ("Value Added Tax Law 2018, Law No. 28/2018 of 13/02/2018"
— la loi réellement en vigueur est la Loi n°049/2023 du 05/09/2023) et des
statuts non conformes au schéma. Voir data/sources/rwanda/README.md.

RWA n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "rwanda"
_SOURCES_DIR = _ROOT / "data" / "sources" / "rwanda"


def test_rwa_vat_standard_rate():
    """Rwanda : taux TVA standard 18% (Loi n°049/2023, Article 4(b))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Article 4" in standard["legal_reference"]


def test_rwa_vat_zero_rated_exports_and_minerals():
    """Taux zéro : exportations biens/services et minerais vendus localement (Article 7)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero_records = data["vat_zero_rated"]
    assert len(zero_records) >= 3
    for record in zero_records:
        assert record["rate"] == "0%"
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert "Article 7" in record["legal_reference"]


def test_rwa_excise_records_present_and_verified():
    """Au moins 5 lignes d'accise vérifiées sur texte primaire (Annexe loi 011/2025)."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert len(data["excise_rates"]) >= 5
    for record in data["excise_rates"]:
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert "011/2025" in record["legal_reference"]


def test_rwa_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés (TVA + accises) sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    used_ids |= {r["source_id"] for r in excise["excise_rates"]}
    assert used_ids <= registered_ids


def test_rwa_archived_vat_law_hash_matches_inventory():
    """La Loi n°049/2023 archivée correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "RWA-RRA-LAW-049-2023-VAT")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Loi n°049/2023 archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_rwa_archived_excise_gazette_hash_matches_inventory():
    """Le Journal Officiel du 29/05/2025 (accises) archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "RWA-MININJUST-OG-2025-05-29")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Journal Officiel 29/05/2025 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_rwa_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "RWA"
    assert len(data["sources"]) >= 2
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_rwa_inventory_csv_structure():
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


def test_rwa_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "RWA"
    assert "vat_rates" in data
    assert "vat_zero_rated" in data


def test_rwa_excise_measures_schema():
    """excise_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "RWA"
    assert "excise_rates" in data


def test_rwa_not_registered_as_supported_jurisdiction():
    """Garde-fou : RWA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "RWA" not in SUPPORTED_JURISDICTIONS


def test_rwa_has_no_fabricated_afcfta_offer():
    """Garde-fou : RWA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "RWA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("RWA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
