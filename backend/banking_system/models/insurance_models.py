"""
<<<<<<< HEAD
Pydantic models for insurance products, insurers, and country insurance profiles
"""

from enum import Enum
from typing import List, Optional
=======
Pydantic models for credit insurance and trade insurance in AfCFTA.

Covers export credit insurance, political risk insurance, and trade finance insurance.
"""

from enum import Enum
from typing import Dict, List, Optional
>>>>>>> origin/main

from pydantic import BaseModel, Field


class InsuranceProductType(str, Enum):
<<<<<<< HEAD
    """Types of insurance products available"""

    EXPORT_CREDIT = "export_credit"
    POLITICAL_RISK = "political_risk"
    PERFORMANCE_GUARANTEE = "performance_guarantee"
    ADVANCE_PAYMENT = "advance_payment"
    TENDER = "tender"
    CONTINGENCY = "contingency"


class InsuranceCoverageScope(str, Enum):
    """Scope of insurance coverage"""

    SINGLE_BUYER = "single_buyer"
    COMPREHENSIVE = "comprehensive"
    POLICY_LIMIT = "policy_limit"


class InsuranceRiskLevel(str, Enum):
    """Risk levels for insurance pricing"""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class InsuranceProduct(BaseModel):
    """Insurance product details"""

    code: str = Field(..., description="Internal product code")
    name_en: str
    name_fr: str
    product_type: InsuranceProductType
    coverage_scope: InsuranceCoverageScope
    coverage_percent: float = Field(..., description="Coverage percentage (0-100)")
    premium_rate_basis_points: float = Field(
        ..., description="Premium rate in basis points (1 bp = 0.01%)"
    )
    min_premium_usd: float = Field(default=500.0)
    max_coverage_usd: float = Field(default=10_000_000.0)
    description: str = ""


class Insurer(BaseModel):
    """Insurance company details"""

    code: str
    name: str
    abbreviation: str
    country_code: str
    credit_rating: str = Field(..., description="Credit rating: AAA, AA, A, BBB, etc.")
    total_capacity_usd_bn: float = Field(..., description="Total underwriting capacity in billions")
    specializations: List[str] = Field(default_factory=list)
    website: Optional[str] = None


class CountryInsuranceProfile(BaseModel):
    """Insurance availability and pricing profile for a country"""

    country_code: str
    country_name: str
    risk_level: InsuranceRiskLevel
    available_products: List[InsuranceProduct] = Field(default_factory=list)
    available_insurers: List[Insurer] = Field(default_factory=list)
    base_premium_rate_pct: float = Field(..., description="Base premium rate for export credit")
    market_confidence: float = Field(
        ..., description="Market confidence level (0-100)", ge=0, le=100
=======
    """Types of insurance products"""

    EXPORT_CREDIT = "export_credit"  # Assurance-crédit export (acheteurs)
    POLITICAL_RISK = "political_risk"  # Risque politique
    PERFORMANCE_GUARANTEE = "performance_guarantee"  # Garantie de performance
    ADVANCE_PAYMENT = "advance_payment"  # Garantie de restitution
    TENDER = "tender"  # Garantie d'appel d'offres
    TRANSPORT = "transport"  # Assurance transport


class InsuranceCoverageScope(str, Enum):
    """Coverage scope for insurance products"""

    SINGLE_BUYER = "single_buyer"  # Couverture acheteur unique
    COMPREHENSIVE = "comprehensive"  # Couverture complète (portefeuille)
    SHORT_TERM = "short_term"  # Court terme (< 180 jours)
    MEDIUM_TERM = "medium_term"  # Moyen terme (180 jours - 2 ans)
    LONG_TERM = "long_term"  # Long terme (2-5+ ans)


class InsuranceRiskLevel(str, Enum):
    """Risk classification for insurance pricing"""

    VERY_LOW = "very_low"  # A1-A2 countries
    LOW = "low"  # A3-A4 countries
    MODERATE = "moderate"  # B countries
    HIGH = "high"  # C countries
    VERY_HIGH = "very_high"  # D countries


class InsuranceProduct(BaseModel):
    """Insurance product available in African country"""

    product_type: InsuranceProductType = Field(
        ..., description="Type of insurance product (export_credit, political_risk, etc.)"
    )
    name_en: str = Field(..., description="English name of the product")
    name_fr: str = Field(..., description="French name of the product")
    description: Optional[str] = None
    coverage_scope: InsuranceCoverageScope = Field(
        default=InsuranceCoverageScope.COMPREHENSIVE,
        description="Scope of coverage",
    )
    min_coverage_usd: Optional[float] = Field(
        default=None, description="Minimum coverage amount in USD"
    )
    max_coverage_usd: Optional[float] = Field(
        default=None, description="Maximum coverage amount in USD"
    )
    coverage_percent: float = Field(
        default=90.0,
        ge=0,
        le=100,
        description="Percentage of losses covered (0-100%)",
    )
    premium_rate_basis_points: float = Field(
        default=150,
        ge=0,
        description="Base premium rate in basis points (ex: 150 = 1.5%)",
    )
    min_premium_usd: Optional[float] = Field(default=None, description="Minimum premium amount")
    deductible_percent: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Deductible as percentage of contract value",
    )
    payment_terms_days: int = Field(default=90, description="Credit period covered in days")
    eligible_sectors: List[str] = Field(
        default_factory=list,
        description="Specific sectors eligible for this product (empty = all sectors)",
    )
    excluded_sectors: List[str] = Field(
        default_factory=list, description="Sectors excluded from coverage"
    )
    geographic_scope: List[str] = Field(
        default_factory=list,
        description="ISO2 codes of eligible buyer countries (empty = unrestricted)",
    )
    documentation_required: List[str] = Field(
        default_factory=list, description="Required documentation types"
    )
    waiting_period_days: int = Field(default=30, description="Waiting period after policy issue")
    max_single_buyer_percent: float = Field(
        default=50.0, description="Max % of portfolio for single buyer"
>>>>>>> origin/main
    )
    notes: Optional[str] = None


class InsuranceQuote(BaseModel):
<<<<<<< HEAD
    """Insurance quote for a specific transaction"""

    country_code: str
    product_type: InsuranceProductType
    amount_usd: float
    base_premium_usd: float
    adjustments: dict = Field(default_factory=dict, description="Premium adjustments by factor")
    adjusted_premium_usd: float
    total_annual_premium_usd: float
    coverage_usd: float
    coverage_percent: float
    insurer_recommended: Optional[str] = None
    quote_valid_days: int = 30


class InsuranceClaim(BaseModel):
    """Insurance claim record"""

    claim_id: str
    country_code: str
    amount_claim_usd: float
    amount_approved_usd: float
    product_type: InsuranceProductType
    status: str = Field(..., description="pending | approved | rejected | paid")
    submission_date: str
    decision_date: Optional[str] = None
=======
    """Insurance premium quote for a specific transaction"""

    country_code: str = Field(..., description="ISO2 code of the buyer country")
    product_type: InsuranceProductType
    contract_value_usd: float = Field(..., gt=0, description="Contract/transaction value")
    risk_level: InsuranceRiskLevel
    payment_terms_days: int = Field(default=90, description="Payment terms in days")
    premium_rate_bps: float = Field(
        ..., description="Premium rate in basis points (already adjusted for risk)"
    )
    base_premium_usd: float = Field(..., description="Base premium amount (before adjustments)")
    risk_adjustment_percent: float = Field(
        default=0, description="Risk adjustment applied to base rate"
    )
    final_premium_usd: float = Field(..., description="Final premium amount to be paid")
    min_premium_usd: Optional[float] = None
    coverage_usd: float = Field(..., description="Amount of coverage provided")
    deductible_usd: float = Field(..., description="Deductible amount")
    validity_days: int = Field(default=365, description="Quote validity in days")
    notes: Optional[str] = None


class Insurer(BaseModel):
    """Insurance company offering products in African market"""

    name: str = Field(..., description="Company name")
    abbreviation: Optional[str] = None
    country_based: str = Field(..., description="ISO2 code of company's base country/headquarters")
    insurance_type: List[str] = Field(
        default_factory=list, description="Types of insurance offered (e.g., 'COFACE', 'SARA')"
    )
    products: List[InsuranceProductType] = Field(
        default_factory=list, description="Insurance products offered"
    )
    active_countries: List[str] = Field(
        default_factory=list, description="ISO2 codes where insurer is active"
    )
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    established_year: Optional[int] = None
    credit_rating: Optional[str] = Field(
        default=None, description="Credit rating (e.g., AA, A+, BBB+)"
    )
    total_capacity_usd_bn: Optional[float] = Field(
        default=None, description="Estimated total capacity in billions USD"
    )
    notes: Optional[str] = None


class CountryInsuranceProfile(BaseModel):
    """Complete insurance profile for a country"""

    country_code: str = Field(..., description="ISO2 country code")
    country_name: str
    risk_level: InsuranceRiskLevel = Field(
        ..., description="Insurance risk classification for premium calculation"
    )
    risk_rating_source: str = Field(
        default="Coface/OECD", description="Source of country risk rating"
    )
    available_insurers: List[Insurer] = Field(
        default_factory=list, description="Insurers active in this country"
    )
    available_products: List[InsuranceProduct] = Field(
        default_factory=list, description="Insurance products available"
    )
    premium_adjustment_percent: float = Field(
        default=0.0,
        description="Country-specific adjustment to premiums (e.g., political risk premium)",
    )
    maximum_insurable_amount_usd: Optional[float] = Field(
        default=None, description="Maximum amount the market can insure for this country"
    )
    market_confidence: str = Field(
        default="moderate",
        description="Market confidence level: low | moderate | high",
    )
    notes: Optional[str] = None
    last_updated: Optional[str] = None


class InsuranceClaim(BaseModel):
    """Insurance claim information"""

    claim_id: str
    country_code: str
    product_type: InsuranceProductType
    claim_amount_usd: float
    claim_date: str  # ISO format
    claim_reason: str  # (e.g., "non_payment", "political_risk", "force_majeure")
    claim_status: str  # "pending", "approved", "rejected", "paid"
    claim_payment_date: Optional[str] = None
    payment_amount_usd: Optional[float] = None
>>>>>>> origin/main
    notes: Optional[str] = None
