"""
Lot O2-0 du plan de simplification : aucune route ne sert un taux qui ne vient
pas d'un fichier tracé.

Deux routes en servaient un, et sont retirées :
  - GraphQL `bulkTariffCalculation` : taux fixe de 5 % étiqueté « AfCFTA
    preferential », quels que soient le couple et la position ;
  - `/api/regional-calculator/*` (`services/enhanced_calculator_v3.py`) :
    médiane d'une bande de taux écrite à la main quand le taux n'était pas
    fourni, et GZALE ajoutée aux accords de tous les pays, CEMAC comprise.

Ces tests échouent si l'une d'elles revient.
"""

import importlib.util

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


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


def test_aucune_route_regional_calculator_montee():
    from routes import register_routes

    api_router = APIRouter(prefix="/api")
    register_routes(api_router)
    chemins = [route.path for route in api_router.routes]

    assert "/api/calcul" in chemins
    assert [c for c in chemins if c.startswith("/api/regional-calculator")] == []


def test_calculateur_regional_v3_retire():
    assert importlib.util.find_spec("services.enhanced_calculator_v3") is None
