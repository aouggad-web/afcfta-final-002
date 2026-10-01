"""
Routes retirées (lot O2-0 du plan de simplification) : elles servaient un taux
ou une donnée tarifaire qui ne venait d'aucun fichier tracé (taux par chapitre,
taux « par défaut », barèmes saisis à la main, calendriers génériques), ou
écrasaient les tarifs sourcés.

Un appelant — écran ou client de l'API — reçoit 410 et, quand elle existe, la
route qui sert la donnée sourcée, plutôt qu'un 404 muet. Aucune donnée n'est
renvoyée. Ce routeur est monté en premier : un chemin retiré l'emporte ainsi
sur une route vivante dont le gabarit le capterait (ex.
/dismantlement/summary/{pays} face à /dismantlement/{pays}/{sh6}).
"""

import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

CALCUL = "POST /api/calcul"

# (méthode, chemin sous /api, route sourcée qui sert la donnée, ou None)
ROUTES_RETIREES = [
    # Calculateur régional v3 : médiane d'une bande de taux saisie à la main.
    ("POST", "/regional-calculator/regional-route", CALCUL),
    ("POST", "/regional-calculator/country-taxes", CALCUL),
    ("POST", "/regional-calculator/supply-chain", CALCUL),
    ("POST", "/regional-calculator/preferential", None),
    ("GET", "/regional-calculator/free-zones", None),
    ("GET", "/regional-calculator/investment-map", None),
    # Ancien calculateur : droit par chapitre, TVA « par défaut ».
    ("POST", "/calculate-tariff", CALCUL),
    ("POST", "/calculate/detailed", CALCUL),
    ("GET", "/calculate/detailed/{country_code}/{hs_code}", CALCUL),
    ("POST", "/enhanced-calculator/dza", CALCUL),
    # Taux par pays ou par SH6 saisis dans le code.
    ("GET", "/country-tariffs/{country_code}", CALCUL),
    ("GET", "/country-tariffs-comparison", CALCUL),
    ("GET", "/all-country-rates", CALCUL),
    ("GET", "/bilateral-tariff/{country_a}/{country_b}/{hs6}", CALCUL),
    ("GET", "/hs6-tariffs/search", CALCUL),
    ("GET", "/hs6-tariffs/chapter/{chapter}", CALCUL),
    ("GET", "/hs6-tariffs/statistics", None),
    ("GET", "/hs6-tariffs/products/african-exports", None),
    ("GET", "/country-hs6-tariffs/available", None),
    ("GET", "/country-hs6-tariffs/{country_code}/search", CALCUL),
    ("GET", "/country-hs6-tariffs/{country_code}/all", CALCUL),
    ("GET", "/country-hs6-tariffs/{country_code}/{hs6_code}", CALCUL),
    ("GET", "/tariffs/detailed/{country_code}/{hs_code}", CALCUL),
    ("GET", "/tariffs/sub-position/{country_code}/{full_code}", CALCUL),
    # Régimes régionaux et calendriers génériques.
    ("GET", "/dismantlement/summary/{country_iso3}", None),
    ("GET", "/dismantlement/impact/{country_iso3}/{hs6}", None),
    ("POST", "/regions/sacu/import-cost", CALCUL),
    ("GET", "/tariffs/north-africa", CALCUL),
    ("GET", "/tariffs/north-africa/{country_code}", CALCUL),
    ("POST", "/crawlers/north-africa/optimal-route", None),
    ("GET", "/crawlers/north-africa/preferential-matrix/{hs_code}", None),
    ("GET", "/trade/north-africa/agreements", None),
    ("GET", "/regions/sadc/protocols", None),
    # Collecte qui réécrivait les tarifs sourcés, et résumés qui en sortaient.
    ("POST", "/tariff-data/collect", None),
    ("POST", "/tariff-data/collect/{country_code}", None),
    ("POST", "/crawl/start", None),
    ("GET", "/crawl/jobs", None),
    ("GET", "/crawl/jobs/{job_id}", None),
    ("GET", "/crawl/jobs/{job_id}/progress", None),
    ("POST", "/crawl/jobs/{job_id}/cancel", None),
    ("GET", "/crawl/registry", None),
    ("GET", "/crawl/countries", None),
    ("GET", "/crawl/notifications/stats", None),
    ("GET", "/regulatory-engine/summary/{country}", None),
]


def _reponse_410(remplacement):
    message = "Route retirée : elle servait des données tarifaires non sourcées." + (
        f" Utiliser {remplacement}, qui ne sert que des données tracées."
        if remplacement
        else " Aucune route ne sert encore cette donnée de façon sourcée."
    )

    def route_retiree():
        return JSONResponse(
            status_code=410,
            content={"code": "ROUTE_RETIREE", "message": message, "remplacement": remplacement},
        )

    return route_retiree


for _methode, _chemin, _remplacement in ROUTES_RETIREES:
    router.add_api_route(
        _chemin, _reponse_410(_remplacement), methods=[_methode], include_in_schema=False
    )


def exemptions_csrf():
    """Couples (méthode, motif) des chemins retirés appelés par une méthode non
    sûre. Ils ne modifient rien et ne renvoient aucune donnée : le jeton CSRF n'y
    protège rien, et sans exemption un POST sans jeton recevrait 403 au lieu du
    410 qui indique la route de remplacement."""
    return [
        (methode, re.compile("/".join(_motif_segment(s) for s in ("/api" + chemin).split("/"))))
        for methode, chemin, _ in ROUTES_RETIREES
        if methode not in ("GET", "HEAD", "OPTIONS")
    ]


def _motif_segment(segment):
    return "[^/]+" if segment.startswith("{") else re.escape(segment)
