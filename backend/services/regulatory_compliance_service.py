"""Source-bound import formalities and government-mandated service providers."""

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
RESOLVED_REPO_ROOT = REPO_ROOT.resolve()

COUNTRY_REGULATORY_PATHS = {
    "CIV": "data/cote-d-ivoire/regulatory_measures.json",
    "COD": "data/drc/regulatory_measures.json",
    "CMR": "data/cameroon/regulatory_measures.json",
    "GHA": "data/ghana/regulatory_measures.json",
    "KEN": "data/kenya/regulatory_measures.json",
    "NGA": "data/nigeria/regulatory_measures.json",
}

_DATASET_REQUIRED_FIELDS = {
    "country",
    "as_of",
    "measure_type",
    "regulatory_measures",
}

_MEASURE_REQUIRED_FIELDS = {
    "record_id",
    "measure_name",
    "measure_category",
    "scope",
    "products",
    "transport",
    "conditions",
    "documents",
    "authority",
    "platform",
    "exemptions",
    "fees",
    "fees_status",
    "source_id",
    "legal_reference",
    "verification_status",
    "mandated_actor_status",
}

# Distinguishes, for a measure with no mandated_actors, whether that's because
# no private/mandated provider is involved (NOT_APPLICABLE — the regulatory
# authority operates the formality directly, confirmed by source text) or
# because a provider is known or suspected to exist but hasn't been
# identified/documented yet (NOT_AVAILABLE). Never inferred silently: a
# measure only gets NOT_APPLICABLE when a source explicitly describes direct
# operation by the authority, not merely from the absence of a documented
# actor.
_MANDATED_ACTOR_STATUSES = {"DOCUMENTED", "NOT_APPLICABLE", "NOT_AVAILABLE"}

# mandate_status values that constitute a confirmed, currently active mandate.
# A measure only counts as DOCUMENTED when at least one actor is in this set —
# a TERMINATED actor (mandate confirmed ended) or an UNVERIFIED one (no source
# confirms it's still active) is retained in mandated_actors as history, but
# never by itself forces the measure-level status to DOCUMENTED. This lets a
# measure whose source now confirms direct administration operation report
# NOT_APPLICABLE/NOT_AVAILABLE while still keeping the historical actor record
# (e.g. GHA-GSA-EASYPASS, taken back in-house by the GSA from 1 July 2026,
# retains Bureau Veritas/Intertek as historical entries without contradicting
# its NOT_APPLICABLE status).
_ACTIVE_MANDATE_STATUSES = {"CONFIRMED_TIME_LIMITED", "CONFIRMED_UNDATED_END"}

# Diplomatic framing surfaced whenever a country's dataset carries at least one
# documented mandated actor. Confiding part of the execution of a formality to
# a mandated provider is presented as a punctual, capacity-support arrangement
# accompanying the administration's own modernization — never as a comment on
# that administration's competence, and never implying the delegation is
# permanent where sources don't say so.
_MANDATED_ACTOR_DELEGATION_NOTE = (
    "Le recours à un prestataire mandaté est une mesure d’exécution ponctuelle, "
    "mise en œuvre en appui à l’administration mandante le temps que celle-ci "
    "achève ses propres réformes et sa modernisation — l’administration demeure "
    "seule détentrice de la mission réglementaire et du pouvoir de décision."
)

_ACTOR_REQUIRED_FIELDS = {
    "actor_name",
    "actor_type",
    "legal_status",
    "mandating_authority",
    "mission",
    "mandate_basis",
    "mandate_status",
    "mandate_duration",
    "mandate_evidence",
    "authorized_fees",
    "authorized_fees_status",
    "delivered_document",
    "verification_status",
}

_EVIDENCE_REQUIRED_FIELDS = {"date", "title", "publisher", "url"}

# LOT 4 (issue #359): optional structured fields layered on top of the free-text
# scope/transport/exemptions fields above. Optional (not in _MEASURE_REQUIRED_FIELDS)
# so datasets that predate this structuring keep validating unchanged; validated for
# internal consistency whenever a country's dataset opts in by including them.
_SCOPE_TYPES = {"GENERAL", "SECTORAL", "CONDITIONAL", "NOT_AVAILABLE"}
_TRANSPORT_MODES = {"MARITIME", "AERIEN", "ROUTIER", "FERROVIAIRE", "MULTIMODAL"}
_STRUCTURED_FIELD_STATUSES = {"DOCUMENTED", "NOT_AVAILABLE"}
_PROCEDURE_STATUSES = {"DOCUMENTED", "PARTIAL", "NOT_AVAILABLE"}


def _validate_structured_scope_fields(measure: Dict[str, Any], context: str) -> None:
    if "scope_type" in measure and measure["scope_type"] not in _SCOPE_TYPES:
        raise ValueError(f"{context} has non-canonical scope_type {measure['scope_type']!r}")

    if "transport_modes" in measure:
        modes = measure["transport_modes"]
        if not isinstance(modes, list) or not modes:
            raise ValueError(f"{context} transport_modes must be a non-empty list")
        invalid = [mode for mode in modes if mode not in _TRANSPORT_MODES]
        if invalid:
            raise ValueError(f"{context} has non-canonical transport_modes: {invalid}")

    if "hs_codes_status" in measure:
        status = measure["hs_codes_status"]
        if status not in _STRUCTURED_FIELD_STATUSES:
            raise ValueError(f"{context} has non-canonical hs_codes_status {status!r}")
        has_codes = bool(measure.get("hs_codes_explicit"))
        if status == "DOCUMENTED" and not has_codes:
            raise ValueError(f"{context} hs_codes_status is DOCUMENTED without hs_codes_explicit")
        if status == "NOT_AVAILABLE" and has_codes:
            raise ValueError(
                f"{context} hs_codes_status is NOT_AVAILABLE while hs_codes_explicit is populated"
            )

    if "thresholds_and_exclusions" in measure:
        block = measure["thresholds_and_exclusions"]
        if not isinstance(block, dict) or {"text", "status"} - set(block):
            raise ValueError(f"{context} thresholds_and_exclusions must have text and status")
        status = block["status"]
        if status not in _STRUCTURED_FIELD_STATUSES:
            raise ValueError(
                f"{context} thresholds_and_exclusions has non-canonical status {status!r}"
            )
        if status == "DOCUMENTED" and not block["text"]:
            raise ValueError(f"{context} thresholds_and_exclusions is DOCUMENTED without text")
        if status == "NOT_AVAILABLE" and block["text"] is not None:
            raise ValueError(
                f"{context} thresholds_and_exclusions is NOT_AVAILABLE but text is populated"
            )

    if "procedure" in measure:
        block = measure["procedure"]
        if not isinstance(block, dict) or {"steps", "official_delay", "status"} - set(block):
            raise ValueError(f"{context} procedure must have steps, official_delay and status")
        status = block["status"]
        if status not in _PROCEDURE_STATUSES:
            raise ValueError(f"{context} procedure has non-canonical status {status!r}")
        if status == "NOT_AVAILABLE" and (
            block["steps"] is not None or block["official_delay"] is not None
        ):
            raise ValueError(
                f"{context} procedure is NOT_AVAILABLE but steps/official_delay is not null"
            )
        if status != "NOT_AVAILABLE" and not block["steps"]:
            raise ValueError(f"{context} procedure status {status!r} requires non-empty steps")

    if "fee_category" in measure and measure["fee_category"] != "REGULATORY_FEE":
        raise ValueError(f"{context} fee_category must be REGULATORY_FEE when present on a measure")


@lru_cache(maxsize=None)
def _read_json(relative_path: str) -> Dict[str, Any]:
    path = (RESOLVED_REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(RESOLVED_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Regulatory source path resolves outside repository: {relative_path}"
        ) from exc
    return json.loads(path.read_text(encoding="utf-8"))


def _is_empty_value(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def _require_non_empty(
    record: Dict[str, Any], fields: set, context: str, allow_empty: Optional[set] = None
) -> None:
    missing = sorted(field for field in fields if field not in record)
    if missing:
        raise ValueError(f"{context} is missing required fields: {', '.join(missing)}")
    nullable_fields = allow_empty or set()
    empty = sorted(
        field
        for field in fields
        if field not in nullable_fields and _is_empty_value(record.get(field))
    )
    if empty:
        raise ValueError(f"{context} has empty required fields: {', '.join(empty)}")


def _normalize_actor(
    actor: Dict[str, Any], measure: Dict[str, Any], source_record_path: str
) -> Dict[str, Any]:
    context = f"Mandated actor {actor.get('actor_name') or '<unknown>'}"
    _require_non_empty(actor, _ACTOR_REQUIRED_FIELDS, context, allow_empty={"authorized_fees"})

    if str(actor["mandate_status"]).casefold() == "active":
        raise ValueError(f"{context} uses an undated bare ACTIVE mandate status")

    evidence = actor["mandate_evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError(f"{context} must include dated mandate evidence")
    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{context} evidence #{index} is not an object")
        _require_non_empty(item, _EVIDENCE_REQUIRED_FIELDS, f"{context} evidence #{index}")

    if actor["authorized_fees"] is not None and actor["authorized_fees_status"] == "NOT_AVAILABLE":
        raise ValueError(f"{context} publishes fees while their status is NOT_AVAILABLE")

    if "fee_category" in actor and actor["fee_category"] != "PROVIDER_FEE":
        raise ValueError(f"{context} fee_category must be PROVIDER_FEE when present on an actor")

    normalized = copy.deepcopy(actor)
    normalized.update(
        {
            "measure_record_id": measure["record_id"],
            "regulatory_authority": measure["authority"],
            "source_id": measure["source_id"],
            "legal_reference": measure["legal_reference"],
            "measure_verification_status": measure["verification_status"],
            "pending_primary_archive": measure.get("pending_primary_archive", False),
            "source_record_path": source_record_path,
        }
    )
    return normalized


def get_supported_regulatory_countries() -> List[str]:
    """Return countries with a source-bound regulatory-compliance dataset."""

    return sorted(COUNTRY_REGULATORY_PATHS)


def get_country_regulatory_compliance(country_iso3: str) -> Optional[Dict[str, Any]]:
    """Return formalities and mandated providers without synthesising missing values."""

    country = country_iso3.upper()
    source_record_path = COUNTRY_REGULATORY_PATHS.get(country)
    if source_record_path is None:
        return None

    dataset = _read_json(source_record_path)
    _require_non_empty(
        dataset,
        _DATASET_REQUIRED_FIELDS,
        f"Regulatory dataset {country}",
        allow_empty={"regulatory_measures"},
    )
    if dataset.get("country") != country:
        raise ValueError(
            f"Regulatory dataset country mismatch: expected {country}, got {dataset.get('country')}"
        )
    if not isinstance(dataset["regulatory_measures"], list):
        raise ValueError(f"Regulatory dataset {country} has a non-list regulatory_measures field")
    if not dataset["regulatory_measures"]:
        raise ValueError(f"Regulatory dataset {country} has no regulatory measures")

    measures: List[Dict[str, Any]] = []
    mandated_actors: List[Dict[str, Any]] = []
    has_documented_delegation = False
    for raw_measure in dataset["regulatory_measures"]:
        if not isinstance(raw_measure, dict):
            raise ValueError(f"Regulatory measure for {country} is not an object")
        _require_non_empty(
            raw_measure,
            _MEASURE_REQUIRED_FIELDS,
            f"Regulatory measure {raw_measure.get('record_id') or '<unknown>'}",
            allow_empty={"fees"},
        )
        if (
            _is_empty_value(raw_measure.get("fees"))
            and raw_measure["fees_status"] != "NOT_AVAILABLE"
        ):
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} omits fees without NOT_AVAILABLE status"
            )
        if (
            raw_measure.get("fees") is not None
            and raw_measure.get("fees_status") == "NOT_AVAILABLE"
        ):
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} publishes fees with NOT_AVAILABLE status"
            )
        _validate_structured_scope_fields(
            raw_measure, f"Regulatory measure {raw_measure['record_id']}"
        )
        actor_status = raw_measure["mandated_actor_status"]
        if actor_status not in _MANDATED_ACTOR_STATUSES:
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} has non-canonical "
                f"mandated_actor_status {actor_status!r}"
            )
        raw_actors = raw_measure.get("mandated_actors", [])
        if not isinstance(raw_actors, list):
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} has a non-list mandated_actors "
                f"({type(raw_actors).__name__})"
            )

        # Normalize (and structurally validate, e.g. rejecting a bare ACTIVE
        # mandate_status) each actor before the measure-level consistency
        # check below, so a malformed actor surfaces its own specific error
        # rather than being masked by the coarser DOCUMENTED/active check.
        normalized_actors = [
            _normalize_actor(actor, raw_measure, source_record_path) for actor in raw_actors
        ]
        has_confirmed_active_actor = any(
            actor.get("mandate_status") in _ACTIVE_MANDATE_STATUSES for actor in normalized_actors
        )
        if actor_status == "DOCUMENTED" and not has_confirmed_active_actor:
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} mandated_actor_status is "
                "DOCUMENTED without any confirmed-active mandated_actors"
            )
        if actor_status != "DOCUMENTED" and has_confirmed_active_actor:
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} has a confirmed-active mandated "
                f"actor but mandated_actor_status is {actor_status!r}, not DOCUMENTED"
            )

        if actor_status == "DOCUMENTED":
            has_documented_delegation = True

        measure = copy.deepcopy(raw_measure)
        measure["mandated_actors"] = normalized_actors
        measure["source_record_path"] = source_record_path
        measures.append(measure)
        mandated_actors.extend(normalized_actors)

    disclaimer = (
        "Simulation informative — non opposable à l’administration douanière. "
        "Un prestataire privé est présenté uniquement comme acteur d’exécution dans la limite "
        "d’un mandat documenté. Les frais, seuils, exemptions et portées SH non prouvés restent "
        "NOT_AVAILABLE."
    )
    if has_documented_delegation:
        disclaimer += " " + _MANDATED_ACTOR_DELEGATION_NOTE

    return {
        "country_iso3": country,
        "as_of": dataset.get("as_of"),
        "measure_type": dataset.get("measure_type"),
        "measure_count": len(measures),
        "mandated_actor_count": len(mandated_actors),
        "measures": measures,
        "mandated_actors": mandated_actors,
        "source_record_path": source_record_path,
        "notes": dataset.get("notes"),
        "disclaimer": disclaimer,
    }
