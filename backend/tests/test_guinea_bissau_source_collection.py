"""
Vérifications d'intégrité de la collecte Guinée-Bissau (UEMOA) : IVA
(import) vérifié sur la page officielle de l'Alfândegas -- 19% standard,
10% Annexe I, 0% export -- PAS le taux uniforme 18% supposé par
l'hypothèse d'harmonisation UEMOA. Corrige une collecte initiale fabriquée
(voir data/sources/guinea-bissau/README.md).
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "guinea-bissau"
_SOURCES_DIR = _ROOT / "data" / "sources" / "guinea-bissau"


def test_gnb_vat_standard_rate_is_19_not_18():
    """Guinée-Bissau : taux standard 19% (Código do IVA, Art. 18º-1) --
    garde-fou explicite contre l'hypothèse d'harmonisation UEMOA à 18%,
    fausse pour ce pays."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "19%"
    assert standard["rate"] != "18%"
    assert standard["verification_status"] == "VERIFIED_OFFICIAL_GUIDE"
    assert "18" in standard["legal_reference"]


def test_gnb_reduced_rate_annex1():
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    reduced = next(r for r in data["vat_rates"] if "REDUCED" in r["record_id"])
    assert reduced["rate"] == "10%"


def test_gnb_zero_rated_exports():
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    zero = data["vat_zero_rated"]
    assert zero
    assert zero[0]["rate"] == "0%"


def test_gnb_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    assert used_ids <= registered_ids


def test_gnb_archived_page_hash_matches_inventory():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "GNB-ALFANDEGAS-IVA-PAGE")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "Page Alfândegas archivée manquante"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]

    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    inventory_row = next(r for r in rows if r["id"] == "GNB-ALFANDEGAS-IVA-PAGE")
    assert inventory_row["sha256"] == primary["sha256"]


def test_gnb_commencement_date_flagged_as_secondary_corroboration():
    """Garde-fou de sincérité : l'entrée en vigueur (2025, distincte de
    l'adoption en 2022) doit être documentée comme corroborée par la presse,
    pas comme archivée depuis une source primaire directement récupérée."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    commencement = next(s for s in sources if s["source_id"] == "GNB-IVA-COMMENCEMENT-2025")
    assert commencement["status"] == "source_blocked"
    assert commencement["sha256"] is None


def test_gnb_no_fabricated_domain_in_urls():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    for s in sources:
        assert "impots.gnb" not in (s.get("url") or "")
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert "impots.gnb" not in (row.get("url") or "")


def test_gnb_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "GNB" not in SUPPORTED_JURISDICTIONS


def test_gnb_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "GNB" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("GNB")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
