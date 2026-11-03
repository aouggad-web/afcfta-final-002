"""Constat E2 : des listes et des requêtes anonymes sans borne faisaient croître
le calcul (et la réponse) avec la taille de l'entrée, sur la boucle du seul
worker. Doublons retirés et listes bornées à 20 ; requêtes de recherche
bornées à 100 caractères ; Redis injoignable n'est plus retenté à chaque appel.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _compter_scores(monkeypatch):
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine

    moteur = get_intelligence_engine()
    original = moteur.calculate_investment_score
    appels = []

    def compte(*args, **kwargs):
        appels.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(moteur, "calculate_investment_score", compte)
    return appels


def test_comparaison_regions_bornee():
    from intelligence.analytics.regional_analytics import get_regional_analytics

    blocs = ["ecowas"] * 1000 + [f"B{i}" for i in range(30)]
    metriques = ["tariff_avg"] * 1000 + [f"m{i}" for i in range(30)]
    resultat = get_regional_analytics().compare_regions(blocs, metriques)
    assert len(resultat["blocs"]) == 20
    assert len(resultat["rankings"]) == 20
    assert all(len(classement) == 20 for classement in resultat["rankings"].values())
    assert resultat["blocs"]["ECOWAS"]["tariff_avg"] != "N/A"


def test_recherche_opportunites_secteurs_dedoublonnes_et_bornes(monkeypatch):
    from intelligence.ai_engine.investment_scoring import COUNTRY_INDICATORS
    from search.enhanced_search import get_search_engine

    appels = _compter_scores(monkeypatch)
    get_search_engine().investment_opportunity_search({"sectors": ["agriculture"] * 999})
    assert len(appels) == len(COUNTRY_INDICATORS)

    appels.clear()
    secteurs = [f"secteur{i}" for i in range(30)]
    get_search_engine().investment_opportunity_search({"sectors": secteurs, "countries": ["mar"]})
    assert len(appels) == 20 and {a[0] for a in appels} == {"MAR"}


def test_radar_pays_dedoublonnes_et_bornes(monkeypatch):
    from dashboard.visualization_engine import get_visualization_engine

    appels = _compter_scores(monkeypatch)
    pays = ["MAR"] * 1000 + [f"X{i:02d}" for i in range(30)]
    donnees = get_visualization_engine().radar_chart_data(pays)
    assert len(appels) == 20
    assert [d["label"] for d in donnees["data"]["datasets"]][:2] == ["MAR", "X00"]


def test_recherche_enrichie_q_bornee_a_100_caracteres():
    from routes.enhanced_search import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    params = {"q": "x" * 100, "type": "country"}
    assert client.get("/enhanced-search/autocomplete", params=params).status_code == 200
    params["q"] += "x"
    assert client.get("/enhanced-search/autocomplete", params=params).status_code == 422
    assert client.get("/enhanced-search/hs-codes", params={"q": "x" * 101}).status_code == 422


def test_redis_injoignable_pas_de_nouvel_essai_avant_le_delai(monkeypatch):
    from performance.caching import cache_layers as cl

    essais = []

    class _ClientRefuse:
        def ping(self):
            raise ConnectionError("connexion refusée")

    class _RedisFactice:
        @staticmethod
        def from_url(*args, **kwargs):
            essais.append(args)
            return _ClientRefuse()

    monkeypatch.setattr(cl, "REDIS_AVAILABLE", True)
    monkeypatch.setattr(cl, "redis", _RedisFactice, raising=False)
    couche = cl.CacheLayer("L1_hot_data", cl.CACHE_LAYERS["L1_hot_data"])

    assert couche.get("k") is None
    assert couche.set("k", 1) is False
    assert couche.get("k") is None
    assert len(essais) == 1

    # Le délai écoulé, la connexion est retentée.
    monkeypatch.setattr(cl, "_DELAI_RECONNEXION_S", 0)
    couche.get("k")
    assert len(essais) == 2
