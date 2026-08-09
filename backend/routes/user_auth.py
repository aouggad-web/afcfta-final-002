"""
User authentication routes — signup, login, logout, current user.

Session is a JWT stored in an httpOnly cookie (7-day TTL). Separate from the
X-API-Key tiered system in `auth.py`, which governs the public trade-data API.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from pymongo import ReturnDocument

from services.email_service import send_welcome_email
from services.user_auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["User Authentication"])

_db = None

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_MAX_AGE = 7 * 24 * 3600


def set_database(database) -> None:
    global _db
    _db = database


def _require_db():
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Comptes utilisateurs indisponibles (base de données non configurée)",
        )
    return _db


class RegisterPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


def _public_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "user"),
    }


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/register")
async def register(payload: RegisterPayload, response: Response, background_tasks: BackgroundTasks):
    db = _require_db()
    email = payload.email.lower()

    existing = await db.users.find_one({"email": email}, {"_id": 1})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email"
        )

    user_doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token(str(user_doc["_id"]), email)
    _set_session_cookie(response, token)

    background_tasks.add_task(send_welcome_email, email, user_doc["name"])

    return _public_user(user_doc)


async def _is_locked_out(db, identifier: str) -> bool:
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if not attempt:
        return False
    if attempt.get("count", 0) < MAX_FAILED_ATTEMPTS:
        return False
    locked_until = attempt.get("locked_until")
    if not locked_until:
        return False
    # MongoDB/BSON stores datetimes without timezone info, so pymongo returns
    # a naive datetime here even though it was written as UTC-aware — compare
    # as UTC-aware on both sides to avoid a TypeError.
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < locked_until


@router.post("/login")
async def login(payload: LoginPayload, response: Response):
    db = _require_db()
    email = payload.email.lower()
    # Keyed by email only (not IP): behind this app's ingress, the proxy hop
    # seen as request.client.host varies between requests from the same
    # browser, which would make an IP-based identifier unreliable.
    identifier = email

    if await _is_locked_out(db, identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de tentatives échouées. Réessayez dans {LOCKOUT_MINUTES} minutes.",
        )

    user_doc = await db.users.find_one({"email": email})
    if not user_doc or not verify_password(payload.password, user_doc.get("password_hash", "")):
        updated = await db.login_attempts.find_one_and_update(
            {"identifier": identifier},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if updated and updated.get("count", 0) >= MAX_FAILED_ATTEMPTS:
            await db.login_attempts.update_one(
                {"identifier": identifier},
                {
                    "$set": {
                        "locked_until": datetime.now(timezone.utc)
                        + timedelta(minutes=LOCKOUT_MINUTES)
                    }
                },
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect"
        )

    await db.login_attempts.delete_one({"identifier": identifier})

    token = create_access_token(str(user_doc["_id"]), email)
    _set_session_cookie(response, token)
    return _public_user(user_doc)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Déconnecté"}


async def get_current_user(request: Request) -> dict:
    db = _require_db()
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée"
        )

    from bson import ObjectId

    user_doc = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )
    return user_doc


@router.get("/me")
async def me(request: Request):
    user_doc = await get_current_user(request)
    return _public_user(user_doc)
