import pytest
from cors_config import DEFAULT_ORIGINS, resolve_cors_origins


def test_resolve_cors_origins_uses_defaults_when_env_unset():
    assert resolve_cors_origins({}) == DEFAULT_ORIGINS


def test_la_production_n_ajoute_aucune_origine_par_defaut():
    """Sans ALLOWED_ORIGINS, la production ne reprend ni localhost ni aucun
    autre domaine : l'application est servie depuis sa propre origine."""
    assert resolve_cors_origins({"APP_ENV": "production"}) == []


def test_la_production_garde_l_url_de_preversion_du_pod():
    env = {
        "APP_ENV": "production",
        "PREVIEW_ENDPOINT": "https://git-sync-41.preview.emergentagent.com",
    }

    assert resolve_cors_origins(env) == ["https://git-sync-41.preview.emergentagent.com"]


@pytest.mark.parametrize("env", [{}, {"APP_ENV": "production"}])
def test_aucun_domaine_tiers_dans_les_origines_par_defaut(env):
    """afcfta.trade ne sert pas l'application : une page publiée sur ce
    domaine lisait les réponses de l'API avec la session du visiteur."""
    origines = resolve_cors_origins(env)

    assert "https://afcfta.trade" not in origines
    assert "https://www.afcfta.trade" not in origines
    assert all(o.startswith("http://localhost:") for o in origines)


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


def test_les_variables_replit_n_ajoutent_plus_d_origine():
    """Replit est abandonné : ses variables n'ouvrent plus rien."""
    env = {
        "APP_ENV": "production",
        "REPLIT_DEV_DOMAIN": "my-repl.replit.dev",
        "REPLIT_APP_DOMAIN": "myapp.repl.co",
    }

    assert resolve_cors_origins(env) == []


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
