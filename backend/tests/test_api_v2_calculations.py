"""Tests de l'endpoint v2 : contrat fail-closed HTTP et moteur canonique v4.

Réunit deux jeux de tests que la fusion de d88d35b avait laissés en conflit :
les régressions HTTP garantissant qu'un tarif fourni par le client ne devient
jamais un calcul vérifié, et la vérification que l'endpoint v2 passe bien par
le moteur canonique pour l'économie ZLECAf.
"""

import pytest
from api.v2.endpoints import CalculationRequest, calculate_tariff_v2, router
from fastapi import FastAPI
from fastapi.testclient import TestClient
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


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("data_status", ["SYNTHETIC", "PARTIAL", "VERIFIED"])
@pytest.mark.parametrize("regime", ["NPF", "ZLECAF"])
def test_client_supplied_provenance_cannot_authorize_calculation(
    client, data_status, regime
):
    # Contract sentinel only: no customs dataset or invented official rate.
    response = client.post(
        "/api/v2/calculations",
        json={
            "line": {
                "commodity": {
                    "country_iso3": "ZZZ",
                    "national_code": "00000000",
                    "hs6": "000000",
                    "digits": 8,
                    "chapter": "00",
                    "description_fr": "Contract test sentinel",
                },
                "measures": [],
                "provenance": {"data_status": data_status},
            },
            "cif_value": 100,
            "regime": regime,
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["data_status"] == "NOT_AVAILABLE"
    assert response.json()["detail"]["code"] == "VERIFIED_TARIFF_PROVIDER_REQUIRED"
    assert "result" not in response.json()


def test_bulk_endpoint_cannot_return_chapter_estimates(client):
    response = client.post(
        "/api/v2/bulk/tariff-calculations",
        json={
            "products": [
                {"hs_code": "870000", "description": "Contract test sentinel"}
            ],
            "routes": [{"origin": "ZZZ", "destination": "ZZZ"}],
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["data_status"] == "NOT_AVAILABLE"
    assert "results" not in response.json()


@pytest.mark.parametrize("hs_code", ["010000", "870000", "999999"])
def test_mobile_lookup_preserves_unknown_tariff_values(client, hs_code):
    response = client.get("/api/v2/mobile/quick-lookup", params={"hs_code": hs_code})
    assert response.status_code == 200
    summary = response.json()["tariff_summary"]
    assert summary["mfn_rate_pct"] is None
    assert summary["afcfta_rate_pct"] is None
    assert summary["data_status"] == "NOT_AVAILABLE"


def test_mobile_empty_query_still_rejected(client):
    assert client.get("/api/v2/mobile/quick-lookup").status_code == 400



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
