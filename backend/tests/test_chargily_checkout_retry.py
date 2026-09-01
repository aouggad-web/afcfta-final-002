"""Tests du retry de create_checkout (backend/services/chargily_service.py).

Hermétiques : httpx.post et time.sleep sont mockés, aucun appel réseau réel.
Couvre les 3 catégories d'échec distinguées par le code :
  - pré-envoi (ConnectError/ConnectTimeout) : retenté, backoff, succès possible
  - ambigu après écriture (autre httpx.HTTPError) : jamais retenté
  - réponse reçue (4xx ou 5xx) : jamais retentée (pas d'idempotence Chargily)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services import chargily_service  # noqa: E402


def _checkout_kwargs():
    return dict(
        amount_dzd=1500,
        success_url="https://example.com/ok",
        failure_url="https://example.com/ko",
        description="test",
        metadata={"user_id": "u1"},
    )


def _fake_response(status_code, json_body=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    return resp


@pytest.fixture(autouse=True)
def _secret_key(monkeypatch):
    monkeypatch.setenv("CHARGILY_SECRET_KEY", "sk_test_dummy")


@pytest.fixture(autouse=True)
def _no_real_sleep():
    with patch("services.chargily_service.time.sleep") as sleep_mock:
        yield sleep_mock


def test_success_on_first_attempt(_no_real_sleep):
    ok = _fake_response(200, {"checkout_url": "https://pay.chargily.net/checkouts/abc"})
    with patch("services.chargily_service.httpx.post", return_value=ok) as post_mock:
        url = chargily_service.create_checkout(**_checkout_kwargs())
    assert url == "https://pay.chargily.net/checkouts/abc"
    assert post_mock.call_count == 1
    _no_real_sleep.assert_not_called()


def test_connect_error_retries_then_succeeds(_no_real_sleep):
    ok = _fake_response(200, {"checkout_url": "https://pay.chargily.net/checkouts/xyz"})
    with patch(
        "services.chargily_service.httpx.post",
        side_effect=[httpx.ConnectError("refused"), ok],
    ) as post_mock:
        url = chargily_service.create_checkout(**_checkout_kwargs())
    assert url == "https://pay.chargily.net/checkouts/xyz"
    assert post_mock.call_count == 2
    # Un seul retry -> un seul sleep, avec le backoff de base (attempt 1).
    _no_real_sleep.assert_called_once_with(chargily_service._CHECKOUT_BACKOFF)


def test_connect_timeout_retries_with_exponential_backoff(_no_real_sleep):
    ok = _fake_response(200, {"checkout_url": "https://pay.chargily.net/checkouts/z"})
    with patch(
        "services.chargily_service.httpx.post",
        side_effect=[httpx.ConnectTimeout("timeout"), httpx.ConnectTimeout("timeout"), ok],
    ):
        url = chargily_service.create_checkout(**_checkout_kwargs())
    assert url == "https://pay.chargily.net/checkouts/z"
    delays = [call.args[0] for call in _no_real_sleep.call_args_list]
    assert delays == [
        chargily_service._CHECKOUT_BACKOFF * 1,
        chargily_service._CHECKOUT_BACKOFF * 2,
    ]


def test_connect_error_exhausts_all_attempts_then_502(_no_real_sleep):
    with patch(
        "services.chargily_service.httpx.post",
        side_effect=httpx.ConnectError("refused"),
    ) as post_mock:
        with pytest.raises(HTTPException) as exc:
            chargily_service.create_checkout(**_checkout_kwargs())
    assert exc.value.status_code == 502
    assert post_mock.call_count == chargily_service._CHECKOUT_ATTEMPTS
    assert _no_real_sleep.call_count == chargily_service._CHECKOUT_ATTEMPTS - 1


def test_read_timeout_after_send_is_never_retried(_no_real_sleep):
    # Le corps a pu atteindre Chargily : rejouer risquerait un double checkout.
    with patch(
        "services.chargily_service.httpx.post",
        side_effect=httpx.ReadTimeout("timed out"),
    ) as post_mock:
        with pytest.raises(HTTPException) as exc:
            chargily_service.create_checkout(**_checkout_kwargs())
    assert exc.value.status_code == 502
    assert "incertain" in exc.value.detail
    assert post_mock.call_count == 1
    _no_real_sleep.assert_not_called()


def test_4xx_response_is_never_retried(_no_real_sleep):
    bad = _fake_response(400)
    with patch("services.chargily_service.httpx.post", return_value=bad) as post_mock:
        with pytest.raises(HTTPException) as exc:
            chargily_service.create_checkout(**_checkout_kwargs())
    assert exc.value.status_code == 502
    assert post_mock.call_count == 1
    _no_real_sleep.assert_not_called()


def test_5xx_response_is_never_retried(_no_real_sleep):
    # Chargily n'expose pas de clé d'idempotence : un 5xx ne prouve pas
    # l'absence de checkout créé, donc on ne rejoue pas non plus.
    down = _fake_response(503)
    with patch("services.chargily_service.httpx.post", return_value=down) as post_mock:
        with pytest.raises(HTTPException) as exc:
            chargily_service.create_checkout(**_checkout_kwargs())
    assert exc.value.status_code == 502
    assert post_mock.call_count == 1
    _no_real_sleep.assert_not_called()


def test_missing_checkout_url_is_502(_no_real_sleep):
    ok_but_empty = _fake_response(200, {})
    with patch("services.chargily_service.httpx.post", return_value=ok_but_empty):
        with pytest.raises(HTTPException) as exc:
            chargily_service.create_checkout(**_checkout_kwargs())
    assert exc.value.status_code == 502
    assert "checkout_url" in exc.value.detail
