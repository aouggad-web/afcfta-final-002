import asyncio
import importlib

import pytest
from starlette.responses import Response


def _set_cookie_header(response: Response) -> str:
    return next(value.decode() for name, value in response.raw_headers if name == b"set-cookie")


def _set_cookie_headers(response: Response) -> list[str]:
    return [value.decode() for name, value in response.raw_headers if name == b"set-cookie"]


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
    "https_enabled, expected_deletion_count",
    [
        # HTTPS: two deletions are needed — one for a legacy unpartitioned
        # session cookie (issued before the #400 Partitioned rollout), one
        # for the current partitioned shape. Each lives in a separate cookie
        # jar; deleting only one leaves the other's session active.
        ("true", 2),
        # HTTP (local dev): sessions were never partitioned there, so a
        # single unpartitioned deletion covers every cookie shape that could
        # exist.
        ("false", 1),
    ],
)
def test_logout_deletes_session_cookie_with_matching_attributes(
    monkeypatch, https_enabled, expected_deletion_count
):
    monkeypatch.setenv("HTTPS_ENABLED", https_enabled)
    import routes.user_auth as user_auth_module

    importlib.reload(user_auth_module)
    try:
        response = Response()
        asyncio.run(user_auth_module.logout(response))

        set_cookies = _set_cookie_headers(response)
        assert len(set_cookies) == expected_deletion_count
        assert all("max-age=0" in c.lower() for c in set_cookies)

        partitioned_count = sum("partitioned" in c.lower() for c in set_cookies)
        unpartitioned_count = len(set_cookies) - partitioned_count
        # Always exactly one legacy (unpartitioned) deletion, and — only on
        # HTTPS — exactly one more for the current partitioned shape.
        assert unpartitioned_count == 1
        assert partitioned_count == (1 if expected_deletion_count == 2 else 0)
    finally:
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(user_auth_module)
