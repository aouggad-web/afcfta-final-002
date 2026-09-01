"""
Vérifications d'intégrité de la collecte CEDEAO (8 nouveaux pays) :
Cape Verde, Gambia, Ghana, Guinea, Liberia, Nigeria, Sierra Leone, Mauritania.

Cape Verde, Guinea, Liberia, Sierra Leone et Mauritania ont depuis été vérifiés
sur texte primaire officiel (archivé, SHA-256) dans des fichiers de test dédiés
(test_cape_verde_source_collection.py, test_guinea_source_collection.py,
test_liberia_source_collection.py, test_sierra_leone_source_collection.py,
test_mauritania_source_collection.py) — même pattern que PR #312 pour l'EAC.
Ce fichier ne couvre donc plus que les 3 pays encore en collecte placeholder :
Gambia, Ghana, Nigeria — voir data/sources/{gmb,gha,nga}/README.md.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_COUNTRY_MAP = {
    "CPV": "cape-verde",
    "GMB": "gambia",
    "GHA": "ghana",
    "GIN": "guinea",
    "LBR": "liberia",
    "NGA": "nigeria",
    "SLE": "sierra-leone",
    "MRT": "mauritania",
}

_VAT_RATES = {
    "CPV": "15%",
    "GMB": "15%",
    "GHA": "15%",
    "GIN": "18%",
    "LBR": "10%",
    "NGA": "7.5%",
    "SLE": "15%",
    "MRT": "16%",
}


def _country_dirs(iso3: str) -> tuple:
    country_name = _COUNTRY_MAP[iso3]
    data_dir = _ROOT / "data" / country_name
    sources_dir = _ROOT / "data" / "sources" / country_name
    return data_dir, sources_dir


# ============================================================================
# Individual country tests (only countries still in placeholder collection —
# CPV/GIN/LBR/SLE/MRT have dedicated verified test files, see module docstring)
# ============================================================================


def test_gmb_vat_standard_rate():
    """Gambia : taux VAT standard 15%."""
    data_dir, _ = _country_dirs("GMB")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == _VAT_RATES["GMB"]


def test_gha_vat_standard_rate():
    """Ghana : taux VAT standard 15%."""
    data_dir, _ = _country_dirs("GHA")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == _VAT_RATES["GHA"]


def test_nga_vat_standard_rate():
    """Nigeria : taux VAT standard 7.5%."""
    data_dir, _ = _country_dirs("NGA")
    data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == _VAT_RATES["NGA"]


# ============================================================================
# Honesty guards (all 8 countries not registered)
# ============================================================================


def test_cedeao_new_countries_not_registered():
    """Garde-fou : aucun nouveau pays CEDEAO n'est enregistré comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    for iso3 in ["CPV", "GMB", "GHA", "GIN", "LBR", "NGA", "SLE", "MRT"]:
        assert (
            iso3 not in SUPPORTED_JURISDICTIONS
        ), f"{iso3} should not be in SUPPORTED_JURISDICTIONS"


def test_cedeao_new_countries_no_fabricated_offers():
    """Garde-fou : aucun nouveau pays n'a d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    for iso3 in ["CPV", "GMB", "GHA", "GIN", "LBR", "NGA", "SLE", "MRT"]:
        assert (
            iso3 not in NATIONAL_OFFER_REGISTRY
        ), f"{iso3} should not be in NATIONAL_OFFER_REGISTRY"
        assert check_conformity(iso3)["status"] == "NO_NATIONAL_OFFER_REGISTERED"


# ============================================================================
# Source structure validation (sample countries)
# ============================================================================


def test_cedeao_sample_inventory_structure():
    """Inventaire CSV conforme pour pays échantillon."""
    for iso3 in ["GHA", "NGA"]:  # Sample Ghana and Nigeria
        _, sources_dir = _country_dirs(iso3)
        with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
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
        assert required_columns <= set(rows[0].keys()), f"{iso3} inventory missing columns"
        pending = [r for r in rows if r["status"] == "source_pending_collection"]
        assert len(pending) > 0, f"{iso3} should have pending sources"


# ============================================================================
# Cross-country consistency
# ============================================================================


def test_cedeao_vat_rates_vary_appropriately():
    """Les taux VAT CEDEAO reflètent les différences nationales : 7.5% (NGA), 10% (LBR), 15% (4 pays), 16% (MRT), 18% (GIN)."""
    rates_found = set()
    for iso3 in ["CPV", "GMB", "GHA", "GIN", "LBR", "NGA", "SLE", "MRT"]:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        rates_found.add(standard["rate"])

    # CEDEAO countries have diverse VAT rates (unlike UEMOA's uniform 18%)
    assert len(rates_found) > 1, "CEDEAO should have multiple VAT rates across countries"
    assert "7.5%" in rates_found, "Nigeria 7.5% VAT should be present"


def test_cedeao_remaining_pending_collection():
    """Les 3 pays CEDEAO non encore vérifiés restent en statut PENDING_COLLECTION."""
    for iso3 in ["GMB", "GHA", "NGA"]:
        _, sources_dir = _country_dirs(iso3)
        with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        pending = [r for r in rows if r["status"] == "source_pending_collection"]
        assert len(pending) > 0, f"{iso3} should have at least one pending source"
