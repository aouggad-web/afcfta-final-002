"""
<<<<<<< HEAD
Insurance registry and country insurance profiles for AfCFTA operations.

Provides:
- Global insurers database
- Insurance products by risk level
- Country-specific insurance profiles linked to risk assessment
"""

from typing import Dict, List

from .models import (
=======
Insurance registry for AfCFTA countries.

Provides:
- Registry of insurers active in African markets
- Insurance products available by country and risk level
- Country insurance profiles linked to risk assessment module
- Premium calculation based on country risk
"""

from typing import Dict, List, Optional

from .models.insurance_models import (
>>>>>>> origin/main
    CountryInsuranceProfile,
    InsuranceCoverageScope,
    InsuranceProduct,
    InsuranceProductType,
    InsuranceRiskLevel,
    Insurer,
)
<<<<<<< HEAD
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
=======

# ─────────────────────────────────────────────────────────────────────────────
# MAJOR INSURANCE COMPANIES OPERATING IN AFRICA
# ─────────────────────────────────────────────────────────────────────────────

MAJOR_INSURERS: Dict[str, Insurer] = {
    "COFACE": Insurer(
        name="Coface Group",
        abbreviation="COFACE",
        country_based="FR",
        insurance_type=["Credit Insurance", "Political Risk"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.POLITICAL_RISK,
        ],
        active_countries=[
            "MA",
            "DZ",
            "TN",
            "EG",
            "NG",
            "GH",
            "CI",
            "SN",
            "KE",
            "TZ",
            "ZA",
            "ZM",
            "MZ",
            "UG",
            "MW",
            "RW",
            "CM",
            "GA",
            "SZ",
        ],
        website="https://www.coface.com",
        email="support@coface.com",
        credit_rating="A",
        total_capacity_usd_bn=15.5,
        established_year=1946,
    ),
    "SMAEX": Insurer(
        name="Société Marocaine d'Assurance à l'Exportation",
        abbreviation="SMAEX",
        country_based="MA",
        insurance_type=["Export Credit Insurance"],
        products=[InsuranceProductType.EXPORT_CREDIT],
        active_countries=["MA", "NG", "SN", "CI", "GH"],
        website="https://www.smaex.ma",
        credit_rating="BBB+",
        established_year=1992,
    ),
    "SARA": Insurer(
        name="SARA - Société Algérienne de Réassurance et d'Assurance",
        abbreviation="SARA",
        country_based="DZ",
        insurance_type=["General Insurance", "Reinsurance"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.TRANSPORT,
        ],
        active_countries=["DZ", "MA", "TN"],
        website="https://www.sara.dz",
        credit_rating="BBB",
        established_year=1974,
    ),
    "COTUNACE": Insurer(
        name="COTUNACE - Compagnie Tunisienne d'Assurance-Crédit à l'Export",
        abbreviation="COTUNACE",
        country_based="TN",
        insurance_type=["Export Credit Insurance"],
        products=[InsuranceProductType.EXPORT_CREDIT],
        active_countries=["TN", "MA", "DZ", "SN"],
        website="https://www.cotunace.com.tn",
        credit_rating="BBB",
        established_year=1989,
    ),
    "ATRADIUS": Insurer(
        name="Atradius Credit Insurance",
        abbreviation="ATRADIUS",
        country_based="NL",
        insurance_type=["Credit Insurance", "Bonding"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.PERFORMANCE_GUARANTEE,
        ],
        active_countries=[
            "ZA",
            "KE",
            "NG",
            "GH",
            "CI",
            "EG",
            "MA",
            "TZ",
            "UG",
            "MW",
        ],
        website="https://www.atradius.com",
        credit_rating="A+",
        total_capacity_usd_bn=12.0,
        established_year=2002,
    ),
    "ZURICH": Insurer(
        name="Zurich Insurance Group",
        abbreviation="ZURICH",
        country_based="CH",
        insurance_type=["General Insurance", "Trade Insurance"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.POLITICAL_RISK,
            InsuranceProductType.TRANSPORT,
        ],
        active_countries=[
            "ZA",
            "KE",
            "NG",
            "GH",
            "TZ",
            "UG",
            "RW",
            "MW",
            "ZM",
            "MA",
        ],
        website="https://www.zurich.co.za",
        credit_rating="AA",
        total_capacity_usd_bn=25.0,
        established_year=1872,
    ),
    "EXPORT_CREDIT": Insurer(
        name="UK Export Finance (UK ECA equivalent)",
        abbreviation="UK-EXPORT",
        country_based="GB",
        insurance_type=["Export Credit Agency", "Political Risk"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.POLITICAL_RISK,
        ],
        active_countries=[
            "NG",
            "GH",
            "ZA",
            "KE",
            "EG",
            "MA",
            "TZ",
            "UG",
            "CM",
            "GA",
        ],
        website="https://www.gov.uk/government/organisations/uk-export-finance",
        credit_rating="AAA",
        established_year=1919,
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# STANDARD INSURANCE PRODUCTS BY RISK LEVEL
>>>>>>> origin/main
# ─────────────────────────────────────────────────────────────────────────────


def _get_products_for_risk_level(risk_level: InsuranceRiskLevel) -> List[InsuranceProduct]:
<<<<<<< HEAD
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
=======
    """Get standard insurance products and pricing for a risk level."""

    base_rate_bps = {
        InsuranceRiskLevel.VERY_LOW: 100,  # 1.00%
        InsuranceRiskLevel.LOW: 150,  # 1.50%
        InsuranceRiskLevel.MODERATE: 250,  # 2.50%
        InsuranceRiskLevel.HIGH: 500,  # 5.00%
        InsuranceRiskLevel.VERY_HIGH: 1000,  # 10.00%
    }

    rate = base_rate_bps.get(risk_level, 250)

    return [
        InsuranceProduct(
            product_type=InsuranceProductType.EXPORT_CREDIT,
            name_en="Export Credit Insurance – Single Buyer",
            name_fr="Assurance-Crédit Export – Acheteur Unique",
            description="Covers non-payment risk for specific buyer",
            coverage_scope=InsuranceCoverageScope.SINGLE_BUYER,
            min_coverage_usd=10_000,
            max_coverage_usd=2_000_000,
            coverage_percent=90.0,
            premium_rate_basis_points=rate,
            deductible_percent=5.0,
            payment_terms_days=90,
            max_single_buyer_percent=100.0,
            min_premium_usd=100,
        ),
        InsuranceProduct(
            product_type=InsuranceProductType.EXPORT_CREDIT,
            name_en="Export Credit Insurance – Comprehensive",
            name_fr="Assurance-Crédit Export – Couverture Complète",
            description="Covers portfolio of buyers with automatic cover",
            coverage_scope=InsuranceCoverageScope.COMPREHENSIVE,
            min_coverage_usd=50_000,
            max_coverage_usd=10_000_000,
            coverage_percent=85.0,
            premium_rate_basis_points=int(rate * 0.85),
            deductible_percent=10.0,
            payment_terms_days=120,
            max_single_buyer_percent=50.0,
            min_premium_usd=500,
        ),
        InsuranceProduct(
            product_type=InsuranceProductType.POLITICAL_RISK,
            name_en="Political Risk Insurance",
            name_fr="Assurance Risque Politique",
            description="Covers transfer risk, expropriation, war, civil disorder",
            coverage_scope=InsuranceCoverageScope.LONG_TERM,
            min_coverage_usd=50_000,
            max_coverage_usd=5_000_000,
            coverage_percent=90.0,
            premium_rate_basis_points=int(rate * 1.5),
            deductible_percent=2.5,
            payment_terms_days=365,
            min_premium_usd=250,
        ),
        InsuranceProduct(
            product_type=InsuranceProductType.PERFORMANCE_GUARANTEE,
            name_en="Performance Guarantee Insurance",
            name_fr="Assurance Garantie de Performance",
            description="Covers failure to perform under contract",
            coverage_scope=InsuranceCoverageScope.SINGLE_BUYER,
            min_coverage_usd=50_000,
            max_coverage_usd=3_000_000,
            coverage_percent=90.0,
            premium_rate_basis_points=int(rate * 2.0),
            deductible_percent=10.0,
            payment_terms_days=180,
            min_premium_usd=300,
        ),
        InsuranceProduct(
            product_type=InsuranceProductType.ADVANCE_PAYMENT,
            name_en="Advance Payment Guarantee Insurance",
            name_fr="Assurance Garantie de Restitution d'Avance",
            description="Covers repayment of advance payments if seller fails",
            coverage_scope=InsuranceCoverageScope.SINGLE_BUYER,
            min_coverage_usd=50_000,
            max_coverage_usd=5_000_000,
            coverage_percent=90.0,
            premium_rate_basis_points=int(rate * 1.8),
            deductible_percent=5.0,
            payment_terms_days=180,
            min_premium_usd=250,
        ),
        InsuranceProduct(
            product_type=InsuranceProductType.TENDER,
            name_en="Tender Guarantee Insurance",
            name_fr="Assurance Garantie d'Appel d'Offres",
            description="Covers bid/tender bond requirements",
            coverage_scope=InsuranceCoverageScope.SINGLE_BUYER,
            min_coverage_usd=10_000,
            max_coverage_usd=1_000_000,
            coverage_percent=100.0,
            premium_rate_basis_points=int(rate * 0.5),
            deductible_percent=0.0,
            payment_terms_days=90,
            min_premium_usd=50,
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY INSURANCE PROFILES (Linked to risk_assessment.py)
# ─────────────────────────────────────────────────────────────────────────────

COUNTRY_INSURANCE_PROFILES: Dict[str, CountryInsuranceProfile] = {}


def _build_country_profiles():
    """Build insurance profiles for all 54 AfCFTA countries, linked to risk assessment."""

    from . import risk_assessment

    # Map country risk ratings to insurance risk levels
    risk_mapping = {
        "A1": InsuranceRiskLevel.VERY_LOW,
        "A2": InsuranceRiskLevel.VERY_LOW,
        "A3": InsuranceRiskLevel.LOW,
        "A4": InsuranceRiskLevel.LOW,
        "B": InsuranceRiskLevel.MODERATE,
        "C": InsuranceRiskLevel.HIGH,
        "D": InsuranceRiskLevel.VERY_HIGH,
    }

    for country_code, risk_profile in risk_assessment.RISK_PROFILES.items():
        insurance_risk = risk_mapping.get(
            risk_profile.country_risk_rating, InsuranceRiskLevel.MODERATE
        )

        # Determine available insurers and products
        available_insurers = [
            insurer
            for insurer in MAJOR_INSURERS.values()
            if country_code in insurer.active_countries
        ]

        if not available_insurers:
            # Fallback: add generic insurers for countries without specific coverage
            available_insurers = [MAJOR_INSURERS.get("ZURICH"), MAJOR_INSURERS.get("ATRADIUS")]
            available_insurers = [i for i in available_insurers if i]

        products = _get_products_for_risk_level(insurance_risk)

        # Market confidence based on insurance availability
        market_confidence = (
            "high"
            if len(available_insurers) >= 3
            else "moderate" if len(available_insurers) >= 1 else "low"
        )

        # Premium adjustments based on additional risk factors
        premium_adj = 0.0
        if risk_profile.forex_risk == "very_high":
            premium_adj += 2.0
        if risk_profile.political_risk == "high":
            premium_adj += 1.5
        if risk_profile.political_risk == "very_high":
            premium_adj += 3.0
>>>>>>> origin/main

        profile = CountryInsuranceProfile(
            country_code=country_code,
            country_name=risk_profile.country_name,
<<<<<<< HEAD
            risk_level=insurance_level,
            available_products=_get_products_for_risk_level(insurance_level),
            available_insurers=selected_insurers,
            base_premium_rate_pct=base_rate,
            market_confidence=market_confidence.get(insurance_level, 50),
            notes=f"Profile linked to risk rating {risk_rating}",
        )

        INSURANCE_PROFILES[country_code] = profile


# Build profiles on module load
=======
            risk_level=insurance_risk,
            risk_rating_source=f"Coface {risk_profile.country_risk_rating}",
            available_insurers=available_insurers,
            available_products=products,
            premium_adjustment_percent=premium_adj,
            maximum_insurable_amount_usd=risk_profile.max_exposure_usd,
            market_confidence=market_confidence,
            notes=risk_profile.notes,
        )
        COUNTRY_INSURANCE_PROFILES[country_code] = profile


# Build profiles on import
>>>>>>> origin/main
_build_country_profiles()


# ─────────────────────────────────────────────────────────────────────────────
<<<<<<< HEAD
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
=======
# PUBLIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def get_country_insurance_profile(country_code: str) -> Optional[CountryInsuranceProfile]:
    """Get insurance profile for a country."""
    return COUNTRY_INSURANCE_PROFILES.get(country_code.upper())


def get_available_insurers(country_code: str) -> List[Insurer]:
    """Get list of insurers active in a country."""
    profile = get_country_insurance_profile(country_code)
    return profile.available_insurers if profile else []


def get_available_products(country_code: str) -> List[InsuranceProduct]:
    """Get list of insurance products available in a country."""
    profile = get_country_insurance_profile(country_code)
    return profile.available_products if profile else []


def get_insurance_registry() -> Dict[str, CountryInsuranceProfile]:
    """Get complete insurance registry for all countries."""
    return COUNTRY_INSURANCE_PROFILES
>>>>>>> origin/main
