"""Liens Google News décodés par googlenewsdecoder 0.2.2 (décodeur simulé, sans réseau)."""

import asyncio
import time

from etl import news_aggregator as na

LIEN = "https://news.google.com/rss/articles/CBMiAbc?oc=5"
SOURCE = "https://www.agenceecofin.com/finance/0611-1-article"
ECHEC = {"success": False, "message": "Request error fetching params: timed out"}


def _decodeur(monkeypatch, *reponses):
    """Remplace le décodeur : l'appel n rend reponses[n] (la dernière ensuite), ou la lève."""
    appels = []

    async def faux(url, **options):
        appels.append(options)
        reponse = reponses[min(len(appels), len(reponses)) - 1]
        if isinstance(reponse, Exception):
            raise reponse
        return reponse

    monkeypatch.setattr(na, "GNEWS_DECODER_AVAILABLE", True)
    monkeypatch.setattr(na, "_gnews_decode", faux)
    return appels


def test_lien_decode_avec_le_resultat_de_la_0_2_2(monkeypatch):
    # 0.2.2 rend {"success": True, "decoded_url": ...} (0.1.7 rendait "status").
    appels = _decodeur(monkeypatch, {"success": True, "decoded_url": SOURCE})
    assert asyncio.run(na._resolve_google_news_url(LIEN)) == SOURCE
    assert appels[0]["timeout"] == 10


def test_echec_du_decodeur_rend_le_lien_google(monkeypatch):
    _decodeur(monkeypatch, ECHEC, TimeoutError("timed out"))
    assert asyncio.run(na._resolve_google_news_url(LIEN)) == LIEN
    assert asyncio.run(na._resolve_google_news_url(LIEN)) == LIEN


def test_reponse_au_compte_gouttes_coupee_au_delai_du_lien(monkeypatch):
    # Le délai de 10 s vaut par opération réseau : une réponse qui arrive octet par
    # octet n'y est jamais soumise. Le délai total du lien la coupe.
    async def goutte(url, **options):
        await asyncio.sleep(3600)

    monkeypatch.setattr(na, "GNEWS_DECODER_AVAILABLE", True)
    monkeypatch.setattr(na, "_gnews_decode", goutte)
    monkeypatch.setattr(na, "_DECODAGE_MAX_S", 0.1)
    debut = time.monotonic()
    assert asyncio.run(na._resolve_google_news_url(LIEN)) == LIEN
    assert time.monotonic() - debut < 5


def test_collecte_decode_les_liens_et_abandonne_apres_trois_echecs(monkeypatch):
    liens = [f"{LIEN}&n={i}" for i in range(8)]

    async def flux(session, url, source_name, *_):
        return [
            {"title": f"Article {i}", "link": lien, "source": source_name, "published_at": "x"}
            for i, lien in enumerate(liens)
        ]

    monkeypatch.setattr(na, "RSS_FEEDS", {"g": {"name": "G", "feeds": {"eco": "u"}}})
    monkeypatch.setattr(na, "fetch_feed", flux)
    succes = {"success": True, "decoded_url": SOURCE}
    appels = _decodeur(monkeypatch, ECHEC, ECHEC, succes, ECHEC, ECHEC, ECHEC)

    articles = asyncio.run(na.fetch_all_news())

    # Un succès remet le compte à zéro ; après trois échecs de suite, plus d'appel.
    assert [a["link"] for a in articles if a["source"] == "G"] == liens[:2] + [SOURCE] + liens[3:]
    assert len(appels) == 6
