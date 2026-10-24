"""Integrity guardrails for the partial Mauritius legal calculation."""
import hashlib
import asyncio
import json
import sys
import types
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from services.national_legal_calculation_service import (  # noqa: E402
    SUPPORTED_JURISDICTIONS,
    calculate_national_legal_layer,
)
from engine.national_customs_calculation import NationalFiscalStore  # noqa: E402

DATA = ROOT / "data/mauritius"
CANONICAL = BACKEND / "data/MUS_tariffs.json"


def _calculate(code="85392110", when=date(2026, 4, 1), duty=30.0):
    return calculate_national_legal_layer(
        jurisdiction="MUS", hs_code=code, on_date=when,
        customs_value=100.0, base_cet_rate=duty, origin="DZA", currency_code="USD"
    )


def test_blank_vat_is_unavailable_and_has_no_complete_total():
    result = _calculate("01022100", duty=0)
    assert result["vat"] is None
    assert result["verified_total"] is None
    assert result["calculation_status"] == "REVIEW_REQUIRED"
    assert result["overall_status"] == "INFORMATIVE_PARTIAL"
    assert "blank" in " ".join(result["missing_elements"]).lower()


def test_exemption_requires_independent_evidence(tmp_path):
    for name in ("excise_measures.json", "import_levies.json"):
        (tmp_path / name).write_bytes((DATA / name).read_bytes())
    vat = json.loads((DATA / "vat_measures.json").read_text())
    vat["vat_exemptions"] = [{
        "record_id": "MUS-VAT-EXEMPT-OFFICIAL-1", "rate": "EXEMPT",
        "effective_from": "2026-04-01", "effective_to": None,
        "legal_status": "CURRENT_OFFICIAL_SCHEDULE", "hs_codes_explicit": ["01022100"],
        "legal_reference": "Independent MRA VAT Act schedule line", "source_id": "MRA-VAT-SCHEDULE",
        "source_sha256": "a" * 64,
    }]
    vat["vat_unavailable"] = []
    (tmp_path / "vat_measures.json").write_text(json.dumps(vat))
    treatment = NationalFiscalStore(tmp_path).vat_treatment(date(2026, 4, 1), "01022100")
    assert treatment["treatment"] == "EXEMPT" and treatment["rate_pct"] == 0


def test_pre_2026_rates_are_unavailable():
    result = _calculate("85392110", date(2026, 3, 31))
    assert result["vat"] is None
    assert result["excise"]["lines"] == []
    assert result["verified_total"] is None


def test_excise_uses_declared_cif_basis_even_when_duty_applies():
    result = _calculate()
    line = result["excise"]["lines"][0]
    assert result["customs_duty"] == 30
    assert line["source_rate"] == 25
    assert line["taxable_base"] == 100
    assert line["amount"] == 25


def test_currency_and_value_remain_coherent_without_fx():
    result = _calculate()
    assert result["customs_value"] == 100
    assert result["currency_code"] == "USD"
    assert all(line["currency"] == "USD" for line in result["excise"]["lines"])


def test_public_route_keeps_usd_value_coherent(monkeypatch):
    from routes import authentic_tariffs as route

    monkeypatch.setattr(route, "get_country_doctrine_status", lambda _country: {"status": "SERVABLE"})
    monkeypatch.setattr(route, "calculate_import_taxes", lambda **_kwargs: {"rates": {"dd_rate_pct": 30}})
    monkeypatch.setattr(route, "get_country_enrichment", lambda _country: {})
    monkeypatch.setattr(route, "build_regulatory_blocks", lambda *_args, **_kwargs: {
        "regulatory_compliance": None, "regulatory_cost": None, "regulatory_reported": None
    })
    result = asyncio.run(route.calculate_taxes_endpoint(
        country_iso3="MUS", hs_code="85392110", cif_value=100,
        language="en", origin="DZA", calculation_date=date(2026, 4, 1),
        remission_eligibility=route.RemissionEligibility.ELIGIBILITY_UNKNOWN,
        authorization_reference=None, authorization_valid_from=None,
        authorization_valid_to=None, authorization_hs_codes=None,
        authorization_goods=None, beneficiary=None, import_purpose=None, quantity=None,
    ))
    national = result["national_legal_calculation"]
    assert national["customs_value"] == 100
    assert national["currency_code"] == "USD"


def test_missing_levies_formalities_and_preference_fail_closed():
    result = _calculate()
    q = result["quality_dimensions"]
    assert q["taxes_and_levies"] != "DOCUMENTED"
    assert q["preference_and_origin"] == "NOT_AVAILABLE"
    assert q["formalities"] == "NOT_AVAILABLE"
    assert result["administrative_requirements"] == []
    assert result["verified_total"] is None
    gaps = " ".join(result["missing_elements"] + result["known_data_gaps"]).lower()
    for term in ("environmental", "tourism", "afcfta", "formalities"):
        assert term in gaps


def test_afcfta_preference_totals_and_savings_are_neutralized(monkeypatch):
    from services.authentic_tariff_service import calculate_import_taxes

    service = types.SimpleNamespace(get_rate=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "exchange_rates", types.SimpleNamespace(get_service=lambda: service))
    result = calculate_import_taxes(
        "MUS", "85392110", 100, origin_country="DZA", language="en"
    )
    assert result["zlecaf_status"] == "NOT_AVAILABLE"
    assert result["zlecaf_calculation"] is None
    assert result["calculation_steps_zlecaf"] == []
    assert result["taxes_summary"]["zlecaf"] is None
    assert result["taxes_summary"]["economie_droits"] is None
    assert result["taxes_summary"]["economie_totale"] is None
    assert result["savings"]["amount"] is None


def test_hs6_and_hs8_both_fail_closed_for_formalities():
    assert _calculate("853921")["administrative_requirements"] == []
    assert _calculate("85392110")["administrative_requirements"] == []


def test_generated_provenance_hashes_are_reproducible():
    digest = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    for filename, collection in (("vat_measures.json", "vat_rates"), ("excise_measures.json", "excise_rates")):
        document = json.loads((DATA / filename).read_text())
        assert document["provenance"]["canonical_sha256"] == digest
        for record in document[collection]:
            assert record["source_sha256"] == digest
            assert record["source_hash_scope"] == (
                "normalized canonical extraction: backend/data/MUS_tariffs.json"
            )
            assert record["source_document_sha256"] is None
            assert record["source_extraction_date"]
            assert record["source_effective_date"] == "2026-04-01"
            assert record["transformation_trace"]
