from cors_config import (
    DEFAULT_ORIGINS,
    resolve_cors_origin_regex,
    resolve_cors_origins,
)


def test_resolve_cors_origins_uses_defaults_when_env_unset():
    assert resolve_cors_origins({}) == DEFAULT_ORIGINS


def test_resolve_cors_origins_parses_allowed_origins_csv():
    env = {"ALLOWED_ORIGINS": "https://a.example.com, https://b.example.com"}

    assert resolve_cors_origins(env) == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_resolve_cors_origins_appends_frontend_url_once():
    env = {
        "ALLOWED_ORIGINS": "https://a.example.com",
        "FRONTEND_URL": "https://front.example.com",
    }

    origins = resolve_cors_origins(env)

    assert origins == ["https://a.example.com", "https://front.example.com"]

    # Already present: must not be duplicated.
    env["ALLOWED_ORIGINS"] = "https://a.example.com,https://front.example.com"
    assert resolve_cors_origins(env) == [
        "https://a.example.com",
        "https://front.example.com",
    ]


def test_resolve_cors_origins_appends_replit_dev_domain():
    env = {"REPLIT_DEV_DOMAIN": "my-repl.replit.dev"}

    origins = resolve_cors_origins(env)

    assert "https://my-repl.replit.dev" in origins


def test_resolve_cors_origins_appends_emergent_preview_endpoint_uppercase():
    env = {
        "ALLOWED_ORIGINS": "https://a.example.com",
        "PREVIEW_ENDPOINT": "https://179aadb8-8837.preview.emergentagent.com",
    }

    origins = resolve_cors_origins(env)

    assert origins == [
        "https://a.example.com",
        "https://179aadb8-8837.preview.emergentagent.com",
    ]


def test_resolve_cors_origins_appends_emergent_preview_endpoint_lowercase():
    # Observed in the wild as lowercase on at least one pod — support both.
    env = {"preview_endpoint": "https://github-dev-sync.preview.emergentagent.com"}

    origins = resolve_cors_origins(env)

    assert "https://github-dev-sync.preview.emergentagent.com" in origins


def test_resolve_cors_origins_does_not_trust_other_emergent_tenants():
    """The allowlist must never accept an arbitrary *.preview.emergentagent.com
    origin just because it matches the platform's domain family — only this
    pod's own resolved preview_endpoint. Anything else is a different,
    unrelated tenant's deployment."""
    env = {"PREVIEW_ENDPOINT": "https://my-own-pod.preview.emergentagent.com"}

    origins = resolve_cors_origins(env)

    assert "https://some-other-tenant.preview.emergentagent.com" not in origins


def test_resolve_cors_origin_regex_is_none_without_replit_app_domain():
    assert resolve_cors_origin_regex({}) is None


def test_resolve_cors_origin_regex_matches_replit_app_domain_when_set():
    import re

    pattern = re.compile(resolve_cors_origin_regex({"REPLIT_APP_DOMAIN": "myapp.repl.co"}))

    assert pattern.fullmatch("https://myapp.repl.co")
    assert not pattern.fullmatch("https://evil.com/https://myapp.repl.co")
