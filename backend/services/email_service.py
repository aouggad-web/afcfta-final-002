"""
SAAS transactional email service (SMTP — Zoho Mail).

Sends the welcome email on signup and the admin notification on contact-form
submission. Runs synchronously via smtplib, so callers MUST invoke these
functions from a FastAPI BackgroundTasks (never directly inside an async
endpoint) to avoid blocking the event loop.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.environ.get("SAAS_EMAIL_ENABLED", "false").lower() == "true"


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email via the configured SMTP provider.

    No-op (logged) when SAAS_EMAIL_ENABLED is not "true", so the app keeps
    working even without SMTP credentials configured.
    """
    if not _enabled():
        logger.info(
            f"Email sending disabled (SAAS_EMAIL_ENABLED != true) — skipped to {to}: {subject}"
        )
        return

    host = os.environ["SAAS_SMTP_HOST"]
    port = int(os.environ.get("SAAS_SMTP_PORT", "587"))
    user = os.environ["SAAS_SMTP_USER"]
    password = os.environ["SAAS_SMTP_PASSWORD"]
    use_tls = os.environ.get("SAAS_SMTP_USE_TLS", "true").lower() == "true"

    message = EmailMessage()
    message["From"] = user
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(user, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
                smtp.login(user, password)
                smtp.send_message(message)
        logger.info(f"Email sent to {to}: {subject}")
    except (smtplib.SMTPException, OSError) as e:
        logger.warning(f"SMTP delivery failed (recipient={to}, subject={subject}): {e}")


def send_welcome_email(recipient: str, name: str) -> None:
    send_email(
        recipient,
        "Bienvenue sur ZLECAf Intelligence",
        f"Bonjour {name},\n\n"
        "Votre compte a été créé avec succès sur la plateforme ZLECAf Intelligence.\n"
        "Vous pouvez dès à présent vous connecter et accéder au tableau de bord.\n\n"
        "Cordialement,\nL'équipe ZLECAf Intelligence",
    )


def send_contact_admin_email(name: str, email: str, message: str) -> None:
    admin_email = os.environ.get("SAAS_SMTP_USER", "")
    if not admin_email:
        logger.warning(
            "Contact-form admin notification skipped: SAAS_SMTP_USER is not configured "
            f"(message from {email} was still stored in MongoDB)"
        )
        return
    send_email(
        admin_email,
        f"Nouveau message de contact — {name}",
        f"Nom : {name}\nEmail : {email}\n\nMessage :\n{message}",
    )
