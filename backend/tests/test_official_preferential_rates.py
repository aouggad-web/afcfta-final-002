import gzip
import json
from importlib import import_module

from services import authentic_tariff_service
from services.authentic_tariff_service import resolve_zlecaf_context
from services.official_preferential_rates import (
    _resolve_offer_line,
    resolve_official_preferential_rate,
)
from services.zlecaf_implementation_registry import (
    APPLIED,
    OFFER_ONLY,
    PARTNER_NOTICE_REQUIRED,
    implementation_decision,
)

from scripts.extract_sars_afcfta_schedule import (
    SOURCE_SHA256,
    classify_rate_expression,
    write_dataset,
)

collector = import_module("scripts.collect_afcfta_etariff_book")


def test_dataset_records_the_reviewed_sars_revision():
    rate = resolve_official_preferential_rate("ZAF", "010121")
    assert rate["source_pdf_sha256"] == SOURCE_SHA256


def test_rate_expression_classification_never_flattens_compound_duties():
    assert classify_rate_expression("free")["ad_valorem_rate_pct"] == 0.0
    assert classify_rate_expression("8,8%")["ad_valorem_rate_pct"] == 8.8
    compound = classify_rate_expression("40% or 240c/kg")
    assert compound["rate_kind"] == "COMPOUND"
    assert compound["ad_valorem_rate_pct"] is None
    assert compound["calculation_status"] == "REQUIRES_QUANTITY"


def test_resolves_exact_free_and_ad_valorem_lines():
    free = resolve_official_preferential_rate("ZAF", "0101.21")
    assert free["hs_code"] == "010121"
    assert free["rate_expression"] == "free"
    assert free["ad_valorem_rate_pct"] == 0.0

    percent = resolve_official_preferential_rate("ZAF", "07108090")
    assert percent["rate_expression"] == "4%"
    assert percent["ad_valorem_rate_pct"] == 4.0


def test_compound_line_is_documented_but_not_value_only_calculable():
    rate = resolve_official_preferential_rate("ZAF", "020110")
    assert rate["rate_expression"] == "40% or 240c/kg"
    assert rate["calculation_status"] == "REQUIRES_QUANTITY"
    assert rate["ad_valorem_rate_pct"] is None


def test_resolution_fails_closed_for_ambiguous_or_unknown_codes():
    # 0201 has multiple national lines: never choose one from a short prefix.
    assert resolve_official_preferential_rate("ZAF", "0201") is None
    assert resolve_official_preferential_rate("ZAF", "999999") is None
    assert resolve_official_preferential_rate("KEN", "010121") is None


def test_zaf_context_uses_the_official_rate_after_legal_gates():
    context = resolve_zlecaf_context("ZAF", "DZA", "07108090", 10.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] == 4.0
    assert context["preference_applied"] is True
    assert context["zlecaf_rate_expression"] == "4%"
    assert context["zlecaf_rate_source"]["page"] == 47


def test_zaf_context_neutralizes_compound_duty_without_quantity():
    context = resolve_zlecaf_context("ZAF", "DZA", "020110", 40.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] is None
    assert context["preference_applied"] is False
    assert context["zlecaf_rate_expression"] == "40% or 240c/kg"
    assert context["zlecaf_rate_calculation_status"] == "REQUIRES_QUANTITY"


def test_kenya_applies_only_to_the_21_origins_named_by_kra():
    accepted = implementation_decision("KEN", "GHA")
    assert accepted["applied"] is True
    assert accepted["status"] == APPLIED
    assert accepted["record"].instrument_id == "EAC/321/2022"

    # Algeria is in the e-Tariff Book query but not in KRA's accepted list.
    refused = implementation_decision("KEN", "DZA")
    assert refused["applied"] is False
    assert refused["status"] == "NOT_AVAILABLE"


def test_kenya_uses_the_exact_eac_line_and_2026_tier():
    rate = resolve_official_preferential_rate("KEN", "01012900", "GHA", as_of_year=2026)
    assert rate["hs_code"] == "01012900"
    assert rate["schedule_year"] == 6
    assert rate["source_column"] == "year6"
    assert rate["rate_expression"] == "10%"
    assert rate["ad_valorem_rate_pct"] == 10.0

    context = resolve_zlecaf_context("KEN", "GHA", "01012900", 25.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] == 10.0
    assert context["zlecaf_rate_source"]["implementation_instrument"] == "EAC/321/2022"


def test_offer_lookup_keeps_exact_nine_digit_lines_and_clamps_final_tier():
    line = {
        "hs_code": "123456789",
        "annual_rate_expressions": {"1": "10", "10": "0"},
    }
    dataset = {
        "legal_effect_status": "OFFER_ONLY",
        "execution_authorized": False,
        "origin_schedule_map": {"AO": "1"},
        "_schedule_indexes": {"1": {line["hs_code"]: line}},
        "agreement": "AfCFTA",
        "source_title": "Official test offer",
        "source_url": "https://example.test/offer",
        "source_api_url": "https://example.test/offer/api",
        "collected_at": "2026-08-17",
    }

    rate = _resolve_offer_line(dataset, "TUN", "AGO", "123456789", 2031)

    assert rate["hs_code"] == "123456789"
    assert rate["schedule"] == "1"  # legacy ISO2 snapshot remains readable
    assert rate["schedule_year"] == 10
    assert rate["source_column"] == "year10"
    assert rate["ad_valorem_rate_pct"] == 0.0


def test_collector_normalizes_origin_schedule_keys_to_iso3(monkeypatch):
    monkeypatch.setattr(
        collector,
        "_request_json",
        lambda *_args, **_kwargs: [{"isHeading": False, "regionCode": "EG", "schedule": "1"}],
    )

    mapping = collector._origin_schedule_map("EG", "EG", ["AO", "BF"])

    assert mapping == {"AGO": "1", "BFA": "1"}


def test_sars_writer_emits_deterministic_gzip(tmp_path):
    output = tmp_path / "schedule.json.gz"
    payload = {"schema_version": 1, "lines": [{"hs_code": "010121"}]}

    write_dataset(output, payload)
    first = output.read_bytes()
    write_dataset(output, payload)

    assert output.read_bytes() == first
    assert json.loads(gzip.decompress(first)) == payload


def test_effective_rate_reports_the_mfn_rate_when_schedule_is_higher(monkeypatch):
    line = {
        "dd_rate": 0.0,
        "vat_rate": 15.0,
        "zlecaf_rate": None,
        "other_taxes_rate": 0.0,
        "taxes_detail": {},
        "description_fr": "Produit test",
        "description_en": "Test product",
        "fiscal_advantages": [],
        "administrative_formalities": [],
    }
    monkeypatch.setattr(authentic_tariff_service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(
        authentic_tariff_service,
        "load_country_tariffs",
        lambda _iso3: {"generated_at": "2026-08-17"},
    )
    monkeypatch.setattr(authentic_tariff_service, "get_tariff_line", lambda *_args: dict(line))
    monkeypatch.setattr(authentic_tariff_service, "load_crawled_position_index", lambda _iso3: None)
    monkeypatch.setattr(authentic_tariff_service, "get_sub_positions", lambda *_args: [])

    result = authentic_tariff_service.calculate_import_taxes(
        "ZAF", "340700", 1000.0, origin_country="DZA"
    )

    assert result["zlecaf_rate_expression"] == "4%"
    assert result["zlecaf_preference_applied"] is False
    assert result["rates"]["effective_zlecaf_rate_pct"] == 0.0


def test_offer_and_domestication_without_partner_notice_never_calculate():
    assert implementation_decision("GHA", "KEN")["status"] == OFFER_ONLY
    assert implementation_decision("ETH", "KEN")["status"] == PARTNER_NOTICE_REQUIRED
    assert resolve_official_preferential_rate("GHA", "0101210000", "KEN") is None
    assert resolve_official_preferential_rate("ETH", "01012100", "KEN") is None

    offer_only = resolve_zlecaf_context("GHA", "KEN", "0101210000", 5.0, 0.0)
    assert offer_only["trade_regime"] != "ZLECAF"
    assert offer_only["zlecaf_rate_calculation_status"] == "NOT_AVAILABLE"

    missing_notice = resolve_zlecaf_context("ETH", "KEN", "01012100", 5.0, 0.0)
    assert missing_notice["trade_regime"] != "ZLECAF"
    assert missing_notice["zlecaf_rate_calculation_status"] == "NOT_AVAILABLE"


def test_accepted_corridor_ignores_unverified_etl_rate_when_exact_line_is_missing():
    context = resolve_zlecaf_context("KEN", "GHA", "99999999", 25.0, 0.0)

    assert context["trade_regime"] == "ZLECAF"
    assert context["zlecaf_eligible"] is True
    assert context["dd_rate_pct"] is None
    assert context["preference_applied"] is False
    assert context["zlecaf_rate_calculation_status"] == "NOT_AVAILABLE"
