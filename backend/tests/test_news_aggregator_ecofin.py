"""Fil d'actualités au plus près de l'activité (08/11/2026) : dépêches du jour
et de la veille, Ecofin lu en direct puis par Google en secours, médias
généralistes réduits à leurs articles économiques."""

import asyncio
from datetime import datetime, timezone

import pytest

from etl import news_aggregator as na

MAINTENANT = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)

# Recherche Google News « site: » : rangée par pertinence, pas par date.
FLUX = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Vieille dépêche sur la banque</title><link>https://a/1</link><pubDate>Tue, 19 Jul 2016 10:57:08 GMT</pubDate></item>
<item><title>Dépêche d'avant-hier sur la banque</title><link>https://a/2</link><pubDate>Fri, 06 Nov 2026 22:00:00 GMT</pubDate></item>
<item><title>Dépêche de la veille sur la banque</title><link>https://a/3</link><pubDate>Sat, 07 Nov 2026 00:30:00 GMT</pubDate></item>
<item><title>Dépêche du jour sur la banque</title><link>https://a/4</link><pubDate>Sun, 08 Nov 2026 09:00:00 GMT</pubDate></item>
<item><title>Match de football du jour</title><link>https://a/5</link><pubDate>Sun, 08 Nov 2026 10:00:00 GMT</pubDate></item>
<item><title>Dépêche sans date sur la banque</title><link>https://a/6</link></item>
</channel></rss>"""

VIDE = """<?xml version="1.0"?><rss version="2.0"><channel><title>vide</title></channel></rss>"""


class _Reponse:
    status = 200

    def __init__(self, corps):
        self._corps = corps

    async def text(self):
        return self._corps

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    """Sert FLUX, ou VIDE pour les adresses de `vides` ; note les adresses lues."""

    def __init__(self, vides=()):
        self.vides = set(vides)
        self.lues = []

    def get(self, url, *args, **kwargs):
        self.lues.append(url)
        return _Reponse(VIDE if url in self.vides else FLUX)


DEBUT_REEL = na.debut_fenetre


@pytest.fixture(autouse=True)
def _horloge(monkeypatch):
    # Horloge figée au 08/11/2026 15:00 UTC : le test ne dépend pas du jour où il tourne.
    monkeypatch.setattr(na, "debut_fenetre", lambda maintenant=None: DEBUT_REEL(MAINTENANT))


def _titres(articles):
    return [a["title"] for a in articles]


def test_fenetre_du_jour_et_de_la_veille():
    assert DEBUT_REEL(MAINTENANT) == datetime(2026, 11, 7, tzinfo=timezone.utc)


def test_seules_les_depeches_du_jour_et_de_la_veille_entrent_les_plus_recentes_d_abord():
    articles = asyncio.run(na.fetch_feed(_Session(), "https://x", "Source", "finance"))
    assert _titres(articles) == [
        "Match de football du jour",
        "Dépêche du jour sur la banque",
        "Dépêche de la veille sur la banque",
    ]


def test_un_media_generaliste_ne_garde_que_l_economie():
    articles = asyncio.run(
        na.fetch_feed(_Session(), "https://x", "BBC Africa", "business", economie_seule=True)
    )
    assert "Match de football du jour" not in _titres(articles)
    assert "Dépêche du jour sur la banque" in _titres(articles)


def test_recherche_google_limitee_a_deux_jours():
    url = "https://news.google.com/rss/search?q=site:theafricareport.com&hl=fr"
    assert na.recherche_recente(url) == "https://news.google.com/rss/search?q=site:theafricareport.com+when:2d&hl=fr"
    deja = "https://news.google.com/rss/search?q=site:agenceecofin.com+when:2d&hl=fr"
    assert na.recherche_recente(deja) == deja
    assert na.recherche_recente("https://www.financialafrik.com/feed/") == "https://www.financialafrik.com/feed/"


def test_ecofin_lu_en_direct_puis_google_en_secours():
    ecofin = na.RSS_FEEDS["agence_ecofin"]
    direct = ecofin["feeds"]["economie"]
    assert "agenceecofin.com/rss" in direct
    assert all("when:2d" in u for u in ecofin["feeds_secours"].values())
    assert ecofin["priority"] is True

    # Flux direct vide → Google en secours.
    session = _Session(vides={direct})
    articles = asyncio.run(na._collecter_source(session, ecofin))
    assert articles and len(session.lues) == 2

    # Flux direct frais → Google n'est pas appelé.
    session = _Session()
    asyncio.run(na._collecter_source(session, ecofin))
    assert session.lues == [direct]


def test_sources_retirees_par_l_exploitant():
    for cle in ("jeune_afrique_eco", "rfi_afrique", "le_monde_afrique"):
        assert cle not in na.RSS_FEEDS


def test_presse_internationale_ne_garde_que_l_afrique():
    flux = FLUX.replace("Dépêche du jour sur la banque", "Banque centrale du Nigeria : hausse des taux")
    session = _Session()
    session.get = lambda url, *a, **k: _Reponse(flux)
    articles = asyncio.run(
        na.fetch_feed(session, "https://x", "The New York Times", "business", economie_seule=True, afrique_seule=True)
    )
    assert _titres(articles) == ["Banque centrale du Nigeria : hausse des taux"]
    assert na.est_africain("Africa's trade zone grows") and not na.est_africain("Fed raises rates")
    for cle in ("nytimes", "wsj", "les_echos"):
        assert na.RSS_FEEDS[cle]["afrique_seule"] is True



# ── Audit D10 (17/11/2026) : seuls les liens http(s) d'un flux sont gardés ──

FLUX_LIENS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Dépêche javascript sur la banque</title><link>javascript:alert(1)</link><pubDate>Sun, 08 Nov 2026 09:00:00 GMT</pubDate></item>
<item><title>Dépêche data sur la banque</title><link>data:text/html,x</link><pubDate>Sun, 08 Nov 2026 09:10:00 GMT</pubDate></item>
<item><title>Dépêche sans lien sur la banque</title><pubDate>Sun, 08 Nov 2026 09:20:00 GMT</pubDate></item>
<item><title>Dépêche web sur la banque</title><link> https://exemple.invalid/a </link><pubDate>Sun, 08 Nov 2026 09:30:00 GMT</pubDate></item>
</channel></rss>"""


def test_un_lien_de_flux_qui_n_est_pas_http_est_ecarte():
    session = _Session()
    session.get = lambda url, *a, **k: _Reponse(FLUX_LIENS)

    articles = asyncio.run(na.fetch_feed(session, "https://x", "Source", "finance"))

    assert [(a["title"], a["link"]) for a in articles] == [
        ("Dépêche web sur la banque", "https://exemple.invalid/a")
    ]
