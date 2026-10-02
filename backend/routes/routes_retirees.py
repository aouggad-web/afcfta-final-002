"""
Routes retirées (lot O2-0 du plan de simplification) : elles servaient, en tout
ou en partie, un taux ou une donnée tarifaire qui ne venait d'aucun fichier
tracé (taux par chapitre, taux « par défaut », barèmes saisis à la main,
calendriers génériques), ou pilotaient la collecte qui écrasait les tarifs
sourcés.

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
# L'Algérie n'a pas de taux ZLECAf sur POST /api/calcul : absente de
# zlecaf_implementation_registry.RECORDS, elle y reçoit NOT_AVAILABLE. Seul le
# chemin historique sert sa préférence (circulaire DGD 482/2024), jusqu'au lot
# O1-b ; test_aucun_taux_invente.py vérifie ce couplage.
HISTORIQUE_DZA = "GET /api/authentic-tariffs/calculate/DZA/{hs_code}?origin={origine}"
CALCUL_ET_DZA = f"{CALCUL} ; préférence ZLECAf de l'Algérie : {HISTORIQUE_DZA}"
RECHERCHE_PUIS_CALCUL = (
    "GET /api/authentic-tariffs/search/{country_iso3}?q={texte} pour trouver la position "
    f"(40 pays ; ses taux ne font pas foi), puis {CALCUL}"
)
POSITION_PAR_POSITION = f"{CALCUL} (position par position)"
PAYS_DU_SOCLE = "GET /api/calcul/pays"
# POST /api/calcul attend une position nationale du socle : un SH6 n'y est servi
# que dans quelques pays. Les positions d'un SH6 se lisent sur le chemin
# historique, dont les taux ne font pas foi.
POSITIONS_SH6 = "GET /api/authentic-tariffs/country/{country_iso3}/sub-positions/{hs6}"
COLLECTE = ("/crawl/", "/tariff-data/collect")

# (méthode, chemin sous /api, route sourcée qui sert la donnée, ou None)
ROUTES_RETIREES = [
    # Calculateur régional v3 : médiane d'une bande de taux saisie à la main.
    ("POST", "/regional-calculator/regional-route", CALCUL),
    ("POST", "/regional-calculator/country-taxes", CALCUL),
    ("POST", "/regional-calculator/supply-chain", CALCUL),
    ("POST", "/regional-calculator/preferential", None),
    ("GET", "/regional-calculator/free-zones", None),
    ("GET", "/regional-calculator/investment-map", None),
    # Ancien calculateur : lignes crawlées mêlées de droits par chapitre en
    # repli et de TVA saisie ; /calculate/detailed et /enhanced-calculator y
    # ajoutaient un taux ZLECAf sans contrôle d'origine.
    ("POST", "/calculate-tariff", CALCUL_ET_DZA),
    ("POST", "/calculate/detailed", CALCUL_ET_DZA),
    ("GET", "/calculate/detailed/{country_code}/{hs_code}", CALCUL_ET_DZA),
    ("POST", "/enhanced-calculator/dza", CALCUL_ET_DZA),
    # Taux par pays ou par SH6 saisis dans le code.
    ("GET", "/country-tariffs/{country_code}", CALCUL_ET_DZA),
    (
        "GET",
        "/country-tariffs-comparison",
        f"{POSITION_PAR_POSITION} ; préférence ZLECAf de l'Algérie : {HISTORIQUE_DZA}",
    ),
    ("GET", "/all-country-rates", POSITION_PAR_POSITION),
    ("GET", "/bilateral-tariff/{country_a}/{country_b}/{hs6}", CALCUL_ET_DZA),
    ("GET", "/hs6-tariffs/search", RECHERCHE_PUIS_CALCUL),
    ("GET", "/hs6-tariffs/chapter/{chapter}", None),
    ("GET", "/hs6-tariffs/statistics", None),
    ("GET", "/hs6-tariffs/products/african-exports", None),
    ("GET", "/country-hs6-tariffs/available", PAYS_DU_SOCLE),
    ("GET", "/country-hs6-tariffs/{country_code}/search", RECHERCHE_PUIS_CALCUL),
    (
        "GET",
        "/country-hs6-tariffs/{country_code}/all",
        f"{POSITION_PAR_POSITION} ; lignes collectées : "
        "GET /api/crawlers/cemac/data/{country_code} (CEMAC), "
        "GET /api/countries/sadc/{country_code}/tariffs (SADC)",
    ),
    ("GET", "/country-hs6-tariffs/{country_code}/{hs6_code}", CALCUL),
    ("GET", "/tariffs/detailed/{country_code}/{hs_code}", CALCUL),
    ("GET", "/tariffs/sub-position/{country_code}/{full_code}", CALCUL),
    # Régimes régionaux et calendriers génériques.
    ("GET", "/dismantlement/summary/{country_iso3}", None),
    (
        "GET",
        "/dismantlement/impact/{country_iso3}/{hs6}",
        f"taux de l'année seulement, aucune route ne sert de calendrier pluriannuel : {CALCUL_ET_DZA}",
    ),
    ("POST", "/regions/sacu/import-cost", CALCUL),
    ("GET", "/tariffs/north-africa", POSITION_PAR_POSITION),
    ("GET", "/tariffs/north-africa/{country_code}", POSITION_PAR_POSITION),
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
    (
        "GET",
        "/regulatory-engine/summary/{country}",
        f"{PAYS_DU_SOCLE} (positions, familles de taxes, date de collecte)",
    ),
]


def _reponse_410(chemin, remplacement):
    if chemin.startswith(COLLECTE):
        message = (
            "Route retirée : elle pilotait la collecte qui écrasait les tarifs sourcés. Aucune "
            "route ne la remplace : le socle se construit hors ligne (scripts/build_socle.py)."
        )
    else:
        message = (
            "Route retirée : elle servait des taux ou un calendrier non sourcés "
            "(en tout ou en partie)."
        ) + (
            f" Donnée tracée : {remplacement}."
            if remplacement
            else " Aucune route ne sert encore cette donnée de façon sourcée."
        )
    if remplacement and CALCUL in remplacement:
        message += (
            f" {CALCUL} attend une position nationale du socle ; positions d'un SH6 : "
            f"{POSITIONS_SH6} (40 pays ; ses taux ne font pas foi)."
        )

    def route_retiree():
        return JSONResponse(
            status_code=410,
            content={"code": "ROUTE_RETIREE", "message": message, "remplacement": remplacement},
        )

    return route_retiree


for _methode, _chemin, _remplacement in ROUTES_RETIREES:
    router.add_api_route(
        _chemin, _reponse_410(_chemin, _remplacement), methods=[_methode], include_in_schema=False
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
