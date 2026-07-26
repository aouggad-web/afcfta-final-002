"""
Vérifications de cohérence transversale de la collecte UEMOA (8 pays :
Sénégal, Bénin, Mali, Côte d'Ivoire, Burkina Faso, Togo, Niger,
Guinée-Bissau).

Chaque pays a désormais son propre fichier de test dédié
(test_senegal_source_collection.py, test_benin_source_collection.py,
test_mali_source_collection.py, test_cote_d_ivoire_source_collection.py,
test_burkina_faso_source_collection.py, test_togo_source_collection.py,
test_niger_source_collection.py, test_guinea_bissau_source_collection.py)
— même pattern que PR #312 pour l'EAC et test_cedeao_source_collection.py
pour la CEDEAO anglophone. Ce fichier ne couvre donc plus que la cohérence
inter-pays.

Point important : l'UEMOA harmonise le Tarif Extérieur Commun, PAS
nécessairement le taux de TVA domestique de chaque État membre. Le Niger
(19%, Article 226 CGI) et la Guinée-Bissau (19%, Article 18º-1 du Código do
IVA) s'écartent tous deux du taux de 18% des six autres pays — vérifié sur
texte primaire dans les deux cas, pas une anomalie à corriger.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_COUNTRY_MAP = {
    "SEN": "senegal",
    "BEN": "benin",
    "MLI": "mali",
    "CIV": "cote-d-ivoire",
    "BFA": "burkina-faso",
    "TGO": "togo",
    "NER": "niger",
    "GNB": "guinea-bissau",
}

_ALL_8 = ["SEN", "BEN", "MLI", "CIV", "BFA", "TGO", "NER", "GNB"]

_EXPECTED_STANDARD_RATES = {
    "SEN": "18%",
    "BEN": "18%",
    "MLI": "18%",
    "CIV": "18%",
    "BFA": "18%",
    "TGO": "18%",
    "NER": "19%",
    "GNB": "19%",
}


def _country_dirs(iso3: str) -> tuple:
    country_name = _COUNTRY_MAP[iso3]
    data_dir = _ROOT / "data" / country_name
    sources_dir = _ROOT / "data" / "sources" / country_name
    return data_dir, sources_dir


def test_all_8_uemoa_countries_have_a_verified_standard_rate():
    """Chaque pays UEMOA a un taux standard vérifié sur texte primaire, dans
    la fourchette réelle observée (18% pour six pays, 19% pour NER et GNB —
    pas une harmonisation à 18% supposée par défaut)."""
    for iso3 in _ALL_8:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        assert standard["rate"] == _EXPECTED_STANDARD_RATES[iso3], f"{iso3}: taux VAT inattendu"
        assert standard["verification_status"] in (
            "VERIFIED_PRIMARY_TEXT",
            "VERIFIED_OFFICIAL_GUIDE",
            "VERIFIED_CONSOLIDATED_HTML",
        ), f"{iso3}: statut de vérification insuffisant"


def test_uemoa_rates_are_not_uniformly_18_percent():
    """Garde-fou de sincérité : au moins un pays doit s'écarter de 18% --
    si ce test échoue, quelqu'un a probablement réappliqué l'hypothèse
    d'harmonisation par défaut plutôt qu'un taux vérifié individuellement."""
    rates = set()
    for iso3 in _ALL_8:
        data_dir, _ = _country_dirs(iso3)
        data = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
        rates.add(standard["rate"])
    assert len(rates) > 1, "les 8 pays UEMOA ne devraient pas être uniformément à un seul taux"


def test_all_8_uemoa_countries_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    for iso3 in _ALL_8:
        assert (
            iso3 not in SUPPORTED_JURISDICTIONS
        ), f"{iso3} should not be in SUPPORTED_JURISDICTIONS"


def test_all_8_uemoa_countries_no_fabricated_offers():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    for iso3 in _ALL_8:
        assert (
            iso3 not in NATIONAL_OFFER_REGISTRY
        ), f"{iso3} should not be in NATIONAL_OFFER_REGISTRY"
        assert check_conformity(iso3)["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_all_8_uemoa_inventories_have_required_columns():
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
    for iso3 in _ALL_8:
        _, sources_dir = _country_dirs(iso3)
        with open(sources_dir / "inventory.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows, f"{iso3}: inventory.csv vide"
        assert required_columns <= set(rows[0].keys()), f"{iso3}: colonnes manquantes"
