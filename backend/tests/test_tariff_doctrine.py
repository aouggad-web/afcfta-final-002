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

import json

import pytest

from fastapi import HTTPException

from services import tariff_doctrine
from services.tariff_doctrine import (
    evaluate_country_file,
    get_country_doctrine_status,
    not_recrawled_http_detail,
    provider_fee_flags,
)
from routes import authentic_tariffs


SYNTHETIC_ISO3 = [
    "AGO", "COM", "DJI", "ERI", "LBY", "MDG", "MOZ", "MRT",
    "MWI", "SDN", "STP", "SYC", "ZMB", "ZWE",
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


def test_doctrine_status_dza_is_servable():
    assert get_country_doctrine_status("DZA")["status"] == "SERVABLE"


def test_doctrine_status_synthetic_country_has_explicit_message():
    for iso3 in ("AGO", "ZWE"):
        status = get_country_doctrine_status(iso3)
        # Après archivage P0-1 : plus de fichier synthétique servi.
        assert status["status"] in ("NOT_RECRALLED", "NO_FILE")
        assert status["message_fr"]


def test_not_recrawled_http_detail_shape():
    detail = not_recrawled_http_detail("AGO")
    assert detail["error"] == "COUNTRY_NOT_RECRALLED"
    assert detail["country_iso3"] == "AGO"
    assert "doctrine" not in detail  # statut sérialisable


# ── Gate de chargement (authentic_tariff_service) ─────────────────────────────


def test_load_country_tariffs_refuses_synthetic_file(tmp_path, monkeypatch):
    from services import authentic_tariff_service as svc

    fake = tmp_path / "SYN_tariffs.json"
    fake.write_text(json.dumps(_synthetic_fixture()), encoding="utf-8")

    monkeypatch.setattr(svc, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(svc, "_tariff_cache", {})
    monkeypatch.setattr(tariff_doctrine, "DATA_DIR", str(tmp_path))
    tariff_doctrine.clear_doctrine_cache()

    assert svc.load_country_tariffs("SYN") is None


def test_load_country_tariffs_accepts_conforming_file(tmp_path, monkeypatch):
    from services import authentic_tariff_service as svc

    fake = tmp_path / "XYZ_tariffs.json"
    fake.write_text(json.dumps(_canonical_fixture()), encoding="utf-8")

    monkeypatch.setattr(svc, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(svc, "_tariff_cache", {})
    monkeypatch.setattr(tariff_doctrine, "DATA_DIR", str(tmp_path))
    tariff_doctrine.clear_doctrine_cache()

    data = svc.load_country_tariffs("XYZ")
    assert data is not None and data["data_format"] == "canonical_v4"


def test_dza_single_source_of_truth_no_stale_duplicate():
    """P0-2 : la copie DZA périmée ne doit plus être servie par tariff_data_service."""
    import os

    stale = "backend/data/tariffs/DZA_tariffs.json"
    assert not os.path.exists(stale), (
        "La copie DZA périmée (juin 2026, 5141 conflits de taux) ne doit plus exister "
        "dans le répertoire de service backend/data/tariffs/"
    )


# ── Gate facade (tariff_provider_service) — bloque aussi PostgreSQL ───────────


def test_provider_refuses_country_even_if_postgres_has_data():
    from services.tariff_provider_service import TariffProviderService

    class FakePostgres:
        def get_country_summary(self, iso3):
            return {"iso3": iso3, "injected": True}

        def get_tariff_line(self, iso3, hs):
            return {"injected": True}

        def get_sub_positions(self, iso3, hs6):
            return [{"code": "0101210010"}]

    provider = TariffProviderService(postgres_factory=FakePostgres)
    # AGO : aucune donnée nationale conforme (synthétique archivé)
    assert provider.get_country_summary("AGO") is None
    assert provider.get_tariff_line("AGO", "010121") is None
    assert provider.get_sub_positions("AGO", "010121") == []


# ── Routes : message explicite COUNTRY_NOT_RECRALLED ──────────────────────────


def test_route_summary_raises_explicit_not_recralled(monkeypatch):
    monkeypatch.setattr(
        authentic_tariffs,
        "get_country_doctrine_status",
        lambda iso3: {
            "status": "NOT_RECRALLED",
            "reason_code": "UNSERVABLE_FORMAT",
            "message_fr": "msg-fr",
            "message_en": "msg-en",
        },
    )
    with pytest.raises(HTTPException) as exc_info:
        import asyncio

        asyncio.run(authentic_tariffs.get_tariff_summary("AGO"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["error"] == "COUNTRY_NOT_RECRALLED"


def test_route_summary_passes_for_servable_country(monkeypatch):
    monkeypatch.setattr(
        authentic_tariffs,
        "get_country_doctrine_status",
        lambda iso3: {"status": "SERVABLE"},
    )
    monkeypatch.setattr(
        authentic_tariffs, "get_tariff_provider_service",
        lambda: type("P", (), {"get_country_summary": staticmethod(lambda c: {"ok": True})})(),
    )
    import asyncio

    result = asyncio.run(authentic_tariffs.get_tariff_summary("DZA"))
    assert result["success"] is True


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
    assert "RPD/IMPOR" in codes, (
        "La redevance de prestation douanière à l'import doit être conservée dans le calcul"
    )


# ── Système tarifaire export par pays + prestataires délégataires ─────────────


def test_providers_registry_tun_documented_from_crawl():
    """Registre : la TUN est documentée depuis la source crawlée (RPD),
    payée par les opérateurs économiques, avec base légale et URL."""
    from services.export_tariff_service import load_providers_registry

    registry = load_providers_registry(force=True)
    tun = registry["countries"]["TUN"]
    assert tun["verification_status"] == "VERIFIE_SOURCE_CRAWLEE"
    provider = tun["providers"][0]
    assert provider["paid_by"] == "OPERATEURS_ECONOMIQUES"
    assert set(provider["fee_codes"]) == {"RPD/IMPOR", "RPD/EXPOR"}
    assert provider["source_url"].startswith("https://")


def test_providers_registry_unverified_countries_serve_nothing():
    """Doctrine : les pays A_DOCUMENTER ne servent aucun prestataire."""
    from services.export_tariff_service import get_country_providers

    assert get_country_providers("GHA") == []
    assert get_country_providers("CIV") == []


def test_tun_export_cascade_ad_valorem_dattes():
    """Export TUN — droit export dattes 1 % (assiette VALEUR DOUANE DINARS)."""
    from services.crawled_data_service import crawled_service
    from services.export_tariff_service import compute_export_taxes

    crawled_service.load(force=True)
    subs = crawled_service.lookup_by_hs6("TUN", "080410")  # dattes
    with_date_export = [
        s for s in subs if any(t["code"] == "DROIT.EXP.DATTES" for t in s.get("export_taxes", []))
    ]
    assert with_date_export, "Les positions dattes TUN doivent avoir leur droit export crawlé"
    code = with_date_export[0]["code_clean"]
    result = compute_export_taxes("TUN", code, customs_value=10000.0)
    assert result["success"] is True
    step = next(s for s in result["export_cascade"] if s["code"] == "DROIT.EXP.DATTES")
    assert step["rate_pct"] == 1.0
    assert step["amount"] == 100.0  # 1% × 10 000
    assert step["base_kind"] == "CUSTOMS_VALUE"


def test_tun_export_cascade_specific_scrap_iron():
    """Export TUN — taxe ferrailles : droit spécifique en dinars au kg
    (assiette PN (KG)), calculé depuis le poids net."""
    from services.crawled_data_service import crawled_service
    from services.export_tariff_service import compute_export_taxes

    crawled_service.load(force=True)
    subs = crawled_service.lookup_by_hs6("TUN", "720410")  # déchets et débris d'acier
    with_scrap = [
        s for s in subs if any(t["code"] == "TAXE/FERRAILLES.EXP" for t in s.get("export_taxes", []))
    ]
    assert with_scrap, "Les positions ferrailles TUN doivent avoir leur taxe export crawlée"
    position = next(
        s for s in with_scrap if s.get("export_taxes") and s["export_taxes"][0].get("raw_value")
    )
    code = position["code_clean"]
    result = compute_export_taxes("TUN", code, quantity=1000.0, net_weight_kg=1000.0)
    assert result["success"] is True
    step = next(s for s in result["export_cascade"] if s["code"] == "TAXE/FERRAILLES.EXP")
    assert step["amount"] > 0
    assert step["calculation_method"] and "Spécifique" in step["calculation_method"]


def test_tun_export_cascade_provider_fee_paid_by_operators():
    """Export TUN — la redevance de prestation douanière (RPD/EXPOR) est
    marquée comme frais de prestataire payé par les opérateurs économiques."""
    from services.crawled_data_service import crawled_service
    from services.export_tariff_service import compute_export_taxes

    crawled_service.load(force=True)
    result = compute_export_taxes("TUN", "01012100015", customs_value=10000.0)
    assert result["success"] is True
    rpd = next(s for s in result["export_cascade"] if s["code"] == "RPD/EXPOR")
    assert rpd["is_provider_fee"] is True
    assert rpd["paid_by"] == "OPERATEURS_ECONOMIQUES"
    assert rpd["legal_basis"]
    assert result["provider_fees"] is not None


def test_export_calculus_refused_without_crawled_data():
    """Doctrine : refus explicite pour un pays sans données export crawlées."""
    from services.export_tariff_service import compute_export_taxes

    result = compute_export_taxes("DZA", "0101210000")
    assert not result.get("success")
    assert result.get("export_data_available") is False
    assert "doctrine" in result["error"]
