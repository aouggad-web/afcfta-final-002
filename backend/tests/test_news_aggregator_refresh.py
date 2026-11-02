"""Rafraîchissement des actualités : cache servi tout de suite, collecte en arrière-plan."""

import asyncio
import json
import threading
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

    async def collecte():
        return [{"title": "frais"}]

    monkeypatch.setattr(na, "fetch_all_news", collecte)

    reponse = asyncio.run(na.get_news(force_refresh=True))
    assert reponse["source"] == "fresh"
    assert reponse["articles"] == [{"title": "frais"}]


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
