"""
Lot O2-0 du plan de simplification : les sources de taux inventés sont retirées.

Le test exigé par la fiche O2-0 échoue si GraphQL renvoie de nouveau un
`tariffRatePct` (taux fixe de 5 % de `bulkTariffCalculation`) ; le second, si un
module qui fabriquait des taux revient.
"""

import importlib.util

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

MODULES_RETIRES = [
    "services.enhanced_calculator_v3",
    "routes.regional_calculator",
    "routes.calculator",
    "routes.enhanced_calculator",
    "services.enhanced_calculator_service",
    "routes.crawl",
    "services.crawl_orchestrator",
    "crawlers.scraper_factory",
    "crawlers.countries.generic_scraper",
    "crawlers.countries.north_africa.tariff_structures",
    "etl.country_hs6_tariffs",
    "etl.country_hs6_tariffs_cedeao_cemac",
    "etl.country_hs6_tariffs_eac_sadc",
    "etl.country_hs6_tariffs_north_other",
    "tax_rates",
    "crawlers.countries.uma_tariff_structures",
    "services.north_africa_intelligence",
]


def test_graphql_ne_renvoie_aucun_taux_de_calcul():
    from api.graphql.schema import router
    from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL

    app = FastAPI()
    app.include_router(router, prefix="/api")
    reponse = TestClient(app).post(
        "/api/graphql",
        json={
            "query": (
                "query Q($calculations: [TariffCalculationInput!]!) "
                "{ bulkTariffCalculation(calculations: $calculations) "
                "{ results { tariffRatePct } } }"
            ),
            "variables": {
                "calculations": [
                    {
                        "originCountry": "KEN",
                        "destinationCountry": "TZA",
                        "hsCode": "010121",
                        "goodsValueUsd": 1000,
                    }
                ]
            },
        },
    )
    assert "tariffRatePct" not in reponse.text
    assert "bulkTariffCalculation" not in GRAPHQL_SCHEMA_SDL
    assert "tariffRatePct" not in GRAPHQL_SCHEMA_SDL


@pytest.mark.parametrize("module", MODULES_RETIRES)
def test_source_de_taux_inventes_retiree(module):
    assert importlib.util.find_spec(module) is None
