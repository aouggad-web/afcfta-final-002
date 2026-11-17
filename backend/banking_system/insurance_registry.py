"""
Insurance registry for AfCFTA countries.

Provides:
- Registry of insurers active in African markets
- Insurance products available by country and risk level
- Country insurance profiles linked to risk assessment module
- Premium calculation based on country risk
"""

from typing import Dict, List, Optional

from .models.insurance_models import (
    CountryInsuranceProfile,
    InsuranceCoverageScope,
    InsuranceProduct,
    InsuranceProductType,
    InsuranceRiskLevel,
    Insurer,
)

# ─────────────────────────────────────────────────────────────────────────────
# MAJOR INSURANCE COMPANIES OPERATING IN AFRICA
# ─────────────────────────────────────────────────────────────────────────────

# Vérifié le 17/11/2026 sur les sites officiels (champ `source`) : seuls des
# ASSUREURS, qu'un exportateur ou un importateur peut contacter (remarque de
# l'exploitant du 16/11/2026 : jamais des réassureurs). Aucune valeur sans
# source : pas de notation ni de capacité, et un contact non publié reste vide.
# `active_countries` vide : toutes destinations, selon la politique de
# l'assureur ; qui peut souscrire est dit par `souscription`/`souscripteurs`.
# Retirés : « SARA » (aucune société de ce nom en Algérie ; l'assureur-crédit
# à l'export y est la CAGEX, le réassureur national la CCR), UK Export Finance
# (réservé aux exportateurs britanniques), Zurich (offre et présence en
# Afrique non vérifiables sur ses pages officielles).
MAJOR_INSURERS: Dict[str, Insurer] = {
    "CAGEX": Insurer(
        name="Compagnie Algérienne d'Assurance et de Garantie des Exportations",
        abbreviation="CAGEX",
        country_based="DZ",
        role="eca",
        insurance_type=[
            "Assurance-crédit à l'export (globale, individuelle)",
            "Assurance-crédit domestique",
            "Assurance foires et salons",
        ],
        products=[InsuranceProductType.EXPORT_CREDIT],
        souscription="pays",
        souscripteurs=["DZ"],
        website="https://www.cagex.dz",
        email="marketingcom@cagex.dz",
        phone="+213 23 31 21 00",
        established_year=1996,
        notes="10, route nationale n° 36, BP 116, Dely-Ibrahim, Alger. Ordonnance n° 96-06 du 10 janvier 1996.",
        source="https://www.cagex.dz",
    ),
    "SMAEX": Insurer(
        name="Société Marocaine d'Assurance à l'Exportation",
        abbreviation="SMAEX",
        country_based="MA",
        role="eca",
        insurance_type=[
            "Assurance-crédit à l'export (personnalisée, simplifiée, moyen terme)",
            "Assurance prospection",
            "Assurance foire",
        ],
        products=[InsuranceProductType.EXPORT_CREDIT],
        souscription="pays",
        souscripteurs=["MA"],
        website="https://www.smaex.com",
        email="smaex@smaex.com",
        phone="+212 5 22 98 20 00",
        established_year=1974,
        notes="24, rue Ali Abderrazak, Casablanca 20 100. Dahir n° 1-73-366 du 23 avril 1974.",
        source="https://www.smaex.com/contact_.php",
    ),
    "COTUNACE": Insurer(
        name="Compagnie Tunisienne pour l'Assurance du Commerce Extérieur",
        abbreviation="COTUNACE",
        country_based="TN",
        role="eca",
        insurance_type=["Assurance-crédit à l'export", "Assurance-crédit des ventes locales"],
        products=[InsuranceProductType.EXPORT_CREDIT],
        souscription="pays",
        souscripteurs=["TN"],
        website="https://www.cotunace.com.tn",
        notes=(
            "14, rue Borjine, 1073 Montplaisir, Tunis (états financiers publiés à la Bourse "
            "de Tunis). Site officiel indisponible lors de la vérification du 17/11/2026 : "
            "téléphone et e-mail non confirmés."
        ),
        source=(
            "https://bvmt.com.tn/sites/default/files/societes/cotunace/etats-financiers/"
            "cotunace-etats-financiers-annuels-31-12-2023.pdf"
        ),
    ),
    "ATIDI": Insurer(
        name="African Trade & Investment Development Insurance",
        abbreviation="ATIDI",
        country_based="KE",
        role="multilateral",
        insurance_type=["Assurance-crédit", "Risque politique et investissement", "Cautions"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.POLITICAL_RISK,
            InsuranceProductType.PERFORMANCE_GUARANTEE,
        ],
        souscription="etats_membres",
        website="https://www.atidi.africa",
        email="info@atidi.africa",
        phone="+254 719 014 000",
        notes="Kenya Re Towers, 5e étage, Ragati Road, Upperhill, Nairobi.",
        source="https://www.atidi.africa/contact-us/",
    ),
    "ICIEC": Insurer(
        name="Islamic Corporation for the Insurance of Investment and Export Credit",
        abbreviation="ICIEC",
        country_based="SA",
        role="multilateral",
        insurance_type=[
            "Assurance-crédit à l'export (crédit acheteur, fournisseur, lettre de crédit)",
            "Assurance des investissements (risque politique)",
        ],
        products=[InsuranceProductType.EXPORT_CREDIT, InsuranceProductType.POLITICAL_RISK],
        souscription="etats_membres",
        website="https://iciec.isdb.org",
        email="ICIEC-Communication@isdb.org",
        phone="+966 12 644 5666",
        established_year=1994,
        notes="Groupe de la Banque islamique de développement, Djeddah.",
        source="https://iciec.isdb.org/contact-us",
    ),
    "COFACE": Insurer(
        name="Coface",
        abbreviation="COFACE",
        country_based="FR",
        role="assureur_credit",
        insurance_type=["Assurance-crédit", "Risque politique"],
        products=[InsuranceProductType.EXPORT_CREDIT, InsuranceProductType.POLITICAL_RISK],
        souscription="ouvert",
        website="https://www.coface.com",
        established_year=1946,
        notes=(
            "Implantations en Afrique : Maroc (www.coface.ma, qui couvre aussi l'Algérie et "
            "la Tunisie), Égypte (www.coface.ae), Afrique du Sud (www.coface.co.za)."
        ),
        source="https://www.coface.com",
    ),
    "ATRADIUS": Insurer(
        name="Atradius",
        abbreviation="ATRADIUS",
        country_based="NL",
        role="assureur_credit",
        insurance_type=["Assurance-crédit", "Cautions"],
        products=[
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.PERFORMANCE_GUARANTEE,
        ],
        souscription="ouvert",
        website="https://group.atradius.com",
        notes="Implantation en Afrique : Afrique du Sud.",
        source="https://group.atradius.com/contact-us/",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# STANDARD INSURANCE PRODUCTS BY RISK LEVEL
# ─────────────────────────────────────────────────────────────────────────────


def _get_products_for_risk_level(risk_level: InsuranceRiskLevel) -> List[InsuranceProduct]:
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
            if not insurer.active_countries or country_code in insurer.active_countries
        ]

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

        profile = CountryInsuranceProfile(
            country_code=country_code,
            country_name=risk_profile.country_name,
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
_build_country_profiles()


# ─────────────────────────────────────────────────────────────────────────────
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
