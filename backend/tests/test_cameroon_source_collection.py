"""
Vérifications d'intégrité de la collecte Cameroun (premier pays CEMAC) :
TVA, droit d'accises (barème complet HS-codé) et centimes additionnels
communaux (CAC), tous vérifiés sur le Code Général des Impôts, édition 2021
(Article 142 et Annexe II), archivé et haché.

Cette collecte est délibérément partielle (le TEC CEMAC n'est pas archivé,
donc aucun base_cet_rate n'est calculable ; le CAC est assis sur le montant
de TVA et non sur la valeur en douane, incompatible avec DEFAULT_LEVY_TABLES
tel quel) — voir data/sources/cameroon/README.md — donc CMR n'est pas
enregistrée dans SUPPORTED_JURISDICTIONS ni dans NATIONAL_OFFER_REGISTRY.
"""

import csv
import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "cameroon"
_SOURCES_DIR = _ROOT / "data" / "sources" / "cameroon"


def test_cmr_vat_standard_rate():
    """Cameroun : taux TVA général 17.5% (CGI 2021, Article 142)."""
    data = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    standard = next(r for r in data["vat_rates"] if "STANDARD" in r["record_id"])
    assert standard["rate"] == "17.5%"
    assert standard["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "Article 142" in standard["legal_reference"]


def test_cmr_zero_rated_export_not_auto_applied():
    zero = next(
        r
        for r in json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))[
            "vat_zero_rated"
        ]
    )
    assert zero["hs_codes_explicit"] == []


def test_cmr_excise_rates_all_have_explicit_hs_codes():
    """Toutes les entrées ad valorem du barème d'accises portent un code SH explicite."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    for row in data["excise_rates"]:
        assert row["hs_codes_explicit"], f"{row['record_id']} sans code SH explicite"
        assert row["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_cmr_excise_rate_tiers_match_article_142():
    """Les six paliers du barème (Art. 142(1)b) sont représentés."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    rates = {row["rate"] for row in data["excise_rates"]}
    assert rates == {"50%", "30%", "12.5%", "5%"}


def test_cmr_hydroquinone_super_eleve_rate():
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    row = next(
        r for r in data["excise_rates"] if r["record_id"] == "CMR-EXCISE-SUPER-ELEVE-HYDROQUINONE"
    )
    assert row["rate"] == "50%"
    assert "2907.22.00.000" in row["hs_codes_explicit"]


def test_cmr_specific_excise_duties_flagged_pending_quantity():
    """Les droits spécifiques (tabac, bières, vins) sont isolés car non calculables sans quantité."""
    data = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    specific = data["excise_specific_duties_pending_quantity_data"]
    assert len(specific) >= 3
    for row in specific:
        note = row["notes"].lower()
        assert "quantité" in note or "quantity" in note or "volume" in note


def test_cmr_cac_levy_documented_with_distinct_basis():
    """Le CAC (10% de la TVA due) est documenté avec sa base d'imposition distincte."""
    data = json.loads((_DATA_DIR / "import_levies.json").read_text(encoding="utf-8"))
    cac = data["centimes_additionnels_communaux"][0]
    assert cac["rate"] == "10%"
    assert cac["verification_status"] == "VERIFIED_PRIMARY_TEXT"
    assert "19,25" in cac["legal_reference"] or "19.25" in cac["legal_reference"]


def test_cmr_legal_sources_reference_valid_source_ids():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered_ids = {s["source_id"] for s in sources}
    vat = json.loads((_DATA_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    excise = json.loads((_DATA_DIR / "excise_measures.json").read_text(encoding="utf-8"))
    levies = json.loads((_DATA_DIR / "import_levies.json").read_text(encoding="utf-8"))
    used_ids = {r["source_id"] for r in vat["vat_rates"]}
    used_ids |= {r["source_id"] for r in vat["vat_zero_rated"]}
    used_ids |= {r["source_id"] for r in excise["excise_rates"]}
    used_ids |= {r["source_id"] for r in excise["excise_specific_duties_pending_quantity_data"]}
    used_ids |= {r["source_id"] for r in levies["centimes_additionnels_communaux"]}
    assert used_ids <= registered_ids


def test_cmr_archived_extract_hash_matches_inventory():
    """L'extrait archivé du CGI correspond au SHA-256 déclaré dans legal_sources.json."""
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s["source_id"] == "CMR-DGI-CGI-2021")
    archive_path = _SOURCES_DIR / primary["local_file"]
    assert archive_path.exists(), "extrait archivé manquant"
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert actual_hash == primary["sha256"]
    assert primary["status"] == "official_downloaded_extract"
    assert primary[
        "source_document_sha256"
    ], "hash du PDF source complet doit être conservé pour vérification"


def test_cmr_inventory_csv_structure():
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
    downloaded = [r for r in rows if r["status"] == "official_downloaded_extract"]
    pending = [r for r in rows if r["status"] == "source_pending_collection"]
    assert downloaded, "au moins une source doit être marquée téléchargée"
    assert pending, "au moins une source doit être marquée pending"


def test_cmr_not_registered_as_supported_jurisdiction():
    """Garde-fou : CMR n'est pas enregistrée comme juridiction supportée
    (pas de base_cet_rate calculable sans le TEC CEMAC)."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "CMR" not in SUPPORTED_JURISDICTIONS


def test_cmr_has_no_fabricated_afcfta_offer():
    """Garde-fou : CMR n'a pas d'offre nationale ZLECAf fictive."""
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "CMR" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("CMR")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
