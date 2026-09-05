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
    REGIONAL_TARIFF_BASE = "REGIONAL_TARIFF_BASE"
    REGIONAL_TARIFF_AMENDMENT = "REGIONAL_TARIFF_AMENDMENT"
    EAC_CET_BASE = "EAC_CET_BASE"
    EAC_CET_AMENDMENT = "EAC_CET_AMENDMENT"
    STAY_OF_APPLICATION = "STAY_OF_APPLICATION"
    DUTY_REMISSION = "DUTY_REMISSION"
    KENYA_NATIONAL_EXEMPTION = "KENYA_NATIONAL_EXEMPTION"
    KENYA_NATIONAL_LEVY = "KENYA_NATIONAL_LEVY"
    NATIONAL_EXEMPTION = "NATIONAL_EXEMPTION"
    NATIONAL_LEVY = "NATIONAL_LEVY"
    PROHIBITION_OR_RESTRICTION = "PROHIBITION_OR_RESTRICTION"
    ADMINISTRATIVE_REQUIREMENT = "ADMINISTRATIVE_REQUIREMENT"


class LegalLayer(str, Enum):
    REGIONAL_COMMON = "REGIONAL_COMMON"
    NATIONAL_COUNTRY = "NATIONAL_COUNTRY"


class RemissionEligibility(str, Enum):
    ELIGIBLE_VERIFIED = "ELIGIBLE_VERIFIED"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    ELIGIBILITY_UNKNOWN = "ELIGIBILITY_UNKNOWN"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"


class LegalOverrideMeasure(BaseModel):
    measure_id: str
    jurisdiction: str
    legal_layer: LegalLayer = LegalLayer.NATIONAL_COUNTRY
    regional_bloc: Optional[str] = None
    customs_territory: Optional[str] = None
    applicable_countries: List[str] = Field(default_factory=list)
    excluded_countries: List[str] = Field(default_factory=list)
    beneficiary_country: Optional[str] = None
    importing_country: Optional[str] = None
    exporting_country: Optional[str] = None
    national_codes: List[str] = Field(default_factory=list)
    end_use: Optional[str] = None
    authorization_required: bool = False
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

    def applies_to(
        self,
        country: str,
        regional_blocs: List[str],
        *,
        exporting_country: Optional[str] = None,
    ) -> bool:
        jurisdiction = self.jurisdiction.strip().upper()
        country = country.strip().upper()
        included = {item.strip().upper() for item in self.applicable_countries}
        excluded = {item.strip().upper() for item in self.excluded_countries}
        if country in excluded:
            return False
        if included and country not in included:
            return False
        if self.importing_country and self.importing_country.strip().upper() != country:
            return False
        if self.exporting_country:
            if not exporting_country:
                return False
            if self.exporting_country.strip().upper() != exporting_country.strip().upper():
                return False
        legacy_regional = (
            self.legal_layer == LegalLayer.NATIONAL_COUNTRY
            and jurisdiction in {"EAC", "KEN"}
            and self.measure_type
            in {
                LegalMeasureType.EAC_CET_BASE,
                LegalMeasureType.EAC_CET_AMENDMENT,
                LegalMeasureType.STAY_OF_APPLICATION,
                LegalMeasureType.DUTY_REMISSION,
            }
            and not self.regional_bloc
            and not self.customs_territory
        )
        if self.legal_layer == LegalLayer.REGIONAL_COMMON or legacy_regional:
            bloc = (
                (
                    self.customs_territory
                    or self.regional_bloc
                    or ("EAC" if legacy_regional else jurisdiction)
                )
                .strip()
                .upper()
            )
            return bool(bloc) and bloc in {item.strip().upper() for item in regional_blocs}
        return jurisdiction in {"ALL", "ANY", country}

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
    # Backwards-compatible default for the Kenya calculator. Generic callers
    # should pass the destination ISO3 explicitly when using another country.
    jurisdiction: str = "KEN"
    # Kenya's historical resolver API did not require a bloc argument. Keep
    # EAC as the compatibility default while callers for other countries (or
    # an explicitly unverified membership) must pass their own list.
    regional_blocs: List[str] = Field(default_factory=lambda: ["EAC"])
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
    legal_layer: Optional[LegalLayer] = None
    jurisdiction: Optional[str] = None
    measure_id: Optional[str] = None
    outcome: str
    rate_before: Optional[float] = None
    rate_after: Optional[float] = None
    legal_reference: Optional[str] = None
    publication_url: Optional[str] = None
    reason: str
