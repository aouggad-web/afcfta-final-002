from datetime import date

from engine.legal_override_engine import LegalOverrideResolver
from engine.schemas.legal_override import (
    LegalOverrideMeasure,
    OverrideContext,
    RemissionEligibility,
)


def measure(measure_id, measure_type, rate, start="2025-07-01", end="2026-06-30", **kw):
    return LegalOverrideMeasure(
        measure_id=measure_id,
        jurisdiction="KEN",
        measure_type=measure_type,
        legal_title="Test official instrument",
        gazette_number="TEST/1",
        gazette_date=date.fromisoformat(start),
        legal_reference="Table I, row 1",
        publication_url=f"https://example.test/{measure_id}.pdf",
        source_hash="a" * 64,
        effective_from=start,
        effective_to=end,
        hs_code_from="87012190",
        hs_code_to="87012190",
        hs_version="HS2022",
        product_description="Test product",
        base_rate=10,
        override_rate=rate,
        rate_unit="%",
        verification_status=kw.pop("verification_status", "VERIFIED_OFFICIAL_EXTRACT"),
        requires_human_review=kw.pop("requires_human_review", False),
        **kw,
    )


def resolve(measures, when="2025-08-01", context=None, complete=True):
    return LegalOverrideResolver(measures, coverage_complete=complete).resolve(
        hs_code="87012190",
        on_date=date.fromisoformat(when),
        base_rate=10,
        context=context,
    )


def test_cet_without_override():
    result = resolve([])
    assert result["applicable_customs_rate"] == 10
    assert result["override_rate"] is None
    assert result["calculation_status"] == "VERIFIED_COMPLETE"


def test_stay_of_application():
    result = resolve([measure("stay", "STAY_OF_APPLICATION", 35)])
    assert result["applicable_customs_rate"] == 35
    assert result["trace"][-1]["measure_id"] == "stay"


def test_conditional_remission_requires_matching_facts():
    remission = measure(
        "remission",
        "DUTY_REMISSION",
        0,
        beneficiary="MANUFACTURER",
        import_purpose="MANUFACTURE_OF_CRANES",
    )
    unresolved = resolve([remission])
    assert unresolved["applicable_customs_rate"] == 10
    assert unresolved["calculation_status"] == "VERIFIED_PARTIAL"
    applied = resolve(
        [remission],
        context=OverrideContext(
            remission_eligibility=RemissionEligibility.ELIGIBLE_VERIFIED,
            authorization_reference="AUTH/2025/1",
            authorization_effective_from="2025-07-01",
            authorization_effective_to="2026-06-30",
            authorization_hs_codes=["87012190"],
        ),
    )
    assert applied["applicable_customs_rate"] == 0
    assert applied["remission_eligibility_status"] == "ELIGIBLE_VERIFIED"


def test_non_eligible_beneficiary_keeps_normal_cet():
    remission = measure("remission-no", "DUTY_REMISSION", 0, beneficiary="MANUFACTURER")
    result = resolve(
        [remission],
        context=OverrideContext(remission_eligibility=RemissionEligibility.NOT_ELIGIBLE),
    )
    assert result["applicable_customs_rate"] == 10
    assert result["remission_eligibility_status"] == "NOT_ELIGIBLE"
    assert result["calculation_status"] == "VERIFIED_COMPLETE"


def test_claimed_eligibility_without_authorization_is_partial():
    remission = measure("remission-missing-auth", "DUTY_REMISSION", 0, beneficiary="MANUFACTURER")
    result = resolve(
        [remission],
        context=OverrideContext(remission_eligibility=RemissionEligibility.ELIGIBLE_VERIFIED),
    )
    assert result["applicable_customs_rate"] == 10
    assert result["remission_eligibility_status"] == "AUTHORIZATION_REQUIRED"
    assert result["requires_eligibility_input"] is True
    assert result["calculation_status"] == "VERIFIED_PARTIAL"


def test_authorization_must_cover_exact_tariff_line():
    remission = measure("remission-wrong-line", "DUTY_REMISSION", 0, beneficiary="MANUFACTURER")
    result = resolve(
        [remission],
        context=OverrideContext(
            remission_eligibility=RemissionEligibility.ELIGIBLE_VERIFIED,
            authorization_reference="AUTH/2025/2",
            authorization_effective_from="2025-07-01",
            authorization_effective_to="2026-06-30",
            authorization_hs_codes=["870121"],
        ),
    )
    assert result["applicable_customs_rate"] == 10
    assert result["remission_eligibility_status"] == "AUTHORIZATION_REQUIRED"


def test_expired_authorization_keeps_normal_cet():
    remission = measure("remission-expired-auth", "DUTY_REMISSION", 0, beneficiary="MANUFACTURER")
    result = resolve(
        [remission],
        context=OverrideContext(
            remission_eligibility=RemissionEligibility.ELIGIBLE_VERIFIED,
            authorization_reference="AUTH/2024/1",
            authorization_effective_from="2024-07-01",
            authorization_effective_to="2025-06-30",
            authorization_hs_codes=["87012190"],
        ),
    )
    assert result["applicable_customs_rate"] == 10
    assert result["remission_eligibility_status"] == "NOT_ELIGIBLE"


def test_national_exemption():
    exemption = measure("exemption", "KENYA_NATIONAL_EXEMPTION", 0)
    assert resolve([exemption])["applicable_customs_rate"] == 0


def test_expired_measure_is_ignored():
    expired = measure("expired", "STAY_OF_APPLICATION", 35)
    assert resolve([expired], when="2026-07-01")["applicable_customs_rate"] == 10


def test_contradictory_instruments_require_review():
    result = resolve(
        [
            measure("conflict-a", "STAY_OF_APPLICATION", 25),
            measure("conflict-b", "STAY_OF_APPLICATION", 35),
        ]
    )
    assert result["calculation_status"] == "CONFLICT_REVIEW"
    assert result["applicable_customs_rate"] == 10


def test_missing_source_verification_forces_partial():
    pending = measure("pending", "STAY_OF_APPLICATION", 35, verification_status="SOURCE_PENDING")
    result = resolve([pending])
    assert result["applicable_customs_rate"] == 35
    assert result["calculation_status"] == "VERIFIED_PARTIAL"


def test_same_code_at_two_dates_uses_temporal_measure():
    first = measure("first", "STAY_OF_APPLICATION", 35)
    second = measure("second", "STAY_OF_APPLICATION", 25, start="2026-07-01", end="2027-06-30")
    assert resolve([first, second], when="2026-06-30")["applicable_customs_rate"] == 35
    assert resolve([first, second], when="2026-07-01")["applicable_customs_rate"] == 25


def test_discontinuous_hs_list_does_not_become_a_range():
    listed = measure("listed", "STAY_OF_APPLICATION", 35, hs_codes=["87012190", "87012990"])
    resolver = LegalOverrideResolver([listed], coverage_complete=True)
    result = resolver.resolve(hs_code="87012590", on_date=date(2025, 8, 1), base_rate=10)
    assert result["applicable_customs_rate"] == 10


def test_incomplete_gazette_coverage_never_becomes_complete():
    result = resolve([], complete=False)
    assert result["calculation_status"] == "VERIFIED_PARTIAL"
    assert result["missing_elements"]
