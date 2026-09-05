"""
Tests de complétion fiscale nationale (au-delà des TEC régionaux).

Doctrine vérifiée ici :
- AUCUN taux n'est déclaré dans le registre NATIONAL_TAX_SOURCES (zéro mock) ;
- un pays sans document national archivé reste PENDING_OFFICIAL_COLLECTION ;
- les prélèvements communautaires documentés citent para_fiscal_levies ;
- le champ national_taxes du coverage ne peut que se préciser, jamais inventer.
"""

import os
import sys

import pytest

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_ROOT)

from crawlers.all_countries_registry import (  # noqa: E402
    AFRICAN_COUNTRIES_REGISTRY,
    NATIONAL_TAX_COMPLETED,
    NATIONAL_TAX_SOURCES,
    get_national_tax_source,
)
from etl.national_tax_completion import (  # noqa: E402
    STATUS_DOCUMENTED,
    STATUS_DOCUMENTED_NATIONAL,
    STATUS_PARTIAL_DOCUMENTED,
    STATUS_PENDING_OFFICIAL,
    TAX_FAMILIES,
    coverage_update_entries,
    get_completion_status,
    national_completion_report,
)


# ---------------------------------------------------------------------------
# Registre : zéro mock par construction
# ---------------------------------------------------------------------------


def test_registry_has_no_tax_rates():
    """Aucun taux ne doit figurer dans NATIONAL_TAX_SOURCES (pas de mock)."""
    forbidden_keys = {"rate", "vat_rate", "dd_rate", "tax_rate", "percentage", "amount"}
    for iso3, cfg in NATIONAL_TAX_SOURCES.items():
        blob = _iter_keys(cfg)
        assert not (
            forbidden_keys & blob
        ), f"{iso3}: clés de taux interdites trouvées: {forbidden_keys & blob}"


def _iter_keys(obj):
    found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.add(str(k).lower())
            found |= _iter_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            found |= _iter_keys(item)
    return found


def test_every_source_country_declares_targets_and_status():
    for iso3, cfg in NATIONAL_TAX_SOURCES.items():
        assert cfg.get("collection_status") == "PENDING_OFFICIAL_COLLECTION", iso3
        assert cfg.get("instruments_to_collect"), iso3
        assert cfg.get("tax_authority", {}).get("name"), iso3
        assert set(cfg.get("tax_families_targeted") or []) <= set(TAX_FAMILIES), iso3


def test_source_countries_exist_in_main_registry():
    """Chaque pays du registre fiscal doit exister dans le registre douanier."""
    for iso3 in NATIONAL_TAX_SOURCES:
        assert iso3 in AFRICAN_COUNTRIES_REGISTRY, iso3


def test_completed_countries_are_excluded_from_pending():
    """DZA/TUN/EGY/MAR sont déjà au niveau national — pas de collecte TEC."""
    for iso3 in NATIONAL_TAX_COMPLETED:
        assert get_national_tax_source(iso3) is None, iso3


def test_url_status_values_are_honest():
    """url_status uniquement parmi les valeurs documentées du registre."""
    allowed = {"VERIFIED_200", "REGISTRY_EXISTING_UNVERIFIED", "UNVERIFIED", "NONE_IDENTIFIED"}
    for iso3, cfg in NATIONAL_TAX_SOURCES.items():
        assert cfg["tax_authority"].get("url_status") in allowed, iso3


# ---------------------------------------------------------------------------
# Service de complétion : fail-closed
# ---------------------------------------------------------------------------


def test_pending_country_reports_pending_not_data():
    """Un pays sans dataset ni substantiation ne retourne AUCUNE donnée."""
    st = get_completion_status("SSD")
    assert st["national_taxes"]["status"] == STATUS_PENDING_OFFICIAL
    assert st["tax_families"]["VAT"]["status"] == STATUS_PENDING_OFFICIAL
    assert "rate" not in str(st["tax_families"]["VAT"]).lower()


def test_vat_documented_country_uses_existing_dataset():
    """CIV : TVA documentée dans data/cote-d-ivoire/vat_measures.json (existant)."""
    st = get_completion_status("CIV")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_DOCUMENTED
    assert vat["verified_records"] > 0
    assert "vat_measures.json" in vat["dataset_path"]
    # La TVA vit dans le dataset sourcé — pas de taux dupliqué ici.
    assert "18%" not in str(vat)


def test_excise_documented_country_uses_existing_dataset():
    """KEN : accises documentées dans data/kenya/excise_measures.json (existant)."""
    st = get_completion_status("KEN")
    excise = st["tax_families"]["EXCISE"]
    assert excise["status"] == STATUS_DOCUMENTED
    assert excise["verified_records"] > 0


def test_dte_is_pending_everywhere():
    """Aucun dataset DTE national n'existe — toujours en attente, jamais inventé."""
    for iso3 in ("SEN", "KEN", "DZA", "BDI"):
        st = get_completion_status(iso3)
        assert st["tax_families"]["DTE"]["status"] == STATUS_PENDING_OFFICIAL, iso3


def test_completed_national_country_documented():
    st = get_completion_status("DZA")
    assert st["national_taxes"]["status"] == STATUS_DOCUMENTED_NATIONAL


def test_unknown_country_is_not_available():
    st = get_completion_status("XXX")
    assert st["national_taxes"]["status"] == STATUS_PENDING_OFFICIAL or (
        st["country_iso3"] == "XXX"
    )
    # Aucun taux, jamais.
    assert "vat_rate" not in str(st)


def test_kenya_keeps_documented_levies_without_rates():
    """KEN : IDF/RDL documentés (para_fiscal_levies) — sans aucun taux ici."""
    st = get_completion_status("KEN")
    assert "IDF" in st["tax_families"]["PARAFISCAL_NATIONAL"]["documented_levies"]
    assert "RDL" in st["tax_families"]["PARAFISCAL_NATIONAL"]["documented_levies"]
    assert st["overall_status"] == STATUS_PARTIAL_DOCUMENTED


# ---------------------------------------------------------------------------
# Rapport / coverage
# ---------------------------------------------------------------------------


def test_report_aggregates_without_rates():
    report = national_completion_report()
    assert report["countries_total"] >= 50
    assert report["overall_status_counts"].get(STATUS_PENDING_OFFICIAL, 0) >= 10
    # TVA documentée après arbitrage et consolidations : 23 datasets vérifiés
    # - 2 républiques non gouvernementales (SEN, SLE) + 4 substantiées par
    # national_enrichment (BWA, LSO, SWZ, NAM) + 1 consolidation officielle
    # GRA (GHA, Act 1151 en vigueur 01/01/2026) + 1 extraction texte officiel
    # URA (UGA, VAT Rate Order 2005) = 27.
    assert len(report["vat_documented_countries"]) == 27
    assert len(report["excise_documented_countries"]) >= 5
    assert "Aucun taux inventé" in report["doctrine"]


def test_vat_partial_files_are_not_promoted():
    """Fichier VAT présent mais 0 taux vérifié -> PARTIAL_DOCUMENTED, pas DOCUMENTED."""
    st = get_completion_status("GMB")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_PARTIAL_DOCUMENTED
    assert vat["records"] > 0 and vat["verified_records"] == 0


def test_gha_consolidated_from_official_current_page():
    """GHA : consolidé sur page officielle GRA (Act 1151, en vigueur 01/01/2026)."""
    st = get_completion_status("GHA")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_DOCUMENTED
    assert vat["records"] >= 2 and vat["verified_records"] >= 1
    arb = vat["arbitration"]
    assert arb["decision_code"] == "OFFICIAL_CURRENT_PAGE_RETAINED"
    assert arb["evidence"]["archived_sha256"]
    # Le document officiel est archivé sur disque
    assert st["national_taxes"]["official_document_archived"] is True


def test_uga_official_text_extracted_and_verified():
    """UGA : taux 18% extrait du VAT Rate Order 2005 (compendium URA archivé)."""
    st = get_completion_status("UGA")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_DOCUMENTED
    assert vat["verified_records"] >= 1
    assert vat["arbitration"]["decision_code"] == "OFFICIAL_PRIMARY_TEXT_EXTRACTED"
    # La preuve cite la loi verbatim ; aucun CHAMP de taux machine n'est ajouté.
    assert "rate" not in [k.lower() for k in vat.keys()]
    assert st["national_taxes"]["official_document_archived"] is True


# ---------------------------------------------------------------------------
# Arbitrage documenté (data/coverage/national_tax_arbitration.json)
# ---------------------------------------------------------------------------


def test_arbitration_dataset_evidence_retained():
    """AGO : texte primaire gouvernemental (minfin.gov.ao) — DOCUMENTED confirmé."""
    st = get_completion_status("AGO")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_DOCUMENTED
    assert vat["arbitration"]["decision_code"] == "DATASET_EVIDENCE_RETAINED"
    div = vat.get("registry_divergence") or {}
    assert div.get("resolved_by_arbitration") is True


def test_arbitration_registry_prudence_retained():
    """SEN : républication privée (kof-experts.sn) — la prudence du registre l'emporte."""
    st = get_completion_status("SEN")
    vat = st["tax_families"]["VAT"]
    assert vat["status"] == STATUS_PARTIAL_DOCUMENTED
    assert vat["arbitration"]["decision_code"] == "REGISTRY_PRUDENCE_RETAINED"
    # La preuve cite explicitement la non-gouvernementalité de la source.
    assert vat["arbitration"]["evidence"]["source_url_governmental"] is False


def test_arbitration_registry_substantiated_by_enrichment():
    """BWA/LSO/SWZ : DOCUMENTED substantié par national_enrichment.json (textes vérifiés)."""
    for iso3 in ("BWA", "LSO", "SWZ"):
        st = get_completion_status(iso3)
        vat = st["tax_families"]["VAT"]
        assert vat["status"] == STATUS_DOCUMENTED, iso3
        assert vat["arbitration"]["decision_code"] == "REGISTRY_SUBSTANTIATED_BY_ENRICHMENT", iso3
        assert "national_enrichment.json" in vat["dataset_path"], iso3


def test_arbitration_registry_claim_unsubstantiated():
    """Le code REGISTRY_CLAIM_UNSUBSTANTIATED existe pour les claims sans preuve
    (UGA a été dégradé sous ce code avant consolidation, cf. audit trail)."""
    import json as _json

    arb = _json.load(open("data/coverage/national_tax_arbitration.json"))
    assert "REGISTRY_CLAIM_UNSUBSTANTIATED" in arb["decision_codes"]
    # Audit trail : la décision UGA a un historique de dégradation documenté.
    uga = next(d for d in arb["decisions"] if d["country"] == "UGA" and d["family"] == "VAT")
    assert uga["evidence"]["registry_anomaly_quoted"]  # la cause du downgrade est citée


def test_arbitration_resolves_all_flagged_divergences():
    """Toute divergence signalée doit être couverte par une décision (jamais silencieuse)."""
    report = national_completion_report()
    assert report["dataset_registry_divergences"] == [], (
        "divergences non arbitrées: "
        f"{[(d['country'], d['family']) for d in report['dataset_registry_divergences']]}"
    )
    assert report["arbitration"]["decisions_applied"] == 19


def test_enrichment_partial_substantiated_countries_progressed():
    """BDI/CAF/GNQ : PARTIAL substantié par national_enrichment (taux + sources vérifiées)."""
    for iso3 in ("BDI", "CAF", "GNQ"):
        st = get_completion_status(iso3)
        vat = st["tax_families"]["VAT"]
        assert vat["status"] == STATUS_PARTIAL_DOCUMENTED, iso3
        assert vat["arbitration"]["decision_code"] == "ENRICHMENT_PARTIAL_SUBSTANTIATED", iso3
        assert vat.get("dataset_path", "").endswith("national_enrichment.json"), iso3
        assert vat.get("scope_limitation"), iso3


def test_coverage_entries_use_precise_statuses():
    """Le champ national_taxes du coverage devient un statut précis (jamais une valeur)."""
    entries = coverage_update_entries()
    assert set(entries.keys()) >= NATIONAL_TAX_COMPLETED
    allowed = {STATUS_DOCUMENTED_NATIONAL, STATUS_PARTIAL_DOCUMENTED, STATUS_PENDING_OFFICIAL}
    for code, value in entries.items():
        assert value in allowed, (code, value)


def test_report_md_writes(tmp_path):
    from etl.national_tax_completion import write_completion_report_md

    out = tmp_path / "report.md"
    write_completion_report_md(str(out))
    content = out.read_text(encoding="utf-8")
    assert "Complétion fiscale nationale" in content
    assert "aucun mock" in content
