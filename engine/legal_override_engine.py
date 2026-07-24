"""Resolve EAC/Kenya tariff overrides without blind precedence.

Only measures whose temporal, tariff and contextual conditions are satisfied
may change the rate.  Missing context creates a partial result; equally
applicable contradictory instruments create ``CONFLICT_REVIEW``.
"""

import json
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from engine.schemas.legal_override import (
    LegalLayer,
    LegalMeasureType,
    LegalOverrideMeasure,
    OverrideContext,
    OverrideTraceStep,
    RemissionEligibility,
)

RATE_STAGES = (
    LegalMeasureType.EAC_CET_AMENDMENT,
    LegalMeasureType.STAY_OF_APPLICATION,
    LegalMeasureType.DUTY_REMISSION,
    LegalMeasureType.KENYA_NATIONAL_EXEMPTION,
    LegalMeasureType.NATIONAL_EXEMPTION,
)

LAYERED_RATE_STAGES = tuple(
    (legal_layer, stage)
    for legal_layer in (LegalLayer.REGIONAL_COMMON, LegalLayer.NATIONAL_COUNTRY)
    for stage in RATE_STAGES
)


def _effective_layer(measure: LegalOverrideMeasure) -> LegalLayer:
    """Return explicit layer, with compatibility for legacy EAC/KEN rows."""
    if (
        measure.legal_layer == LegalLayer.NATIONAL_COUNTRY
        and measure.jurisdiction.strip().upper() in {"EAC", "KEN"}
        and measure.measure_type
        in {
            LegalMeasureType.EAC_CET_BASE,
            LegalMeasureType.EAC_CET_AMENDMENT,
            LegalMeasureType.STAY_OF_APPLICATION,
            LegalMeasureType.DUTY_REMISSION,
        }
        and not measure.regional_bloc
        and not measure.customs_territory
    ):
        return LegalLayer.REGIONAL_COMMON
    return measure.legal_layer


def load_legal_measures(path: Path) -> List[LegalOverrideMeasure]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [LegalOverrideMeasure(**row) for row in payload.get("measures", [])]


class LegalOverrideResolver:
    def __init__(
        self,
        measures: Iterable[LegalOverrideMeasure],
        *,
        coverage_complete: bool = False,
        regional_coverage_complete: Optional[bool] = None,
        national_coverage_complete: Optional[bool] = None,
    ):
        self.measures = list(measures)
        self.regional_coverage_complete = (
            coverage_complete
            if regional_coverage_complete is None
            else regional_coverage_complete
        )
        self.national_coverage_complete = (
            coverage_complete
            if national_coverage_complete is None
            else national_coverage_complete
        )

    @staticmethod
    def _condition(value: Optional[str], actual: Optional[str]) -> str:
        if not value or value.upper() in {"ALL", "ANY"}:
            return "MATCH"
        if actual is None:
            return "UNKNOWN"
        allowed = {part.strip().upper() for part in value.split(",")}
        return "MATCH" if actual.strip().upper() in allowed else "NO_MATCH"

    def _context_result(self, measure: LegalOverrideMeasure, context: OverrideContext) -> str:
        checks = (
            self._condition(measure.origin_scope, context.origin),
            self._condition(measure.beneficiary, context.beneficiary),
            self._condition(measure.import_purpose, context.import_purpose),
        )
        if "NO_MATCH" in checks:
            return "NO_MATCH"
        if measure.quantity_limit is not None:
            if context.quantity is None:
                return "UNKNOWN"
            if context.quantity > measure.quantity_limit:
                return "NO_MATCH"
        return "UNKNOWN" if "UNKNOWN" in checks else "MATCH"

    @staticmethod
    def _is_conditional_remission(measure: LegalOverrideMeasure) -> bool:
        return measure.measure_type == LegalMeasureType.DUTY_REMISSION and bool(
            measure.beneficiary
            or measure.import_purpose
            or measure.quantity_limit is not None
            or measure.condition_text
        )

    @staticmethod
    def _authorization_result(
        context: OverrideContext, hs_code: str, on_date: date
    ) -> tuple[str, str]:
        status = context.remission_eligibility
        if status == RemissionEligibility.NOT_ELIGIBLE:
            return "NOT_ELIGIBLE", "The importer states that it is not an authorized beneficiary."
        if status == RemissionEligibility.ELIGIBILITY_UNKNOWN:
            return "ELIGIBILITY_UNKNOWN", "Importer eligibility is unknown."
        if status == RemissionEligibility.AUTHORIZATION_REQUIRED:
            return "AUTHORIZATION_REQUIRED", "An official authorization or allocation is required."
        if not context.authorization_reference:
            return "AUTHORIZATION_REQUIRED", "The authorization reference is missing."
        if not context.authorization_effective_from or not context.authorization_effective_to:
            return "AUTHORIZATION_REQUIRED", "The authorization validity period is incomplete."
        if not (
            context.authorization_effective_from <= on_date <= context.authorization_effective_to
        ):
            return (
                "NOT_ELIGIBLE",
                "The supplied authorization is not effective on the calculation date.",
            )
        requested = "".join(ch for ch in hs_code if ch.isdigit())
        authorized = {
            "".join(ch for ch in code if ch.isdigit()) for code in context.authorization_hs_codes
        }
        if not requested or requested not in authorized:
            return (
                "AUTHORIZATION_REQUIRED",
                "The exact requested tariff line is absent from the authorized-goods list.",
            )
        return (
            "ELIGIBLE_VERIFIED",
            "The dated authorization expressly covers the requested tariff line.",
        )

    def _authorized_context_result(
        self, measure: LegalOverrideMeasure, context: OverrideContext
    ) -> str:
        """Authorization proves beneficiary/purpose; origin and quantity remain factual gates."""
        checks = (self._condition(measure.origin_scope, context.origin),)
        if "NO_MATCH" in checks:
            return "NO_MATCH"
        if measure.quantity_limit is not None:
            if context.quantity is None:
                return "UNKNOWN"
            if context.quantity > measure.quantity_limit:
                return "NO_MATCH"
        return "UNKNOWN" if "UNKNOWN" in checks else "MATCH"

    def resolve(
        self,
        *,
        hs_code: str,
        on_date: date,
        base_rate: float,
        context: Optional[OverrideContext] = None,
    ) -> dict:
        context = context or OverrideContext()
        current_rate = base_rate
        trace: List[OverrideTraceStep] = [
            OverrideTraceStep(
                stage=LegalMeasureType.EAC_CET_BASE.value,
                legal_layer=LegalLayer.REGIONAL_COMMON,
                jurisdiction=",".join(context.regional_blocs),
                outcome="APPLIED",
                rate_before=None,
                rate_after=base_rate,
                reason="Base CET rate supplied by the dated canonical tariff line.",
            )
        ]
        missing: List[str] = []
        sources = set()
        layer_sources = {layer: set() for layer in LegalLayer}
        eligibility_status = None
        requires_eligibility_input = False
        coverage_complete = (
            self.regional_coverage_complete and self.national_coverage_complete
        )
        status = "VERIFIED_COMPLETE" if coverage_complete else "VERIFIED_PARTIAL"
        if not self.regional_coverage_complete:
            missing.append("EAC gazette coverage is not complete for the requested date.")
        if not self.national_coverage_complete:
            missing.append(
                f"{context.jurisdiction} national-measure coverage is not complete for the requested date."
            )

        potentially_relevant = [
            m
            for m in self.measures
            if m.applies_to(context.jurisdiction, context.regional_blocs)
            and m.is_effective(on_date)
            and m.covers_hs(hs_code)
        ]
        candidates = []
        for measure in potentially_relevant:
            if measure.classification_allows_automatic_application():
                candidates.append(measure)
            else:
                missing.append(
                    f"{measure.measure_id}: HS6 mapping or human review does not permit automatic application."
                )
                trace.append(
                    OverrideTraceStep(
                        stage=measure.measure_type.value,
                        legal_layer=_effective_layer(measure),
                        jurisdiction=measure.jurisdiction,
                        measure_id=measure.measure_id,
                        outcome="MAPPING_REVIEW_REQUIRED",
                        rate_before=current_rate,
                        rate_after=current_rate,
                        legal_reference=measure.legal_reference,
                        publication_url=measure.publication_url,
                        reason=(
                            "Une mesure publiée dans la gazette pourrait concerner ce produit, "
                            "mais son rattachement SH6 ou ses conditions d’application "
                            "nécessitent une vérification."
                        ),
                    )
                )

        for legal_layer, stage in LAYERED_RATE_STAGES:
            matched: List[LegalOverrideMeasure] = []
            for measure in (
                m
                for m in candidates
                if _effective_layer(m) == legal_layer and m.measure_type == stage
            ):
                sources.add(measure.publication_url)
                layer_sources[_effective_layer(measure)].add(measure.publication_url)
                condition = self._context_result(measure, context)
                if self._is_conditional_remission(measure):
                    eligibility, eligibility_reason = self._authorization_result(
                        context, hs_code, on_date
                    )
                    eligibility_status = eligibility
                    if eligibility in {"ELIGIBILITY_UNKNOWN", "AUTHORIZATION_REQUIRED"}:
                        requires_eligibility_input = True
                        missing.append(f"{measure.measure_id}: {eligibility_reason}")
                        trace.append(
                            OverrideTraceStep(
                                stage=stage.value,
                                legal_layer=_effective_layer(measure),
                                jurisdiction=measure.jurisdiction,
                                measure_id=measure.measure_id,
                                outcome=eligibility,
                                rate_before=current_rate,
                                rate_after=current_rate,
                                legal_reference=measure.legal_reference,
                                publication_url=measure.publication_url,
                                reason=eligibility_reason,
                            )
                        )
                        continue
                    if eligibility == "NOT_ELIGIBLE":
                        trace.append(
                            OverrideTraceStep(
                                stage=stage.value,
                                legal_layer=_effective_layer(measure),
                                jurisdiction=measure.jurisdiction,
                                measure_id=measure.measure_id,
                                outcome="NOT_ELIGIBLE",
                                rate_before=current_rate,
                                rate_after=current_rate,
                                legal_reference=measure.legal_reference,
                                publication_url=measure.publication_url,
                                reason=eligibility_reason,
                            )
                        )
                        continue
                    condition = self._authorized_context_result(measure, context)
                if not measure.verification_status.startswith("VERIFIED"):
                    missing.append(
                        f"{measure.measure_id}: official source or extraction is not fully verified."
                    )
                if condition == "UNKNOWN":
                    missing.append(
                        f"{measure.measure_id}: beneficiary/origin/purpose/quantity context is missing."
                    )
                    trace.append(
                        OverrideTraceStep(
                            stage=stage.value,
                            legal_layer=_effective_layer(measure),
                            jurisdiction=measure.jurisdiction,
                            measure_id=measure.measure_id,
                            outcome="CONDITION_UNRESOLVED",
                            rate_before=current_rate,
                            rate_after=current_rate,
                            legal_reference=measure.legal_reference,
                            publication_url=measure.publication_url,
                            reason=measure.condition_text
                            or "Conditional measure requires more facts.",
                        )
                    )
                elif condition == "MATCH":
                    matched.append(measure)

            missing_rate = [m for m in matched if m.override_rate is None]
            for measure in missing_rate:
                missing.append(f"{measure.measure_id}: no computable ad valorem override rate.")
                trace.append(
                    OverrideTraceStep(
                        stage=stage.value,
                        legal_layer=_effective_layer(measure),
                        jurisdiction=measure.jurisdiction,
                        measure_id=measure.measure_id,
                        outcome="RATE_UNRESOLVED",
                        rate_before=current_rate,
                        rate_after=current_rate,
                        legal_reference=measure.legal_reference,
                        publication_url=measure.publication_url,
                        reason=measure.condition_text
                        or "The legal measure uses a non-ad-valorem or unresolved rate.",
                    )
                )
            matched = [m for m in matched if m.override_rate is not None]
            rates = {m.override_rate for m in matched}
            if len(rates) > 1:
                status = "CONFLICT_REVIEW"
                missing.append(
                    f"{stage.value}: contradictory applicable override rates " f"{sorted(rates)}."
                )
                for measure in matched:
                    trace.append(
                        OverrideTraceStep(
                            stage=stage.value,
                            legal_layer=_effective_layer(measure),
                            jurisdiction=measure.jurisdiction,
                            measure_id=measure.measure_id,
                            outcome="CONFLICT",
                            rate_before=current_rate,
                            rate_after=measure.override_rate,
                            legal_reference=measure.legal_reference,
                            publication_url=measure.publication_url,
                            reason="Another equally applicable instrument gives a different rate.",
                        )
                    )
                break
            if matched:
                measure = matched[0]
                before = current_rate
                if measure.override_rate is not None:
                    current_rate = measure.override_rate
                trace.append(
                    OverrideTraceStep(
                        stage=stage.value,
                        legal_layer=_effective_layer(measure),
                        jurisdiction=measure.jurisdiction,
                        measure_id=measure.measure_id,
                        outcome="APPLIED",
                        rate_before=before,
                        rate_after=current_rate,
                        legal_reference=measure.legal_reference,
                        publication_url=measure.publication_url,
                        reason=measure.condition_text or "All recorded conditions matched.",
                    )
                )

        restrictions = []
        requirements = []
        for measure in candidates:
            if measure.measure_type not in {
                LegalMeasureType.PROHIBITION_OR_RESTRICTION,
                LegalMeasureType.ADMINISTRATIVE_REQUIREMENT,
            }:
                continue
            condition = self._context_result(measure, context)
            if condition == "MATCH":
                target = (
                    restrictions
                    if measure.measure_type == LegalMeasureType.PROHIBITION_OR_RESTRICTION
                    else requirements
                )
                target.append(measure.model_dump())
                sources.add(measure.publication_url)
                layer_sources[_effective_layer(measure)].add(measure.publication_url)
            elif condition == "UNKNOWN":
                missing.append(f"{measure.measure_id}: administrative condition unresolved.")

        if missing and status != "CONFLICT_REVIEW":
            status = "VERIFIED_PARTIAL"
        serialized_trace = [step.model_dump() for step in trace]
        return {
            "base_rate": base_rate,
            "override_rate": current_rate if current_rate != base_rate else None,
            "applicable_customs_rate": current_rate,
            "calculation_status": status,
            "trace": serialized_trace,
            "missing_elements": list(dict.fromkeys(missing)),
            "restrictions": restrictions,
            "administrative_requirements": requirements,
            "sources_used": sorted(sources),
            "remission_eligibility_status": eligibility_status,
            "requires_eligibility_input": requires_eligibility_input,
            "legal_layers": {
                LegalLayer.REGIONAL_COMMON.value: {
                    "regional_blocs": context.regional_blocs,
                    "country_scope": context.jurisdiction,
                    "coverage_complete": self.regional_coverage_complete,
                    "trace": [
                        item
                        for item in serialized_trace
                        if item["legal_layer"] == LegalLayer.REGIONAL_COMMON
                    ],
                    "sources_used": sorted(layer_sources[LegalLayer.REGIONAL_COMMON]),
                },
                LegalLayer.NATIONAL_COUNTRY.value: {
                    "country": context.jurisdiction,
                    "coverage_complete": self.national_coverage_complete,
                    "trace": [
                        item
                        for item in serialized_trace
                        if item["legal_layer"] == LegalLayer.NATIONAL_COUNTRY
                    ],
                    "sources_used": sorted(layer_sources[LegalLayer.NATIONAL_COUNTRY]),
                },
            },
        }
