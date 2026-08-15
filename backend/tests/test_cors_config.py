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


def test_resolve_cors_origin_regex_always_matches_emergent_preview_subdomains():
    import re

    pattern = re.compile(resolve_cors_origin_regex({}))

    assert pattern.fullmatch(
        "https://179aadb8-8837-44c3-9417-5ef9bb7609e0.preview.emergentagent.com"
    )
    assert pattern.fullmatch("https://github-dev-sync.preview.emergentagent.com")
    assert not pattern.fullmatch("https://evil.com/https://x.preview.emergentagent.com")
    assert not pattern.fullmatch("https://notpreview.emergentagent.com.evil.com")


def test_resolve_cors_origin_regex_includes_replit_app_domain_when_set():
    import re

    pattern = re.compile(resolve_cors_origin_regex({"REPLIT_APP_DOMAIN": "myapp.repl.co"}))

    assert pattern.fullmatch("https://myapp.repl.co")
    # Emergent pattern must still be present alongside it.
    assert pattern.fullmatch("https://foo.preview.emergentagent.com")
