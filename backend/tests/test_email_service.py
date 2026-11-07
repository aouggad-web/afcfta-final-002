"""
E-mails transactionnels : le certificat du serveur SMTP est toujours vérifié.

Hermétiques : smtplib est remplacé, aucune connexion n'est ouverte.
"""

import ssl
import sys
from pathlib import Path

import pytest

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services import email_service  # noqa: E402


@pytest.fixture
def connexions(monkeypatch):
    ouvertes = []

    class _FauxSMTP:
        def __init__(self, host, port, timeout=None, context=None):
            self.port, self.context = port, context
            self.messages = []
            ouvertes.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def ehlo(self):
            pass

        def starttls(self, context=None):
            self.context = context

        def login(self, user, password):
            pass

        def send_message(self, message):
            self.messages.append(message)

    monkeypatch.setattr(email_service.smtplib, "SMTP", _FauxSMTP)
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", _FauxSMTP)
    for nom, valeur in {
        "SAAS_EMAIL_ENABLED": "true",
        "SAAS_SMTP_HOST": "smtp.zoho.com",
        "SAAS_SMTP_USER": "noreply@example.com",
        "SAAS_SMTP_PASSWORD": "mot-de-passe-factice",
    }.items():
        monkeypatch.setenv(nom, valeur)
    return ouvertes


def _verifie(contexte):
    return (
        contexte is not None
        and contexte.verify_mode == ssl.CERT_REQUIRED
        and contexte.check_hostname
    )


@pytest.mark.parametrize("port, use_tls", [("587", "true"), ("465", "false")])
def test_certificat_du_serveur_verifie(connexions, monkeypatch, port, use_tls):
    # Sans contexte, smtplib.SMTP_SSL (port 465) accepte n'importe quel certificat.
    monkeypatch.setenv("SAAS_SMTP_PORT", port)
    monkeypatch.setenv("SAAS_SMTP_USE_TLS", use_tls)
    email_service.send_email("client@example.com", "Objet", "Corps")
    (connexion,) = connexions
    assert connexion.port == int(port) and len(connexion.messages) == 1
    assert _verifie(connexion.context)
