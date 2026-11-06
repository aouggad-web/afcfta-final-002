"""Rafraîchissement des actualités : cache servi tout de suite, collecte en arrière-plan."""

import asyncio
import json
import threading
import time
from datetime import datetime, timedelta

from etl import news_aggregator as na


def _ecrire_cache(chemin, quand, articles):
    chemin.write_text(
        json.dumps({"last_update": quand.isoformat(), "articles": articles}), encoding="utf-8"
    )


def test_cache_perime_servi_sans_attendre_puis_rafraichi_en_arriere_plan(tmp_path, monkeypatch):
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now() - timedelta(days=2), [{"title": "ancien"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)
    libere = threading.Event()

    async def collecte_lente():
        libere.wait(5)  # une source externe lente ne doit pas bloquer la réponse
        return [{"title": "nouveau"}]

    monkeypatch.setattr(na, "fetch_all_news", collecte_lente)

    reponse = asyncio.run(na.get_news())
    assert reponse["source"] == "cache"
    assert reponse["articles"] == [{"title": "ancien"}]

    fil = na._background_refresh_thread
    assert fil is not None and fil.is_alive()
    # Une seconde requête pendant la collecte ne lance pas un second fil.
    asyncio.run(na.get_news())
    assert na._background_refresh_thread is fil

    libere.set()
    fil.join(5)
    assert json.loads(cache.read_text(encoding="utf-8"))["articles"] == [{"title": "nouveau"}]
    assert not (tmp_path / "news_cache.json.tmp").exists()


def test_actualiser_attend_la_collecte(tmp_path, monkeypatch):
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now(), [{"title": "ancien"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)
    # Fenêtre de fraîcheur désactivée : le cache vient d'être écrit.
    monkeypatch.setattr(na, "_FENETRE_FRAICHEUR_S", 0)

    async def collecte():
        return [{"title": "frais"}]

    monkeypatch.setattr(na, "fetch_all_news", collecte)

    reponse = asyncio.run(na.get_news(force_refresh=True))
    assert reponse["source"] == "fresh"
    assert reponse["articles"] == [{"title": "frais"}]


def _collecte_bloquante(monkeypatch, appels, duree=0.3):
    """Collecte factice qui bloque sa boucle d'événements (appel synchrone)."""

    async def collecte():
        appels.append(1)
        time.sleep(duree)
        return [{"title": f"frais {len(appels)}"}]

    monkeypatch.setattr(na, "fetch_all_news", collecte)


def test_actualiser_ordre_reel_du_bouton_une_seule_collecte(tmp_path, monkeypatch):
    # NewsDashboard.jsx : 3 requêtes force_refresh en parallèle, puis
    # country-of-the-week une fois qu'elles ont répondu.
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now() - timedelta(hours=1), [{"title": "ancien"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)
    appels = []
    _collecte_bloquante(monkeypatch, appels)

    async def clic():
        trois = await asyncio.gather(*(na.get_news(force_refresh=True) for _ in range(3)))
        return trois, await na.get_news(force_refresh=True)

    trois, quatrieme = asyncio.run(clic())
    na._background_refresh_thread.join(5)

    assert len(appels) == 1
    assert [r["source"] for r in trois] == ["fresh"] * 3
    assert all(r["articles"] == [{"title": "frais 1"}] for r in trois)
    # Dans la fenêtre de fraîcheur : le cache tout juste collecté, sans collecte.
    assert quatrieme["articles"] == [{"title": "frais 1"}]


def test_actualiser_ne_bloque_pas_la_boucle(tmp_path, monkeypatch):
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now() - timedelta(hours=1), [{"title": "ancien"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)
    appels = []
    _collecte_bloquante(monkeypatch, appels)

    async def battement(arret, retards):
        while not arret.is_set():
            debut = time.perf_counter()
            await asyncio.sleep(0.01)
            retards.append(time.perf_counter() - debut - 0.01)

    async def scenario():
        arret, retards = asyncio.Event(), []
        pouls = asyncio.create_task(battement(arret, retards))
        await asyncio.sleep(0.02)
        reponses = await asyncio.gather(*(na.get_news(force_refresh=True) for _ in range(3)))
        arret.set()
        await pouls
        return reponses, max(retards)

    reponses, pire_retard = asyncio.run(scenario())
    na._background_refresh_thread.join(5)

    assert [r["source"] for r in reponses] == ["fresh"] * 3
    # La collecte bloque 0,3 s, mais dans son propre fil : la boucle reste libre.
    assert pire_retard < 0.15


def test_actualiser_rend_le_cache_si_la_collecte_depasse_l_attente(tmp_path, monkeypatch):
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now() - timedelta(hours=1), [{"title": "ancien"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)
    monkeypatch.setattr(na, "_ATTENTE_ACTUALISER_MAX_S", 0.5)
    libere = threading.Event()

    async def collecte_interminable():
        libere.wait(5)
        return [{"title": "trop tard"}]

    monkeypatch.setattr(na, "fetch_all_news", collecte_interminable)

    try:
        debut = time.perf_counter()
        reponse = asyncio.run(na.get_news(force_refresh=True))
        assert time.perf_counter() - debut < 3
        assert reponse["source"] == "cache"
        assert reponse["articles"] == [{"title": "ancien"}]
    finally:
        # Libérer la collecte avant que monkeypatch ne rende NEWS_CACHE_FILE :
        # sinon, sur un échec, elle écrirait dans le vrai cache.
        libere.set()
        na._background_refresh_thread.join(5)


def test_cache_a_jour_ne_declenche_aucune_collecte(tmp_path, monkeypatch):
    cache = tmp_path / "news_cache.json"
    _ecrire_cache(cache, datetime.now(), [{"title": "du jour"}])
    monkeypatch.setattr(na, "NEWS_CACHE_FILE", str(cache))
    monkeypatch.setattr(na, "_background_refresh_thread", None)

    async def interdite():
        raise AssertionError("aucune collecte attendue pour un cache du jour")

    monkeypatch.setattr(na, "fetch_all_news", interdite)

    reponse = asyncio.run(na.get_news())
    assert reponse["articles"] == [{"title": "du jour"}]
    assert na._background_refresh_thread is None
