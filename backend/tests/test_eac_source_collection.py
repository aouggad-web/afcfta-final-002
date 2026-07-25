"""
Vérifications d'intégrité de la collecte EAC (Tanzanie, Ouganda, Rwanda) :
sources localisées, taux de TVA enregistrés, structure d'inventaire.
Cette collecte est délibérément partielle (TVA seule, offres ZLECAf non ingérées
et pas encore localisées au niveau des schémas d'offre nationale par HS10) — voir
data/sources/{tza,uga,rwa}/README.md — donc TZA/UGA/RWA ne sont pas enregistrées
dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY : ces tests
vérifient les données collectées elles-mêmes, pas un calcul de bout en bout.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_COUNTRY_MAP = {
    "TZA": "tanzania",
    "UGA": "uganda",
    "RWA": "rwanda",
}


def _country_dirs(iso3: str) -> tuple:
    country_name = _COUNTRY_MAP[iso3]
    data_dir = _ROOT / "data" / country_name
    sources_dir = _ROOT / "data" / "sources" / country_name
    return data_dir, sources_dir


# ============================================================================
# Tanzania (TZA)
# ============================================================================


def test_tza_vat_measures_standard_rate():
    """Tanzanie : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("TZA")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_tza_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("TZA")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_tza_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("TZA")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_tza_not_registered_as_supported_jurisdiction():
    """Garde-fou : TZA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "TZA" not in SUPPORTED_JURISDICTIONS


def test_tza_has_no_fabricated_afcfta_offer():
    """Garde-fou : TZA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "TZA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("TZA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Uganda (UGA)
# ============================================================================


def test_uga_vat_measures_standard_rate():
    """Ouganda : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("UGA")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_uga_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("UGA")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_uga_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("UGA")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_uga_not_registered_as_supported_jurisdiction():
    """Garde-fou : UGA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "UGA" not in SUPPORTED_JURISDICTIONS


def test_uga_has_no_fabricated_afcfta_offer():
    """Garde-fou : UGA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "UGA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("UGA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Rwanda (RWA)
# ============================================================================


def test_rwa_vat_measures_standard_rate():
    """Rwanda : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("RWA")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_rwa_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("RWA")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_rwa_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("RWA")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_rwa_not_registered_as_supported_jurisdiction():
    """Garde-fou : RWA n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "RWA" not in SUPPORTED_JURISDICTIONS


def test_rwa_has_no_fabricated_afcfta_offer():
    """Garde-fou : RWA n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "RWA" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("RWA")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Cross-country consistency
# ============================================================================


def test_eac_trio_all_have_18_percent_vat():
    """Les trois pays EAC (TZA, UGA, RWA) ont tous 18% de TVA."""
    for iso3 in ["TZA", "UGA", "RWA"]:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        assert standard["rate"] == "18%", f"{iso3}: taux VAT != 18%"


def test_eac_all_pending_collection_status():
    """Tous les pays EAC commencent en statut PENDING_COLLECTION."""
    for iso3 in ["TZA", "UGA", "RWA"]:
        _, sources_dir = _country_dirs(iso3)
        with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        pending = [r for r in rows if r["status"] == "source_pending_collection"]
        assert len(pending) > 0, f"{iso3}: aucune source pending trouvée"
