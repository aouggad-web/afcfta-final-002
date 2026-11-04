"""Masquage des secrets passés en URL dans les journaux (constat C2 de l'audit)."""

import io
import logging
import logging.config

import httpx
import pytest
from log_redaction import RedactingFormatter, build_logging_config, redact

SENTINEL = "SENTINELLE-NON-SECRETE-123"


@pytest.fixture
def logging_isole():
    """Restaure la configuration de logging modifiée par un test."""
    root = logging.getLogger()
    etat = (root.handlers[:], root.level)
    niveaux = {n: logging.getLogger(n).level for n in ("httpx", "httpcore")}
    yield
    root.handlers[:], root.level = etat[0], etat[1]
    for nom, niveau in niveaux.items():
        logging.getLogger(nom).setLevel(niveau)


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
