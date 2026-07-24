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


def _preference(profile: Mapping[str, Any], importing_country: str, exporting_country: str, hs6: str, on_date: date):
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
    reciprocity = str(profile.get("reciprocity_status", pref.get("reciprocity_status", "UNKNOWN"))).upper()
    origin = str(profile.get("origin_rule_status", pref.get("origin_rule_status", "UNKNOWN"))).upper()
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
) -> dict[str, Any]:
    """Calculate a dated import line using one common regional layer and one
    national destination layer.

    Regional and national records are injected by providers.  If a provider
    cannot establish a legal fact, the result is ``VERIFIED_PARTIAL`` and the
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

    if base_rate is None:
        for key in ("base_rate", "base_tariff_rate", "regional_tariff_rate", "national_tariff_rate"):
            if profile.get(key) is not None:
                base_rate = float(profile[key])
                break
    missing: list[str] = []
    if territory is None and len(blocs) > 1:
        missing.append("Multiple customs territories are applicable; tariff authority priority requires review.")
    if base_rate is None:
        base_rate = 0.0
        missing.append("No dated regional or national base tariff rate was supplied.")

    auth = _authorization_context(authorizations)
    context = OverrideContext(
        jurisdiction=destination,
        regional_blocs=blocs,
        origin=profile.get("origin", origin),
        beneficiary=profile.get("beneficiary"),
        import_purpose=intended_use or profile.get("import_purpose"),
        quantity=profile.get("quantity"),
        remission_eligibility=auth.get("remission_eligibility", RemissionEligibility.ELIGIBILITY_UNKNOWN),
        authorization_reference=auth.get("authorization_reference"),
        authorization_effective_from=auth.get("authorization_effective_from"),
        authorization_effective_to=auth.get("authorization_effective_to"),
        authorization_hs_codes=list(auth.get("authorization_hs_codes", [])),
        authorization_goods=list(auth.get("authorization_goods", [])),
    )
    measures = [
        _as_measure(item, layer=LegalLayer.REGIONAL_COMMON, country=destination, territory=territory)
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
    override = resolver.resolve(hs_code=requested_code or hs6_digits, on_date=on_date, base_rate=base_rate, context=context)
    missing.extend(override["missing_elements"])
    customs_rate = override["applicable_customs_rate"]
    customs_duty = round(value * customs_rate / 100.0, 2)

    computed: dict[str, float] = {"CUSTOMS_DUTY": customs_duty, "DD": customs_duty}
    tax_lines = []
    taxes = [_row(item) for item in national_taxes]
    taxes = [item for item in taxes if _iso(item.get("country_iso3", destination)) == destination and _active(item, on_date)]
    for tax in sorted(taxes, key=lambda item: int(item.get("sequence", 100))):
        rate = tax.get("rate_pct", tax.get("rate"))
        code = str(tax.get("code", tax.get("tax_type", tax.get("tax_id", "TAX"))))
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
        tax_lines.append({"code": code, "name": tax.get("name", code), "rate": float(rate), "basis": basis_amount, "amount": amount, "legal_reference": tax.get("legal_reference"), "source_id": tax.get("source_id")})

    preference_rate, preference_missing, preference_status = _preference(profile, destination, origin, hs6_digits, on_date)
    if preference_missing:
        missing.append(preference_missing)
    if preference_rate is not None and preference_rate != customs_rate:
        customs_rate = preference_rate
        customs_duty = round(value * customs_rate / 100.0, 2)
        computed["CUSTOMS_DUTY"] = computed["DD"] = customs_duty

    formalities = []
    for item in profile.get("administrative_formalities", []):
        row = _row(item)
        if _active(row, on_date) and (not row.get("hs6") or str(row["hs6"])[:6] == hs6_digits):
            formalities.append(row)
    total = round(customs_duty + sum(item["amount"] for item in tax_lines), 2)
    by_code = {item["code"].upper(): item for item in tax_lines}
    vat_line = next((item for code, item in by_code.items() if code in {"VAT", "TVA"}), None)
    excise_lines = [item for code, item in by_code.items() if "EXCISE" in code or code in {"ED", "ET"}]
    levy_lines = [item for code, item in by_code.items() if item not in excise_lines and item is not vat_line]
    status = override["calculation_status"]
    if missing and status != "CONFLICT_REVIEW":
        status = "VERIFIED_PARTIAL"
    return {
        "importing_country": destination,
        "exporting_country": origin,
        "hs6": hs6_digits,
        "national_code": national_code,
        "calculation_date": on_date.isoformat(),
        "currency_code": currency_code,
        "customs_territory": territory,
        "base_tariff_rate": base_rate,
        "override_applied": override["override_rate"],
        "applicable_customs_rate": customs_rate,
        "customs_duty": customs_duty,
        "taxes": tax_lines,
        # Compatibility aliases used by the Kenya legal response while the
        # generic API exposes the normalized ``taxes`` list.
        "vat": vat_line,
        "excise": {"amount": round(sum(item["amount"] for item in excise_lines), 2), "lines": excise_lines},
        "idf": next((item for code, item in by_code.items() if code == "IDF"), None),
        "rdl": next((item for code, item in by_code.items() if code == "RDL"), None),
        "other_levies": {item["code"]: item for item in levy_lines if item["code"].upper() not in {"IDF", "RDL"}},
        "verified_total": total,
        "missing_elements": list(dict.fromkeys(missing)),
        "calculation_status": status,
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
    }
