"""
Moteur de calcul des droits et taxes — Schéma v4
================================================

Calcule de façon déterministe et auditable le montant de chaque droit/taxe
d'une ligne tarifaire, en respectant :
  - l'assiette déclarée de chaque mesure (basis / basis_includes)
  - l'ordre d'application (sequence)
  - la nature du taux (ad valorem / spécifique / mixte / exonéré)
  - le régime demandé (NPF ou ZLECAf)

Exemple Algérie (séquence réelle, Circ. 419 DGD) :
  1. D.D   (seq 10) : 5%  sur valeur CAF
  2. T.C.S (seq 20) : 3%  sur valeur CAF
  3. PRCT  (seq 30) : 2%  sur valeur CAF
  4. T.V.A (seq 90) : 9%  sur CAF + D.D + T.C.S + PRCT  (basis_includes)
"""

from dataclasses import dataclass, field
from math import isfinite
from typing import Dict, List, Optional

from schemas.canonical_model import (
    LEGAL_DISCLAIMER_FR,
    CanonicalTariffLine,
    DataStatus,
    DutyBasis,
    RateType,
)


@dataclass
class MeasureResult:
    """Résultat de calcul pour une mesure"""

    code: str
    name_fr: str
    rate_applied_pct: Optional[float]
    basis_label: str
    basis_amount: float
    amount: float
    regime: str  # "NPF" ou "ZLECAF"
    legal_reference: Optional[str] = None
    note: Optional[str] = None


@dataclass
class CalculationResult:
    """Décomposition complète du calcul"""

    country_iso3: str
    national_code: str
    cif_value: float
    currency: str
    regime: str
    lines: List[MeasureResult] = field(default_factory=list)
    total_duties_taxes: float = 0.0
    landed_cost: float = 0.0
    effective_rate_pct: float = 0.0
    data_status: str = DataStatus.SYNTHETIC.value
    disclaimer: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class CalculationUnavailable(ValueError):
    """Incomplete inputs must never be turned into a complete tax total."""

    code = "CALCULATION_UNAVAILABLE"

    def __init__(self, issues: List[str]):
        self.issues = tuple(issues)
        super().__init__("; ".join(issues))


def _validate_inputs(line, cif_value, quantity, currency, regime):
    issues = []

    def nonnegative(value):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value >= 0
        )

    if not nonnegative(cif_value) or cif_value == 0:
        issues.append("cif_value: positive finite value required")
    if quantity is not None and (not nonnegative(quantity) or quantity == 0):
        issues.append("quantity: positive finite value required")
    if regime not in {"NPF", "ZLECAF"}:
        issues.append("regime: NPF or ZLECAF required")
    if not isinstance(currency, str) or not currency.strip():
        issues.append("currency: explicit currency required")
    provenance = line.provenance
    if provenance.data_status == DataStatus.SYNTHETIC:
        issues.append("provenance: synthetic tariff data is not calculable")
    if not (provenance.source_name or "").strip() or not (
        (provenance.source_url or "").strip() or (provenance.source_document or "").strip()
    ):
        issues.append("provenance: source name and source document or URL required")
    if not line.measures:
        issues.append("measures: no documented measures supplied")

    previous = set()
    for measure in sorted(line.measures, key=lambda m: m.sequence):
        code = measure.code
        if not code.strip() or code in previous:
            issues.append(f"{code}: empty or duplicate measure code")
        if (
            measure.country_iso3 != line.commodity.country_iso3
            or measure.national_code != line.commodity.national_code
        ):
            issues.append(f"{code}: measure does not belong to this national position")
        if measure.basis in (DutyBasis.OTHER, DutyBasis.FOB):
            issues.append(f"{code}: explicit {measure.basis.value} input or method required")
        if measure.basis == DutyBasis.CIF_PLUS_INCLUDED:
            if any(c not in previous for c in measure.basis_includes):
                issues.append(f"{code}: unresolved basis dependency")
            if len(measure.basis_includes) != len(set(measure.basis_includes)):
                issues.append(f"{code}: duplicate basis dependency")
        if measure.rate_type not in {
            RateType.AD_VALOREM,
            RateType.SPECIFIC,
            RateType.MIXED,
            RateType.EXEMPT,
        }:
            issues.append(f"{code}: unsupported rate type {measure.rate_type}")
        if measure.rate_type != RateType.EXEMPT:
            rate = measure.rate_pct
            if regime == "ZLECAF" and measure.is_zlecaf_applicable:
                rate = measure.zlecaf_rate_pct
                if rate is None:
                    issues.append(f"{code}: documented preferential rate required")
            if measure.rate_type in (RateType.AD_VALOREM, RateType.MIXED) and not nonnegative(rate):
                issues.append(f"{code}: finite nonnegative ad valorem rate required")
            if measure.rate_type in (RateType.SPECIFIC, RateType.MIXED):
                if regime == "ZLECAF" and measure.is_zlecaf_applicable:
                    issues.append(f"{code}: preferential specific amount is not modeled")
                if not nonnegative(measure.specific_amount):
                    issues.append(f"{code}: finite nonnegative specific amount required")
                if not (measure.specific_unit or "").strip():
                    issues.append(f"{code}: specific unit required")
                elif (
                    "/" not in measure.specific_unit
                    or not measure.specific_unit.split("/", 1)[1].strip()
                    or measure.specific_unit.split("/", 1)[0].strip().upper()
                    != str(currency).upper()
                ):
                    issues.append(f"{code}: specific unit currency must match calculation currency")
                if quantity is None:
                    issues.append(f"{code}: quantity required")
            if measure.basis == DutyBasis.QUANTITY and measure.rate_type != RateType.SPECIFIC:
                # A percentage of a physical quantity has no monetary meaning.
                issues.append(f"{code}: quantity basis requires a specific rate")
        previous.add(code)
    if issues:
        raise CalculationUnavailable(issues)


def compute_duties(
    line: CanonicalTariffLine,
    cif_value: float,
    quantity: Optional[float] = None,
    currency: str = "LOCAL",
    regime: str = "NPF",
) -> CalculationResult:
    """
    Calcule l'ensemble des droits et taxes d'une ligne tarifaire.

    Args:
        line:      ligne tarifaire canonique sourcée, mesures complètes et
                   dépendances d'assiette résolues ; sinon CalculationUnavailable
        cif_value: valeur CAF dans la monnaie du pays
        quantity:  quantité physique (requise si une mesure est SPECIFIC/MIXED)
        regime:    "NPF" ou "ZLECAF"
    """
    regime = regime.upper() if isinstance(regime, str) else ""
    _validate_inputs(line, cif_value, quantity, currency, regime)
    result = CalculationResult(
        country_iso3=line.commodity.country_iso3,
        national_code=line.commodity.national_code,
        cif_value=cif_value,
        currency=currency,
        regime=regime,
        data_status=line.provenance.data_status.value,
    )
    if line.provenance.data_status != DataStatus.VERIFIED:
        result.disclaimer = LEGAL_DISCLAIMER_FR

    # Montants calculés par code de mesure (pour assiettes cumulées)
    computed: Dict[str, float] = {}

    # Tri par séquence d'application
    measures = sorted(line.measures, key=lambda m: getattr(m, "sequence", 100))

    for m in measures:
        rate_type = getattr(m, "rate_type", RateType.AD_VALOREM)
        basis = getattr(m, "basis", DutyBasis.CIF)
        basis_includes = getattr(m, "basis_includes", []) or []

        # --- Taux applicable selon le régime ---
        rate = m.rate_pct
        note = None
        if regime == "ZLECAF" and m.is_zlecaf_applicable and m.zlecaf_rate_pct is not None:
            rate = m.zlecaf_rate_pct
            note = "Taux préférentiel ZLECAf (certificat d'origine ZLECAf requis)"

        # --- Assiette ---
        if basis in (DutyBasis.CIF, DutyBasis.CUSTOMS_VALUE, DutyBasis.FOB):
            basis_amount = cif_value
            basis_label = basis.value
        elif basis == DutyBasis.CIF_PLUS_INCLUDED:
            missing = [c for c in basis_includes if c not in computed]
            if missing:
                result.warnings.append(
                    f"{m.code}: mesures d'assiette non calculées en amont: {missing} "
                    f"(vérifier les champs sequence)"
                )
            basis_amount = cif_value + sum(computed.get(c, 0.0) for c in basis_includes)
            basis_label = "CAF + " + " + ".join(basis_includes) if basis_includes else "CAF"
        elif basis == DutyBasis.QUANTITY:
            basis_amount = quantity or 0.0
            basis_label = f"Quantité ({getattr(m, 'specific_unit', None) or 'unité'})"
            if quantity is None:
                result.warnings.append(f"{m.code}: droit spécifique mais quantité absente")
        else:  # OTHER
            basis_amount = cif_value
            basis_label = (
                getattr(m, "basis_note", None) or "Assiette non spécifiée (CAF par défaut)"
            )
            result.warnings.append(f"{m.code}: assiette OTHER — calcul indicatif sur CAF")

        # --- Montant ---
        amount = 0.0
        if rate_type == RateType.EXEMPT or (
            rate is not None and rate == 0 and rate_type == RateType.AD_VALOREM
        ):
            amount = 0.0
        if rate_type in (RateType.AD_VALOREM, RateType.MIXED) and rate:
            amount += basis_amount * rate / 100.0
        if rate_type in (RateType.SPECIFIC, RateType.MIXED):
            spec = getattr(m, "specific_amount", None)
            if spec is not None:
                if quantity is None:
                    result.warnings.append(
                        f"{m.code}: montant spécifique ignoré (quantité absente)"
                    )
                else:
                    amount += spec * quantity

        if not isfinite(amount) or not isfinite(basis_amount):
            raise CalculationUnavailable([f"{m.code}: non-finite calculation result"])
        amount = round(amount, 2)
        computed[m.code] = amount

        result.lines.append(
            MeasureResult(
                code=m.code,
                name_fr=m.name_fr,
                rate_applied_pct=rate,
                basis_label=basis_label,
                basis_amount=round(basis_amount, 2),
                amount=amount,
                regime="ZLECAF" if note else "NPF",
                legal_reference=getattr(m, "legal_reference", None),
                note=note,
            )
        )

    result.total_duties_taxes = round(sum(l.amount for l in result.lines), 2)
    result.landed_cost = round(cif_value + result.total_duties_taxes, 2)
    if not isfinite(result.total_duties_taxes) or not isfinite(result.landed_cost):
        raise CalculationUnavailable(["total: non-finite calculation result"])
    result.effective_rate_pct = (
        round(result.total_duties_taxes / cif_value * 100.0, 2) if cif_value else 0.0
    )
    return result
