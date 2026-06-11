"""
Test du moteur de calcul — Cas réel DZA 0101211100
===================================================

Pur-sang arabe de course (reproducteur), conformepro.dz :
  D.D = 5 %, T.C.S = 3 %, PRCT = 2 %, T.V.A = 9 % sur (CAF+D.D+TCS+PRCT)

Résultats attendus (CIF = 1 000 000 DZD) :
  NPF effectif  = 19,90 %   → droits totaux = 199 000 DZD
  Économie ZLECAf (DD = 0 %) = 54 500 DZD
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, Measure, Provenance,
    MeasureType, RateType, DutyBasis, DataStatus, ReliabilityGrade, SCHEMA_VERSION,
)
from calculation import compute_duties

CIF = 1_000_000.0


def _build_line() -> CanonicalTariffLine:
    commodity = CommodityCode(
        country_iso3="DZA",
        national_code="0101211100",
        hs6="010121",
        digits=10,
        description_fr="Chevaux > Reproducteurs de race pure > De course > De pur sang arabe",
        chapter="01",
        hs_version="HS2022",
    )

    measures = [
        Measure(
            country_iso3="DZA", national_code="0101211100",
            measure_type=MeasureType.CUSTOMS_DUTY, code="D.D",
            name_fr="Droit de Douane", name_en="Customs Duty",
            rate_pct=5.0, rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF, sequence=10,
            legal_reference="Art. 16 Code des Douanes",
            is_zlecaf_applicable=True, zlecaf_rate_pct=0.0,
        ),
        Measure(
            country_iso3="DZA", national_code="0101211100",
            measure_type=MeasureType.OTHER_TAX, code="T.C.S",
            name_fr="Taxe de Contribution de Solidarité",
            rate_pct=3.0, rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF, sequence=20,
            legal_reference="Circ. 419 DGD",
            is_zlecaf_applicable=False,
        ),
        Measure(
            country_iso3="DZA", national_code="0101211100",
            measure_type=MeasureType.LEVY, code="PRCT",
            name_fr="Prélèvement à la Compensation du Transport",
            rate_pct=2.0, rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF, sequence=30,
            legal_reference="Circ. 419 DGD",
            is_zlecaf_applicable=False,
        ),
        Measure(
            country_iso3="DZA", national_code="0101211100",
            measure_type=MeasureType.VAT, code="T.V.A",
            name_fr="Taxe sur la Valeur Ajoutée",
            rate_pct=9.0, rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF_PLUS_INCLUDED,
            basis_includes=["D.D", "T.C.S", "PRCT"],
            sequence=90,
            legal_reference="Code des Taxes sur le Chiffre d'Affaires",
            is_zlecaf_applicable=False,
        ),
    ]

    provenance = Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name="conformepro.dz — tarif intégré algérien (agrégateur privé)",
        source_url="https://conformepro.dz",
    )

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
    )


def test_npf_effective_rate():
    line = _build_line()
    result = compute_duties(line, CIF, regime="NPF")

    # D.D = 50 000, T.C.S = 30 000, PRCT = 20 000
    # TVA base = 1 000 000 + 50 000 + 30 000 + 20 000 = 1 100 000
    # TVA = 9 % × 1 100 000 = 99 000
    # Total = 50 000 + 30 000 + 20 000 + 99 000 = 199 000
    assert result.total_duties_taxes == 199_000.0, (
        f"Attendu 199 000, obtenu {result.total_duties_taxes}"
    )
    assert result.effective_rate_pct == 19.90, (
        f"Attendu 19.90 %, obtenu {result.effective_rate_pct}"
    )
    assert len(result.warnings) == 0, f"Avertissements inattendus : {result.warnings}"
    print(f"  NPF effectif : {result.effective_rate_pct} %  ✓")


def test_zlecaf_savings():
    line = _build_line()
    npf = compute_duties(line, CIF, regime="NPF")
    zlecaf = compute_duties(line, CIF, regime="ZLECAF")

    # Sous ZLECAf : D.D = 0
    # T.C.S = 30 000, PRCT = 20 000
    # TVA base = 1 000 000 + 0 + 30 000 + 20 000 = 1 050 000
    # TVA = 9 % × 1 050 000 = 94 500
    # Total ZLECAf = 30 000 + 20 000 + 94 500 = 144 500
    # Économie = 199 000 - 144 500 = 54 500
    savings = round(npf.total_duties_taxes - zlecaf.total_duties_taxes, 2)
    assert savings == 54_500.0, f"Économie ZLECAf attendue 54 500 DZD, obtenu {savings}"
    print(f"  Économie ZLECAf : {savings} DZD  ✓")


def test_breakdown_completeness():
    line = _build_line()
    result = compute_duties(line, CIF)
    codes = {item.code for item in result.lines}
    assert {"D.D", "T.C.S", "PRCT", "T.V.A"} == codes
    print(f"  Décomposition complète : {codes}  ✓")


def test_disclaimer_on_partial():
    line = _build_line()
    result = compute_duties(line, CIF)
    assert result.disclaimer is not None, "Disclaimer attendu pour données PARTIAL"
    print(f"  Disclaimer présent  ✓")


if __name__ == "__main__":
    print(f"=== Test calcul DZA 0101211100 (CAF = {CIF:,.0f} DZD) ===")
    test_npf_effective_rate()
    test_zlecaf_savings()
    test_breakdown_completeness()
    test_disclaimer_on_partial()
    print("Tous les tests passent.")
