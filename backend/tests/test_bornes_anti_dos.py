"""Constat E2 : des listes et des requêtes anonymes sans borne faisaient croître
le calcul (et la réponse) avec la taille de l'entrée, sur la boucle du seul
worker. Doublons retirés et listes bornées à 20 ; requêtes de recherche
bornées à 100 caractères ; Redis injoignable n'est plus retenté à chaque appel.
"""

import pytest
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


class _RedisRefuse:
    """Module redis factice : chaque connexion est comptée, puis refusée."""

    ConnectionError = ConnectionError

    def __init__(self, erreur=ConnectionError):
        self.essais = 0
        self.erreur = erreur

    def from_url(self, *args, **kwargs):
        self.essais += 1
        return self

    def ping(self):
        raise self.erreur("connexion refusée")


def test_cache_service_redis_injoignable_pas_de_nouvel_essai_avant_30_s(monkeypatch):
    import time

    from services import cache_service as cs

    horloge = [1000.0]
    redis_refuse = _RedisRefuse()
    monkeypatch.setattr(time, "monotonic", lambda: horloge[0])
    monkeypatch.setattr(cs, "REDIS_AVAILABLE", True)
    monkeypatch.setattr(cs, "CACHE_ENABLED", True)
    monkeypatch.setattr(cs, "redis", redis_refuse)
    monkeypatch.setattr(cs, "_redis_client", None)
    monkeypatch.setattr(cs, "_dernier_echec", None)
    monkeypatch.setattr(cs, "_DISK_CACHE_ENABLED", False)
    monkeypatch.setattr(cs, "_MEMORY_STORE", {})

    assert cs.cache_get("k") is None
    assert cs.cache_set("k", 1) is True  # repli mémoire
    horloge[0] += 29.9
    assert cs.cache_get("k") == 1
    assert redis_refuse.essais == 1

    # 30 s après l'échec, la connexion est retentée.
    horloge[0] += 0.1
    cs.cache_get("k")
    assert redis_refuse.essais == 2


# Hôte muet (redis.TimeoutError) et REDIS_URL vide (ValueError) n'héritent pas
# de redis.ConnectionError : ils passent par l'autre branche d'échec.
@pytest.mark.parametrize("erreur", [ConnectionError, TimeoutError])
def test_cache_ia_redis_injoignable_pas_de_nouvel_essai_avant_30_s(monkeypatch, erreur):
    import time

    from services import redis_cache_service as rcs

    horloge = [1000.0]
    redis_refuse = _RedisRefuse(erreur)
    monkeypatch.setattr(time, "monotonic", lambda: horloge[0])
    monkeypatch.setattr(rcs, "redis", redis_refuse)
    service = rcs.RedisCacheService("redis://localhost:6379")

    assert service.get("p", {}) is None
    assert service.set("p", {}, {"v": 1}) is False
    horloge[0] += 29.9
    assert service.is_connected is False
    assert redis_refuse.essais == 1

    # 30 s après l'échec, la connexion est retentée.
    horloge[0] += 0.1
    service.get("p", {})
    assert redis_refuse.essais == 2
