"""
Vérifications d'intégrité de la collecte RDC (République Démocratique du Congo) :
source primaire archivée et hachée (Ordonnance-loi n° 10/001 du 20 août 2010,
Article 35 — TVA 16%), collectée via LEGANET.CD. RDC a rejoint l'EAC en 2022 et
applique le CET EAC déjà archivé pour le Kenya.

Cette collecte est délibérément partielle (TVA seule ; accises, prélèvements et
offre ZLECAf nationale non collectés) — voir data/sources/drc/README.md — donc
COD n'est pas enregistrée dans SUPPORTED_JURISDICTIONS ni dans
NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "drc"
_SOURCES_DIR = _ROOT / "data" / "sources" / "drc"


def test_cod_vat_measures_standard_rate():
    """RDC : taux VAT standard 16% (Ordonnance-loi 10/001/2010, Article 35)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "16%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Article 35" in standard["legal_reference"]


def test_cod_zero_rated_export_not_auto_applied():
    """Le taux zéro export n'a pas de code SH explicite : jamais auto-appliqué."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = data["vat_zero_rated"][0]
    assert zero["hs_codes_explicit"] == []


def test_cod_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    vat_source_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_cod_archived_source_hash_matches_inventory():
    """Le fichier archivé de l'Ordonnance-loi TVA correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "COD-LEGANET-OL-10-001-2010-TVA")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "archive HTML manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]
    assert primary["status"] == "official_downloaded"


def test_cod_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises, au moins une source téléchargée et une pending."""
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
    downloaded = [r for r in rows if r["status"] == "official_downloaded"]
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert downloaded, "au moins une source doit être marquée téléchargée"
    assert pending, "au moins une source doit être marquée pending"


def test_cod_not_registered_as_supported_jurisdiction():
    """Garde-fou : COD n'est pas enregistrée comme juridiction supportée
    (excise_measures.json et import_levies.json manquants)."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "COD" not in SUPPORTED_JURISDICTIONS


def test_cod_has_no_fabricated_afcfta_offer():
    """Garde-fou : COD n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "COD" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("COD")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
