"""
Vérifications d'intégrité de la première collecte Afrique du Sud (ZAF) :
taux TVA standard et registre de sources. Cette collecte est délibérément
partielle (TVA seule, offre ZLECAf non ingérée) — voir
data/sources/south_africa/README.md — donc ZAF n'est pas enregistrée dans
SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY : ces tests
vérifient les données collectées elles-mêmes, pas un calcul de bout en bout.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_ZAF_DATA = _ROOT / "data" / "south_africa"
_ZAF_SOURCES = _ROOT / "data" / "sources" / "south_africa"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vat_measures_standard_rate_is_fifteen_percent():
    data = json.loads((_ZAF_DATA / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if r["record_id"].startswith("ZAF-VAT-RATE-STANDARD"))
    assert standard["rate"] == "15%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_legal_sources_reference_valid_source_ids():
    sources = json.loads((_ZAF_DATA / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((_ZAF_DATA / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids, "chaque source_id cité en données doit être dans le registre"


def test_archived_html_files_match_recorded_hashes():
    """Les deux archives HTML (petites, conservées telles quelles) doivent
    correspondre exactement au hash consigné dans le registre — détecte
    toute altération ou erreur de transcription."""
    sources = {
        s["source_id"]: s
        for s in json.loads((_ZAF_DATA / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    }
    html_files = {
        "ZAF-SARS-VAT-GUIDE-20260725": "sars-types-of-tax-vat.html",
        "ZAF-SARS-SCHEDULES-INDEX-20260725": "sars-schedules-to-customs-and-excise-act.html",
    }
    for source_id, filename in html_files.items():
        path = _ZAF_SOURCES / "official" / filename
        assert path.exists(), f"archive manquante : {path}"
        assert _sha256(path) == sources[source_id]["sha256"]


def test_afcfta_agreement_excerpt_exists_and_is_small():
    """Le PDF officiel (12 Mo) n'est pas archivé — seul un extrait de
    citation légale l'est, conformément à la politique de poids."""
    excerpt = _ZAF_SOURCES / "extracted" / "sars-schedule10-part8-afcfta-agreement-excerpt.txt"
    assert excerpt.exists()
    assert excerpt.stat().st_size < 20_000, "l'extrait doit rester une citation, pas le texte intégral"
    text = excerpt.read_text(encoding="utf-8")
    assert "1 January 2021" in text
    assert "AFRICAN CONTINENTAL FREE TRADE AREA" in text


def test_inventory_csv_has_required_columns_and_pending_row():
    with open(_ZAF_SOURCES / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "le barème ligne à ligne ZLECAf (Schedule 1 Part 1) doit être marqué PENDING, pas absent"


def test_zaf_is_not_registered_as_a_supported_jurisdiction_yet():
    """Garde-fou de sincérité : tant que la couche fiscale ZAF est
    incomplète (TVA seule, pas d'accises/prélèvements/offre ZLECAf), le
    calculateur ne doit pas prétendre servir un calcul vérifié pour ZAF."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "ZAF" not in SUPPORTED_JURISDICTIONS


def test_zaf_has_no_fabricated_afcfta_national_offer():
    """Garde-fou de sincérité : sans le barème Schedule 1 Part 1 ingéré,
    ZAF ne doit apparaître dans aucun registre d'offre nationale ZLECAf."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "ZAF" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("ZAF")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
