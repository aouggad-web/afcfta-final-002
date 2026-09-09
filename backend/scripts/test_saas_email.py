"""
Manual SMTP smoke test for the SaaS email service.

Usage:
    cd /app/backend && python scripts/test_saas_email.py <recipient_email>

Sends a real test email through the configured SAAS_SMTP_* provider (see
.env) to the given recipient, using the same send_email() function used by
the welcome-email and contact-form-notification flows.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from services.email_service import send_email  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_saas_email.py <recipient_email>")
        sys.exit(1)

    recipient = sys.argv[1]

    print(f"SAAS_EMAIL_ENABLED = {os.environ.get('SAAS_EMAIL_ENABLED')}")
    print(f"SAAS_SMTP_HOST     = {os.environ.get('SAAS_SMTP_HOST')}")
    print(f"SAAS_SMTP_PORT     = {os.environ.get('SAAS_SMTP_PORT')}")
    print(f"SAAS_SMTP_USER     = {os.environ.get('SAAS_SMTP_USER')}")
    print(f"Sending test email to: {recipient}...")

    send_email(
        to=recipient,
        subject="Test SMTP — ZLECAf Intelligence",
        body="Ceci est un email de test envoyé depuis le script scripts/test_saas_email.py.\n\nSi vous recevez ce message, la configuration SMTP SAAS_SMTP_* fonctionne correctement.",
    )

    print(
        "Done. Check the logs above for 'Email sent' (success) or 'SMTP delivery failed' (error)."
    )


if __name__ == "__main__":
    main()
