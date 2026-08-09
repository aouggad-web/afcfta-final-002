"""Contact form route — stores the message and notifies the admin by email."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

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


@router.post("")
async def submit_contact(payload: ContactPayload, background_tasks: BackgroundTasks):
    if _db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Formulaire de contact indisponible")

    doc = {
        "name": payload.name.strip(),
        "email": payload.email.lower(),
        "message": payload.message.strip(),
        "created_at": datetime.now(timezone.utc),
    }
    await _db.contact_messages.insert_one(doc)

    background_tasks.add_task(send_contact_admin_email, doc["name"], doc["email"], doc["message"])

    return {"message": "Message envoyé avec succès"}
