"""
Tests de la doctrine tarifaire (audit P0-1) et du surfacage export/prestataires.

Référence : audits/AUDIT_CALCULATEUR_DONNEES_TARIFAIRES_2026-09-01.md
- P0-1 : refus explicite des fichiers pays synthétiques (enhanced_v2 sans
  provenance) — 14 pays : AGO, COM, DJI, ERI, LBY, MDG, MOZ, MRT, MWI,
  SDN, STP, SYC, ZMB, ZWE.
- P0-2 : unicité de la source DZA (copie périmée juin archivée).
- Directives : sources officielles import/export + frais de prestataires
  (redevances de prestations douanières) marqués explicitement.
"""

from services.tariff_doctrine import (
    crawl_enregistre,
    evaluate_country_file,
    get_country_doctrine_status,
    not_recrawled_http_detail,
    provider_fee_flags,
)

SYNTHETIC_ISO3 = [
    "AGO",
    "COM",
    "DJI",
    "ERI",
    "LBY",
    "MDG",
    "MOZ",
    "MRT",
    "MWI",
    "SDN",
    "STP",
    "SYC",
    "ZMB",
    "ZWE",
]


def _canonical_fixture(status="VERIFIED", source_url="https://douane.example/tarif"):
    return {
        "data_format": "canonical_v4",
        "summary": {
            "data_status": status,
            "source_name": "Direction Générale des Douanes",
            "source_url": source_url,
        },
        "tariff_lines": [],
    }


def _synthetic_fixture():
    return {
        "data_format": "enhanced_v2",
        "summary": {"total_sub_positions": 16141},
        "tariff_lines": [],
    }


# ── evaluate_country_file ────────────────────────────────────────────────────


def test_evaluate_accepts_verified_canonical_file():
    ok, reason, _ = evaluate_country_file(_canonical_fixture())
    assert ok and reason == "OK"


def test_evaluate_accepts_crawled_authentic_status():
    ok, reason, _ = evaluate_country_file(_canonical_fixture(status="CRAWLED_AUTHENTIC"))
    assert ok


def test_evaluate_refuses_synthetic_enhanced_v2_format():
    ok, reason_code, detail = evaluate_country_file(_synthetic_fixture())
    assert not ok
    assert reason_code == "UNSERVABLE_FORMAT"
    assert "canonical_v4" in detail


def test_evaluate_refuses_missing_source_url():
    ok, reason_code, _ = evaluate_country_file(_canonical_fixture(source_url=""))
    assert not ok
    assert reason_code == "MISSING_SOURCE"


def test_evaluate_refuses_unknown_status():
    fixture = _canonical_fixture()
    fixture["summary"]["data_status"] = "SYNTHETIC"
    ok, reason_code, _ = evaluate_country_file(fixture)
    assert not ok
    assert reason_code == "UNSERVABLE_STATUS"


# ── Statut doctrine par pays (fichiers réels) ─────────────────────────────────


def test_dza_is_consulted_from_its_registered_crawl():
    # Le fichier ETL algérien (conformepro) est supprimé : l'Algérie n'est plus
    # servie que par le crawl DGD inscrit au registre des sources.
    assert get_country_doctrine_status("DZA")["status"] == "NO_FILE"
    assert crawl_enregistre("DZA")


def test_doctrine_status_synthetic_country_has_explicit_message():
    for iso3 in ("AGO", "ZWE"):
        status = get_country_doctrine_status(iso3)
        # Après archivage P0-1 : plus de fichier synthétique servi.
        assert status["status"] in ("NOT_RECRAWLED", "NO_FILE")
        assert status["message_fr"]


def test_not_recrawled_http_detail_shape():
    detail = not_recrawled_http_detail("AGO")
    assert detail["error"] == "COUNTRY_NOT_RECRAWLED"
    assert detail["country_iso3"] == "AGO"
    assert "doctrine" not in detail  # statut sérialisable


# ── Une seule copie servie par jeu de données ─────────────────────────────────


def test_dza_single_source_of_truth_no_stale_duplicate():
    """P0-2 : la copie DZA périmée ne doit plus être servie par tariff_data_service."""
    import os

    stale = "backend/data/tariffs/DZA_tariffs.json"
    assert not os.path.exists(stale), (
        "La copie DZA périmée (juin 2026, 5141 conflits de taux) ne doit plus exister "
        "dans le répertoire de service backend/data/tariffs/"
    )


# ── Export & frais de prestataires (TUN, source douane.gov.tn) ────────────────


def test_provider_fee_flags_detect_redevance_prestation():
    flags = provider_fee_flags({"code": "RPD/IMPOR", "name": "REDEV.PREST.DOUA/EXP"})
    assert flags["is_provider_fee"] is True
    flags_vat = provider_fee_flags({"code": "TVA/AP", "name": "TAXE VALEUR AJOUTEE"})
    assert flags_vat["is_provider_fee"] is False


def test_tun_export_taxes_surfaced_with_provider_fees():
    """Directive export : les taxes export crawlées (douane.gov.tn) sont servies,
    avec marquage explicite des redevances de prestations douanières."""
    from services.crawled_data_service import crawled_service

    crawled_service.load(force=True)
    export = crawled_service.get_export_taxes("TUN", "01012100015")
    assert export is not None, "TUN doit exposer ses taxes export crawlées"
    codes = [t["code"] for t in export["export_taxes"]]
    assert "RPD/EXPOR" in codes
    assert export["source"] == "douane.gov.tn"
    rpd = next(t for t in export["export_taxes"] if t["code"] == "RPD/EXPOR")
    assert rpd["is_provider_fee"] is True


def test_tun_import_taxes_include_provider_fee():
    from services.crawled_data_service import crawled_service

    crawled_service.load(force=True)
    position = crawled_service.lookup("TUN", "01012100015")
    assert position is not None
    codes = [t["code"] for t in position["taxes"]]
    assert (
        "RPD/IMPOR" in codes
    ), "La redevance de prestation douanière à l'import doit être conservée dans le calcul"


# ── Système tarifaire export par pays + prestataires délégataires ─────────────


