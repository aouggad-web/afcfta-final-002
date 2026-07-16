"""Tests for the canonical v4 calculation endpoint."""

import pytest

from api.v2.endpoints import CalculationRequest, calculate_tariff_v2
from schemas.canonical_model import (
    SCHEMA_VERSION,
    CanonicalTariffLine,
    CommodityCode,
    DataStatus,
    DutyBasis,
    Measure,
    MeasureType,
    Provenance,
    RateType,
    ReliabilityGrade,
)


def _dza_line() -> CanonicalTariffLine:
    commodity = CommodityCode(
        country_iso3="DZA",
        national_code="0101211100",
        hs6="010121",
        digits=10,
        description_fr="Chevaux > Reproducteurs de race pure > De course",
        chapter="01",
        hs_version="HS2022",
    )
    measures = [
        Measure(
            country_iso3="DZA",
            national_code="0101211100",
            measure_type=MeasureType.CUSTOMS_DUTY,
            code="D.D",
            name_fr="Droit de Douane",
            rate_pct=5.0,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF,
            sequence=10,
            is_zlecaf_applicable=True,
            zlecaf_rate_pct=0.0,
        ),
        Measure(
            country_iso3="DZA",
            national_code="0101211100",
            measure_type=MeasureType.OTHER_TAX,
            code="T.C.S",
            name_fr="Taxe de Contribution de Solidarité",
            rate_pct=3.0,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF,
            sequence=20,
        ),
        Measure(
            country_iso3="DZA",
            national_code="0101211100",
            measure_type=MeasureType.LEVY,
            code="PRCT",
            name_fr="Prélèvement à la Compensation du Transport",
            rate_pct=2.0,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF,
            sequence=30,
        ),
        Measure(
            country_iso3="DZA",
            national_code="0101211100",
            measure_type=MeasureType.VAT,
            code="T.V.A",
            name_fr="Taxe sur la Valeur Ajoutée",
            rate_pct=9.0,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF_PLUS_INCLUDED,
            basis_includes=["D.D", "T.C.S", "PRCT"],
            sequence=90,
        ),
    ]
    provenance = Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name="conformepro.dz",
    )
    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
    )


@pytest.mark.asyncio
async def test_calculate_tariff_v2_uses_canonical_engine_for_zlecaf_savings():
    request = CalculationRequest(
        line=_dza_line(),
        cif_value=1_000_000.0,
        currency="DZD",
        regime="ZLECAF",
    )

    response = await calculate_tariff_v2(request)

    assert response["success"] is True
    assert response["calculation_engine"] == "engine.calculation.compute_duties"
    assert response["data_status"] == "PARTIAL"
    assert response["disclaimer"] is not None
    assert response["result"]["total_duties_taxes"] == 144_500.0
    assert response["result"]["landed_cost"] == 1_144_500.0
    assert response["result"]["effective_rate_pct"] == 14.45
    assert {line["code"] for line in response["result"]["lines"]} == {
        "D.D",
        "T.C.S",
        "PRCT",
        "T.V.A",
    }
