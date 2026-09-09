"""Contact form route — stores the message and notifies the admin by email."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from services.email_service import send_contact_admin_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contact", tags=["Contact"])

_db = None


def set_database(database) -> None:
    global _db
    _db = database


class ContactPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("name", "message")
    @classmethod
    def _not_blank_after_strip(cls, value: str) -> str:
        # min_length=1 is checked before this runs, so a whitespace-only
        # value (e.g. "   ") would otherwise pass validation, get stored,
        # and be emailed as an empty message while the UI reports success.
        stripped = value.strip()
        if not stripped:
            raise ValueError("Ce champ ne peut pas être vide.")
        return stripped


@router.post("")
async def submit_contact(
    payload: ContactPayload, request: Request, background_tasks: BackgroundTasks
):
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Formulaire de contact indisponible",
        )

    # Audit trail: the caller's real IP is the only reliable way to tell a
    # genuine web submission (this route) apart from an admin notification
    # produced some other way (a manual send_contact_admin_email() call, or a
    # message sent straight through the SMTP mailbox). See geo_service for the
    # X-Forwarded-For handling tied to TRUSTED_PROXY_HOPS.
    from services import geo_service

    submit_ip = geo_service.client_ip(request)

    doc = {
        "name": payload.name,
        "email": payload.email.lower(),
        "message": payload.message,
        "submit_ip": submit_ip,
        "created_at": datetime.now(timezone.utc),
    }
    await _db.contact_messages.insert_one(doc)

    logger.info(
        "Contact form submitted via /api/contact "
        f"(name={doc['name']!r}, email={doc['email']!r}, ip={submit_ip})"
    )

    background_tasks.add_task(send_contact_admin_email, doc["name"], doc["email"], doc["message"])

    return {"message": "Message envoyé avec succès"}
