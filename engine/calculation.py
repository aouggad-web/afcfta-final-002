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
from typing import List, Optional, Dict

from schemas.canonical_model import (
    CanonicalTariffLine, RateType, DutyBasis, DataStatus,
    LEGAL_DISCLAIMER_FR,
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
    regime: str                      # "NPF" ou "ZLECAF"
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
        line:      ligne tarifaire canonique (schéma v4 ; v3 accepté, assiette CAF
                   et séquence par défaut seront alors appliquées avec avertissement)
        cif_value: valeur CAF dans la monnaie du pays
        quantity:  quantité physique (requise si une mesure est SPECIFIC/MIXED)
        regime:    "NPF" ou "ZLECAF"
    """
    regime = regime.upper()
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
            basis_label = getattr(m, "basis_note", None) or "Assiette non spécifiée (CAF par défaut)"
            result.warnings.append(f"{m.code}: assiette OTHER — calcul indicatif sur CAF")

        # --- Montant ---
        amount = 0.0
        if rate_type == RateType.EXEMPT or (rate is not None and rate == 0 and rate_type == RateType.AD_VALOREM):
            amount = 0.0
        if rate_type in (RateType.AD_VALOREM, RateType.MIXED) and rate:
            amount += basis_amount * rate / 100.0
        if rate_type in (RateType.SPECIFIC, RateType.MIXED):
            spec = getattr(m, "specific_amount", None)
            if spec is not None:
                if quantity is None:
                    result.warnings.append(f"{m.code}: montant spécifique ignoré (quantité absente)")
                else:
                    amount += spec * quantity

        amount = round(amount, 2)
        computed[m.code] = amount

        result.lines.append(MeasureResult(
            code=m.code,
            name_fr=m.name_fr,
            rate_applied_pct=rate,
            basis_label=basis_label,
            basis_amount=round(basis_amount, 2),
            amount=amount,
            regime="ZLECAF" if note else "NPF",
            legal_reference=getattr(m, "legal_reference", None),
            note=note,
        ))

    result.total_duties_taxes = round(sum(l.amount for l in result.lines), 2)
    result.landed_cost = round(cif_value + result.total_duties_taxes, 2)
    result.effective_rate_pct = (
        round(result.total_duties_taxes / cif_value * 100.0, 2) if cif_value else 0.0
    )
    return result
