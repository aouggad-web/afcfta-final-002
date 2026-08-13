"""
User authentication routes — signup, login, logout, current user.

Session is a JWT stored in an httpOnly cookie (7-day TTL). Separate from the
X-API-Key tiered system in `auth.py`, which governs the public trade-data API.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from services.email_service import send_welcome_email
from services.user_auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["User Authentication"])

_db = None

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_MAX_AGE = 7 * 24 * 3600
# Same flag the CSRF/security-headers middlewares use to decide the Secure
# cookie attribute — keep the session cookie usable in HTTP dev/internal
# environments instead of silently never being sent back by the browser.
_COOKIE_SECURE = os.environ.get("HTTPS_ENABLED", "false").lower() == "true"


def _issue_session_token(user_id: str, email: str) -> str:
    """create_access_token() reads JWT_SECRET from the environment and raises
    KeyError if it's unset — turn that into a clear 503 instead of an opaque
    500 when the JWT signing config is missing."""
    try:
        return create_access_token(user_id, email)
    except KeyError:
        logger.error("JWT_SECRET is not configured — cannot issue session tokens")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Comptes utilisateurs indisponibles (configuration JWT manquante)",
        )


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

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Le nom ne peut pas être vide.")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt silently ignores bytes past the 72nd, so two different
        # passwords sharing the first 72 UTF-8 bytes would hash identically —
        # reject up front instead of accepting a password that doesn't fully
        # matter for authentication.
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Le mot de passe est trop long (72 octets maximum une fois encodé en UTF-8)."
            )
        return value


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


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
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/register")
async def register(
    payload: RegisterPayload,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
):
    db = _require_db()
    email = str(payload.email)

    existing = await db.users.find_one({"email": email}, {"_id": 1})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email"
        )

    # bcrypt is CPU-bound and takes ~100-300ms at this cost factor — run it
    # off the event loop so a burst of signups doesn't stall every other
    # request this worker is handling.
    password_hash = await run_in_threadpool(hash_password, payload.password)
    # IP et pays d'inscription : signal de référence pour l'audit des paiements
    # (une incohérence ultérieure se voit, sans jamais bloquer automatiquement).
    from services import geo_service

    user_doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": password_hash,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
        "signup_ip": geo_service.client_ip(request),
        "signup_country": geo_service.country_from_request(request),
    }
    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        # Two concurrent registrations for the same email both passed the
        # find_one check above; the unique index on users.email catches the
        # second insert. Surface the same 409 as the normal duplicate path
        # instead of letting this bubble up as an unhandled 500.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email"
        )
    user_doc["_id"] = result.inserted_id

    token = _issue_session_token(str(user_doc["_id"]), email)
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
    if datetime.now(timezone.utc) < locked_until:
        return True
    # Lockout window has elapsed: reset the counter instead of leaving a
    # stale count >= MAX_FAILED_ATTEMPTS in place. Without this, a single
    # fresh bad guess right after expiry immediately re-locks the account —
    # letting anyone who knows the victim's email keep it locked out
    # indefinitely with one guess every LOCKOUT_MINUTES, even though they
    # never learn the correct password. Deleting means a new lockout again
    # requires MAX_FAILED_ATTEMPTS fresh failures, not just one.
    await db.login_attempts.delete_one({"identifier": identifier})
    return False


@router.post("/login")
async def login(payload: LoginPayload, response: Response):
    db = _require_db()
    email = str(payload.email)
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
    password_ok = False
    if user_doc:
        # Same threadpool offload as registration — bcrypt verification is
        # just as CPU-bound as hashing and must not block the event loop.
        password_ok = await run_in_threadpool(
            verify_password, payload.password, user_doc.get("password_hash", "")
        )
    if not user_doc or not password_ok:
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

    token = _issue_session_token(str(user_doc["_id"]), email)
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

    try:
        user_id = ObjectId(payload["sub"])
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée"
        )

    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )
    return user_doc


@router.get("/me")
async def me(request: Request):
    user_doc = await get_current_user(request)
    return _public_user(user_doc)
