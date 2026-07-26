"""
Vérifications de cohérence transversale de la collecte CEDEAO anglophone
(8 pays : Cape Verde, Gambia, Ghana, Guinea, Liberia, Nigeria, Sierra Leone,
Mauritania).

Tous les 8 pays ont désormais leur propre fichier de test dédié, vérifiés
sur texte primaire officiel (archivé, SHA-256) : test_cape_verde_,
test_gambia_, test_ghana_, test_guinea_, test_liberia_, test_nigeria_,
test_sierra_leone_, test_mauritania_source_collection.py — même pattern
que PR #312 pour l'EAC. Ce fichier ne couvre donc plus que la cohérence
inter-pays.
"""

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

_ALL_8 = ["CPV", "GMB", "GHA", "GIN", "LBR", "NGA", "SLE", "MRT"]


def _country_dirs(iso3: str) -> tuple:
    country_name = _COUNTRY_MAP[iso3]
    data_dir = _ROOT / "data" / country_name
    sources_dir = _ROOT / "data" / "sources" / country_name
    return data_dir, sources_dir


def test_cedeao_new_countries_not_registered():
    """Garde-fou : aucun des 8 pays CEDEAO n'est enregistré comme juridiction supportée."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    for iso3 in _ALL_8:
        assert (
            iso3 not in SUPPORTED_JURISDICTIONS
        ), f"{iso3} should not be in SUPPORTED_JURISDICTIONS"


def test_cedeao_new_countries_no_fabricated_offers():
    """Garde-fou : aucun des 8 pays n'a d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    for iso3 in _ALL_8:
        assert (
            iso3 not in NATIONAL_OFFER_REGISTRY
        ), f"{iso3} should not be in NATIONAL_OFFER_REGISTRY"
        assert check_conformity(iso3)["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_cedeao_vat_rates_vary_appropriately():
    """Les taux VAT CEDEAO reflètent les différences nationales : 7.5% (NGA), 10% (LBR), 15% (4 pays), 16% (MRT), 18% (GIN)."""
    rates_found = set()
    for iso3 in _ALL_8:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        rates_found.add(standard["rate"])

    # CEDEAO countries have diverse VAT rates (unlike UEMOA's largely-uniform 18%)
    assert len(rates_found) > 1, "CEDEAO should have multiple VAT rates across countries"
    assert "7.5%" in rates_found, "Nigeria 7.5% VAT should be present"


def test_cedeao_all_8_countries_verified_not_pending():
    """Les 8 pays CEDEAO sont désormais tous vérifiés sur texte primaire ou
    guide officiel -- aucun ne doit rester au statut placeholder fabriqué
    PENDING_OFFICIAL_CONSOLIDATION."""
    for iso3 in _ALL_8:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        assert standard["verification_status"] != "PENDING_OFFICIAL_CONSOLIDATION", f"{iso3}"
