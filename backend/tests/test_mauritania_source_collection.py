"""
Vérifications d'intégrité de la collecte Mauritanie (CEDEAO, lot 3) :
TVA et taxe de consommation (équivalent accises), vérifiées sur le Code
Général des Impôts (version officielle janvier 2023, Loi n°2019-018 du
29 avril 2019), archivé et haché.

Corrige une affirmation non vérifiée d'une source secondaire (taux TVA 18%
sur produits pétroliers/téléphonie) — absente du texte primaire (Article
230), donc non incluse. Voir data/sources/mauritania/README.md.

Collecte délibérément incomplète : TOF, taxe sur les assurances, taxe de
circulation sur les viandes non archivées. MRT n'est donc pas enregistrée
dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "mauritania"
_SOURCES_DIR = _ROOT / "data" / "sources" / "mauritania"


def test_mrt_vat_standard_rate():
    """Mauritanie : taux standard 16% (CGI, Article 230)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "16%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "230" in standard["legal_reference"]


def test_mrt_vat_zero_rated_exports():
    """Mauritanie : exportations taux zéro (Art. 230-2)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    exports = next(r for r in data["vat_zero_rated"] if "EXPORTS" in r["record_id"])
    assert exports["rate"] == "0%"
    assert exports["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_mrt_no_unverified_18pct_rate():
    """Garde-fou sincérité : pas de taux 18% fabriqué (produits pétroliers/téléphonie non vérifié sur texte primaire)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    all_rates = {r["rate"] for r in data["vat_rates"]}
    all_rates |= {r["rate"] for r in data.get("vat_zero_rated", [])}
    all_rates |= {r["rate"] for r in data.get("vat_exemptions", [])}
    assert "18%" not in all_rates


def test_mrt_legal_sources_reference_valid_source_ids():
    """Tous les source_id utilisés sont déclarés dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat.get("vat_zero_rated", [])}
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    used_ids |= {r["source_id"] for r in excise["excise_rates"]}
    assert used_ids <= registered_ids


def test_mrt_archived_cgi_hash_matches_inventory():
    """Le CGI 2023 archivé correspond au SHA-256 déclaré."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "MRT-DGI-CGI-2023")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "CGI 2023 archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]


def test_mrt_legal_sources_structure():
    """legal_sources.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "MRT"
    assert len(data["sources"]) >= 1


def test_mrt_inventory_csv_structure():
    """inventory.csv possède les colonnes requises."""
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


def test_mrt_vat_measures_schema():
    """vat_measures.json respecte le schéma."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["country"] == "MRT"
    assert "vat_rates" in data


def test_mrt_excise_measures_exist():
    """excise_measures.json contient le barème de la taxe de consommation (10 catégories, 22 lignes)."""
    wrapper = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    assert wrapper["schema_version"] == "1.0"
    assert wrapper["country"] == "MRT"
    data = wrapper["excise_rates"]
    assert isinstance(data, list)
    assert (
        len(data) == 22
    ), "Barème Article 263 : 8 lignes pétrole + 4 alcools + tabac + eaux + 3 laitiers + fer + ciment + plastique + tel-carte + tel-portable"
    for record in data:
        assert record["verification_status"] == "VERIFIED_PRIMARY_TEXT"
        assert record["source_id"] == "MRT-DGI-CGI-2023"


def test_mrt_excise_spirits_highest_rate():
    """Mauritanie : spiritueux (whisky/vodka/rhum/gin) portent le taux le plus élevé du barème (294%)."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))[
        "excise_rates"
    ]
    spirits = next(r for r in data if "SPIRITS" in r["record_id"])
    assert spirits["rate"] == 294
    ad_valorem_rates = [r["rate"] for r in data if "percentage" in r["rate_basis"]]
    assert spirits["rate"] == max(ad_valorem_rates)


def test_mrt_excise_hs_codes_for_dairy_and_construction():
    """Mauritanie : produits laitiers, fer à béton, ciment, téléphonie portent des codes SH explicites."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))[
        "excise_rates"
    ]
    rebar = next(r for r in data if "REBAR" in r["record_id"])
    cement = next(r for r in data if "CEMENT" in r["record_id"])
    uht_milk = next(r for r in data if "UHT-MILK" in r["record_id"])
    assert rebar["hs_codes_explicit"] == ["7214.20.00.10", "7214.20.00.90"]
    assert cement["hs_codes_explicit"] == ["2523.10", "2523.90"]
    assert uht_milk["hs_codes_explicit"] == ["0401"]


def test_mrt_excise_specific_duty_petroleum():
    """Mauritanie : les produits pétroliers sont taxés en droits spécifiques (Ouguiya/litre), pas ad valorem."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))[
        "excise_rates"
    ]
    petrol = next(r for r in data if "PETROL-REGULAR" in r["record_id"])
    assert "Ouguiya per liter" in petrol["rate_basis"]
    assert petrol["rate"] == 5.7


def test_mrt_not_registered_as_supported_jurisdiction():
    """Garde-fou : MRT n'est pas enregistrée comme juridiction supportée."""
    pytest = __import__("pytest")
    national_legal_calculation_service = pytest.importorskip(
        "services.national_legal_calculation_service"
    )
    SUPPORTED_JURISDICTIONS = national_legal_calculation_service.SUPPORTED_JURISDICTIONS
    assert "MRT" not in SUPPORTED_JURISDICTIONS


def test_mrt_has_no_fabricated_afcfta_offer():
    """Garde-fou : MRT n'a pas d'offre nationale ZLECAf fictive."""
    pytest = __import__("pytest")
    afcfta_national_offers = pytest.importorskip("etl.afcfta_national_offers")
    NATIONAL_OFFER_REGISTRY = afcfta_national_offers.NATIONAL_OFFER_REGISTRY
    check_conformity = afcfta_national_offers.check_conformity

    assert "MRT" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("MRT")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
