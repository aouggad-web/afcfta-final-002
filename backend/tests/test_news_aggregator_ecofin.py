"""Ecofin dans le fil : dépêches récentes d'abord, source prioritaire (08/11/2026)."""

import asyncio

from etl import news_aggregator as na

# Recherche Google News « site: » : rangée par pertinence, pas par date.
FLUX = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Vieille depeche 2016</title><link>https://a/1</link><pubDate>Tue, 19 Jul 2016 10:57:08 GMT</pubDate></item>
<item><title>Depeche du 3 novembre</title><link>https://a/2</link><pubDate>Tue, 03 Nov 2026 07:33:00 GMT</pubDate></item>
<item><title>Depeche du 7 novembre</title><link>https://a/3</link><pubDate>Sat, 07 Nov 2026 11:20:00 GMT</pubDate></item>
</channel></rss>"""


class _Reponse:
    status = 200

    async def text(self):
        return FLUX

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    def get(self, *args, **kwargs):
        return _Reponse()


def test_les_entrees_les_plus_recentes_sont_gardees():
    articles = asyncio.run(
        na.fetch_feed(_Session(), "https://x", "Agence Ecofin", "economie", max_entries=2)
    )
    assert [a["title"] for a in articles] == ["Depeche du 7 novembre", "Depeche du 3 novembre"]


def test_ecofin_limite_aux_sept_derniers_jours_et_prioritaire():
    ecofin = na.RSS_FEEDS["agence_ecofin"]
    assert all("when:7d" in url for url in ecofin["feeds"].values())
    assert ecofin["priority"] is True
    assert ecofin["max_entries"] >= 10
