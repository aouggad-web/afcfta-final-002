"""
Vérifications d'intégrité de la collecte Niger (UEMOA, lot 2) :
TVA et accises, vérifiées sur le Code Général des Impôts 2023 (édition consolidée),
archivé et haché. Taux standard 19% (Art. 226) + accises représentatives
(bière, cigarettes, carburants).

Collecte délibérément incomplète : taux réduit non extrait; droits complémentaires
(PCS, prélèvements) déférés.
NER n'est donc pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY. Voir data/sources/niger/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "niger"
_SOURCES_DIR = _ROOT / "data" / "sources" / "niger"


def test_ner_vat_standard_rate():
    """Niger : taux standard 19% (CGI, Article 226)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next((r for r in data["vat_rates"] if "STANDARD" in r["record_id"]), None)
    assert standard is not None, "Taux standard 19% manquant"
    assert standard["rate"] == "19%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "226" in standard["legal_reference"]


def test_ner_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_ner_archived_cgi_hash_matches_inventory():
    """Le CGI 2023 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "NER-DGI-CGI-2023")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2023 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_ner_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "NER"
    assert len(data["sources"]) >= 1


def test_ner_inventory_csv_structure():
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


def test_ner_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "NER"
    assert "vat_rates" in data


def test_ner_not_registered_as_supported_jurisdiction():
    """Garde-fou : NER n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "NER" not in SUPPORTED_JURISDICTIONS


def test_ner_has_no_fabricated_afcfta_offer():
    """Garde-fou : NER n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "NER" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("NER")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_ner_excise_measures_exist():
    """excise_measures.json existe et contient accises représentatives."""
    excise_path = _DATA_DIR / "excise_measures.json"
    assert excise_path.exists(), "excise_measures.json manquant"
    data = json.loads(excise_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 4, "Au minimum 4 lignes accise (bière, cigarettes, essence, gazole)"


def test_ner_excise_cigarettes_rate():
    """Niger : accise cigarettes 48%."""
    excise_path = _DATA_DIR / "excise_measures.json"
    data = json.loads(excise_path.read_text(encoding="utf-8"))
    cigarettes = next((r for r in data if "CIGARETTES" in r["record_id"]), None)
    assert cigarettes is not None, "Accise cigarettes manquante"
    assert cigarettes["rate"] == 48
    assert cigarettes["verification_status"] == "PENDING_COLLECTION"


def test_ner_excise_fuel_rates():
    """Niger : accises carburants essence 42% / gazole 28%."""
    excise_path = _DATA_DIR / "excise_measures.json"
    data = json.loads(excise_path.read_text(encoding="utf-8"))
    gasoline = next((r for r in data if "GASOLINE" in r["record_id"]), None)
    diesel = next((r for r in data if "DIESEL" in r["record_id"]), None)
    assert gasoline is not None
    assert diesel is not None
    assert gasoline["rate"] == 42
    assert diesel["rate"] == 28
