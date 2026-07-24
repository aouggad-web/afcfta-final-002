import asyncio
from datetime import date

from routes import authentic_tariffs

from engine.schemas.legal_override import RemissionEligibility


def _base_result():
    return {"rates": {"dd_rate_pct": 35}, "hs6": "100199"}


def test_kenya_endpoint_passes_authorization_to_legal_layer(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        authentic_tariffs, "calculate_import_taxes", lambda **kwargs: _base_result()
    )

    def fake_legal(**kwargs):
        captured.update(kwargs)
        return {
            "calculation_status": "VERIFIED_PARTIAL",
            "remission_eligibility_status": "ELIGIBLE_VERIFIED",
        }

    monkeypatch.setattr(authentic_tariffs, "calculate_kenya_legal_layer", fake_legal)
    result = asyncio.run(
        authentic_tariffs.calculate_taxes_endpoint(
            country_iso3="KEN",
            hs_code="10019910",
            cif_value=10000,
            language="fr",
            origin="UGA",
            calculation_date=date(2026, 7, 24),
            remission_eligibility=RemissionEligibility.ELIGIBLE_VERIFIED,
            authorization_reference="AUTH/2026/1",
            authorization_valid_from=date(2026, 7, 1),
            authorization_valid_to=date(2027, 6, 30),
            authorization_hs_codes="10019910,10019990",
            authorization_goods="wheat input",
            beneficiary=None,
            import_purpose=None,
            quantity=None,
        )
    )
    assert result["kenya_legal_calculation"]["remission_eligibility_status"] == "ELIGIBLE_VERIFIED"
    assert captured["authorization_hs_codes"] == ["10019910", "10019990"]
    assert captured["base_cet_rate"] == 35


def test_non_kenya_endpoint_does_not_invoke_kenya_layer(monkeypatch):
    monkeypatch.setattr(
        authentic_tariffs, "calculate_import_taxes", lambda **kwargs: _base_result()
    )
    monkeypatch.setattr(
        authentic_tariffs,
        "calculate_kenya_legal_layer",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    result = asyncio.run(
        authentic_tariffs.calculate_taxes_endpoint(
            country_iso3="GHA",
            hs_code="10019910",
            cif_value=10000,
            language="fr",
            origin="KEN",
            calculation_date=date(2026, 7, 24),
            remission_eligibility=RemissionEligibility.ELIGIBILITY_UNKNOWN,
            authorization_reference=None,
            authorization_valid_from=None,
            authorization_valid_to=None,
            authorization_hs_codes=None,
            authorization_goods=None,
            beneficiary=None,
            import_purpose=None,
            quantity=None,
        )
    )
    assert "kenya_legal_calculation" not in result
