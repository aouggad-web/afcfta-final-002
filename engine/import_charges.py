"""Generic regional + national import-charge calculation.

Kenya remains supported by ``engine.kenya_customs_calculation``.  New country
integrations should call :func:`calculate_import_charges` and inject the
regional tariff/override and national fiscal providers for the destination.
No rate is inferred from a country name or from a current membership.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Mapping, Optional

from engine.customs_territory_registry import CustomsTerritoryRegistry
from engine.legal_override_engine import LegalOverrideResolver
from engine.schemas.legal_override import (
    LegalLayer,
    LegalOverrideMeasure,
    OverrideContext,
    RemissionEligibility,
)


def _row(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(vars(value))


def _iso(value: Any) -> str:
    return str(value or "").strip().upper()


_VERIFIED_STATUS_PREFIXES = (
    "VERIFIED",
    "OFFICIAL_SOURCE_IDENTIFIED",
    "SOURCE_ARCHIVED",
    "EFFECTIVE_DATE_DOCUMENTED",
    "CALCULATION_VALIDATED",
    "DOCUMENTED_SCOPE_READY",
)
_UNVERIFIED_STATUS_TOKENS = {
    "AVAILABLE_UNVERIFIED",
    "UNVERIFIED_SOURCE",
    "SOURCE_PENDING",
    "PENDING",
    "PARTIAL",
    "NOT_AVAILABLE",
    "UNKNOWN",
    "STRUCTURE_VALIDATED",
    "INGESTED",
}

QUALITY_DIMENSION_KEYS = (
    "source",
    "temporal_validity",
    "classification",
    "taxes_and_levies",
    "preference_and_origin",
    "formalities",
)
QUALITY_DIMENSION_VALUES = frozenset(
    {
        "DOCUMENTED",
        "PARTIAL",
        "UNVERIFIED",
        "NOT_AVAILABLE",
        "NOT_APPLICABLE",
    }
)
OVERALL_STATUS_VALUES = frozenset(
    {
        "INFORMATIVE_COMPLETE",
        "INFORMATIVE_PARTIAL",
        "CALCULATION_UNAVAILABLE",
        "REVIEW_REQUIRED",
    }
)
OVERALL_STATUS_ALIASES = {
    "BLOCKED_BASE_TARIFF": "CALCULATION_UNAVAILABLE",
    "UNVERIFIED_SOURCE": "REVIEW_REQUIRED",
    "CONFLICT_REVIEW": "REVIEW_REQUIRED",
    "VERIFIED_COMPLETE": "INFORMATIVE_COMPLETE",
    "VERIFIED_PARTIAL": "INFORMATIVE_PARTIAL",
}


def validate_quality_dimensions(
    dimensions: Mapping[str, Any], *, require_all: bool = False
) -> dict[str, str]:
    """Validate the closed vocabulary used by the six quality dimensions."""
    if not isinstance(dimensions, Mapping):
        raise TypeError("quality_dimensions must be a mapping")
    unknown_keys = set(dimensions) - set(QUALITY_DIMENSION_KEYS)
    if unknown_keys:
        raise ValueError(f"Unknown quality dimension(s): {sorted(unknown_keys)}")
    invalid = {
        key: value for key, value in dimensions.items() if value not in QUALITY_DIMENSION_VALUES
    }
    if invalid:
        raise ValueError(f"Invalid quality dimension value(s): {invalid}")
    if require_all:
        missing_keys = set(QUALITY_DIMENSION_KEYS) - set(dimensions)
        if missing_keys:
            raise ValueError(f"Missing quality dimension(s): {sorted(missing_keys)}")
    return {key: dimensions[key] for key in dimensions}


def aggregate_overall_status(
    dimensions: Mapping[str, Any],
    *,
    base_available: bool = True,
    determinant_unverified: bool = False,
) -> str:
    """Aggregate quality dimensions without scores or compensating averages."""
    values = validate_quality_dimensions(dimensions, require_all=True)
    if not base_available or any(
        values[key] == "NOT_AVAILABLE"
        for key in ("source", "temporal_validity", "classification", "taxes_and_levies")
    ):
        return "CALCULATION_UNAVAILABLE"
    if determinant_unverified or any(value == "UNVERIFIED" for value in values.values()):
        return "REVIEW_REQUIRED"
    if all(value in {"DOCUMENTED", "NOT_APPLICABLE"} for value in values.values()):
        return "INFORMATIVE_COMPLETE"
    if any(value in {"DOCUMENTED", "PARTIAL"} for value in values.values()) and any(
        value in {"PARTIAL", "UNVERIFIED", "NOT_AVAILABLE"} for value in values.values()
    ):
        return "INFORMATIVE_PARTIAL"
    return "REVIEW_REQUIRED"


def _is_verified_status(value: Any) -> bool:
    normalized = str(value or "").strip().upper()
    return bool(normalized) and normalized.startswith(_VERIFIED_STATUS_PREFIXES)


def _component_status(row: Mapping[str, Any], *, default_verified: bool = False) -> str:
    """Normalize adapter certification labels to VERIFIED/UNVERIFIED.

    Legacy fixtures that provide a source id and an effective date are treated
    as verified for compatibility. Production providers should pass an
    explicit verification_status or certification level from the tariff
    manifest.
    """
    raw = row.get(
        "verification_status",
        row.get("certification_status", row.get("certification_level")),
    )
    if raw is not None:
        token = str(raw).strip().upper()
        if _is_verified_status(token):
            if row.get("_require_provenance") and not (
                row.get("source_id") and row.get("hs_version") and row.get("effective_from")
            ):
                return "UNVERIFIED"
            return "VERIFIED"
        if token in _UNVERIFIED_STATUS_TOKENS or token:
            return "UNVERIFIED"
    if (
        row.get("source_id")
        and row.get("effective_from")
        and (not row.get("_require_provenance") or row.get("hs_version"))
    ):
        return "VERIFIED"
    return "VERIFIED" if default_verified else "UNVERIFIED"


def _base_metadata(profile: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("base_tariff", "base_tariff_metadata", "tariff_metadata"):
        value = profile.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _documentation_status(status: str) -> str:
    if status in {
        "VERIFIED",
        "SOURCE_ARCHIVED",
        "OFFICIAL_SOURCE_IDENTIFIED",
        "EFFECTIVE_DATE_DOCUMENTED",
    }:
        return "DOCUMENTED"
    if status in {"MISSING", "UNVERIFIED", "UNVERIFIED_SOURCE"}:
        return "UNVERIFIED"
    return "PARTIAL"


def _quality_dimensions(
    profile: Mapping[str, Any],
    *,
    base_status: str,
    base_component: Mapping[str, Any],
    tax_lines: list[Mapping[str, Any]],
    national_coverage_complete: bool,
    hs6_digits: str,
    preference_status: str,
) -> dict[str, str]:
    source = (
        "DOCUMENTED"
        if (
            base_status == "VERIFIED"
            and base_component.get("source_id")
            and base_component.get("source_hash")
            and (
                base_component.get("source_authority")
                or base_component.get("source_title")
                or base_component.get("source_url")
            )
        )
        else "PARTIAL" if base_component.get("source_id") else "UNVERIFIED"
    )
    temporal = "DOCUMENTED" if base_component.get("effective_from") else "PARTIAL"
    classification = "DOCUMENTED" if len(hs6_digits) == 6 else "UNVERIFIED"
    if tax_lines:
        taxes = (
            "DOCUMENTED"
            if all(
                item.get("verification_status") == "VERIFIED"
                and item.get("source_hash")
                and (item.get("source_authority") or item.get("source_title"))
                for item in tax_lines
            )
            else "PARTIAL"
        )
    else:
        # A missing national provider is a partial fiscal layer when the
        # customs duty itself is available; the global status remains
        # informative-partial rather than hiding the verified component.
        taxes = "DOCUMENTED" if national_coverage_complete else "PARTIAL"
    preference = {
        "NO_PREFERENCE_REQUESTED": "NOT_APPLICABLE",
        "VERIFIED_APPLICABLE": "DOCUMENTED",
        "NOT_APPLICABLE": "NOT_APPLICABLE",
        "EXPIRED": "PARTIAL",
    }.get(preference_status, "UNVERIFIED")
    if "administrative_formalities" not in profile:
        formalities = "NOT_APPLICABLE"
    elif profile.get("administrative_formalities"):
        formalities = (
            "DOCUMENTED"
            if all(
                isinstance(item, Mapping)
                and item.get("source_hash")
                and (item.get("source_authority") or item.get("source_title"))
                for item in profile.get("administrative_formalities", [])
            )
            else "PARTIAL"
        )
    else:
        formalities = "NOT_AVAILABLE"
    provided = validate_quality_dimensions(profile.get("quality_dimensions") or {})
    # Callers may annotate a dimension as partial/unverified, but cannot turn
    # absent source/date evidence into DOCUMENTED.
    for key in ("classification", "taxes_and_levies", "preference_and_origin", "formalities"):
        value = provided.get(key)
        if value in {"DOCUMENTED", "PARTIAL", "UNVERIFIED", "NOT_AVAILABLE", "NOT_APPLICABLE"}:
            # A caller may lower a dimension to PARTIAL/UNVERIFIED, but may
            # not promote an internal assertion to DOCUMENTED here.
            if value != "DOCUMENTED":
                if key == "classification":
                    classification = value
                elif key == "taxes_and_levies":
                    taxes = value
                elif key == "preference_and_origin":
                    preference = value
                elif key == "formalities":
                    formalities = value
    return {
        "source": source,
        "temporal_validity": temporal,
        "classification": classification,
        "taxes_and_levies": taxes,
        "preference_and_origin": preference,
        "formalities": formalities,
    }


def _date(value: Any) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _active(row: Mapping[str, Any], on_date: date) -> bool:
    start = row.get("effective_from", row.get("valid_from"))
    end = row.get("effective_to", row.get("valid_to"))
    if start and _date(start) > on_date:
        return False
    if end and _date(end) < on_date:
        return False
    return row.get("legal_status") not in {"EXPIRED", "REPEALED"}


def _territory_for(
    importing_country: str,
    on_date: date,
    importer_profile: Mapping[str, Any],
    territory_memberships: Iterable[Any],
) -> tuple[Optional[str], list[str]]:
    explicit = importer_profile.get("customs_territory")
    if explicit:
        return _iso(explicit), [_iso(explicit)]
    memberships = [_row(item) for item in territory_memberships]
    active = [
        item
        for item in memberships
        if _iso(item.get("country_iso3")) == importing_country
        and _active(item, on_date)
        and item.get("implementation_status") in {None, "ACTIVE", "TRANSITIONAL"}
    ]
    # A membership list is sufficient for the generic calculator; providers
    # may additionally pass a CustomsTerritoryRegistry for priority selection.
    ids = [_iso(item.get("territory_id")) for item in active if item.get("territory_id")]
    return (ids[0] if len(ids) == 1 else None), ids


def _as_measure(item: Any, *, layer: LegalLayer, country: str, territory: Optional[str]):
    row = _row(item)
    row.setdefault("jurisdiction", territory or country)
    row.setdefault("legal_layer", layer.value)
    row.setdefault("customs_territory", territory)
    row.setdefault("applicable_countries", [country])
    row.setdefault("publication_url", "")
    row.setdefault("verification_status", "SOURCE_PENDING")
    row.setdefault("legal_title", row.get("measure_id", "Unidentified legal measure"))
    row.setdefault("legal_reference", row.get("measure_id", "Unidentified legal measure"))
    row.setdefault("effective_from", "1900-01-01")
    row.setdefault("measure_type", "NATIONAL_EXEMPTION")
    row.setdefault("product_description", "Unspecified product")
    return LegalOverrideMeasure(**row)


def _authorization_context(authorizations: Any) -> dict[str, Any]:
    if not authorizations:
        return {}
    if isinstance(authorizations, Mapping):
        return dict(authorizations)
    return {"authorization_hs_codes": list(authorizations)}


def _preference(
    profile: Mapping[str, Any],
    importing_country: str,
    exporting_country: str,
    hs6: str,
    on_date: date,
):
    pref = profile.get("preferential_regime") or profile.get("preference")
    if not pref:
        return None, None, "NO_PREFERENCE_REQUESTED"
    pref = _row(pref)
    missing = []
    if pref.get("importing_country") and _iso(pref["importing_country"]) != importing_country:
        return None, None, "NOT_APPLICABLE"
    if pref.get("exporting_country") and _iso(pref["exporting_country"]) != exporting_country:
        return None, None, "NOT_APPLICABLE"
    if pref.get("hs6") and str(pref["hs6"])[:6] != hs6[:6]:
        return None, None, "NOT_APPLICABLE"
    if not _active(pref, on_date):
        return None, "Preferential regime is outside its dated validity.", "EXPIRED"
    reciprocity = str(
        profile.get("reciprocity_status", pref.get("reciprocity_status", "UNKNOWN"))
    ).upper()
    origin = str(
        profile.get("origin_rule_status", pref.get("origin_rule_status", "UNKNOWN"))
    ).upper()
    if reciprocity not in {"VERIFIED", "RECIPROCAL", "ACTIVE"}:
        missing.append("Reciprocity is not verified for the selected preferential regime.")
    if origin not in {"VERIFIED", "SATISFIED", "ORIGIN_CONFIRMED"}:
        missing.append("Rule of origin is not verified for the selected preferential regime.")
    rate = pref.get("preferential_rate", pref.get("rate"))
    if rate is None:
        missing.append("No sourced preferential rate was supplied for the HS6.")
    if missing:
        return None, " ".join(missing), "ELIGIBILITY_UNKNOWN"
    return float(rate), None, "VERIFIED_APPLICABLE"


def calculate_import_charges(
    importing_country: str,
    exporting_country: str,
    hs6: str,
    national_code: Optional[str] = None,
    customs_value: Optional[float] = None,
    calculation_date: Optional[date] = None,
    importer_profile: Optional[Mapping[str, Any]] = None,
    intended_use: Optional[str] = None,
    authorizations: Any = None,
    *,
    base_rate: Optional[float] = None,
    regional_measures: Iterable[Any] = (),
    national_overrides: Iterable[Any] = (),
    national_taxes: Iterable[Any] = (),
    territory_memberships: Iterable[Any] = (),
    regional_coverage_complete: bool = False,
    national_coverage_complete: bool = False,
    currency_code: str = "LOCAL",
    base_rate_status: Optional[str] = None,
    base_tariff_verification_status: Optional[str] = None,
    base_source_id: Optional[str] = None,
    base_source_hash: Optional[str] = None,
    base_hs_version: Optional[str] = None,
    base_effective_from: Any = None,
    base_effective_to: Any = None,
) -> dict[str, Any]:
    """Calculate a dated import line using one common regional layer and one
    national destination layer.

    Regional and national records are injected by providers.  If a provider
    cannot establish a source or date fact, the result is ``INFORMATIVE_PARTIAL`` and the
    missing fact is returned instead of a guessed rate.
    """
    profile = dict(importer_profile or {})
    destination = _iso(importing_country)
    origin = _iso(exporting_country)
    requested_code = "".join(ch for ch in str(national_code or hs6) if ch.isdigit())
    hs6_digits = "".join(ch for ch in str(hs6) if ch.isdigit())[:6]
    on_date = _date(calculation_date)
    value = float(customs_value or 0.0)
    territory, blocs = _territory_for(destination, on_date, profile, territory_memberships)
    if profile.get("regional_blocs"):
        blocs = [_iso(item) for item in profile["regional_blocs"]]
    if territory and territory not in blocs:
        blocs.insert(0, territory)

    base_meta = _base_metadata(profile)
    if base_rate is None:
        for key in (
            "base_rate",
            "base_tariff_rate",
            "regional_tariff_rate",
            "national_tariff_rate",
        ):
            if profile.get(key) is not None:
                base_rate = float(profile[key])
                break
    base_missing = base_rate is None
    explicit_base_status = (
        base_rate_status
        or base_tariff_verification_status
        or base_meta.get("verification_status")
        or base_meta.get("certification_status")
        or profile.get("base_tariff_verification_status")
        or profile.get("base_rate_status")
    )
    explicit_base_provenance = bool(
        explicit_base_status
        or base_source_id
        or base_source_hash
        or base_hs_version
        or base_effective_from
        or base_meta
    )
    # Complete coverage is the backwards-compatible fixture contract. In
    # production, providers should pass an explicit manifest status.
    if explicit_base_status is None and not base_missing:
        # A tariff attached to a customs territory requires verified regional
        # coverage. National coverage may infer verification only for a
        # national-only destination with no regional bloc selected.
        regional_scope = bool(territory or blocs)
        inferred_verified = (
            regional_coverage_complete if regional_scope else national_coverage_complete
        )
        explicit_base_status = "VERIFIED" if inferred_verified else "UNVERIFIED_SOURCE"
    base_component = {
        "verification_status": explicit_base_status or "MISSING",
        "source_id": base_source_id or base_meta.get("source_id") or profile.get("base_source_id"),
        "source_hash": base_source_hash
        or base_meta.get("source_hash")
        or profile.get("base_source_hash"),
        "source_authority": base_meta.get("source_authority") or profile.get("source_authority"),
        "source_title": base_meta.get("source_title") or profile.get("source_title"),
        "source_url": base_meta.get("source_url") or profile.get("source_url"),
        "legal_reference": base_meta.get("legal_reference") or profile.get("legal_reference"),
        "source_date": base_meta.get("source_date") or profile.get("source_date"),
        "hs_version": base_hs_version
        or base_meta.get("hs_version")
        or profile.get("base_hs_version"),
        "effective_from": base_effective_from
        or base_meta.get("effective_from")
        or profile.get("base_effective_from"),
        "effective_to": base_effective_to
        or base_meta.get("effective_to")
        or profile.get("base_effective_to"),
        "_require_provenance": explicit_base_provenance,
    }
    base_status = "MISSING" if base_missing else _component_status(base_component)
    missing: list[str] = []
    if territory is None and len(blocs) > 1:
        missing.append(
            "Multiple customs territories are applicable; tariff authority priority requires review."
        )
    if base_missing:
        base_rate = 0.0
        missing.append("No dated verified regional or national base tariff rate was supplied.")
    elif base_status != "VERIFIED":
        missing.append(
            "Base tariff rate is present but its source, HS version, or effective date is not sufficiently verified."
        )

    auth = _authorization_context(authorizations)
    context = OverrideContext(
        jurisdiction=destination,
        regional_blocs=blocs,
        origin=profile.get("origin", origin),
        beneficiary=profile.get("beneficiary"),
        import_purpose=intended_use or profile.get("import_purpose"),
        quantity=profile.get("quantity"),
        remission_eligibility=auth.get(
            "remission_eligibility", RemissionEligibility.ELIGIBILITY_UNKNOWN
        ),
        authorization_reference=auth.get("authorization_reference"),
        authorization_effective_from=auth.get("authorization_effective_from"),
        authorization_effective_to=auth.get("authorization_effective_to"),
        authorization_hs_codes=list(auth.get("authorization_hs_codes", [])),
        authorization_goods=list(auth.get("authorization_goods", [])),
    )
    measures = [
        _as_measure(
            item, layer=LegalLayer.REGIONAL_COMMON, country=destination, territory=territory
        )
        for item in regional_measures
    ] + [
        _as_measure(item, layer=LegalLayer.NATIONAL_COUNTRY, country=destination, territory=None)
        for item in national_overrides
    ]
    resolver = LegalOverrideResolver(
        measures,
        regional_coverage_complete=regional_coverage_complete,
        national_coverage_complete=national_coverage_complete,
    )
    override = resolver.resolve(
        hs_code=requested_code or hs6_digits, on_date=on_date, base_rate=base_rate, context=context
    )
    missing.extend(override["missing_elements"])
    customs_rate = override["applicable_customs_rate"]
    customs_duty = round(value * customs_rate / 100.0, 2)

    computed: dict[str, float] = {"CUSTOMS_DUTY": customs_duty, "DD": customs_duty}
    tax_lines = []
    taxes = [_row(item) for item in national_taxes]
    taxes = [
        item
        for item in taxes
        if _iso(item.get("country_iso3", destination)) == destination and _active(item, on_date)
    ]
    for tax in sorted(taxes, key=lambda item: int(item.get("sequence", 100))):
        rate = tax.get("rate_pct", tax.get("rate"))
        code = str(tax.get("code", tax.get("tax_type", tax.get("tax_id", "TAX"))))
        tax_status = _component_status(tax)
        if tax_status != "VERIFIED":
            missing.append(
                f"{code}: source, version, or effective date is not sufficiently verified."
            )
        if rate is None:
            missing.append(f"{code}: no computable verified rate supplied.")
            continue
        basis = str(tax.get("basis", "CIF")).upper()
        includes = tax.get("basis_includes", []) or []
        if basis in {"CIF", "CUSTOMS_VALUE", "FOB"}:
            basis_amount = value
        elif basis in {"CIF_PLUS_INCLUDED", "CIF_PLUS_DUTY"}:
            basis_amount = value + sum(computed.get(str(item), 0.0) for item in includes)
            if not includes and basis == "CIF_PLUS_DUTY":
                basis_amount += customs_duty
        elif basis == "QUANTITY":
            quantity = profile.get("quantity")
            if quantity is None:
                missing.append(f"{code}: quantity is required for the specific basis.")
                continue
            basis_amount = float(quantity)
        else:
            missing.append(f"{code}: unsupported tax basis {basis}.")
            continue
        amount = round(basis_amount * float(rate) / 100.0, 2)
        computed[code] = amount
        tax_lines.append(
            {
                "component_type": code,
                "code": code,
                "name": tax.get("name", code),
                "source_rate": rate,
                "rate": float(rate),
                "rate_type": tax.get("rate_type", "AD_VALOREM"),
                "taxable_base": basis_amount,
                "calculated_amount": amount,
                "currency": currency_code,
                "basis": basis_amount,
                "amount": amount,
                "legal_reference": tax.get("legal_reference"),
                "source_id": tax.get("source_id"),
                "source_hash": tax.get("source_hash"),
                "effective_from": tax.get("effective_from", tax.get("valid_from")),
                "effective_to": tax.get("effective_to", tax.get("valid_to")),
                "hs_version": tax.get("hs_version"),
                "verification_status": tax_status,
                "status": tax_status,
                "components_included": list(includes),
                "components_missing": [],
                "source_authority": tax.get("source_authority"),
                "source_title": tax.get("source_title"),
                "documentation_status": _documentation_status(tax_status),
                "assumptions": list(tax.get("assumptions", [])),
                "data_gaps": [],
            }
        )

    preference_rate, preference_missing, preference_status = _preference(
        profile, destination, origin, hs6_digits, on_date
    )
    if preference_missing:
        missing.append(preference_missing)
    if preference_rate is not None and preference_rate != customs_rate:
        customs_rate = preference_rate
        customs_duty = round(value * customs_rate / 100.0, 2)
        computed["CUSTOMS_DUTY"] = computed["DD"] = customs_duty

    quality_dimensions = _quality_dimensions(
        profile,
        base_status=base_status,
        base_component=base_component,
        tax_lines=tax_lines,
        national_coverage_complete=national_coverage_complete,
        hs6_digits=hs6_digits,
        preference_status=preference_status,
    )
    formalities = []
    for item in profile.get("administrative_formalities", []):
        row = _row(item)
        if _active(row, on_date) and (not row.get("hs6") or str(row["hs6"])[:6] == hs6_digits):
            formalities.append(row)
    total = round(customs_duty + sum(item["amount"] for item in tax_lines), 2)
    by_code = {item["code"].upper(): item for item in tax_lines}
    vat_line = next((item for code, item in by_code.items() if code in {"VAT", "TVA"}), None)
    excise_lines = [
        item for code, item in by_code.items() if "EXCISE" in code or code in {"ED", "ET"}
    ]
    levy_lines = [
        item for code, item in by_code.items() if item not in excise_lines and item is not vat_line
    ]
    status = override["calculation_status"]
    if base_missing:
        status = "BLOCKED_BASE_TARIFF"
    elif base_status != "VERIFIED":
        status = "UNVERIFIED_SOURCE"
    elif status != "CONFLICT_REVIEW" and (
        missing
        or any(
            value not in {"DOCUMENTED", "NOT_APPLICABLE"} for value in quality_dimensions.values()
        )
    ):
        # Compatibility status retained for existing consumers.
        status = "INFORMATIVE_PARTIAL"
    elif status != "CONFLICT_REVIEW":
        status = "INFORMATIVE_COMPLETE"
    overall_status = aggregate_overall_status(
        quality_dimensions,
        base_available=not base_missing,
        determinant_unverified=(
            status == "CONFLICT_REVIEW"
            or base_status != "VERIFIED"
            or any(value == "UNVERIFIED" for value in quality_dimensions.values())
            or any(item.get("verification_status") == "UNVERIFIED" for item in tax_lines)
        ),
    )
    customs_component = {
        "component_type": "CUSTOMS_DUTY",
        "code": "CUSTOMS_DUTY",
        "source_rate": base_rate if not base_missing else None,
        "rate": base_rate if not base_missing else None,
        "rate_type": "AD_VALOREM",
        "taxable_base": value,
        "calculated_amount": customs_duty,
        "currency": currency_code,
        "amount": customs_duty,
        "verification_status": "BLOCKED_BASE_TARIFF" if base_missing else base_status,
        "status": "BLOCKED_BASE_TARIFF" if base_missing else base_status,
        "source_id": base_component.get("source_id"),
        "source_hash": base_component.get("source_hash"),
        "effective_from": base_component.get("effective_from"),
        "effective_to": base_component.get("effective_to"),
        "hs_version": base_component.get("hs_version"),
        "components_included": ["CUSTOMS_VALUE", "BASE_TARIFF", "APPLICABLE_OVERRIDES"],
        "components_missing": (["BASE_TARIFF"] if base_missing else []),
        "source_authority": base_component.get("source_authority"),
        "source_title": base_component.get("source_title"),
        "legal_reference": base_component.get("legal_reference"),
        "documentation_status": _documentation_status("MISSING" if base_missing else base_status),
        "assumptions": ["ad valorem base applied to customs value"],
        "data_gaps": (["base tariff"] if base_missing else []),
    }
    component_statuses = {
        "base_tariff": dict(base_component, status=base_status),
        "customs_duty": customs_component,
        "taxes": tax_lines,
    }
    payable_total = (
        None if overall_status in {"CALCULATION_UNAVAILABLE", "REVIEW_REQUIRED"} else total
    )
    return {
        "importing_country": destination,
        "exporting_country": origin,
        "hs6": hs6_digits,
        "national_code": national_code,
        "calculation_date": on_date.isoformat(),
        "currency_code": currency_code,
        "customs_territory": territory,
        "base_tariff_rate": base_rate,
        "base_tariff_verification_status": base_status,
        "base_tariff_source_id": base_component.get("source_id"),
        "base_tariff_effective_from": base_component.get("effective_from"),
        "base_tariff_effective_to": base_component.get("effective_to"),
        "base_tariff_hs_version": base_component.get("hs_version"),
        "override_applied": override["override_rate"],
        "applicable_customs_rate": customs_rate,
        "customs_duty": customs_duty,
        "taxes": tax_lines,
        # Compatibility aliases used by the Kenya legal response while the
        # generic API exposes the normalized ``taxes`` list.
        "vat": vat_line,
        "excise": {
            "amount": round(sum(item["amount"] for item in excise_lines), 2),
            "lines": excise_lines,
        },
        "idf": next((item for code, item in by_code.items() if code == "IDF"), None),
        "rdl": next((item for code, item in by_code.items() if code == "RDL"), None),
        "other_levies": {
            item["code"]: item for item in levy_lines if item["code"].upper() not in {"IDF", "RDL"}
        },
        "verified_total": payable_total,
        "simulated_total": total,
        "total_payable": payable_total,
        "component_statuses": component_statuses,
        "amounts": [customs_component, *tax_lines],
        "components_included": ["CUSTOMS_DUTY", *[item["code"] for item in tax_lines]],
        "components_missing": list(dict.fromkeys(missing)),
        "missing_elements": list(dict.fromkeys(missing)),
        "calculation_status": status,
        "status": status,
        "overall_status": overall_status,
        "technical_validation_status": (
            "CALCULATION_VALIDATED"
            if status in {"INFORMATIVE_COMPLETE", "INFORMATIVE_PARTIAL"}
            else status
        ),
        "informational_only": True,
        "legally_binding": False,
        "administrative_confirmation_required": True,
        "source_authority": base_component.get("source_authority")
        or base_component.get("source_id"),
        "source_date": base_component.get("source_date"),
        "effective_date": base_component.get("effective_from"),
        "completeness_status": overall_status,
        "quality_dimensions": quality_dimensions,
        "known_data_gaps": list(dict.fromkeys(missing)),
        "legal_reliance_allowed": False,
        "simulation_only": overall_status == "REVIEW_REQUIRED",
        "amount_display_allowed": overall_status != "CALCULATION_UNAVAILABLE",
        "base_tariff": {
            "rate": base_rate if not base_missing else None,
            "status": base_status,
            "source_id": base_component.get("source_id"),
            "source_hash": base_component.get("source_hash"),
            "source_authority": base_component.get("source_authority"),
            "source_date": base_component.get("source_date"),
            "hs_version": base_component.get("hs_version"),
            "effective_from": base_component.get("effective_from"),
            "effective_to": base_component.get("effective_to"),
        },
        "monetary_components": [customs_component, *tax_lines],
        "preference_status": preference_status,
        "preference_rate": preference_rate,
        "legal_justification": override["trace"],
        "legal_layers": override.get("legal_layers"),
        "formalities": formalities,
        "restrictions": override["restrictions"],
        "administrative_requirements": override["administrative_requirements"],
        "sources_used": override["sources_used"],
        "remission_eligibility_status": override["remission_eligibility_status"],
        "requires_eligibility_input": override["requires_eligibility_input"],
        "administrative_confirmation_recommended": True,
        "disclaimer": {
            "informational_only": True,
            "legally_binding": False,
            "message": "Simulation informative fondée sur les données disponibles.",
        },
    }
