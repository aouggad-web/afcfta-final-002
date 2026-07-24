"""Auditable Kenya customs calculation built on the legal override resolver."""

import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from engine.legal_override_engine import LegalOverrideResolver
from engine.schemas.legal_override import LegalOverrideMeasure, OverrideContext


def _pct(value) -> Optional[float]:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*%\s*", value)
    return float(match.group(1)) if match else None


def _active(rows, on_date: date):
    iso = on_date.isoformat()
    return [
        row
        for row in rows
        if row.get("effective_from", "9999-12-31") <= iso
        and (not row.get("effective_to") or iso <= row["effective_to"])
        and row.get("legal_status") not in {"REPEALED", "EXPIRED"}
    ]


def _hs_match(row, hs_code: str) -> bool:
    clean = re.sub(r"\D", "", hs_code)
    explicit = [re.sub(r"\D", "", x) for x in row.get("hs_codes_explicit", [])]
    return not explicit or any(
        clean.startswith(code) or code.startswith(clean) for code in explicit
    )


class KenyaFiscalStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        self.excise = json.loads((data_dir / "excise_measures.json").read_text(encoding="utf-8"))
        self.levies = json.loads((data_dir / "import_levies.json").read_text(encoding="utf-8"))

    def percentage_measure(self, table: str, on_date: date, hs_code: str):
        rows = self.levies.get(table, [])
        general_tables = {"import_declaration_fee", "railway_development_levy"}
        return next(
            (
                row
                for row in _active(rows, on_date)
                if (table in general_tables or row.get("hs_codes_explicit"))
                and _hs_match(row, hs_code)
                and _pct(row.get("rate")) is not None
            ),
            None,
        )

    def vat_rate(self, on_date: date, hs_code: str):
        rows = _active(self.vat["vat_rates"], on_date)
        specific = [r for r in rows if r.get("hs_codes_explicit") and _hs_match(r, hs_code)]
        standard = [r for r in rows if r["record_id"].startswith("VAT-RATE-STANDARD")]
        return next((r for r in specific + standard if _pct(r.get("rate")) is not None), None)

    def excise_rates(self, on_date: date, hs_code: str):
        return [
            r
            for r in _active(self.excise["excise_rates"], on_date)
            if r.get("hs_codes_explicit") and _hs_match(r, hs_code)
        ]


def _calculate_kenya_customs_legacy(
    *,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    measures: Iterable[LegalOverrideMeasure],
    fiscal_store: KenyaFiscalStore,
    context: Optional[OverrideContext] = None,
    coverage_complete: bool = False,
    currency_code: str = "KES",
) -> dict:
    resolver = LegalOverrideResolver(measures, coverage_complete=coverage_complete)
    override = resolver.resolve(
        hs_code=hs_code,
        on_date=on_date,
        base_rate=base_cet_rate,
        context=context,
    )
    customs_rate = override["applicable_customs_rate"]
    customs_duty = round(customs_value * customs_rate / 100, 2)

    excise = 0.0
    excise_lines = []
    missing = list(override["missing_elements"])
    for row in fiscal_store.excise_rates(on_date, hs_code):
        rate = _pct(row.get("rate"))
        if rate is None:
            missing.append(
                f"{row['record_id']}: specific or mixed excise needs quantity/unit data."
            )
            continue
        basis = customs_value + customs_duty
        amount = round(basis * rate / 100, 2)
        excise += amount
        excise_lines.append(
            {
                "record_id": row["record_id"],
                "component_type": "EXCISE",
                "source_rate": rate,
                "rate": rate,
                "rate_type": "AD_VALOREM",
                "taxable_base": basis,
                "calculated_amount": amount,
                "currency": currency_code,
                "basis": basis,
                "amount": amount,
                "legal_reference": row["legal_reference"],
                "source_id": row["source_id"],
                "source_authority": row.get("source_authority"),
                "source_title": row.get("source_title"),
                "effective_from": row.get("effective_from"),
                "effective_to": row.get("effective_to"),
                "documentation_status": "PARTIAL",
                "assumptions": ["ad valorem excise applied to customs value plus duty"],
                "data_gaps": ["official archive and independent comparison pending"],
            }
        )

    levy_amounts = {}
    for table, label in (
        ("import_declaration_fee", "idf"),
        ("railway_development_levy", "rdl"),
        ("export_and_investment_promotion_levy", "export_investment_promotion_levy"),
        ("sugar_development_levy", "sugar_development_levy"),
        ("other_import_levies", "other_import_levies"),
    ):
        row = fiscal_store.percentage_measure(table, on_date, hs_code)
        if row:
            rate = _pct(row["rate"])
            levy_amounts[label] = {
                "component_type": label.upper(),
                "source_rate": rate,
                "rate": rate,
                "rate_type": "AD_VALOREM",
                "taxable_base": customs_value,
                "calculated_amount": round(customs_value * rate / 100, 2),
                "currency": currency_code,
                "amount": round(customs_value * rate / 100, 2),
                "legal_reference": row["legal_reference"],
                "source_id": row["source_id"],
                "source_authority": row.get("source_authority"),
                "source_title": row.get("source_title"),
                "effective_from": row.get("effective_from"),
                "effective_to": row.get("effective_to"),
                "documentation_status": "PARTIAL",
                "assumptions": ["ad valorem levy applied to customs value"],
                "data_gaps": ["official archive and independent comparison pending"],
            }
        else:
            levy_amounts[label] = None

    vat_row = fiscal_store.vat_rate(on_date, hs_code)
    vat_basis = round(customs_value + customs_duty + excise, 2)
    vat_rate = _pct(vat_row["rate"]) if vat_row else None
    vat = round(vat_basis * vat_rate / 100, 2) if vat_rate is not None else None
    if not vat_row:
        missing.append("No verified VAT measure matched the product and date.")

    known_levies = sum(entry["amount"] for entry in levy_amounts.values() if entry is not None)
    verified_total = round(customs_duty + excise + (vat or 0) + known_levies, 2)
    status = override["calculation_status"]
    if not coverage_complete:
        status = "UNVERIFIED_SOURCE"
        missing.append("Kenya CET source, HS version, or legal effective date is not sufficiently verified.")
    elif missing and status != "CONFLICT_REVIEW":
        status = "INFORMATIVE_PARTIAL"
    # Keep the legacy path compatible, but expose the same canonical global
    # status and closed quality vocabulary as the shared calculator.
    legacy_quality_dimensions = {
        "source": "PARTIAL" if coverage_complete else "UNVERIFIED",
        "temporal_validity": "PARTIAL",
        "classification": "DOCUMENTED" if len(hs_code) >= 6 else "UNVERIFIED",
        "taxes_and_levies": "DOCUMENTED" if vat_row else "PARTIAL",
        "preference_and_origin": "UNVERIFIED",
        "formalities": "NOT_AVAILABLE",
    }
    from engine.import_charges import aggregate_overall_status
    legacy_overall_status = aggregate_overall_status(
        legacy_quality_dimensions,
        base_available=coverage_complete and status != "BLOCKED_BASE_TARIFF",
        determinant_unverified=(
            status in {"UNVERIFIED_SOURCE", "CONFLICT_REVIEW"}
            or any(value == "UNVERIFIED" for value in legacy_quality_dimensions.values())
        ),
    )
    payable_total = verified_total if legacy_overall_status not in {"CALCULATION_UNAVAILABLE", "REVIEW_REQUIRED"} else None
    sources = set(override["sources_used"])
    sources.update(r["source_id"] for r in excise_lines)
    if vat_row:
        sources.add(vat_row["source_id"])
    for entry in levy_amounts.values():
        if entry:
            sources.add(entry["source_id"])

    warning = None
    if status == "UNVERIFIED_SOURCE":
        warning = (
            f"Simulation non vérifiée : {verified_total:,.2f} {currency_code}. "
            "La source, la version SH ou la date d’effet du CET Kenya doit être documentée et recoupée."
        )
    elif status == "INFORMATIVE_PARTIAL":
        warning = (
            f"Montant informatif : {verified_total:,.2f} {currency_code}. "
            "Résultat partiel : une dérogation tarifaire EAC ou une condition "
            "susceptible d’affecter ce produit doit être confirmée. "
            "Ne pas utiliser ce montant comme référence administrative."
        )
    national_layer = dict(override["legal_layers"]["NATIONAL_COUNTRY"])
    national_layer["taxes_and_levies"] = {
        "vat": (
            {
                "component_type": "VAT",
                "source_rate": vat_rate,
                "rate": vat_rate,
                "rate_type": "AD_VALOREM",
                "taxable_base": vat_basis,
                "calculated_amount": vat,
                "currency": currency_code,
                "amount": vat,
                "source_id": vat_row["source_id"],
                "source_authority": vat_row.get("source_authority"),
                "source_title": vat_row.get("source_title"),
                "legal_reference": vat_row.get("legal_reference"),
                "effective_from": vat_row.get("effective_from"),
                "effective_to": vat_row.get("effective_to"),
                "documentation_status": "PARTIAL",
                "assumptions": ["VAT applied to customs value plus duty and excise"],
                "data_gaps": [] if vat_row else ["VAT measure unavailable"],
            }
            if vat_row
            else None
        ),
        "excise": {"amount": round(excise, 2), "lines": excise_lines},
        "levies": levy_amounts,
    }
    return {
        "hs_code": hs_code,
        "calculation_date": on_date.isoformat(),
        "customs_value": customs_value,
        "currency_code": currency_code,
        "base_cet_rate": base_cet_rate,
        "override_applied": override["override_rate"],
        "applicable_customs_rate": customs_rate,
        "legal_justification": override["trace"],
        "customs_duty": customs_duty,
        "vat_basis": vat_basis,
        "vat": (
            {"rate": vat_rate, "amount": vat, "source_id": vat_row["source_id"]}
            if vat_row
            else None
        ),
        "excise": {"amount": round(excise, 2), "lines": excise_lines},
        "idf": levy_amounts["idf"],
        "rdl": levy_amounts["rdl"],
        "other_levies": {
            key: value
            for key, value in levy_amounts.items()
            if key not in {"idf", "rdl"} and value is not None
        },
        "verified_total": payable_total,
        "simulated_total": verified_total,
        "total_payable": payable_total,
        "status": status,
        "overall_status": legacy_overall_status,
        "technical_validation_status": "CALCULATION_VALIDATED" if legacy_overall_status in {"INFORMATIVE_COMPLETE", "INFORMATIVE_PARTIAL"} else legacy_overall_status,
        "completeness_status": legacy_overall_status,
        "known_data_gaps": list(dict.fromkeys(missing)),
        "legal_reliance_allowed": False,
        "simulation_only": legacy_overall_status == "REVIEW_REQUIRED",
        "informational_only": True,
        "legally_binding": False,
        "administrative_confirmation_recommended": True,
        "quality_dimensions": legacy_quality_dimensions,
        "disclaimer": {
            "informational_only": True,
            "legally_binding": False,
            "message": "Simulation informative fondée sur les données disponibles.",
        },
        "amount_display_allowed": legacy_overall_status != "CALCULATION_UNAVAILABLE",
        "missing_elements": list(dict.fromkeys(missing)),
        "calculation_status": status,
        "sources_used": sorted(sources),
        "restrictions": override["restrictions"],
        "administrative_requirements": override["administrative_requirements"],
        "display_warning": warning,
        "remission_eligibility_status": override["remission_eligibility_status"],
        "requires_eligibility_input": override["requires_eligibility_input"],
        "legal_layers": {
            "REGIONAL_COMMON": override["legal_layers"]["REGIONAL_COMMON"],
            "NATIONAL_COUNTRY": national_layer,
        },
    }



def _kenya_tax_rows(fiscal_store: KenyaFiscalStore, on_date: date, hs_code: str) -> list[dict]:
    """Adapt verified Kenya fiscal tables to the generic tax-layer shape."""
    rows: list[dict] = []
    excise_codes: list[str] = []
    for item in fiscal_store.excise_rates(on_date, hs_code):
        rate = _pct(item.get("rate"))
        code = f"EXCISE-{item['record_id']}"
        excise_codes.append(code)
        rows.append(
            {
                "tax_id": item["record_id"],
                "country_iso3": "KEN",
                "code": code,
                "name": item.get("name", "Excise Duty"),
                "rate_pct": rate,
                "basis": "CIF_PLUS_INCLUDED",
                "basis_includes": ["CUSTOMS_DUTY"],
                "sequence": 40,
                "legal_reference": item.get("legal_reference"),
                "source_id": item.get("source_id"),
                "effective_from": item.get("effective_from", "1900-01-01"),
            }
        )
    for table, label in (
        ("import_declaration_fee", "IDF"),
        ("railway_development_levy", "RDL"),
        ("export_and_investment_promotion_levy", "EXPORT_INVESTMENT_PROMOTION_LEVY"),
        ("sugar_development_levy", "SUGAR_DEVELOPMENT_LEVY"),
        ("other_import_levies", "OTHER_IMPORT_LEVY"),
    ):
        item = fiscal_store.percentage_measure(table, on_date, hs_code)
        if item:
            rows.append(
                {
                    "tax_id": item["record_id"],
                    "country_iso3": "KEN",
                    "code": label,
                    "name": label,
                    "rate_pct": _pct(item.get("rate")),
                    "basis": "CUSTOMS_VALUE",
                    "sequence": 50,
                    "legal_reference": item.get("legal_reference"),
                    "source_id": item.get("source_id"),
                    "effective_from": item.get("effective_from", "1900-01-01"),
                }
            )
    vat = fiscal_store.vat_rate(on_date, hs_code)
    if vat:
        rows.append(
            {
                "tax_id": vat["record_id"],
                "country_iso3": "KEN",
                "code": "VAT",
                "name": "Value Added Tax",
                "rate_pct": _pct(vat.get("rate")),
                "basis": "CIF_PLUS_INCLUDED",
                "basis_includes": ["CUSTOMS_DUTY", *excise_codes],
                "sequence": 90,
                "legal_reference": vat.get("legal_reference"),
                "source_id": vat.get("source_id"),
                "effective_from": vat.get("effective_from", "1900-01-01"),
            }
        )
    return rows


def calculate_kenya_customs(
    *,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    measures: Iterable[LegalOverrideMeasure],
    fiscal_store: KenyaFiscalStore,
    context: Optional[OverrideContext] = None,
    coverage_complete: bool = False,
    currency_code: str = "KES",
) -> dict:
    """Compatibility facade over :func:`calculate_import_charges`.

    The Kenya-specific fiscal JSON remains an injected national provider; the
    regional override resolution and tax sequencing are shared with all other
    importing countries.
    """
    from engine.import_charges import calculate_import_charges

    context = context or OverrideContext(jurisdiction="KEN", regional_blocs=["EAC"])
    tax_rows = _kenya_tax_rows(fiscal_store, on_date, hs_code)
    result = calculate_import_charges(
        importing_country="KEN",
        exporting_country=context.origin or "",
        hs6=hs_code[:6],
        national_code=hs_code,
        customs_value=customs_value,
        calculation_date=on_date,
        importer_profile={
            "regional_blocs": context.regional_blocs or ["EAC"],
            "beneficiary": context.beneficiary,
            "import_purpose": context.import_purpose,
            "quantity": context.quantity,
            "origin": context.origin,
        },
        authorizations={
            "remission_eligibility": context.remission_eligibility,
            "authorization_reference": context.authorization_reference,
            "authorization_effective_from": context.authorization_effective_from,
            "authorization_effective_to": context.authorization_effective_to,
            "authorization_hs_codes": context.authorization_hs_codes,
            "authorization_goods": context.authorization_goods,
        },
        # A CET rate without an archived, dated and verified source is not an
        # applicable base for Kenya.  Keep the supplied rate in the request
        # context, but withhold it from the generic calculator in that case.
        base_rate=base_cet_rate if coverage_complete else None,
        regional_measures=measures,
        national_taxes=tax_rows,
        regional_coverage_complete=coverage_complete,
        national_coverage_complete=coverage_complete,
        currency_code=currency_code,
    )
    if not any(item.get("code", "").upper() == "VAT" for item in result["taxes"]):
        result["missing_elements"].append("No verified VAT measure matched the product and date.")
        if result.get("calculation_status") != "BLOCKED_BASE_TARIFF":
            result["calculation_status"] = "INFORMATIVE_PARTIAL"
            result["status"] = "INFORMATIVE_PARTIAL"
        result["overall_status"] = "CALCULATION_UNAVAILABLE"
        result["verified_total"] = None
        result["total_payable"] = None
        result["amount_display_allowed"] = False
        result["simulation_only"] = False
    result["customs_value"] = customs_value
    result["base_cet_rate"] = base_cet_rate
    # The generic engine already computed the canonical global status. Keep it
    # intact; only the missing-VAT guard above can upgrade it to unavailable.
    result["administrative_confirmation_recommended"] = True
    result["disclaimer"] = {
        "informational_only": True,
        "legally_binding": False,
        "message": "Simulation informative fondée sur les données disponibles.",
    }
    if result.get("overall_status") == "CALCULATION_UNAVAILABLE":
        result["display_warning"] = (
            "Donnée indispensable manquante : aucun total n'est affiché."
        )
    elif result.get("overall_status") == "REVIEW_REQUIRED":
        simulated = result.get("simulated_total")
        amount = f"{simulated:,.2f}" if isinstance(simulated, (int, float)) else "—"
        result["display_warning"] = (
            f"Simulation à confirmer : {amount} {currency_code}. "
            "Une donnée déterminante de source, date ou condition doit être revue. "
            "Ne pas utiliser ce montant comme référence administrative."
        )
    else:
        result["display_warning"] = None
    return result
