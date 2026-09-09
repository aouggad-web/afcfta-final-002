"""
Vérifie que la clé WTO (Ocp-Apim-Subscription-Key) est bien envoyée dans les
requêtes — l'API WTO (Azure APIM) l'exige, sinon 401.

Sans réseau: on mocke requests.get pour capturer les headers.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import services.wto_service as wto


class _FakeResp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"data": []}


def test_retry_helper_forwards_headers(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["headers"] = headers
        return _FakeResp()

    monkeypatch.setattr(wto.requests, "get", fake_get)
    wto.make_wto_request_with_retry(
        "https://api.wto.org/x", headers={"Ocp-Apim-Subscription-Key": "K"}
    )
    assert captured["headers"] == {"Ocp-Apim-Subscription-Key": "K"}


def test_service_sends_auth_header_when_key_set(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["headers"] = headers
        return _FakeResp()

    monkeypatch.setattr(wto.requests, "get", fake_get)
    svc = wto.WTOService()
    svc.api_key = "MYKEY"
    svc.get_trade_indicators("NGA", "ITS_MTV_AX")
    assert captured["headers"]["Ocp-Apim-Subscription-Key"] == "MYKEY"


def test_no_auth_header_when_key_missing(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["headers"] = headers
        return _FakeResp()

    monkeypatch.setattr(wto.requests, "get", fake_get)
    svc = wto.WTOService()
    svc.api_key = ""
    svc.get_trade_indicators("NGA", "ITS_MTV_AX")
    # Pas de clé → pas de header d'auth (None), au lieu d'un header vide trompeur.
    assert captured["headers"] is None
