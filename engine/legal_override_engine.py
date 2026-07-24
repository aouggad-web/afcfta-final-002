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
    LegalMeasureType,
    LegalOverrideMeasure,
    OverrideContext,
    OverrideTraceStep,
)


RATE_STAGES = (
    LegalMeasureType.EAC_CET_AMENDMENT,
    LegalMeasureType.STAY_OF_APPLICATION,
    LegalMeasureType.DUTY_REMISSION,
    LegalMeasureType.KENYA_NATIONAL_EXEMPTION,
)


def load_legal_measures(path: Path) -> List[LegalOverrideMeasure]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [LegalOverrideMeasure(**row) for row in payload.get("measures", [])]


class LegalOverrideResolver:
    def __init__(
        self,
        measures: Iterable[LegalOverrideMeasure],
        *,
        coverage_complete: bool = False,
    ):
        self.measures = list(measures)
        self.coverage_complete = coverage_complete

    @staticmethod
    def _condition(value: Optional[str], actual: Optional[str]) -> str:
        if not value or value.upper() in {"ALL", "ANY"}:
            return "MATCH"
        if actual is None:
            return "UNKNOWN"
        allowed = {part.strip().upper() for part in value.split(",")}
        return "MATCH" if actual.strip().upper() in allowed else "NO_MATCH"

    def _context_result(
        self, measure: LegalOverrideMeasure, context: OverrideContext
    ) -> str:
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
                outcome="APPLIED",
                rate_before=None,
                rate_after=base_rate,
                reason="Base CET rate supplied by the dated canonical tariff line.",
            )
        ]
        missing: List[str] = []
        sources = set()
        status = "VERIFIED_COMPLETE" if self.coverage_complete else "VERIFIED_PARTIAL"
        if not self.coverage_complete:
            missing.append("EAC gazette coverage is not complete for the requested date.")

        potentially_relevant = [
            m
            for m in self.measures
            if m.jurisdiction.upper() in {"EAC", context.jurisdiction.upper()}
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

        for stage in RATE_STAGES:
            matched: List[LegalOverrideMeasure] = []
            for measure in (m for m in candidates if m.measure_type == stage):
                condition = self._context_result(measure, context)
                sources.add(measure.publication_url)
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
                            measure_id=measure.measure_id,
                            outcome="CONDITION_UNRESOLVED",
                            rate_before=current_rate,
                            rate_after=current_rate,
                            legal_reference=measure.legal_reference,
                            publication_url=measure.publication_url,
                            reason=measure.condition_text or "Conditional measure requires more facts.",
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
                    f"{stage.value}: contradictory applicable override rates "
                    f"{sorted(rates)}."
                )
                for measure in matched:
                    trace.append(
                        OverrideTraceStep(
                            stage=stage.value,
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
            elif condition == "UNKNOWN":
                missing.append(f"{measure.measure_id}: administrative condition unresolved.")

        if missing and status != "CONFLICT_REVIEW":
            status = "VERIFIED_PARTIAL"
        return {
            "base_rate": base_rate,
            "override_rate": current_rate if current_rate != base_rate else None,
            "applicable_customs_rate": current_rate,
            "calculation_status": status,
            "trace": [step.model_dump() for step in trace],
            "missing_elements": list(dict.fromkeys(missing)),
            "restrictions": restrictions,
            "administrative_requirements": requirements,
            "sources_used": sorted(sources),
        }
