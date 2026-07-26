"""
Vérifications d'intégrité de la collecte Togo (UEMOA) : TVA seule, taux
standard vérifié verbatim (Article 323 du CGI) via un bulletin officiel OTR.
Corrige une collecte initiale fabriquée (voir data/sources/togo/README.md).
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "togo"
_SOURCES_DIR = _ROOT / "data" / "sources" / "togo"


def test_tgo_vat_standard_rate():
    """Togo : taux standard 18% (CGI, Article 323)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "323" in standard["legal_reference"]


def test_tgo_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_tgo_archived_cahier_fiscal_hash_matches_inventory():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "TGO-OTR-CAHIER-FISCAL-2017")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Cahier Fiscal 2017 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "TGO-OTR-CAHIER-FISCAL-2017")
    assert inventory_row["sha256"] == primary["sha256"]


def test_tgo_scanned_pdf_honestly_flagged_not_extracted():
    """Garde-fou de sincérité : le CGI 2018 (scanné, sans OCR) ne doit jamais
    être déclaré avec un sha256 ou un statut 'downloaded' -- seulement
    signalé comme bloqué."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    scanned = next(s for s in sources if s["source_id"] == "TGO-CGI-2018-SCANNED-UNUSABLE")
    assert scanned["sha256"] is None
    assert scanned["local_file"] is None
    assert scanned["status"] == "source_blocked"


def test_tgo_no_fabricated_domain_in_urls():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    for s in sources:
        assert "impots.tgo" not in (s.get("url") or "")
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert "impots.tgo" not in (row.get("url") or "")


def test_tgo_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "TGO" not in SUPPORTED_JURISDICTIONS


def test_tgo_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "TGO" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("TGO")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
