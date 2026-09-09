"""
Vérifications d'intégrité de la collecte Liberia (CEDEAO, lot 3) :
Goods tax / services tax (équivalent TVA), vérifiées sur le Liberia Revenue
Code As Amended (consolidation 2020), archivé et haché.

Alerte sincérité : une source secondaire affirme un taux passé de 10% à 12%
en avril 2025, mais les amendements 2024/2025 sont des PDF scannés
inexploitables sans OCR (indisponible dans cet environnement) — même
blocage que le Togo. Les taux publiés restent donc ceux de 2020, avec
avertissement explicite sur chaque enregistrement. Voir
data/sources/liberia/README.md.

Collecte délibérément incomplète : barème détaillé des accises (Schedule I)
non trouvé dans le texte accessible. LBR n'est donc pas enregistrée dans
SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "liberia"
_SOURCES_DIR = _ROOT / "data" / "sources" / "liberia"


def test_lbr_goods_tax_standard_rate():
    """Liberia : taux standard goods tax 10% (Section 1000(b)(3), consolidation 2020)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "GOODS-TAX-STANDARD" in r["record_id"])
    assert standard["rate"] == "10%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "1000" in standard["legal_reference"]


def test_lbr_services_tax_standard_rate():
    """Liberia : taux standard services tax 10% (Section 1021(b)(1))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "SERVICES-TAX-STANDARD" in r["record_id"])
    assert standard["rate"] == "10%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_lbr_telecom_surtax():
    """Liberia : surtaxe télécommunications +5% (Section 1021(b)(2))."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    surtax = next(r for r in data["vat_rates"] if "TELECOM-SURTAX" in r["record_id"])
    assert surtax["rate"] == "5%"
    assert surtax["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_lbr_rate_records_flag_possible_supersession():
    """Garde-fou sincérité : chaque taux 2020 porte un avertissement explicite de risque d'obsolescence."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    for record in data["vat_rates"]:
        assert "possibly superseded" in record["legal_reference"].lower()


def test_lbr_unverified_amendments_not_used_as_source_for_rates():
    """Garde-fou sincérité : les amendements 2024/2025 (bloqués, non-OCR) ne sont source d'aucun taux publié."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_source_ids = {r["source_id"] for r in data["vat_rates"]}
    used_source_ids |= {r["source_id"] for r in data.get("vat_zero_rated", [])}
    assert "LBR-LRA-AMENDMENT-DEC2024" not in used_source_ids
    assert "LBR-LRA-AMENDMENT-DEC2025" not in used_source_ids


def test_lbr_blocked_sources_documented():
    """Les amendements bloqués (scannés, sans OCR) sont documentés avec status source_blocked."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    blocked = [s for s in sources if s["status"] == "source_blocked"]
    assert len(blocked) == 2
    for s in blocked:
        assert s["verification_status"] == "PENDING_COLLECTION"
        assert s["sha256"] is None


def test_lbr_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés dans vat_measures sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_lbr_archived_revenue_code_hash_matches_inventory():
    """Le Revenue Code 2020 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "LBR-LRA-REVENUE-CODE-2020")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Revenue Code 2020 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_lbr_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "LBR"
    assert len(data["sources"]) == 3


def test_lbr_inventory_csv_structure():
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
    assert len(rows) == 3


def test_lbr_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "LBR"
    assert "vat_rates" in data


def test_lbr_not_registered_as_supported_jurisdiction():
    """Garde-fou : LBR n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "LBR" not in SUPPORTED_JURISDICTIONS


def test_lbr_has_no_fabricated_afcfta_offer():
    """Garde-fou : LBR n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "LBR" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("LBR")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
