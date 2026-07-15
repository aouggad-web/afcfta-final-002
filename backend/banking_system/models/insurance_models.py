"""
Pydantic models for insurance products, insurers, and country insurance profiles
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class InsuranceProductType(str, Enum):
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
    )
    notes: Optional[str] = None


class InsuranceQuote(BaseModel):
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
    notes: Optional[str] = None
