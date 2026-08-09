"""
SaaS layer tests — new user account system (register/login/logout/me) and
contact form. Session = JWT in httpOnly cookie `access_token`. Mutating
requests require an `X-CSRF-Token` header matching the `csrf_token` cookie
(obtained via GET /api/health first).
"""

import os
import re
import uuid

import pytest
import requests


def _read_public_backend_url() -> str:
    """Read the real public HTTPS URL straight from frontend/.env.

    conftest.py rewrites os.environ["REACT_APP_BACKEND_URL"] to
    http://localhost:8001 for reachability reasons (shared with hundreds of
    other test modules). That is fine for plain data-endpoint tests, but the
    SaaS session cookie `access_token` is issued with `Secure=True`, so a
    plain-HTTP client (this includes `requests`, which enforces the Secure
    cookie flag via http.cookiejar) will receive but never RE-SEND that
    cookie over http://localhost — causing false 401s that do not reproduce
    in a real browser (always HTTPS). We must hit the real HTTPS origin.
    """
    env_path = "/app/frontend/.env"
    try:
        with open(env_path, encoding="utf-8") as fh:
            match = re.search(r"^REACT_APP_BACKEND_URL=(.+)$", fh.read(), re.MULTILINE)
            if match:
                return match.group(1).strip().rstrip("/")
    except OSError:
        pass
    return os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


BASE_URL = _read_public_backend_url()

ADMIN_EMAIL = "admin@afcfta-zlecaf.com"
ADMIN_PASSWORD = "ZlecafAdmin2026!"


def _unique_email():
    return f"TEST_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def session():
    """A requests session with a valid CSRF token already primed."""
    s = requests.Session()
    resp = s.get(f"{BASE_URL}/api/health", timeout=15)
    assert resp.status_code == 200
    token = resp.headers.get("X-CSRF-Token") or s.cookies.get("csrf_token")
    assert token, "CSRF token was not issued by /api/health"
    s.headers.update({"X-CSRF-Token": token})
    return s


class TestRegister:
    def test_register_new_user_success(self, session):
        email = _unique_email()
        payload = {"name": "TEST User", "email": email, "password": "SecurePass123"}
        resp = session.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["email"] == email.lower()
        assert data["name"] == "TEST User"
        assert data["role"] == "user"
        assert "id" in data and isinstance(data["id"], str)
        # session cookie must be set
        assert "access_token" in session.cookies

        # GET /api/auth/me must reflect the same user (persistence + session)
        me = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert me.status_code == 200
        assert me.json()["email"] == email.lower()

    def test_register_duplicate_email_returns_409(self, session):
        email = _unique_email()
        payload = {"name": "TEST Dup", "email": email, "password": "SecurePass123"}
        first = session.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
        assert first.status_code == 200

        # New session (fresh CSRF) to attempt duplicate registration
        s2 = requests.Session()
        r2 = s2.get(f"{BASE_URL}/api/health", timeout=15)
        token2 = r2.headers.get("X-CSRF-Token") or s2.cookies.get("csrf_token")
        s2.headers.update({"X-CSRF-Token": token2})
        dup = s2.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
        assert dup.status_code == 409
        assert "existe" in dup.json()["detail"].lower()
        # duplicate attempt must NOT log the attacker's session in
        assert "access_token" not in s2.cookies

    def test_register_short_password_returns_422(self, session):
        email = _unique_email()
        payload = {"name": "TEST Short", "email": email, "password": "short1"}
        resp = session.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
        assert resp.status_code == 422


class TestLoginLogout:
    def _register(self, session):
        email = _unique_email()
        password = "SecurePass123"
        payload = {"name": "TEST LoginUser", "email": email, "password": password}
        resp = session.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
        assert resp.status_code == 200
        return email, password

    def test_login_success_and_me_persistence(self, session):
        email, password = self._register(session)
        # log out first, then log back in with a fresh session
        session.post(f"{BASE_URL}/api/auth/logout", json={}, timeout=15)

        login_resp = session.post(
            f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15
        )
        assert login_resp.status_code == 200
        assert login_resp.json()["email"] == email.lower()
        assert "access_token" in session.cookies

        me = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert me.status_code == 200
        assert me.json()["email"] == email.lower()

    def test_login_wrong_password_returns_401(self, session):
        email, _password = self._register(session)
        resp = session.post(
            f"{BASE_URL}/api/auth/login", json={"email": email, "password": "WrongPassword999"}, timeout=15
        )
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_logout_clears_session(self, session):
        email, password = self._register(session)
        logout_resp = session.post(f"{BASE_URL}/api/auth/logout", json={}, timeout=15)
        assert logout_resp.status_code == 200

        me = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert me.status_code == 401

    def test_admin_login_works(self, session):
        resp = session.post(
            f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"
        assert data["email"] == ADMIN_EMAIL


class TestBruteForceLockout:
    def test_five_failed_attempts_then_lockout_even_with_correct_password(self, session):
        email = _unique_email()
        password = "SecurePass123"
        reg = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"name": "TEST Lockout", "email": email, "password": password},
            timeout=15,
        )
        assert reg.status_code == 200
        session.post(f"{BASE_URL}/api/auth/logout", json={}, timeout=15)

        # 5 failed attempts
        for i in range(5):
            resp = session.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": "WrongPassword!"},
                timeout=15,
            )
            assert resp.status_code == 401, f"attempt {i + 1} expected 401, got {resp.status_code}"

        # 6th attempt — even with the CORRECT password — must be locked out (429)
        locked_resp = session.post(
            f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15
        )
        assert locked_resp.status_code == 429, locked_resp.text
        detail = locked_resp.json().get("detail", "")
        assert "15" in detail and ("minute" in detail.lower())


class TestContactForm:
    def test_submit_contact_success(self, session):
        payload = {
            "name": "TEST Contact Sender",
            "email": _unique_email(),
            "message": "This is an automated backend test message.",
        }
        resp = session.post(f"{BASE_URL}/api/contact", json=payload, timeout=20)
        assert resp.status_code == 200, resp.text
        assert "succ" in resp.json()["message"].lower()

    def test_submit_contact_missing_field_returns_422(self, session):
        payload = {"name": "TEST Incomplete", "message": "no email field"}
        resp = session.post(f"{BASE_URL}/api/contact", json=payload, timeout=15)
        assert resp.status_code == 422


class TestCSRFEnforcement:
    def test_post_without_csrf_token_is_rejected(self):
        s = requests.Session()
        s.get(f"{BASE_URL}/api/health", timeout=15)  # primes the csrf cookie, but we don't send header
        resp = s.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nobody@example.com", "password": "irrelevant"},
            timeout=15,
        )
        assert resp.status_code == 403
