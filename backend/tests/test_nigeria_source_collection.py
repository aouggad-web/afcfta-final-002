"""
Vérifications d'intégrité de la collecte Nigeria (CEDEAO) : TVA seule,
vérifiée sur le Nigeria Tax Act, 2025 (Act No. 7) -- qui abroge et remplace
la Value Added Tax Act Cap V1 LFN 2004 à compter du 1er janvier 2026.
Corrige une collecte initiale fabriquée (voir data/sources/nigeria/README.md).
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "nigeria"
_SOURCES_DIR = _ROOT / "data" / "sources" / "nigeria"


def test_nga_vat_standard_rate_current_law():
    """Nigeria : taux standard 7.5% (Nigeria Tax Act 2025, Section 147), en vigueur."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(
        r
        for r in data["vat_rates"]
        if "STANDARD" in r["record_id"] and r["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    )
    assert standard["rate"] == "7.5%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Section 147" in standard["legal_reference"]
    assert standard["effective_from"] == "2026-01-01"


def test_nga_repealed_law_is_flagged_not_current():
    """Garde-fou : l'ancienne base légale (VAT Act 2004) doit être marquée REPEALED,
    jamais présentée comme le texte actuellement en vigueur."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    repealed = [r for r in data["vat_rates"] if r["legal_status"] == "REPEALED"]
    assert repealed, "l'ancienne loi doit être explicitement marquée REPEALED"
    assert repealed[0]["effective_to"] == "2025-12-31"


def test_nga_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    assert used_ids <= registered_ids


def test_nga_archived_gazette_hash_matches_inventory():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "NGA-NASS-TAX-ACT-2025")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Nigeria Tax Act 2025 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "NGA-NASS-TAX-ACT-2025")
    assert inventory_row["sha256"] == primary["sha256"]


def test_nga_no_fabricated_domain_remains():
    for path in (_DATA_DIR / "legal_sources.json", _SOURCES_DIR / "inventory.csv"):
        text = path.read_text(encoding="utf-8")
        assert "impots.nga" not in text


def test_nga_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "NGA" not in SUPPORTED_JURISDICTIONS


def test_nga_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "NGA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("NGA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
