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
            "calculation_status": "INFORMATIVE_PARTIAL",
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
    assert result["informational_only"] is True
    assert result["legally_binding"] is False
    assert result["disclaimer"]["legally_binding"] is False
    assert result["administrative_confirmation_required"] is True
    assert result["overall_status"] == "INFORMATIVE_PARTIAL"
    assert set(result["quality_dimensions"]) == {
        "source", "temporal_validity", "classification", "taxes_and_levies",
        "preference_and_origin", "formalities",
    }


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


def test_api_quality_boundary_preserves_all_four_global_statuses(monkeypatch):
    statuses = (
        "INFORMATIVE_COMPLETE",
        "INFORMATIVE_PARTIAL",
        "CALCULATION_UNAVAILABLE",
        "REVIEW_REQUIRED",
    )
    quality = {
        "source": "DOCUMENTED",
        "temporal_validity": "DOCUMENTED",
        "classification": "DOCUMENTED",
        "taxes_and_levies": "DOCUMENTED",
        "preference_and_origin": "NOT_APPLICABLE",
        "formalities": "NOT_APPLICABLE",
    }
    monkeypatch.setattr(authentic_tariffs, "calculate_import_taxes", lambda **kwargs: _base_result())
    for status in statuses:
        monkeypatch.setattr(
            authentic_tariffs,
            "calculate_kenya_legal_layer",
            lambda **kwargs: {"overall_status": status, "quality_dimensions": quality},
        )
        result = asyncio.run(
            authentic_tariffs.calculate_taxes_endpoint(
                country_iso3="KEN", hs_code="10019910", cif_value=10000,
                language="fr", origin="UGA", calculation_date=date(2026, 7, 24),
                remission_eligibility=RemissionEligibility.ELIGIBILITY_UNKNOWN,
                authorization_reference=None, authorization_valid_from=None,
                authorization_valid_to=None, authorization_hs_codes=None,
                authorization_goods=None, beneficiary=None, import_purpose=None, quantity=None,
            )
        )
        assert result["overall_status"] == status
        assert result["informational_only"] is True
        assert result["legally_binding"] is False
        assert set(result["quality_dimensions"]) == set(quality)
