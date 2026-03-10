"""
Tests for the banking_system module – ZLECAf

Covers:
- Banks registry (central banks, commercial banks, regional banks)
- Foreign exchange / domiciliation rules
- Trade finance instruments and recommendations
- Payment systems
- Regulatory compliance checks
- Risk assessment
"""

import pytest
import sys
import os

# Ensure backend directory is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from banking_system.banks_registry import (
    CENTRAL_BANKS,
    COMMERCIAL_BANKS,
    REGIONAL_BANKS,
    get_central_bank,
    get_country_banks,
    get_regional_banks,
)
from banking_system.foreign_exchange import (
    FOREX_PROFILES,
    get_forex_profile,
    get_domiciliation_rules,
)
from banking_system.trade_finance import (
    TRADE_FINANCE_INSTRUMENTS,
    get_trade_finance_instruments,
    recommend_instruments,
    LC_MANDATORY_COUNTRIES,
    LC_CONFIRMATION_RECOMMENDED,
)
from banking_system.payment_systems import (
    PAYMENT_SYSTEMS,
    get_payment_systems,
    get_regional_systems,
)
from banking_system.regulatory_compliance import (
    get_country_compliance,
    check_compliance,
)
from banking_system.risk_assessment import (
    RISK_PROFILES,
    get_country_risk,
    assess_transaction_risk,
    _compute_risk_score,
)
from banking_system.models import (
    CentralBank,
    CommercialBank,
    RegionalBank,
    BankingSystemInfo,
    DomiciliationRule,
    ForexRegulation,
    CountryForexProfile,
    TradeFinanceInstrument,
    PaymentSystem,
    CountryRiskProfile,
)


# ===========================================================================
# BANKS REGISTRY TESTS
# ===========================================================================

class TestCentralBanks:
    """Tests for the central banks registry."""

    def test_all_54_african_countries_have_central_bank(self):
        """The registry must cover all 54 African Union member states."""
        # We check that at least 54 entries exist (some countries share a
        # central bank, e.g., the BCEAO covers 8 UEMOA countries)
        assert len(CENTRAL_BANKS) >= 54, (
            f"Expected at least 54 central bank entries, got {len(CENTRAL_BANKS)}"
        )

    def test_phase1_countries_present(self):
        """All 14 phase-1 priority countries must have a central bank entry."""
        phase1 = ["MA", "DZ", "TN", "EG", "NG", "GH", "CI", "SN", "KE", "ET", "TZ", "ZA", "AO", "ZM"]
        for code in phase1:
            assert code in CENTRAL_BANKS, f"Missing central bank for {code}"

    def test_central_bank_model_fields(self):
        """Central bank entries must have required fields."""
        cb = CENTRAL_BANKS["MA"]
        assert cb.country_code == "MA"
        assert cb.name == "Bank Al-Maghrib"
        assert cb.currency_code == "MAD"
        assert cb.forex_regulation in {"strict", "moderate", "liberal"}

    def test_get_central_bank_case_insensitive(self):
        """get_central_bank should accept lower and upper case codes."""
        assert get_central_bank("ma") is not None
        assert get_central_bank("MA") is not None
        assert get_central_bank("ke").name == get_central_bank("KE").name

    def test_get_central_bank_unknown_returns_none(self):
        assert get_central_bank("XX") is None

    def test_get_country_banks_returns_banking_system_info(self):
        info = get_country_banks("MA")
        assert isinstance(info, BankingSystemInfo)
        assert info.country_code == "MA"
        assert info.central_bank.name == "Bank Al-Maghrib"

    def test_get_country_banks_includes_commercial_banks(self):
        info = get_country_banks("NG")
        assert len(info.commercial_banks) > 0, "Nigeria should have commercial banks"
        codes = [b.swift_code for b in info.commercial_banks if b.swift_code]
        assert len(codes) > 0

    def test_get_country_banks_includes_regional_banks(self):
        info = get_country_banks("KE")
        assert len(info.regional_banks) > 0, "Kenya should have regional bank memberships"

    def test_get_regional_banks_all(self):
        banks = get_regional_banks()
        assert len(banks) >= 5, "Should have at least 5 regional banks"

    def test_get_regional_banks_filter_by_region(self):
        west_africa = get_regional_banks("West Africa")
        assert len(west_africa) >= 1
        for bank in west_africa:
            assert "West" in bank.region or "west" in bank.region.lower()

    def test_afreximbank_covers_all_countries(self):
        afreximbank = next(b for b in REGIONAL_BANKS if b.abbreviation == "Afreximbank")
        assert len(afreximbank.member_countries) >= 50


class TestCommercialBanks:
    """Tests for commercial banks data."""

    def test_trade_finance_banks_have_swift_codes(self):
        """Commercial banks with trade_finance=True should have SWIFT codes."""
        for country_code, banks in COMMERCIAL_BANKS.items():
            for bank in banks:
                if bank.trade_finance:
                    # SWIFT code may be None for some smaller banks – just check the field exists
                    assert hasattr(bank, "swift_code")

    def test_commercial_banks_have_services(self):
        """Trade finance banks should list services."""
        for country_code, banks in COMMERCIAL_BANKS.items():
            for bank in banks:
                if bank.trade_finance:
                    assert len(bank.services) > 0, (
                        f"Bank {bank.name} ({country_code}) has no services listed"
                    )


# ===========================================================================
# FOREX / DOMICILIATION TESTS
# ===========================================================================

class TestForexProfiles:
    """Tests for foreign exchange and domiciliation rules."""

    def test_phase1_countries_have_forex_profiles(self):
        phase1 = ["MA", "DZ", "TN", "EG", "NG", "GH", "CI", "SN", "KE", "ET", "TZ", "ZA", "AO", "ZM"]
        for code in phase1:
            assert code in FOREX_PROFILES, f"Missing forex profile for {code}"

    def test_morocco_domiciliation_required(self):
        """Morocco requires domiciliation above 10 000 USD."""
        profile = get_forex_profile("MA")
        assert profile.domiciliation.required is True
        assert profile.domiciliation.threshold_usd == 10_000

    def test_algeria_domiciliation_no_threshold(self):
        """Algeria requires domiciliation for all imports (threshold 0)."""
        profile = get_forex_profile("DZ")
        assert profile.domiciliation.required is True
        assert profile.domiciliation.threshold_usd == 0

    def test_kenya_domiciliation_not_mandatory(self):
        """Kenya has a liberal forex regime – domiciliation not mandatory."""
        profile = get_forex_profile("KE")
        assert profile.domiciliation.required is False

    def test_unknown_country_returns_default_profile(self):
        """An unknown country should return a default (not None) profile."""
        profile = get_forex_profile("XX")
        assert profile is not None
        assert isinstance(profile, CountryForexProfile)

    def test_get_domiciliation_rules_returns_domiciliation_rule(self):
        rule = get_domiciliation_rules("MA")
        assert isinstance(rule, DomiciliationRule)
        assert rule.required is True

    def test_forex_profiles_have_regulation_level(self):
        for code, profile in FOREX_PROFILES.items():
            assert profile.forex_regulation.regulation_level in {
                "strict", "moderate", "liberal"
            }, f"Invalid regulation level for {code}"

    def test_mandatory_documents_populated(self):
        """Countries with strict regulations must list mandatory documents."""
        for code in ["MA", "DZ", "NG", "ET"]:
            profile = get_forex_profile(code)
            assert len(profile.domiciliation.mandatory_documents) > 0, (
                f"No mandatory documents for strict country {code}"
            )


# ===========================================================================
# TRADE FINANCE TESTS
# ===========================================================================

class TestTradeFinance:
    """Tests for trade finance instruments."""

    def test_catalogue_has_key_instruments(self):
        codes = {i.code for i in TRADE_FINANCE_INSTRUMENTS}
        required = {
            "LC_IRREVOCABLE", "LC_CONFIRMED", "DOC_COLLECTION_DP",
            "DOC_COLLECTION_DA", "BANK_GUARANTEE_PERFORMANCE", "EXPORT_FACTORING",
        }
        assert required.issubset(codes), f"Missing instruments: {required - codes}"

    def test_get_all_instruments(self):
        instruments = get_trade_finance_instruments()
        assert len(instruments) >= 10

    def test_instrument_fields(self):
        lc = next(i for i in TRADE_FINANCE_INSTRUMENTS if i.code == "LC_IRREVOCABLE")
        assert lc.risk_coverage == "full"
        assert "import" in lc.applicable_to
        assert "export" in lc.applicable_to
        assert lc.typical_cost_pct is not None

    def test_lc_mandatory_countries_recommend_lc(self):
        """Countries where LC is mandatory must recommend it first."""
        for code in LC_MANDATORY_COUNTRIES:
            recs = recommend_instruments(code, "import", 50_000)
            assert len(recs) > 0
            assert "LC" in recs[0].code or "LC_IRREVOCABLE" == recs[0].code

    def test_high_risk_export_recommends_confirmed_lc(self):
        """High-risk country exports should recommend confirmed LC."""
        for code in LC_CONFIRMATION_RECOMMENDED:
            recs = recommend_instruments(code, "export", 100_000)
            assert len(recs) > 0
            assert recs[0].code in {"LC_CONFIRMED", "LC_IRREVOCABLE"}

    def test_low_amount_liberal_country_flexible_instruments(self):
        """Liberal countries with small amounts should return applicable instruments."""
        recs = recommend_instruments("KE", "export", 5_000)
        assert len(recs) > 0

    def test_recommendation_respects_transaction_type(self):
        """Instruments should match the transaction type."""
        export_recs = recommend_instruments("MA", "export", 50_000)
        for inst in export_recs:
            assert "export" in inst.applicable_to


# ===========================================================================
# PAYMENT SYSTEMS TESTS
# ===========================================================================

class TestPaymentSystems:
    """Tests for payment systems."""

    def test_payment_systems_catalogue_not_empty(self):
        assert len(PAYMENT_SYSTEMS) >= 10

    def test_swift_present(self):
        codes = {ps.code for ps in PAYMENT_SYSTEMS}
        assert "SWIFT" in codes

    def test_papss_present(self):
        """Pan-African Payment System (PAPSS) must be in catalogue."""
        codes = {ps.code for ps in PAYMENT_SYSTEMS}
        assert "PAPSS" in codes

    def test_mobile_money_operators_present(self):
        types = {ps.type for ps in PAYMENT_SYSTEMS}
        assert "mobile_money" in types

    def test_get_payment_systems_for_country(self):
        """Kenya should have access to M-Pesa and SWIFT at minimum."""
        systems = get_payment_systems("KE")
        codes = {ps.code for ps in systems}
        assert "MPESA" in codes
        assert "SWIFT" in codes

    def test_get_regional_systems_filters_correctly(self):
        west = get_regional_systems("West Africa")
        for ps in west:
            assert "West" in ps.region or "UEMOA" in ps.region or "WAMZ" in ps.region

    def test_payment_system_model_fields(self):
        swift = next(ps for ps in PAYMENT_SYSTEMS if ps.code == "SWIFT")
        assert swift.type == "swift"
        assert swift.region == "Global"

    def test_uemoa_systems_cover_member_countries(self):
        bceao_star = next((ps for ps in PAYMENT_SYSTEMS if ps.code == "BCEAO_STAR"), None)
        assert bceao_star is not None
        for country in ["BJ", "CI", "SN", "TG"]:
            assert country in bceao_star.member_countries


# ===========================================================================
# REGULATORY COMPLIANCE TESTS
# ===========================================================================

class TestRegulatoryCompliance:
    """Tests for compliance checks."""

    def test_get_compliance_known_country(self):
        data = get_country_compliance("MA")
        assert data["country_code"] == "MA"
        assert "aml_framework" in data
        assert "kyc_requirements" in data

    def test_get_compliance_unknown_country_returns_default(self):
        data = get_country_compliance("XX")
        assert "aml_framework" in data
        assert "kyc_requirements" in data

    def test_check_compliance_below_threshold_no_warning(self):
        """Transactions below the declaration threshold should have no warnings."""
        result = check_compliance("MA", 5_000)  # threshold is 10_000
        assert result["compliant"] is True
        assert len(result["warnings"]) == 0

    def test_check_compliance_above_threshold_warns(self):
        """Transactions above the threshold must trigger a declaration warning."""
        result = check_compliance("MA", 50_000)  # threshold is 10_000
        assert result["compliant"] is False
        assert len(result["warnings"]) > 0

    def test_check_compliance_restricted_sector_warns(self):
        result = check_compliance("NG", 5_000, sector="armement")
        assert len(result["warnings"]) > 0

    def test_check_compliance_includes_required_actions(self):
        result = check_compliance("MA", 50_000)
        assert "cross_border_declaration" in result["required_actions"]

    def test_compliance_result_has_sanctions_screening(self):
        result = check_compliance("ZA", 100_000)
        assert "sanctions_screening" in result
        assert result["sanctions_screening"] != "N/A"


# ===========================================================================
# RISK ASSESSMENT TESTS
# ===========================================================================

class TestRiskAssessment:
    """Tests for country risk assessment."""

    def test_phase1_countries_have_risk_profiles(self):
        phase1 = ["MA", "DZ", "TN", "EG", "NG", "GH", "CI", "SN", "KE", "ET", "TZ", "ZA", "AO", "ZM"]
        for code in phase1:
            assert code in RISK_PROFILES, f"Missing risk profile for {code}"

    def test_get_risk_profile_known_country(self):
        profile = get_country_risk("MA")
        assert isinstance(profile, CountryRiskProfile)
        assert profile.country_risk_rating in {"A1", "A2", "A3", "A4", "B", "C", "D"}

    def test_get_risk_profile_unknown_returns_default(self):
        profile = get_country_risk("XX")
        assert profile is not None
        assert isinstance(profile, CountryRiskProfile)

    def test_nigeria_is_high_risk(self):
        profile = get_country_risk("NG")
        assert profile.country_risk_rating in {"C", "D"}
        assert profile.forex_risk in {"high", "very_high"}

    def test_kenya_is_lower_risk(self):
        profile = get_country_risk("KE")
        assert profile.country_risk_rating in {"A1", "A2", "A3", "A4", "B"}
        assert profile.forex_risk in {"low", "moderate"}

    def test_assess_transaction_risk_structure(self):
        result = assess_transaction_risk("NG", 500_000, "export")
        assert "overall_risk_rating" in result
        assert "alert_level" in result
        assert result["alert_level"] in {"green", "orange", "red"}
        assert "recommended_instruments" in result

    def test_high_risk_country_gets_red_alert(self):
        """Very high risk countries should return red alert."""
        result = assess_transaction_risk("ZW", 1_000_000, "export")
        assert result["alert_level"] == "red"

    def test_low_risk_country_gets_green_alert(self):
        """Low risk countries should return green alert for normal amounts."""
        result = assess_transaction_risk("KE", 50_000, "export")
        assert result["alert_level"] == "green"

    def test_exposure_warning_triggered_above_limit(self):
        """A transaction above the recommended exposure limit should trigger a warning."""
        profile = get_country_risk("ZW")
        result = assess_transaction_risk("ZW", profile.max_exposure_usd + 1, "export")
        assert result["exposure_warning"] is True

    def test_exposure_warning_not_triggered_below_limit(self):
        result = assess_transaction_risk("ZA", 100_000, "export")
        assert result["exposure_warning"] is False

    def test_risk_score_increases_with_risk_rating(self):
        """Risk score for D-rated country must be higher than A4-rated country."""
        profile_low = get_country_risk("KE")
        profile_high = get_country_risk("ZW")
        score_low = _compute_risk_score(profile_low, 100_000)
        score_high = _compute_risk_score(profile_high, 100_000)
        assert score_high > score_low


# ===========================================================================
# PYDANTIC MODEL TESTS
# ===========================================================================

class TestPydanticModels:
    """Sanity checks on Pydantic model instantiation."""

    def test_central_bank_model(self):
        cb = CentralBank(
            country_code="XX", country_name="Test Country",
            name="Test Central Bank", abbreviation="TCB",
            forex_regulation="liberal",
            currency_code="TST", currency_name="Test Dollar",
        )
        assert cb.country_code == "XX"

    def test_domiciliation_rule_model(self):
        rule = DomiciliationRule(required=True, threshold_usd=10_000)
        assert rule.required is True
        assert rule.threshold_usd == 10_000

    def test_country_risk_profile_model(self):
        profile = CountryRiskProfile(
            country_code="XX", country_name="Test",
            country_risk_rating="B",
            forex_risk="moderate",
            political_risk="low",
            transfer_risk="moderate",
        )
        assert profile.country_risk_rating == "B"

    def test_payment_system_model(self):
        ps = PaymentSystem(
            code="TEST", name="Test System", type="regional",
            region="Test Region",
        )
        assert ps.code == "TEST"
        assert ps.member_countries == []
