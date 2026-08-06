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
    "source_id",
    "legal_reference",
    "verification_status",
}

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
        if field not in nullable_fields and record.get(field) in (None, "")
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
    if dataset.get("country") != country:
        raise ValueError(
            f"Regulatory dataset country mismatch: expected {country}, got {dataset.get('country')}"
        )

    measures: List[Dict[str, Any]] = []
    mandated_actors: List[Dict[str, Any]] = []
    for raw_measure in dataset.get("regulatory_measures", []):
        if not isinstance(raw_measure, dict):
            raise ValueError(f"Regulatory measure for {country} is not an object")
        _require_non_empty(
            raw_measure,
            _MEASURE_REQUIRED_FIELDS,
            f"Regulatory measure {raw_measure.get('record_id') or '<unknown>'}",
        )
        if (
            raw_measure.get("fees") is not None
            and raw_measure.get("fees_status") == "NOT_AVAILABLE"
        ):
            raise ValueError(
                f"Regulatory measure {raw_measure['record_id']} publishes fees with NOT_AVAILABLE status"
            )

        measure = copy.deepcopy(raw_measure)
        normalized_actors = [
            _normalize_actor(actor, raw_measure, source_record_path)
            for actor in raw_measure.get("mandated_actors", [])
        ]
        measure["mandated_actors"] = normalized_actors
        measure["source_record_path"] = source_record_path
        measures.append(measure)
        mandated_actors.extend(copy.deepcopy(normalized_actors))

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
        "disclaimer": (
            "Simulation informative — non opposable à l’administration douanière. "
            "Un prestataire privé est présenté uniquement comme acteur d’exécution dans la limite "
            "d’un mandat documenté. Les frais, seuils, exemptions et portées SH non prouvés restent "
            "NOT_AVAILABLE."
        ),
    }
