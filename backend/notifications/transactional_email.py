"""
Transactional Email Service (SaaS user-facing emails)
=====================================================

Distinct from ``email_notifier.py`` (which sends *operational* crawler alerts
to a fixed admin list). This service sends *transactional* emails to end users
of the AfCFTA / ZLECAf SaaS — account verification, welcome, quota alerts —
each addressed to a single dynamic recipient and branded with the official
domain.

Official identity (all overridable via environment variables):
  - Sender  : "AfCFTA ZLECAf <noreply@afcfta-zlecaf.com>"
  - Reply-To: support@afcfta-zlecaf.com
  - App URL : https://afcfta-zlecaf.com

Configuration (environment variables)
-------------------------------------
  SAAS_EMAIL_ENABLED     Enable/disable sending (default: false)
  SAAS_SMTP_HOST         SMTP server hostname
  SAAS_SMTP_PORT         SMTP server port (default: 587)
  SAAS_SMTP_USER         SMTP username
  SAAS_SMTP_PASSWORD     SMTP password
  SAAS_SMTP_USE_TLS      STARTTLS (default: true)
  SAAS_EMAIL_FROM        From header (default: AfCFTA ZLECAf <noreply@afcfta-zlecaf.com>)
  SAAS_EMAIL_REPLY_TO    Reply-To header (default: support@afcfta-zlecaf.com)
  SAAS_APP_BASE_URL      Base URL used to build links (default: https://afcfta-zlecaf.com)

Usage
-----
    from backend.notifications.transactional_email import get_transactional_email_service

    svc = get_transactional_email_service()
    await svc.send_verification_email(
        to="user@example.com",
        verification_url="https://afcfta-zlecaf.com/verify?token=...",
        name="Amine",
    )
"""

from __future__ import annotations

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import Optional

try:
    import aiosmtplib

    AIOSMTPLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    AIOSMTPLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

# Official SaaS identity — used as safe defaults when env vars are unset.
DEFAULT_FROM = "AfCFTA ZLECAf <noreply@afcfta-zlecaf.com>"
DEFAULT_REPLY_TO = "support@afcfta-zlecaf.com"
DEFAULT_APP_BASE_URL = "https://afcfta-zlecaf.com"
BRAND_NAME = "AfCFTA ZLECAf"


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class TransactionalEmailService:
    """Sends branded, single-recipient transactional emails over SMTP."""

    def __init__(self) -> None:
        self.enabled = _env_bool("SAAS_EMAIL_ENABLED", False)
        self.smtp_host = os.getenv("SAAS_SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SAAS_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SAAS_SMTP_USER", "")
        self.smtp_password = os.getenv("SAAS_SMTP_PASSWORD", "")
        self.use_tls = _env_bool("SAAS_SMTP_USE_TLS", True)
        self.from_email = os.getenv("SAAS_EMAIL_FROM", DEFAULT_FROM)
        self.reply_to = os.getenv("SAAS_EMAIL_REPLY_TO", DEFAULT_REPLY_TO)
        self.app_base_url = os.getenv("SAAS_APP_BASE_URL", DEFAULT_APP_BASE_URL).rstrip("/")

        if self.enabled and not AIOSMTPLIB_AVAILABLE:
            logger.warning(
                "aiosmtplib not installed; transactional emails are disabled. "
                "Install it with `pip install aiosmtplib`."
            )
            self.enabled = False

    def is_enabled(self) -> bool:
        """True only when sending is enabled AND minimally configured."""
        return bool(
            self.enabled
            and AIOSMTPLIB_AVAILABLE
            and self.smtp_host
            and self.smtp_user
        )

    # ------------------------------------------------------------------ #
    # Low-level send                                                      #
    # ------------------------------------------------------------------ #
    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        """Send a single email. Returns True on success, False otherwise.

        When the service is disabled/unconfigured, logs and returns False
        instead of raising, so callers (e.g. signup) never fail because email
        is not wired up yet.
        """
        _, addr = parseaddr(to)
        if not addr or "@" not in addr:
            logger.error("Refusing to send transactional email: invalid recipient %r", to)
            return False

        if not self.is_enabled():
            logger.info(
                "Transactional email suppressed (service disabled/unconfigured): "
                "to=%s subject=%r",
                addr,
                subject,
            )
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = addr
        if self.reply_to:
            msg["Reply-To"] = self.reply_to
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.use_tls,
            )
            logger.info("Transactional email sent: to=%s subject=%r", addr, subject)
            return True
        except Exception as exc:  # noqa: BLE001 - report, never crash the caller
            logger.error("Failed to send transactional email to %s: %s", addr, exc)
            return False

    # ------------------------------------------------------------------ #
    # High-level messages                                                 #
    # ------------------------------------------------------------------ #
    async def send_verification_email(
        self, to: str, verification_url: str, name: Optional[str] = None
    ) -> bool:
        """Send the account-verification email with the activation link."""
        greeting_fr = f"Bonjour {name}," if name else "Bonjour,"
        greeting_en = f"Hello {name}," if name else "Hello,"
        subject = f"{BRAND_NAME} — Confirmez votre e-mail / Confirm your email"
        text = (
            f"{greeting_fr}\n\n"
            f"Merci de votre inscription sur {BRAND_NAME}. "
            f"Confirmez votre adresse e-mail pour activer votre clé API :\n"
            f"{verification_url}\n\n"
            f"Ce lien expire dans 24 heures. Si vous n'êtes pas à l'origine de "
            f"cette demande, ignorez cet e-mail.\n\n"
            f"— L'équipe {BRAND_NAME}\n"
            f"{self.app_base_url}\n\n"
            f"---\n\n"
            f"{greeting_en}\n\n"
            f"Thanks for signing up to {BRAND_NAME}. "
            f"Confirm your email address to activate your API key:\n"
            f"{verification_url}\n\n"
            f"This link expires in 24 hours. If you didn't request this, "
            f"you can safely ignore this email.\n\n"
            f"— The {BRAND_NAME} team\n"
            f"{self.app_base_url}\n"
        )
        html = self._layout(
            title="Confirmez votre e-mail",
            body_html=f"""
                <p style="margin:0 0 16px">{_esc(greeting_fr)}</p>
                <p style="margin:0 0 16px">Merci de votre inscription sur
                    <strong>{BRAND_NAME}</strong>. Cliquez sur le bouton
                    ci-dessous pour confirmer votre adresse e-mail et activer
                    votre clé API.</p>
                {self._button("Confirmer mon e-mail", verification_url)}
                <p style="margin:16px 0 0;color:#6b7280;font-size:13px">
                    Ce lien expire dans 24 heures. Si vous n'êtes pas à
                    l'origine de cette demande, ignorez cet e-mail.</p>
                <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
                <p style="margin:0 0 16px;color:#6b7280">{_esc(greeting_en)}
                    Confirm your email to activate your API key:</p>
                {self._button("Confirm my email", verification_url)}
            """,
        )
        return await self.send(to=to, subject=subject, html=html, text=text)

    async def send_welcome_email(
        self, to: str, tier: str = "free", name: Optional[str] = None
    ) -> bool:
        """Send the welcome email once an account is verified/activated."""
        greeting_fr = f"Bienvenue {name} !" if name else "Bienvenue !"
        subject = f"{BRAND_NAME} — Votre compte est actif / Your account is active"
        dashboard_url = f"{self.app_base_url}/account"
        text = (
            f"{greeting_fr}\n\n"
            f"Votre compte {BRAND_NAME} (offre « {tier} ») est actif. "
            f"Retrouvez votre clé API et votre consommation ici :\n"
            f"{dashboard_url}\n\n"
            f"Besoin d'aide ? {self.reply_to}\n\n"
            f"— L'équipe {BRAND_NAME}\n"
        )
        html = self._layout(
            title="Votre compte est actif",
            body_html=f"""
                <p style="margin:0 0 16px">{_esc(greeting_fr)}</p>
                <p style="margin:0 0 16px">Votre compte
                    <strong>{BRAND_NAME}</strong> (offre
                    « {_esc(tier)} ») est actif. Accédez à votre clé API et
                    suivez votre consommation depuis votre espace.</p>
                {self._button("Ouvrir mon espace", dashboard_url)}
                <p style="margin:16px 0 0;color:#6b7280;font-size:13px">
                    Besoin d'aide ? Écrivez-nous à {_esc(self.reply_to)}.</p>
            """,
        )
        return await self.send(to=to, subject=subject, html=html, text=text)

    # ------------------------------------------------------------------ #
    # Presentation helpers                                                #
    # ------------------------------------------------------------------ #
    def _button(self, label: str, url: str) -> str:
        safe_url = _esc(url)
        return (
            f'<table role="presentation" cellspacing="0" cellpadding="0" '
            f'style="margin:8px 0">'
            f'<tr><td style="border-radius:8px;background:#047857">'
            f'<a href="{safe_url}" '
            f'style="display:inline-block;padding:12px 24px;color:#ffffff;'
            f'font-weight:600;text-decoration:none;border-radius:8px">'
            f"{_esc(label)}</a></td></tr></table>"
            f'<p style="margin:8px 0 0;font-size:12px;color:#9ca3af;'
            f'word-break:break-all">{safe_url}</p>'
        )

    def _layout(self, title: str, body_html: str) -> str:
        sender_name = parseaddr(self.from_email)[0] or BRAND_NAME
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_esc(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:#f3f4f6;padding:24px 0">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;
                    overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,
                    'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#111827">
        <tr><td style="background:#047857;padding:24px 32px">
          <span style="color:#ffffff;font-size:18px;font-weight:700;
                       letter-spacing:.3px">{_esc(sender_name)}</span>
        </td></tr>
        <tr><td style="padding:32px">{body_html}</td></tr>
        <tr><td style="padding:20px 32px;background:#f9fafb;border-top:1px solid #e5e7eb">
          <p style="margin:0;font-size:12px;color:#9ca3af">
            {_esc(BRAND_NAME)} — Calculateur commercial ZLECAf ·
            <a href="{_esc(self.app_base_url)}"
               style="color:#047857;text-decoration:none">{_esc(self.app_base_url)}</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _esc(value: str) -> str:
    """Minimal HTML escaping for values interpolated into templates."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Module-level singleton -------------------------------------------------- #
_service: Optional[TransactionalEmailService] = None


def get_transactional_email_service() -> TransactionalEmailService:
    """Return a lazily-instantiated shared service (reads env at first use)."""
    global _service
    if _service is None:
        _service = TransactionalEmailService()
    return _service
