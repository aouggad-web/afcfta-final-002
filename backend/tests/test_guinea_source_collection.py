"""
Vérifications d'intégrité de la collecte Guinée (UEMOA, lot 3) :
TVA et accises sur la production intérieure, vérifiées sur le Code Général
des Impôts (édition 2022, amendée par la loi de finances 2023), archivé et
haché.

Collecte délibérément incomplète : accises à l'importation renvoient au
Tarif des Douanes (Art. 435-II), non archivé dans ce cycle ; TVA taux
réduit/exonérations détaillées non extraites. GIN n'est donc pas
enregistrée dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY.
Voir data/sources/guinea/README.md.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "guinea"
_SOURCES_DIR = _ROOT / "data" / "sources" / "guinea"


def test_gin_vat_standard_rate():
    """Guinée : taux standard 18% (CGI, Article 373-I)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "373" in standard["legal_reference"]


def test_gin_vat_zero_rated_exports():
    """Guinée : exportations directes taux zéro (Art. 373-II-1)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero_rated = data["vat_zero_rated"]
    exports = next((r for r in zero_rated if "EXPORTS" in r["record_id"]), None)
    assert exports is not None
    assert exports["rate"] == "0%"
    assert exports["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_gin_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    used_ids |= {r["source_id"] for r in vat.get("vat_exemptions", [])}
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    used_ids |= {r["source_id"] for r in excise}
    assert used_ids <= registered_ids


def test_gin_archived_cgi_hash_matches_inventory():
    """Le CGI 2022/2023 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "GIN-DGI-CGI-2022-2023")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2022/2023 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_gin_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "GIN"
    assert len(data["sources"]) >= 1
    for source in data["sources"]:
        assert "source_id" in source
        assert "verification_status" in source


def test_gin_inventory_csv_structure():
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


def test_gin_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "GIN"
    assert "vat_rates" in data


def test_gin_excise_measures_exist():
    """excise_measures.json contient le barème complet de 16 catégories (Art. 435-I)."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 16, "Le barème Article 435-I compte 16 catégories de produits"
    for record in data:
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert record["source_id"] == "GIN-DGI-CGI-2022-2023"


def test_gin_excise_tobacco_rate():
    """Guinée : accise tabac 35% (Art. 435-I-a), le taux le plus élevé du barème."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    tobacco = next(r for r in data if "TOBACCO" in r["record_id"])
    assert tobacco["rate"] == 35
    assert all(r["rate"] <= 35 for r in data), "Le tabac doit porter le taux le plus élevé"


def test_gin_excise_zero_rated_categories():
    """Guinée : jus de fruits, eaux sucrées, boissons énergisantes et fruits/légumes importés à 0%."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    zero_rated_ids = {"FRUIT-JUICE", "SWEETENED-WATER", "ENERGY-DRINKS", "IMPORTED-FRUIT-VEG"}
    zero_records = [r for r in data if any(z in r["record_id"] for z in zero_rated_ids)]
    assert len(zero_records) == 4
    assert all(r["rate"] == 0 for r in zero_records)


def test_gin_not_registered_as_supported_jurisdiction():
    """Garde-fou : GIN n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "GIN" not in SUPPORTED_JURISDICTIONS


def test_gin_has_no_fabricated_afcfta_offer():
    """Garde-fou : GIN n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "GIN" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("GIN")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
