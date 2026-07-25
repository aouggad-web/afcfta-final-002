"""Auditable national customs calculation built on the legal override resolver.

Généralisation du moteur initialement conçu pour le Kenya (PR #307) : la
composition CET + override juridique daté + accises + TVA + prélèvements
nationaux est commune à toute juridiction disposant d'un corpus de mesures
vérifiées et datées. ``engine/kenya_customs_calculation.py`` reste un module
de compatibilité rétroactive pour les appelants existants.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable, Optional, Tuple

from engine.legal_override_engine import LegalOverrideResolver
from engine.schemas.legal_override import LegalOverrideMeasure, OverrideContext

# Tables de prélèvements appliquées sans exigence de correspondance HS
# explicite (prélèvement général sur toute importation) — comportement
# historique du Kenya (IDF, RDL). Une juridiction dont les prélèvements
# nationaux suivent une autre logique peut fournir son propre ensemble via
# ``NationalFiscalStore(..., general_levy_tables=...)``.
DEFAULT_GENERAL_LEVY_TABLES = frozenset({"import_declaration_fee", "railway_development_levy"})

# Association (nom de table dans import_levies.json -> clé de sortie),
# comportement historique du Kenya. Une juridiction avec une nomenclature de
# prélèvements différente peut fournir sa propre liste via l'argument
# ``levy_tables`` de ``calculate_national_customs``.
DEFAULT_LEVY_TABLES: Tuple[Tuple[str, str], ...] = (
    ("import_declaration_fee", "idf"),
    ("railway_development_levy", "rdl"),
    ("export_and_investment_promotion_levy", "export_investment_promotion_levy"),
    ("sugar_development_levy", "sugar_development_levy"),
    ("other_import_levies", "other_import_levies"),
)


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


class NationalFiscalStore:
    """Charge les mesures fiscales nationales (TVA, accises, prélèvements)
    d'une juridiction depuis son répertoire ``data/<pays>/``."""

    def __init__(
        self,
        data_dir: Path,
        general_levy_tables: frozenset = DEFAULT_GENERAL_LEVY_TABLES,
    ):
        self.data_dir = data_dir
        self.general_levy_tables = general_levy_tables
        self.vat = json.loads((data_dir / "vat_measures.json").read_text(encoding="utf-8"))
        self.excise = json.loads((data_dir / "excise_measures.json").read_text(encoding="utf-8"))
        self.levies = json.loads((data_dir / "import_levies.json").read_text(encoding="utf-8"))

    def percentage_measure(self, table: str, on_date: date, hs_code: str):
        rows = self.levies.get(table, [])
        return next(
            (
                row
                for row in _active(rows, on_date)
                if (table in self.general_levy_tables or row.get("hs_codes_explicit"))
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


def calculate_national_customs(
    *,
    jurisdiction: str,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    measures: Iterable[LegalOverrideMeasure],
    fiscal_store: NationalFiscalStore,
    context: Optional[OverrideContext] = None,
    coverage_complete: bool = False,
    currency_code: str = "USD",
    levy_tables: Tuple[Tuple[str, str], ...] = DEFAULT_LEVY_TABLES,
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
                "rate": rate,
                "basis": basis,
                "amount": amount,
                "legal_reference": row["legal_reference"],
                "source_id": row["source_id"],
            }
        )

    levy_amounts = {}
    for table, label in levy_tables:
        row = fiscal_store.percentage_measure(table, on_date, hs_code)
        if row:
            rate = _pct(row["rate"])
            levy_amounts[label] = {
                "rate": rate,
                "amount": round(customs_value * rate / 100, 2),
                "legal_reference": row["legal_reference"],
                "source_id": row["source_id"],
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
    if missing and status != "CONFLICT_REVIEW":
        status = "VERIFIED_PARTIAL"
    sources = set(override["sources_used"])
    sources.update(r["source_id"] for r in excise_lines)
    if vat_row:
        sources.add(vat_row["source_id"])
    for entry in levy_amounts.values():
        if entry:
            sources.add(entry["source_id"])

    warning = None
    if status == "VERIFIED_PARTIAL":
        warning = (
            f"Droits et taxes vérifiés : {verified_total:,.2f} {currency_code}. "
            "Résultat partiel : une dérogation tarifaire EAC ou une condition "
            "susceptible d’affecter ce produit reste à vérifier. "
            "Le total ne doit pas être utilisé pour une déclaration en douane."
        )
    return {
        "jurisdiction": jurisdiction,
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
        "idf": levy_amounts.get("idf"),
        "rdl": levy_amounts.get("rdl"),
        "other_levies": {
            key: value
            for key, value in levy_amounts.items()
            if key not in {"idf", "rdl"} and value is not None
        },
        "verified_total": verified_total,
        "missing_elements": list(dict.fromkeys(missing)),
        "calculation_status": status,
        "sources_used": sorted(sources),
        "restrictions": override["restrictions"],
        "administrative_requirements": override["administrative_requirements"],
        "display_warning": warning,
        "remission_eligibility_status": override["remission_eligibility_status"],
        "requires_eligibility_input": override["requires_eligibility_input"],
    }
