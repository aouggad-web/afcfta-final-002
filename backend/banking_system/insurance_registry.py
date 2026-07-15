"""
Insurance registry and country insurance profiles for AfCFTA operations.

Provides:
- Global insurers database
- Insurance products by risk level
- Country-specific insurance profiles linked to risk assessment
"""

from typing import Dict, List

from .models import (
    CountryInsuranceProfile,
    InsuranceCoverageScope,
    InsuranceProduct,
    InsuranceProductType,
    InsuranceRiskLevel,
    Insurer,
)
from .risk_assessment import RISK_PROFILES

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL INSURERS
# ─────────────────────────────────────────────────────────────────────────────

MAJOR_INSURERS = {
    "COFACE": Insurer(
        code="COFACE",
        name="Compagnie Française d'Assurance pour le Commerce Extérieur",
        abbreviation="COFACE",
        country_code="FR",
        credit_rating="A",
        total_capacity_usd_bn=50.0,
        specializations=["export_credit", "political_risk", "buyer_credit"],
        website="https://www.coface.com",
    ),
    "SMAEX": Insurer(
        code="SMAEX",
        name="Société Marocaine d'Assurance à l'Exportation",
        abbreviation="SMAEX",
        country_code="MA",
        credit_rating="BBB",
        total_capacity_usd_bn=3.0,
        specializations=["export_credit"],
        website="https://www.smaex.ma",
    ),
    "SARA": Insurer(
        code="SARA",
        name="Société Algérienne de Réassurance et d'Assurance",
        abbreviation="SARA",
        country_code="DZ",
        credit_rating="BB",
        total_capacity_usd_bn=2.0,
        specializations=["export_credit", "local_cover"],
    ),
    "COTUNACE": Insurer(
        code="COTUNACE",
        name="Compagnie Tunisienne d'Assurance et de Crédit à l'Export",
        abbreviation="COTUNACE",
        country_code="TN",
        credit_rating="BBB",
        total_capacity_usd_bn=1.5,
        specializations=["export_credit"],
    ),
    "ATRADIUS": Insurer(
        code="ATRADIUS",
        name="Atradius Dutch State Business N.V.",
        abbreviation="Atradius",
        country_code="NL",
        credit_rating="A+",
        total_capacity_usd_bn=45.0,
        specializations=["export_credit", "political_risk", "performance_guarantee"],
        website="https://www.atradius.com",
    ),
    "ZURICH": Insurer(
        code="ZURICH",
        name="Zurich Global Corporate",
        abbreviation="Zurich",
        country_code="CH",
        credit_rating="AAA",
        total_capacity_usd_bn=75.0,
        specializations=["export_credit", "political_risk", "performance_guarantee"],
        website="https://www.zurich.com",
    ),
    "UK_EXPORT_FINANCE": Insurer(
        code="UK_EXPORT_FINANCE",
        name="UK Export Finance",
        abbreviation="UKEF",
        country_code="GB",
        credit_rating="AAA",
        total_capacity_usd_bn=100.0,
        specializations=["export_credit", "political_risk", "buyer_credit"],
        website="https://www.gov.uk/government/organisations/uk-export-finance",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# INSURANCE PRODUCTS BY RISK LEVEL
# ─────────────────────────────────────────────────────────────────────────────


def _get_products_for_risk_level(risk_level: InsuranceRiskLevel) -> List[InsuranceProduct]:
    """Get insurance products available for a risk level."""

    base_rates = {
        InsuranceRiskLevel.VERY_LOW: 1.00,
        InsuranceRiskLevel.LOW: 1.50,
        InsuranceRiskLevel.MODERATE: 2.50,
        InsuranceRiskLevel.HIGH: 5.00,
        InsuranceRiskLevel.VERY_HIGH: 10.00,
    }

    base_rate = base_rates.get(risk_level, 2.50)

    products = [
        InsuranceProduct(
            code="EXPORT_CREDIT_SINGLE",
            name_en="Export Credit - Single Buyer",
            name_fr="Crédit Export - Monoacheteur",
            product_type=InsuranceProductType.EXPORT_CREDIT,
            coverage_scope=InsuranceCoverageScope.SINGLE_BUYER,
            coverage_percent=90.0,
            premium_rate_basis_points=base_rate * 100,
            min_premium_usd=500.0,
            max_coverage_usd=5_000_000.0,
            description="Protection for single buyer transactions",
        ),
        InsuranceProduct(
            code="EXPORT_CREDIT_COMPREHENSIVE",
            name_en="Export Credit - Comprehensive",
            name_fr="Crédit Export - Couverture Globale",
            product_type=InsuranceProductType.EXPORT_CREDIT,
            coverage_scope=InsuranceCoverageScope.COMPREHENSIVE,
            coverage_percent=85.0,
            premium_rate_basis_points=(base_rate * 0.8) * 100,
            min_premium_usd=1000.0,
            max_coverage_usd=50_000_000.0,
            description="Multi-buyer annual export credit policy",
        ),
        InsuranceProduct(
            code="POLITICAL_RISK",
            name_en="Political Risk Insurance",
            name_fr="Assurance Risque Politique",
            product_type=InsuranceProductType.POLITICAL_RISK,
            coverage_scope=InsuranceCoverageScope.POLICY_LIMIT,
            coverage_percent=95.0,
            premium_rate_basis_points=(base_rate * 1.5) * 100,
            min_premium_usd=750.0,
            max_coverage_usd=25_000_000.0,
            description="Coverage for political risk including confiscation, war, currency inconvertibility",
        ),
        InsuranceProduct(
            code="PERFORMANCE_GUARANTEE",
            name_en="Performance Guarantee Bond",
            name_fr="Garantie de Bonne Exécution",
            product_type=InsuranceProductType.PERFORMANCE_GUARANTEE,
            coverage_scope=InsuranceCoverageScope.POLICY_LIMIT,
            coverage_percent=100.0,
            premium_rate_basis_points=(base_rate * 0.5) * 100,
            min_premium_usd=250.0,
            max_coverage_usd=10_000_000.0,
            description="Bond covering supplier's performance obligations",
        ),
        InsuranceProduct(
            code="ADVANCE_PAYMENT_GUARANTEE",
            name_en="Advance Payment Guarantee",
            name_fr="Garantie d'Avance de Fonds",
            product_type=InsuranceProductType.ADVANCE_PAYMENT,
            coverage_scope=InsuranceCoverageScope.POLICY_LIMIT,
            coverage_percent=100.0,
            premium_rate_basis_points=(base_rate * 0.75) * 100,
            min_premium_usd=300.0,
            max_coverage_usd=10_000_000.0,
            description="Guarantee reimbursement of advance payments if buyer defaults",
        ),
        InsuranceProduct(
            code="TENDER_GUARANTEE",
            name_en="Tender/Bid Guarantee Bond",
            name_fr="Garantie de Soumission",
            product_type=InsuranceProductType.TENDER,
            coverage_scope=InsuranceCoverageScope.POLICY_LIMIT,
            coverage_percent=100.0,
            premium_rate_basis_points=(base_rate * 0.3) * 100,
            min_premium_usd=200.0,
            max_coverage_usd=5_000_000.0,
            description="Bond required during tender/bidding process",
        ),
    ]

    return products


# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY INSURANCE PROFILES
# ─────────────────────────────────────────────────────────────────────────────

# Build profiles for all 54 countries
INSURANCE_PROFILES: Dict[str, CountryInsuranceProfile] = {}


def _build_country_profiles():
    """Build insurance profiles for all countries linked to risk assessment."""

    risk_to_insurance_level = {
        "A1": InsuranceRiskLevel.VERY_LOW,
        "A2": InsuranceRiskLevel.LOW,
        "A3": InsuranceRiskLevel.MODERATE,
        "A4": InsuranceRiskLevel.MODERATE,
        "B": InsuranceRiskLevel.HIGH,
        "C": InsuranceRiskLevel.VERY_HIGH,
        "D": InsuranceRiskLevel.VERY_HIGH,
    }

    base_rates_pct = {
        InsuranceRiskLevel.VERY_LOW: 1.00,
        InsuranceRiskLevel.LOW: 1.50,
        InsuranceRiskLevel.MODERATE: 2.50,
        InsuranceRiskLevel.HIGH: 5.00,
        InsuranceRiskLevel.VERY_HIGH: 10.00,
    }

    market_confidence = {
        InsuranceRiskLevel.VERY_LOW: 100,
        InsuranceRiskLevel.LOW: 90,
        InsuranceRiskLevel.MODERATE: 75,
        InsuranceRiskLevel.HIGH: 50,
        InsuranceRiskLevel.VERY_HIGH: 25,
    }

    for country_code, risk_profile in RISK_PROFILES.items():
        risk_rating = risk_profile.country_risk_rating
        insurance_level = risk_to_insurance_level.get(risk_rating, InsuranceRiskLevel.MODERATE)
        base_rate = base_rates_pct.get(insurance_level, 2.50)

        # Select appropriate insurers
        if insurance_level == InsuranceRiskLevel.VERY_LOW:
            selected_insurers = [
                MAJOR_INSURERS["ZURICH"],
                MAJOR_INSURERS["UK_EXPORT_FINANCE"],
                MAJOR_INSURERS["ATRADIUS"],
            ]
        elif insurance_level == InsuranceRiskLevel.LOW:
            selected_insurers = [
                MAJOR_INSURERS["COFACE"],
                MAJOR_INSURERS["ZURICH"],
                MAJOR_INSURERS["ATRADIUS"],
            ]
        elif insurance_level == InsuranceRiskLevel.MODERATE:
            selected_insurers = [
                MAJOR_INSURERS["COFACE"],
                MAJOR_INSURERS["ATRADIUS"],
                MAJOR_INSURERS["SMAEX"],
            ]
        elif insurance_level == InsuranceRiskLevel.HIGH:
            selected_insurers = [
                MAJOR_INSURERS["COFACE"],
                MAJOR_INSURERS["SARA"],
                MAJOR_INSURERS["COTUNACE"],
            ]
        else:  # VERY_HIGH
            selected_insurers = [
                MAJOR_INSURERS["UK_EXPORT_FINANCE"],
                MAJOR_INSURERS["ZURICH"],
                MAJOR_INSURERS["COFACE"],
            ]

        profile = CountryInsuranceProfile(
            country_code=country_code,
            country_name=risk_profile.country_name,
            risk_level=insurance_level,
            available_products=_get_products_for_risk_level(insurance_level),
            available_insurers=selected_insurers,
            base_premium_rate_pct=base_rate,
            market_confidence=market_confidence.get(insurance_level, 50),
            notes=f"Profile linked to risk rating {risk_rating}",
        )

        INSURANCE_PROFILES[country_code] = profile


# Build profiles on module load
_build_country_profiles()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────


def get_country_insurance_profile(country_code: str) -> CountryInsuranceProfile:
    """Get insurance profile for a country."""
    country_code = country_code.upper()
    return INSURANCE_PROFILES.get(
        country_code,
        CountryInsuranceProfile(
            country_code=country_code,
            country_name=country_code,
            risk_level=InsuranceRiskLevel.MODERATE,
            available_products=_get_products_for_risk_level(InsuranceRiskLevel.MODERATE),
            available_insurers=[MAJOR_INSURERS["COFACE"]],
            base_premium_rate_pct=2.50,
            market_confidence=50,
            notes="Default profile for unmapped country",
        ),
    )


def get_available_insurers(country_code: str = None) -> List[Insurer]:
    """Get available insurers for a country (or global list if None)."""
    if country_code:
        profile = get_country_insurance_profile(country_code)
        return profile.available_insurers
    return list(MAJOR_INSURERS.values())


def get_available_products(country_code: str, risk_level: InsuranceRiskLevel = None):
    """Get available insurance products for a country."""
    if risk_level is None:
        profile = get_country_insurance_profile(country_code)
        risk_level = profile.risk_level

    return _get_products_for_risk_level(risk_level)
