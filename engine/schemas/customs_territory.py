"""Generic, dated customs-territory and trade-measure entities.

The schema separates a common regional tariff from country fiscal layers. It
does not infer that a present-day membership was effective historically.
"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TerritoryType(str, Enum):
    CUSTOMS_UNION = "CUSTOMS_UNION"
    FREE_TRADE_AREA = "FREE_TRADE_AREA"
    NATIONAL = "NATIONAL"


class ImplementationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRANSITIONAL = "TRANSITIONAL"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    INACTIVE = "INACTIVE"


class CoverageStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    AVAILABLE_UNVERIFIED = "AVAILABLE_UNVERIFIED"
    SOURCE_PENDING = "SOURCE_PENDING"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class CustomsTerritory(BaseModel):
    territory_id: str
    name: str
    territory_type: TerritoryType
    tariff_authority: bool = False
    priority: int = Field(100, ge=0)
    source_id: str


class TerritoryMembership(BaseModel):
    territory_id: str
    country_iso3: str
    valid_from: date
    valid_to: Optional[date] = None
    implementation_status: ImplementationStatus
    source_id: str

    def is_active(self, on_date: date) -> bool:
        return (
            self.implementation_status
            in {ImplementationStatus.ACTIVE, ImplementationStatus.TRANSITIONAL}
            and self.valid_from <= on_date
            and (self.valid_to is None or on_date <= self.valid_to)
        )


class RegionalTariff(BaseModel):
    tariff_id: str
    territory_id: str
    hs6: str
    hs_version: str
    rate: Optional[float] = None
    rate_unit: str = "%"
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus


class NationalTariff(BaseModel):
    tariff_id: str
    country_iso3: str
    hs6: str
    national_code: Optional[str] = None
    hs_version: str
    rate: Optional[float] = None
    rate_unit: str = "%"
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus


class LegalOverrideScope(BaseModel):
    measure_id: str
    customs_territory: Optional[str] = None
    applicable_countries: List[str] = Field(default_factory=list)
    excluded_countries: List[str] = Field(default_factory=list)
    beneficiary_country: Optional[str] = None
    importing_country: Optional[str] = None
    exporting_country: Optional[str] = None
    origin_scope: Optional[str] = None
    hs6: Optional[str] = None
    national_codes: List[str] = Field(default_factory=list)
    end_use: Optional[str] = None
    beneficiary: Optional[str] = None
    authorization_required: bool = False
    effective_from: date
    effective_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus
    requires_human_review: bool = False


class RegionalLegalOverride(LegalOverrideScope):
    measure_type: str
    legal_title: str
    legal_reference: str
    publication_url: Optional[str] = None
    base_rate: Optional[float] = None
    override_rate: Optional[float] = None
    rate_unit: Optional[str] = None
    condition_text: Optional[str] = None


class NationalLegalOverride(LegalOverrideScope):
    country_iso3: str
    measure_type: str
    legal_title: str
    legal_reference: str
    publication_url: Optional[str] = None
    base_rate: Optional[float] = None
    override_rate: Optional[float] = None
    rate_unit: Optional[str] = None
    condition_text: Optional[str] = None


class TariffReference(BaseModel):
    tariff_id: str
    territory_id: Optional[str] = None
    country_iso3: Optional[str] = None
    hs_version: str
    tariff_year: Optional[int] = None
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    source_url: Optional[str] = None
    verification_status: CoverageStatus


class PreferentialRegime(BaseModel):
    regime_id: str
    name: str
    territory_id: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    origin_rule_required: bool = True
    reciprocity_required: bool = True
    source_id: str
    verification_status: CoverageStatus


class ReciprocityStatus(BaseModel):
    regime_id: str
    importing_country: str
    exporting_country: str
    valid_from: date
    valid_to: Optional[date] = None
    status: str
    source_id: str


class OriginRule(BaseModel):
    rule_id: str
    regime_id: str
    hs6_from: Optional[str] = None
    hs6_to: Optional[str] = None
    rule_text: str
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus


class NationalTax(BaseModel):
    tax_id: str
    country_iso3: str
    tax_type: str
    code: Optional[str] = None
    name: Optional[str] = None
    rate_pct: Optional[float] = None
    rate_unit: str = "%"
    basis: str = "CIF"
    basis_includes: List[str] = Field(default_factory=list)
    sequence: int = 100
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus


class AdministrativeFormality(BaseModel):
    formality_id: str
    country_iso3: str
    requirement_type: str
    hs6_from: Optional[str] = None
    hs6_to: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    source_id: str
    verification_status: CoverageStatus


class HsConcordance(BaseModel):
    hs_version_source: str
    hs6_source: str
    hs_version_target: str
    hs6_target: str
    country_iso3: str
    national_code: str
    mapping_type: str
    confidence: float = Field(ge=0, le=1)
    source_id: str
    valid_from: date
    valid_to: Optional[date] = None


class CountryCoveragePeriod(BaseModel):
    country_iso3: str
    valid_from: date
    valid_to: Optional[date] = None
    base_tariff_coverage: CoverageStatus
    regional_override_coverage: CoverageStatus
    national_tax_coverage: CoverageStatus
    national_exemption_coverage: CoverageStatus
    preferential_tariff_coverage: CoverageStatus
    reciprocity_coverage: CoverageStatus
    rules_of_origin_coverage: CoverageStatus
    formalities_coverage: CoverageStatus
    overall_calculation_confidence: float = Field(ge=0, le=1)
    complete_hs6_count: int = Field(ge=0)
    partial_hs6_count: int = Field(ge=0)
    missing_sources: List[str] = Field(default_factory=list)
