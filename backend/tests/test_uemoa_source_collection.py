"""
Vérifications d'intégrité de la collecte UEMOA (Sénégal, Bénin, Mali) :
sources localisées, taux de TVA enregistrés, structure d'inventaire.
Cette collecte est délibérément partielle (VAT seule, offres ZLECAf non ingérées
et pas encore localisées au niveau des schémas d'offre nationale par HS10) — voir
data/sources/{sen,ben,mli}/README.md — donc SEN/BEN/MLI ne sont pas enregistrées
dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY : ces tests
vérifient les données collectées elles-mêmes, pas un calcul de bout en bout.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_COUNTRY_MAP = {
    "SEN": "senegal",
    "BEN": "benin",
    "MLI": "mali",
}


def _country_dirs(iso3: str) -> tuple:
    country_name = _COUNTRY_MAP[iso3]
    data_dir = _ROOT / "data" / country_name
    sources_dir = _ROOT / "data" / "sources" / country_name
    return data_dir, sources_dir


# ============================================================================
# Senegal (SEN)
# ============================================================================


def test_sen_vat_measures_standard_rate():
    """Sénégal : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("SEN")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_sen_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("SEN")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_sen_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("SEN")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_sen_not_registered_as_supported_jurisdiction():
    """Garde-fou : SEN n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "SEN" not in SUPPORTED_JURISDICTIONS


def test_sen_has_no_fabricated_afcfta_offer():
    """Garde-fou : SEN n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "SEN" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("SEN")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Benin (BEN)
# ============================================================================


def test_ben_vat_measures_standard_rate():
    """Bénin : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("BEN")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_ben_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("BEN")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_ben_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("BEN")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_ben_not_registered_as_supported_jurisdiction():
    """Garde-fou : BEN n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "BEN" not in SUPPORTED_JURISDICTIONS


def test_ben_has_no_fabricated_afcfta_offer():
    """Garde-fou : BEN n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "BEN" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("BEN")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Mali (MLI)
# ============================================================================


def test_mli_vat_measures_standard_rate():
    """Mali : taux VAT standard 18%."""
    data_dir, _ = _country_dirs("MLI")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "18%"
    assert standard["legal_status"] == "IN_FORCE_AS_OF_CONSOLIDATION"
    assert standard["source_id"]
    assert standard["legal_reference"]


def test_mli_legal_sources_reference_valid_source_ids():
    """Les source_id cités en VAT measures doivent être dans le registre des sources."""
    data_dir, _ = _country_dirs("MLI")
    sources = json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    vat_source_ids = {r["source_id"] for r in vat["vat_rates"]}
    registered_ids = {s["source_id"] for s in sources}
    assert vat_source_ids <= registered_ids


def test_mli_inventory_csv_structure():
    """Inventaire CSV conforme : colonnes requises et statut pending."""
    _, sources_dir = _country_dirs("MLI")
    with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_columns = {
        "id", "institution", "title", "legal_date", "accessed_at", "url",
        "local_file", "sha256", "coverage", "status", "notes",
    }
    assert required_columns <= set(rows[0].keys())
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert pending, "au moins une source doit être marquée pending"


def test_mli_not_registered_as_supported_jurisdiction():
    """Garde-fou : MLI n'est pas enregistrée comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "MLI" not in SUPPORTED_JURISDICTIONS


def test_mli_has_no_fabricated_afcfta_offer():
    """Garde-fou : MLI n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity
    assert "MLI" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("MLI")["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Cross-country consistency
# ============================================================================


def test_uemoa_trio_all_have_18_percent_vat():
    """Les trois pays UEMOA (SEN, BEN, MLI) ont tous 18% de TVA (harmonisation)."""
    for iso3 in ["SEN", "BEN", "MLI"]:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        assert standard["rate"] == "18%", f"{iso3}: taux VAT != 18%"


def test_uemoa_all_pending_collection_status():
    """Tous les pays UEMOA commencent en statut PENDING_COLLECTION."""
    for iso3 in ["SEN", "BEN", "MLI"]:
        _, sources_dir = _country_dirs(iso3)
        with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        pending = [r for r in rows if r["status"] == "source_pending_collection"]
        assert len(pending) > 0, f"{iso3}: aucune source pending trouvée"
