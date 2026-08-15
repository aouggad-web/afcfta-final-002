import asyncio
import importlib

import pytest
from starlette.responses import Response


def _set_cookie_header(response: Response) -> str:
    return next(value.decode() for name, value in response.raw_headers if name == b"set-cookie")


@pytest.mark.parametrize(
    "https_enabled, expected_samesite, expects_secure, expects_partitioned",
    [
        # HTTPS deployments (incl. the Emergent preview iframe, a cross-site
        # top-level document): SameSite=None so the cookie still comes back
        # on our own authenticated requests, which requires Secure. Chrome's
        # CHIPS also requires Partitioned for that cross-site case, or the
        # cookie is dropped despite SameSite=None; Secure being set.
        ("true", "samesite=none", True, True),
        # Plain HTTP (local dev): SameSite=None without Secure would be
        # rejected by browsers, so fall back to Lax (still same-origin-safe).
        ("false", "samesite=lax", False, False),
    ],
)
def test_session_cookie_samesite_matches_https_flag(
    monkeypatch, https_enabled, expected_samesite, expects_secure, expects_partitioned
):
    monkeypatch.setenv("HTTPS_ENABLED", https_enabled)
    import routes.user_auth as user_auth_module

    importlib.reload(user_auth_module)
    try:
        response = Response()
        user_auth_module._set_session_cookie(response, "dummy-token")

        set_cookie = _set_cookie_header(response)
        assert expected_samesite in set_cookie.lower()
        assert ("secure" in set_cookie.lower()) == expects_secure
        assert ("partitioned" in set_cookie.lower()) == expects_partitioned
        assert "httponly" in set_cookie.lower()
    finally:
        # Restore the module to its default (HTTPS_ENABLED unset) state so a
        # leftover reload doesn't leak into tests running after this one —
        # monkeypatch undoes the env var, but not an already-reloaded module.
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(user_auth_module)


@pytest.mark.parametrize(
    "https_enabled, expects_partitioned",
    [("true", True), ("false", False)],
)
def test_logout_deletes_session_cookie_with_matching_attributes(
    monkeypatch, https_enabled, expects_partitioned
):
    monkeypatch.setenv("HTTPS_ENABLED", https_enabled)
    import routes.user_auth as user_auth_module

    importlib.reload(user_auth_module)
    try:
        response = Response()
        asyncio.run(user_auth_module.logout(response))

        set_cookie = _set_cookie_header(response)
        # A mismatched deletion (missing SameSite/Secure/Partitioned) would
        # silently miss a CHIPS-partitioned cookie, since it lives in a
        # separate jar from the unpartitioned one.
        assert ("partitioned" in set_cookie.lower()) == expects_partitioned
    finally:
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(user_auth_module)
