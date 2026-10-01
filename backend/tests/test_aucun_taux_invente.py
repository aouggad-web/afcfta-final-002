"""
Lot O2-0 du plan de simplification : aucune route ne sert un taux qui ne vient
pas d'un fichier tracé.

Les routes qui en servaient un sont retirées (liste : routes/routes_retirees.py),
notamment :
  - GraphQL `bulkTariffCalculation` : taux fixe de 5 % étiqueté « AfCFTA
    preferential », quels que soient le couple et la position ;
  - `/api/regional-calculator/*` (`services/enhanced_calculator_v3.py`) :
    médiane d'une bande de taux écrite à la main quand le taux n'était pas
    fourni, et GZALE ajoutée aux accords de tous les pays, CEMAC comprise ;
  - l'ancien calculateur (`/api/calculate-tariff`, `/api/calculate/detailed`,
    `/api/enhanced-calculator`), les taux par chapitre ou saisis
    (`/api/country-tariffs`, `/api/hs6-tariffs/*`, `/api/country-hs6-tariffs/*`,
    `/api/tariffs/detailed`), les calendriers et régimes génériques
    (`/api/dismantlement/impact`, `/api/regions/sacu/import-cost`,
    `/api/tariffs/north-africa`, `/api/crawlers/north-africa/optimal-route`) ;
  - la collecte qui réécrivait les tarifs sourcés (`/api/crawl/*`,
    `/api/tariff-data/collect`).

Un chemin retiré répond 410 avec la route sourcée de remplacement, sans
donnée. Ces tests échouent si l'une de ces routes ou de ces sources revient.
"""

import importlib.util
import re

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from routes import register_routes
from routes.routes_retirees import ROUTES_RETIREES
from routes.routes_retirees import router as routes_retirees_router

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

# Clés qui portaient un taux saisi dans le code, sans fichier source.
CLES_DE_TAUX_SAISIS = {
    "tva_rate",
    "vat_rate",
    "dd_bands",
    "dd_bands_pct",
    "cet_bands",
    "national_taxes",
    "tariff_bands",
    "common_taxes",
}


GESTIONNAIRES_410 = {r.endpoint for r in routes_retirees_router.routes}


def _chemin_concret(gabarit):
    return re.sub(r"\{[^}]+\}", "KEN", gabarit)


def _client(router):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(scope="module")
def api_router():
    api_router = APIRouter(prefix="/api")
    register_routes(api_router)
    return api_router


def _routes_vivantes(api_router):
    return [
        (m, r.path)
        for r in api_router.routes
        if isinstance(r, APIRoute) and r.endpoint not in GESTIONNAIRES_410
        for m in r.methods
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


def test_aucune_route_vivante_ne_sert_un_chemin_retire(api_router):
    vivantes = set(_routes_vivantes(api_router))
    retirees = {(m, "/api" + c) for m, c, _ in ROUTES_RETIREES}

    assert ("POST", "/api/calcul") in vivantes
    assert vivantes & retirees == set()


@pytest.mark.parametrize("methode,gabarit,remplacement", ROUTES_RETIREES)
def test_chemin_retire_repond_410_sans_donnee(api_router, methode, gabarit, remplacement):
    reponse = _client(api_router).request(methode, "/api" + _chemin_concret(gabarit), json={})
    corps = reponse.json()

    assert reponse.status_code == 410
    assert set(corps) == {"code", "message", "remplacement"}
    assert corps["code"] == "ROUTE_RETIREE"
    assert corps["remplacement"] == remplacement


def test_l_application_repond_410_sans_jeton_csrf_et_protege_les_routes_vivantes():
    # Application de production, middlewares compris : un client de l'API qui
    # poste sans jeton CSRF sur un chemin retiré doit lire le 410 et la route de
    # remplacement, pas un 403 ; une route vivante reste protégée.
    from server import app

    client = TestClient(app)
    statuts = {
        gabarit: client.request(methode, "/api" + _chemin_concret(gabarit), json={}).status_code
        for methode, gabarit, _ in ROUTES_RETIREES
    }

    assert {g: s for g, s in statuts.items() if s != 410} == {}
    assert client.post("/api/calcul", json={}).status_code == 403


def test_les_chemins_retires_ne_masquent_aucune_route_vivante(api_router):
    client = _client(routes_retirees_router)
    masquees = [
        (m, chemin)
        for m, chemin in _routes_vivantes(api_router)
        if client.request(m, _chemin_concret(chemin).removeprefix("/api")).status_code == 410
    ]

    assert masquees == []


def _cles(objet):
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            yield cle
            yield from _cles(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _cles(valeur)


@pytest.mark.parametrize(
    "chemin",
    [
        "/api/crawlers/cemac/countries",
        "/api/crawlers/cemac/data-summary",
        "/api/crawlers/cemac/data/TCD?page_size=1",
        "/api/regions/sacu/customs-union",
        "/api/regions/north-africa/countries",
        "/api/regions/north-africa/compare",
        "/api/regions/uma/intelligence",
    ],
)
def test_route_vivante_sans_taux_saisi(api_router, chemin):
    # Routes gardées (métadonnées, données des fichiers crawlés) dont on a
    # retiré les taux écrits dans le code : TVA, bandes de droits, taxes.
    from auth import require_admin, require_auth

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[require_auth] = lambda: {"tier": "test"}
    app.dependency_overrides[require_admin] = lambda: {"tier": "admin"}
    reponse = TestClient(app).get(chemin)

    assert reponse.status_code == 200, reponse.text
    assert CLES_DE_TAUX_SAISIS & set(_cles(reponse.json())) == set()


@pytest.mark.parametrize("module", MODULES_RETIRES)
def test_source_de_taux_inventes_retiree(module):
    assert importlib.util.find_spec(module) is None
