"""Routes OMC : aucun appel réseau dans la boucle d'événements (audit D2).

Le client OMC est synchrone (30 s de délai, 5 essais, `time.sleep`). Les
routes le font tourner dans un thread, au plus deux à la fois, et valident
les codes reçus avant tout appel.
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes import trade_data  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(trade_data.router, prefix="/api")
    # Un sémaphore neuf par test : il est lié à la boucle qui l'utilise.
    monkeypatch.setattr(trade_data, "_APPELS_OMC", asyncio.Semaphore(2))
    return TestClient(app)


def test_l_appel_omc_tourne_hors_de_la_boucle(client, monkeypatch):
    dans_la_boucle = []

    def faux_client(reporter, partner, product_code):
        try:
            asyncio.get_running_loop()
            dans_la_boucle.append(True)
        except RuntimeError:
            dans_la_boucle.append(False)
        return {"ok": True}

    monkeypatch.setattr(trade_data.wto_service, "get_tariff_data", faux_client)

    assert client.get("/api/trade-data/wto/KEN/TZA").json() == {"ok": True}
    assert dans_la_boucle == [False]


@pytest.mark.parametrize(
    "chemin",
    [
        "/api/trade-data/wto/KENYA/TZA",
        "/api/trade-data/wto/KEN/TZA?product_code=abc",
        "/api/trade-data/latest?reporter=K1N&partner=TZA",
        "/api/trade-data/compare-sources?" + "&".join(["countries=KEN"] * 11),
        "/api/trade-data/compare-sources?countries=KEN&countries=T%26Z",
    ],
)
def test_entrees_invalides_refusees_sans_appel(client, monkeypatch, chemin):
    def interdit(*_args, **_kwargs):
        raise AssertionError("appel OMC")

    monkeypatch.setattr(trade_data.wto_service, "get_tariff_data", interdit)
    monkeypatch.setattr(trade_data.data_source_selector, "get_latest_trade_data", interdit)
    monkeypatch.setattr(trade_data.data_source_selector, "compare_data_sources", interdit)

    assert client.get(chemin).status_code == 422, chemin


def test_au_dela_de_deux_appels_simultanes_refus_immediat(client, monkeypatch):
    bloque = asyncio.Semaphore(0)
    monkeypatch.setattr(trade_data, "_APPELS_OMC", bloque)

    reponse = client.get("/api/trade-data/wto/KEN/TZA")

    assert reponse.status_code == 503
