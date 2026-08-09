#!/usr/bin/env python3
"""
Test the SaaS transactional email service (Zoho / any SMTP).

Usage:
    # Load your real .env first, then:
    python scripts/test_saas_email.py you@example.com

Sends a verification-style test email to the given recipient using the
current SAAS_* environment variables. Prints the resolved configuration and
whether the send succeeded, so you can confirm your Zoho setup end to end.
"""

import asyncio
import sys
from pathlib import Path

# Make `backend` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.notifications.transactional_email import (  # noqa: E402
    get_transactional_email_service,
)


async def main(recipient: str) -> int:
    svc = get_transactional_email_service()

    print("Resolved configuration")
    print("-" * 40)
    print(f"  enabled     : {svc.enabled}")
    print(f"  smtp_host   : {svc.smtp_host!r}")
    print(f"  smtp_port   : {svc.smtp_port}")
    print(f"  smtp_user   : {svc.smtp_user!r}")
    print(f"  use_tls     : {svc.use_tls}")
    print(f"  from_email  : {svc.from_email!r}")
    print(f"  reply_to    : {svc.reply_to!r}")
    print(f"  is_enabled(): {svc.is_enabled()}")
    print("-" * 40)

    if not svc.is_enabled():
        print(
            "\n[!] Service is NOT enabled/configured. Set SAAS_EMAIL_ENABLED=true "
            "and the SAAS_SMTP_* variables in your .env, then retry."
        )
        return 1

    print(f"\nSending test verification email to {recipient} ...")
    ok = await svc.send_verification_email(
        to=recipient,
        verification_url=f"{svc.app_base_url}/verify?token=TEST-TOKEN-123",
        name="Test",
    )
    if ok:
        print("[OK] Email sent successfully. Check the inbox (and spam folder).")
        return 0
    print(
        "[FAIL] Send returned False. Check the logs above for the SMTP error "
        "(wrong region host, bad app password, or SPF/DKIM not set)."
    )
    return 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_saas_email.py <recipient-email>")
        raise SystemExit(64)
    raise SystemExit(asyncio.run(main(sys.argv[1])))
