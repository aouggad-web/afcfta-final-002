"""Masquage des secrets passés en URL dans les journaux (constat C2 de l'audit)."""

import io
import logging
import logging.config

import httpx
import pytest
from log_redaction import RedactingFormatter, build_logging_config, redact

SENTINEL = "SENTINELLE-NON-SECRETE-123"


_LOGGERS_CONFIGURES = (
    "httpx",
    "httpx2",
    "httpcore",
    "pymongo",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


@pytest.fixture
def logging_isole():
    """Restaure la configuration de logging modifiée par un test."""
    root = logging.getLogger()
    etat = (root.handlers[:], root.level)
    etats = {}
    for nom in _LOGGERS_CONFIGURES:
        lg = logging.getLogger(nom)
        etats[nom] = (lg.handlers[:], lg.level, lg.propagate, lg.disabled)
    yield
    root.handlers[:], root.level = etat[0], etat[1]
    for nom, (handlers, niveau, propagate, disabled) in etats.items():
        lg = logging.getLogger(nom)
        lg.handlers[:] = handlers
        lg.setLevel(niveau)
        lg.propagate = propagate
        lg.disabled = disabled


def test_masque_le_jeton_oec_dans_une_url():
    url = f"https://api-v2.oec.world/tesseract/data.jsonrecords?cube=trade&token={SENTINEL}"
    out = redact(f"GET {url}")
    assert SENTINEL not in out
    assert "token=***" in out
    assert "cube=trade" in out


def test_masque_chaque_parametre_secret_et_garde_les_autres():
    texte = (
        f"https://comtradeapi.un.org/data?reporterCode=12&subscription-key={SENTINEL}"
        f"&period=2024 https://x.test/a?api_key={SENTINEL}&key={SENTINEL}#access_token={SENTINEL}"
    )
    out = redact(texte)
    assert SENTINEL not in out
    assert "reporterCode=12" in out and "period=2024" in out


def test_ne_touche_pas_au_texte_ordinaire():
    texte = "cache key=product_0901_fr_2024 token valide ; aucune URL ici"
    assert redact(texte) == texte


def test_formateur_masque_la_traceback():
    record = None
    try:
        raise RuntimeError(f"Client error for url 'https://api.test/x?token={SENTINEL}'")
    except RuntimeError:
        import sys

        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1, "OEC API error", None, sys.exc_info()
        )
    sortie = RedactingFormatter("%(message)s").format(record)
    assert "RuntimeError" in sortie  # la traceback est bien présente…
    assert SENTINEL not in sortie  # …mais sans le secret


def test_configuration_serveur_masque_httpx_et_les_erreurs(logging_isole):
    logging.config.dictConfig(build_logging_config("INFO"))
    flux = io.StringIO()
    logging.getLogger().handlers[0].setStream(flux)

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={}))
    with httpx.Client(transport=transport) as client:
        client.get(
            "https://api-v2.oec.world/tesseract/data.jsonrecords", params={"token": SENTINEL}
        )
    logging.getLogger("services.real_trade_data_service").error(
        f"OEC API error: Client error '403' for url 'https://api.test/x?token={SENTINEL}'"
    )

    sortie = flux.getvalue()
    assert "HTTP Request" not in sortie  # httpx relevé à WARNING
    assert "OEC API error" in sortie  # les erreurs applicatives restent journalisées
    assert SENTINEL not in sortie


# --- Point 17 de l'audit : journal sans secret ni donnée personnelle ---------


def _sortie(niveau="INFO"):
    """Configuration du serveur, sortie redirigée vers un tampon."""
    logging.config.dictConfig(build_logging_config(niveau))
    flux = io.StringIO()
    logging.getLogger().handlers[0].setStream(flux)
    return flux


def test_masque_les_nouveaux_secrets_et_garde_les_parametres_ordinaires():
    texte = (
        f"/?token_hash={SENTINEL}&type=recovery /cb?code={SENTINEL}&state=1 "
        f"/x?password={SENTINEL}&client_secret={SENTINEL}&signature={SENTINEL} "
        f"/y?license_key={SENTINEL}&secret={SENTINEL}&cube=trade&hs_code=0901 "
        f"Authorization: Bearer {SENTINEL}-abcdefgh "
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJl"
    )
    out = redact(texte)
    assert SENTINEL not in out
    assert "eyJzdWIi" not in out
    for garde in ("type=recovery", "state=1", "cube=trade", "hs_code=0901"):
        assert garde in out


def test_reduit_les_adresses_e_mail_a_leur_domaine():
    out = redact("Email sent to prenom.nom+promo@exemple.dz (message from a@b.co)")
    assert out == "Email sent to ***@exemple.dz (message from ***@b.co)"


@pytest.mark.parametrize("niveau", ["info", " Info ", "", None, "xyz"])
def test_log_level_mal_ecrit_ne_bloque_plus_le_demarrage(logging_isole, niveau):
    """dictConfig refusait « info » (docs/emergent.env.template) : backend arrêté."""
    logging.config.dictConfig(build_logging_config(niveau))
    assert logging.getLogger().level == logging.INFO


def test_uvicorn_passe_par_le_masquage_et_n_ecrit_plus_sa_ligne_d_acces(logging_isole):
    import uvicorn

    # Uvicorn pose sa propre configuration (Config) avant d'importer l'appli.
    uvicorn.Config("server:app")
    flux = _sortie()

    assert not logging.getLogger("uvicorn.access").hasHandlers()
    logging.getLogger("uvicorn.error").error(f"Exception in ASGI application /x?token={SENTINEL}")
    sortie = flux.getvalue()
    assert "Exception in ASGI application" in sortie
    assert SENTINEL not in sortie


def test_ligne_utc_a_la_milliseconde_avec_rid(logging_isole):
    flux = _sortie()
    logging.getLogger("test.ligne").warning("bonjour")

    import re

    assert re.match(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z \[WARNING\] test\.ligne rid=-: bonjour$",
        flux.getvalue().strip(),
    )


def test_un_message_ne_peut_pas_fabriquer_une_fausse_ligne(logging_isole):
    flux = _sortie()
    logging.getLogger("middlewares.csrf_protection").warning(
        "CSRF: missing token for POST %s", "/a\n2026-01-01T00:00:00.000Z [INFO] faux: ok"
    )
    assert len(flux.getvalue().strip().splitlines()) == 1


def test_httpx2_ne_journalise_plus_chaque_requete(logging_isole):
    flux = _sortie()
    logging.getLogger("httpx2").info(f"HTTP Request: GET https://x.test/?token={SENTINEL}")
    assert flux.getvalue() == ""


def test_masque_cles_brutes_identifiants_d_url_et_basic():
    texte = (
        f"stripe sk_live_{SENTINEL[:8]}abcd whsec_{SENTINEL[:8]} sb_secret_{SENTINEL} "
        f"ghp_{'A' * 36} redis://:{SENTINEL}@redis:6379/0 https://moi:{SENTINEL}@h.test/x "
        "Authorization: Basic dXNlcjpwYXNzd29yZDEyMzQ1Ng=="
    )
    out = redact(texte)
    assert SENTINEL not in out and "SENTINEL" not in out
    assert "ghp_AAAA" not in out and "dXNlcjpw" not in out
    assert "redis://***@redis:6379/0" in out


def test_reduit_aussi_les_adresses_unicode():
    out = redact("contact jöhn@exämple.dz et محمد@مثال.الجزائر")
    assert "jöhn" not in out and "محمد" not in out
    assert "***@exämple.dz" in out and "***@مثال.الجزائر" in out


def test_ne_masque_pas_un_chemin_ou_un_parametre_entier():
    assert redact("/api/a@b.co") == "/api/***@b.co"
    assert redact("?email=x@y.co&cube=trade") == "?email=***@y.co&cube=trade"


@pytest.mark.parametrize("niveau, attendu", [("warn", logging.WARNING), ("FATAL", logging.CRITICAL)])
def test_alias_de_niveau_toujours_acceptes(logging_isole, niveau, attendu):
    logging.config.dictConfig(build_logging_config(niveau))
    assert logging.getLogger().level == attendu


def test_la_trace_d_uvicorn_ne_finit_pas_par_un_retour_echappe(logging_isole):
    flux = _sortie()
    logging.getLogger("uvicorn.error").error("Exception in ASGI application\n")
    assert flux.getvalue().rstrip("\n").endswith("Exception in ASGI application")


def test_la_ligne_websocket_d_uvicorn_perd_l_adresse_et_la_query(logging_isole):
    """Uvicorn l'écrit sur uvicorn.error, que la coupure de uvicorn.access n'atteint pas."""
    flux = _sortie()
    logging.getLogger("uvicorn.error").info(
        '%s - "WebSocket %s" 403', "198.51.100.23:51234", f"/api/ws/x?api_key={SENTINEL}&q=1"
    )
    sortie = flux.getvalue()
    assert '- "WebSocket /api/ws/x" 403' in sortie
    assert "198.51.100.23" not in sortie and SENTINEL not in sortie and "q=1" not in sortie


@pytest.mark.parametrize("nom", ["stripe", "anthropic", "urllib3", "pymongo", "httpcore2"])
def test_en_debug_les_bibliotheques_n_ecrivent_pas_leurs_requetes(logging_isole, nom):
    flux = _sortie("debug")
    logging.getLogger(nom).debug("Request body: name=Prénom Nom&email=a%40b.co")
    assert flux.getvalue() == ""
