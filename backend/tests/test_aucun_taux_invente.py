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
donnée. Ces tests échouent si l'une de ces routes ou de ces sources revient, si
un remplacement nomme une route qui n'existe pas, si le chemin historique et le
socle divergent sur un taux ZLECAf, ou si le taux EAC servi s'écarte du barème
publié au journal officiel.
"""

import importlib.util
import re

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from routes import register_routes
from routes.routes_retirees import HISTORIQUE_DZA, POSITIONS_SH6, ROUTES_RETIREES
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
    "dd_reduction",
}

# Un taux saisi peut aussi se cacher dans un texte (« TEC CEMAC (4 bands: 5%,
# 10%...) ») ou sous une clé nouvelle : aucun texte ne doit contenir de
# pourcentage, et aucun nombre ne doit se trouver sous une clé de taux, sauf
# dans les sous-arbres nommés ci-dessous.
POURCENTAGE = re.compile(r"\d\s*%")
NOMBRE_EN_TEXTE = re.compile(r"\s*-?\d+(?:[.,]\d+)?\s*")
CLE_DE_TAUX = re.compile(r"rate|taux|pct|tva|vat|duty|droit|band|reduction", re.IGNORECASE)
SOUS_ARBRES_AUTORISES = {
    "tariff_lines": "lignes lues dans le fichier crawlé",
    "dd_rate_range": "fourchette calculée depuis le fichier crawlé",
    "corporate_tax_rate": "impôt sur les sociétés : hors périmètre (finance)",
    "revenue_shares": "partage des recettes SACU : hors périmètre (finance)",
    "revenue_sharing": "partage des recettes SACU : hors périmètre (finance)",
}


# Chemins (clés, codes ISO3 remplacés par « * ») des seuls nombres servis hors
# sous-arbres autorisés : population, PIB, compteurs, pagination.
NOMBRES_AUTORISES = {
    ("combined_gdp_bn_usd",),
    ("combined_population_m",),
    ("countries_with_data",),
    ("total_countries",),
    ("total_sub_positions",),
    ("total_tariff_lines",),
    ("comparison", "*", "gdp_bn_usd"),
    ("comparison", "*", "population_m"),
    ("comparison", "cemac", "gdp_usd_billion"),
    ("comparison", "cemac", "members"),
    ("comparison", "cemac", "population_million"),
    ("comparison", "sadc", "gdp_usd_billion"),
    ("comparison", "sadc", "members"),
    ("comparison", "sadc", "population_million"),
    ("countries", "chapters_covered"),
    ("countries", "gdp_bn_usd"),
    ("countries", "lines_with_sub_positions"),
    ("countries", "population_m"),
    ("countries", "sub_positions"),
    ("country_intelligence", "*", "gdp_bn_usd"),
    ("country_intelligence", "*", "population_m"),
    ("country_intelligence", "*", "special_zones_count"),
    ("framework", "current_agreement"),
    ("framework", "founded"),
    ("framework", "member_count"),
    ("investment_zones", "by_country", "*", "operational"),
    ("investment_zones", "by_country", "*", "port_connected"),
    ("investment_zones", "by_country", "*", "total"),
    ("investment_zones", "operational_zones"),
    ("investment_zones", "port_connected_zones"),
    ("investment_zones", "total_zones"),
    ("pagination", "page"),
    ("pagination", "page_size"),
    ("pagination", "pages"),
    ("pagination", "total"),
}


GESTIONNAIRES_410 = {r.endpoint for r in routes_retirees_router.routes}

# Routes retirées qui servaient un taux ZLECAf par pays : leur 410 nomme le
# chemin historique pour l'Algérie tant que /calcul ne la sert pas.
ROUTES_ZLECAF_PAR_PAYS = {
    ("POST", "/calculate-tariff"),
    ("POST", "/calculate/detailed"),
    ("GET", "/calculate/detailed/{country_code}/{hs_code}"),
    ("POST", "/enhanced-calculator/dza"),
    ("GET", "/country-tariffs/{country_code}"),
    ("GET", "/country-tariffs-comparison"),
    ("GET", "/bilateral-tariff/{country_a}/{country_b}/{hs6}"),
    ("GET", "/dismantlement/impact/{country_iso3}/{hs6}"),
}


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


def _motif_de_gabarit(gabarit):
    segments = ("[^/]+" if s.startswith("{") else re.escape(s) for s in gabarit.split("/"))
    return re.compile("/".join(segments))


def test_chaque_remplacement_nomme_une_route_vivante(api_router):
    vivantes = [(m, _motif_de_gabarit(c)) for m, c in _routes_vivantes(api_router)]
    textes = [r for _, _, r in ROUTES_RETIREES if r] + [POSITIONS_SH6]
    nommees = {
        (m, "/api" + c.split("?")[0])
        for texte in textes
        for m, c in re.findall(r"\b(GET|POST) /api(/[^\s;,()]+)", texte)
    }
    absentes = sorted(
        (m, c) for m, c in nommees if not any(m == mv and mo.fullmatch(c) for mv, mo in vivantes)
    )
    sans_api = [
        (m, c)
        for t in textes
        for m, c in re.findall(r"\b(GET|POST) (/\S*)", t)
        if not c.startswith("/api/")
    ]
    parametres = {
        (m, r.path): {p.alias for p in r.dependant.query_params}
        for r in api_router.routes
        if isinstance(r, APIRoute)
        for m in r.methods
    }
    inconnus = [
        (m, c, q)
        for t in textes
        for m, c, qs in re.findall(r"\b(GET|POST) /api(/[^\s;,()?]+)\??([^\s;,()]*)", t)
        for q in re.findall(r"(\w+)=", qs)
        if not any(
            m == mv and _motif_de_gabarit(cv).fullmatch("/api" + c) and q in noms
            for (mv, cv), noms in parametres.items()
        )
    ]

    assert nommees and absentes == [] and sans_api == [] and inconnus == []


def test_le_remplacement_algerien_suit_la_route_unique():
    # Tant que POST /api/calcul ne sert pas la préférence ZLECAf de l'Algérie,
    # les 410 nomment le chemin historique ; le jour où il la sert (lot O1-b),
    # ce test échoue et HISTORIQUE_DZA doit quitter les remplacements.
    from services import socle
    from services.preference import taux_preferentiels

    position, _ = socle.position("DZA", "0101211100")
    servi_par_calcul = taux_preferentiels(position, "DZA", "EGY", "0101211100")["applique"]
    nommant = {(m, c) for m, c, r in ROUTES_RETIREES if HISTORIQUE_DZA in (r or "")}

    assert nommant == (set() if servi_par_calcul else ROUTES_ZLECAF_PAR_PAYS)


def test_l_exemption_csrf_ne_vaut_que_pour_le_post_du_chemin_retire():
    # L'exemption porte sur le chemin aiguillé, en entier, et sur la seule
    # méthode POST : un « ? » ou « # » encodé qui fait sortir le chemin du
    # gabarit retiré, un suffixe ou une autre méthode retombent sous la
    # protection CSRF.
    from server import app

    client = TestClient(app)
    statuts = {
        (m, c): client.request(m, c, json={}).status_code
        for m, c in [
            ("POST", "/api/crawl/start%3F/x"),
            ("POST", "/api/crawl/start%23/x"),
            ("POST", "/api/%3F/x"),
            ("POST", "/api/crawl/start-xyz"),
            ("POST", "/api/tariff-data/collect/DZA/extra"),
            ("PUT", "/api/crawl/start"),
            ("DELETE", "/api/crawl/jobs/J1/cancel"),
        ]
    }

    assert {k: s for k, s in statuts.items() if s != 403} == {}


def _echantillon(iso3, n=6):
    from services import socle

    codes = sorted(socle.charger(iso3)["positions"])
    return codes[:: max(1, len(codes) // n)][:n]


def test_le_chemin_historique_et_le_socle_servent_le_meme_taux_zlecaf():
    # Parité entre le chemin historique et le moteur du socle : quand le chemin
    # historique applique une préférence, le socle doit porter les mêmes taux
    # préférentiels, droit de douane et autres taxes (TPI marocaine). Pour EGY,
    # MAR et l'EAC, les deux chemins lisent le même calendrier national : ce
    # test ne prouve pas la provenance du taux (voir le test du barème EAC) ;
    # seule ZAF y confronte deux sources distinctes. Exception nommée :
    # l'Algérie, que le socle ne sert pas encore (lot O1-b).
    from services import socle
    from services.authentic_tariff_service import calculate_import_taxes
    from services.preference import taux_preferentiels

    destinations = ["DZA", "EGY", "KEN", "MAR", "RWA", "TZA", "UGA", "ZAF"]
    origines = ["EGY", "GHA", "KEN", "MAR", "ZAF", "TUN", "CMR", "NGA"]
    ecarts, compares = [], set()
    for destination in destinations:
        for code in _echantillon(destination):
            position, _ = socle.position(destination, code)
            for origine in (o for o in origines if o != destination):
                calcul = calculate_import_taxes(
                    destination,
                    code,
                    10000,
                    apply_zlecaf=True,
                    origin_country=origine,
                    fob_value=10000,
                )
                if "error" in calcul or not calcul.get("zlecaf_preference_applied"):
                    continue
                compares.add(destination)
                servi = calcul["rates"]["effective_zlecaf_rate_pct"]
                prefs = taux_preferentiels(position, destination, origine, code)
                taux = (prefs.get("taux") or {}) if prefs["applique"] else {}
                au_socle = (taux.get("DD") or {}).get("taux")
                if au_socle is None or abs(float(servi) - float(au_socle)) > 1e-6:
                    ecarts.append((destination, origine, code, "DD", servi, au_socle))
                etapes = {
                    e["code"]: e["rate_pct"] for e in calcul.get("calculation_steps_zlecaf") or []
                }
                for taxe, t in taux.items():
                    if taxe != "DD" and abs(float(etapes.get(taxe, 0.0)) - float(t["taux"])) > 1e-6:
                        ecarts.append(
                            (destination, origine, code, taxe, etapes.get(taxe), t["taux"])
                        )

    assert compares == set(destinations), sorted(set(destinations) - compares)
    assert {e[0] for e in ecarts} <= {"DZA"}, ecarts
    assert any(e[0] == "DZA" for e in ecarts), (
        "plus aucune préférence algérienne servie par le seul chemin historique : "
        "revoir HISTORIQUE_DZA dans routes_retirees.py"
    )


def test_le_taux_eac_servi_est_celui_du_journal_officiel():
    # Provenance : pour KEN, RWA, TZA et UGA, le taux préférentiel servi doit
    # être celui de l'annexe publiée au journal officiel (barème de catégorie
    # A, lu ici directement), plafonné au NPF.
    import datetime
    import json
    from pathlib import Path

    from services.authentic_tariff_service import calculate_import_taxes

    bareme = json.loads(
        (Path(__file__).parents[1] / "data/zlecaf_ken/bareme_categorie_a.json").read_text(
            encoding="utf-8"
        )
    )
    premiere, derniere = bareme["_premiere_annee"], bareme["_derniere_annee"]
    annee = min(max(datetime.date.today().year, premiere), derniere)
    compares, ecarts = 0, []
    for destination in ["KEN", "RWA", "TZA", "UGA"]:
        for code in _echantillon(destination):
            calcul = calculate_import_taxes(
                destination,
                code,
                10000,
                apply_zlecaf=True,
                origin_country="EGY",
                fob_value=10000,
            )
            if "error" in calcul or not calcul.get("zlecaf_preference_applied"):
                continue
            ligne = bareme["positions"].get(f"{code[:4]}.{code[4:6]}.{code[6:8]}")
            if ligne is None:
                ecarts.append((destination, code, "hors barème"))
                continue
            attendu = min(
                float(ligne["annuites_pct"][annee - premiere]),
                float(calcul["rates"]["dd_rate_pct"]),
            )
            compares += 1
            if abs(calcul["rates"]["effective_zlecaf_rate_pct"] - attendu) > 1e-6:
                ecarts.append(
                    (destination, code, calcul["rates"]["effective_zlecaf_rate_pct"], attendu)
                )

    assert compares and ecarts == []


def test_les_chemins_retires_ne_masquent_aucune_route_vivante(api_router):
    client = _client(routes_retirees_router)
    masquees = [
        (m, chemin)
        for m, chemin in _routes_vivantes(api_router)
        if client.request(m, _chemin_concret(chemin).removeprefix("/api")).status_code == 410
    ]

    assert masquees == []


def _feuilles(objet, cles=()):
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            yield from _feuilles(valeur, cles + (str(cle),))
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _feuilles(valeur, cles)
    else:
        yield cles, objet


def _taux_saisis(corps):
    for cles, valeur in _feuilles(corps):
        if SOUS_ARBRES_AUTORISES.keys() & set(cles):
            continue
        nombre = (isinstance(valeur, (int, float)) and not isinstance(valeur, bool)) or (
            isinstance(valeur, str) and NOMBRE_EN_TEXTE.fullmatch(valeur) is not None
        )
        chemin = tuple("*" if re.fullmatch(r"[A-Z]{3}", c) else c for c in cles)
        if CLES_DE_TAUX_SAISIS & set(cles):
            yield cles, valeur
        elif nombre and (
            any(CLE_DE_TAUX.search(cle) for cle in cles) or chemin not in NOMBRES_AUTORISES
        ):
            yield cles, valeur
        elif isinstance(valeur, str) and POURCENTAGE.search(valeur):
            yield cles, valeur


@pytest.mark.parametrize(
    "chemin",
    [
        "/api/crawlers/cemac/countries",
        "/api/crawlers/cemac/data-summary",
        "/api/crawlers/cemac/data/TCD?page_size=1",
        "/api/regions/sacu/customs-union",
        "/api/regions/north-africa/countries",
        # chapter est encore envoyé : la route n'en tire plus de taux.
        "/api/regions/north-africa/compare?countries=MAR,EGY,TUN&chapter=84",
        "/api/regions/uma/intelligence",
        "/api/crawlers/north-africa/trade-flows",
        "/api/analysis/sadc-vs-cemac",
    ],
)
def test_route_vivante_sans_taux_saisi(api_router, chemin):
    # Routes gardées (métadonnées, données des fichiers crawlés) dont on a
    # retiré les taux écrits dans le code : TVA, bandes de droits, taxes,
    # réductions préférentielles.
    from auth import require_admin, require_auth

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[require_auth] = lambda: {"tier": "test"}
    app.dependency_overrides[require_admin] = lambda: {"tier": "admin"}
    reponse = TestClient(app).get(chemin)

    assert reponse.status_code == 200, reponse.text
    assert list(_taux_saisis(reponse.json())) == []


def test_les_sous_arbres_exemptes_sont_ceux_du_fichier(api_router):
    import json
    from auth import require_admin, require_auth
    from routes.cemac_crawlers import DATA_DIR

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[require_auth] = lambda: {"tier": "test"}
    app.dependency_overrides[require_admin] = lambda: {"tier": "admin"}
    client = TestClient(app)
    for pays in ["CMR", "CAF", "COG", "GAB", "GNQ", "TCD"]:
        fichier = json.loads((DATA_DIR / f"{pays}_tariffs.json").read_text(encoding="utf-8"))
        lignes = fichier["positions"]
        dd = [ln["taxes"]["DD"] for ln in lignes if "DD" in ln.get("taxes", {})]
        servi = client.get(f"/api/crawlers/cemac/data/{pays}?page_size=500").json()
        assert "tariff_lines" in servi, servi
        servi = servi["tariff_lines"]
        assert servi == lignes[:500], pays
        resume = {
            c["iso3"]: c for c in client.get("/api/crawlers/cemac/data-summary").json()["countries"]
        }
        attendu = {"min": min(dd), "max": max(dd), "avg": round(sum(dd) / len(dd), 2)}
        assert resume[pays]["dd_rate_range"] == attendu, pays


@pytest.mark.parametrize("module", MODULES_RETIRES)
def test_source_de_taux_inventes_retiree(module):
    assert importlib.util.find_spec(module) is None
