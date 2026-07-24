"""Temporal and conditional legal measures applied above a base tariff.

This schema deliberately keeps legal scope separate from the canonical tariff
line.  A canonical line answers "what does the CET table say?"; a
``LegalOverrideMeasure`` answers "does a later or conditional legal instrument
change that answer for this import, on this date?".
"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LegalMeasureType(str, Enum):
    EAC_CET_BASE = "EAC_CET_BASE"
    EAC_CET_AMENDMENT = "EAC_CET_AMENDMENT"
    STAY_OF_APPLICATION = "STAY_OF_APPLICATION"
    DUTY_REMISSION = "DUTY_REMISSION"
    KENYA_NATIONAL_EXEMPTION = "KENYA_NATIONAL_EXEMPTION"
    KENYA_NATIONAL_LEVY = "KENYA_NATIONAL_LEVY"
    PROHIBITION_OR_RESTRICTION = "PROHIBITION_OR_RESTRICTION"
    ADMINISTRATIVE_REQUIREMENT = "ADMINISTRATIVE_REQUIREMENT"


class RemissionEligibility(str, Enum):
    ELIGIBLE_VERIFIED = "ELIGIBLE_VERIFIED"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    ELIGIBILITY_UNKNOWN = "ELIGIBILITY_UNKNOWN"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"


class LegalOverrideMeasure(BaseModel):
    measure_id: str
    jurisdiction: str
    measure_type: LegalMeasureType
    legal_title: str
    gazette_number: Optional[str] = None
    gazette_date: Optional[date] = None
    legal_reference: str
    publication_url: str
    source_hash: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    hs_code_from: Optional[str] = None
    hs_code_to: Optional[str] = None
    hs_codes: List[str] = Field(default_factory=list)
    hs_version: str = "HS2022"
    product_description: str
    base_rate: Optional[float] = None
    override_rate: Optional[float] = None
    rate_unit: Optional[str] = None
    beneficiary: Optional[str] = None
    origin_scope: Optional[str] = None
    import_purpose: Optional[str] = None
    quantity_limit: Optional[float] = None
    condition_text: Optional[str] = None
    verification_status: str
    requires_human_review: bool = False
    mapping_status: str = "DIRECT_HS"
    mapping_confidence: int = Field(100, ge=0, le=100)

    def classification_allows_automatic_application(self) -> bool:
        return (
            self.mapping_status in {"DIRECT_HS", "EXACT_INDEX_MATCH", "VALIDATED_HS6"}
            and self.mapping_confidence >= 90
            and not self.requires_human_review
            and bool(self.hs_codes or self.hs_code_from)
        )

    def is_effective(self, on_date: date) -> bool:
        return self.effective_from <= on_date and (
            self.effective_to is None or on_date <= self.effective_to
        )

    def covers_hs(self, hs_code: str) -> bool:
        code = "".join(ch for ch in hs_code if ch.isdigit())
        explicit = {"".join(ch for ch in item if ch.isdigit()) for item in self.hs_codes}
        if explicit:
            return code in explicit
        start = "".join(ch for ch in (self.hs_code_from or "") if ch.isdigit())
        end = "".join(ch for ch in (self.hs_code_to or self.hs_code_from or "") if ch.isdigit())
        if not start:
            return True
        code = code[: len(start)]
        return start <= code <= end


class OverrideContext(BaseModel):
    jurisdiction: str = "KEN"
    origin: Optional[str] = None
    beneficiary: Optional[str] = None
    import_purpose: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0)
    remission_eligibility: RemissionEligibility = RemissionEligibility.ELIGIBILITY_UNKNOWN
    authorization_reference: Optional[str] = None
    authorization_effective_from: Optional[date] = None
    authorization_effective_to: Optional[date] = None
    authorization_hs_codes: List[str] = Field(default_factory=list)
    authorization_goods: List[str] = Field(default_factory=list)


class OverrideTraceStep(BaseModel):
    stage: str
    measure_id: Optional[str] = None
    outcome: str
    rate_before: Optional[float] = None
    rate_after: Optional[float] = None
    legal_reference: Optional[str] = None
    publication_url: Optional[str] = None
    reason: str
