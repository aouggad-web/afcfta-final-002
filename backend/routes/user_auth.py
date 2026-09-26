"""
User authentication routes — signup, login, logout, current user.

Session is a JWT stored in an httpOnly cookie (7-day TTL). Separate from the
X-API-Key tiered system in `auth.py`, which governs the public trade-data API.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from services import supabase_auth
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

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, value):
        if not isinstance(value, str):
            return value
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


def _add_partitioned_attribute(response: Response, cookie_name: str) -> None:
    """Starlette 0.37.2 has no `partitioned` param on set_cookie()/delete_cookie() —
    append the attribute to the raw Set-Cookie header instead. Chrome's CHIPS
    requires it for a SameSite=None; Secure cookie to survive in a cross-site
    third-party context (e.g. the Emergent preview iframe); without it the
    cookie is silently dropped there even though SameSite=None; Secure is set.

    Patches the LAST matching Set-Cookie header, not the first: logout()
    emits two Set-Cookie headers for the same cookie name (one legacy
    unpartitioned deletion, one partitioned deletion) and only the second
    one should gain the attribute.
    """
    prefix = f"{cookie_name}=".encode()
    for i in range(len(response.raw_headers) - 1, -1, -1):
        name, value = response.raw_headers[i]
        if name == b"set-cookie" and value.startswith(prefix):
            response.raw_headers[i] = (name, value + b"; Partitioned")
            break


def _set_session_cookie(response: Response, token: str, max_age: int = COOKIE_MAX_AGE) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=_COOKIE_SECURE,
        # SameSite=None (not Lax): the app can be viewed inside the Emergent
        # preview iframe, where the top-level document is a different site —
        # a Lax cookie is never sent on our own fetches in that nested
        # context, so authenticated requests fail there despite a successful
        # login. SameSite=None requires Secure, hence tied to _COOKIE_SECURE.
        samesite="none" if _COOKIE_SECURE else "lax",
        max_age=max_age,
        path="/",
    )
    if _COOKIE_SECURE:
        _add_partitioned_attribute(response, "access_token")


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
    # Pays d'inscription : il impose le moyen de paiement (Algérie → Chargily).
    # Il est déduit de l'adresse IP, qui n'est pas conservée.
    from services import geo_service

    user_doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": password_hash,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
        "signup_country": await geo_service.resolve_country(request),
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
    # A CHIPS-partitioned cookie lives in a separate jar from an unpartitioned
    # one — deleting only one shape leaves the other active. Sessions issued
    # before the Partitioned rollout (#400) are unpartitioned SameSite=Lax;
    # sessions issued after are SameSite=None; Secure; Partitioned. Emit both
    # deletions so either shape of pre-existing session cookie is cleared,
    # regardless of when it was issued. Browsers accept multiple Set-Cookie
    # headers for the same name/path when their Partitioned status differs —
    # that distinction is exactly what CHIPS uses to pick the jar.
    response.delete_cookie(
        "access_token",
        path="/",
        secure=_COOKIE_SECURE,
        samesite="lax",
    )
    if _COOKIE_SECURE:
        response.delete_cookie(
            "access_token",
            path="/",
            secure=_COOKIE_SECURE,
            samesite="none",
        )
        _add_partitioned_attribute(response, "access_token")
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
    if payload:
        from bson import ObjectId

        try:
            query = {"_id": ObjectId(payload["sub"])}
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée"
            )
    else:
        # Session Supabase : le compte Mongo est relié par `supabase_id`
        # (posé par POST /auth/session ou le script de transfert).
        supabase_payload = supabase_auth.decode_token(token)
        if not supabase_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée"
            )
        query = {"supabase_id": supabase_payload["sub"]}

    user_doc = await db.users.find_one(query)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )
    return user_doc


@router.get("/me")
async def me(request: Request):
    user_doc = await get_current_user(request)
    return _public_user(user_doc)


# ── Comptes Supabase ────────────────────────────────────────────────────────


async def _link_or_create_supabase_user(db, request: Request, payload: dict) -> tuple:
    """Premier passage d'un compte Supabase : relie le compte Mongo existant
    (même email) ou en crée un. L'email doit être confirmé côté Supabase —
    c'est ce qui prouve que la personne possède l'adresse avant de lui
    rattacher un compte existant. Retourne (compte, créé ?)."""
    try:
        supabase_user = await supabase_auth.get_admin_user(payload["sub"])
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Comptes indisponibles (configuration Supabase incomplète)",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Service d'authentification injoignable, réessayez.",
        )
    if not supabase_user.get("email_confirmed_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirmez d'abord votre adresse email (lien reçu par email).",
        )

    email = str(payload["email"]).strip().lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        if existing.get("supabase_id") and existing["supabase_id"] != payload["sub"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ce compte est déjà rattaché à une autre identité.",
            )
        await db.users.update_one(
            {"_id": existing["_id"]}, {"$set": {"supabase_id": payload["sub"]}}
        )
        existing["supabase_id"] = payload["sub"]
        return existing, False

    from services import geo_service

    metadata = supabase_user.get("user_metadata") or {}
    name = " ".join(str(metadata.get("name") or "").split())[:100] or email.split("@")[0]
    user_doc = {
        "name": name,
        "email": email,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
        "supabase_id": payload["sub"],
        "signup_country": await geo_service.resolve_country(request),
    }
    if metadata.get("terms_version"):
        # Preuve du consentement (RGPD art. 7) : version acceptée et date.
        user_doc["consents"] = [
            {
                "document": "cgu_privacy",
                "version": str(metadata["terms_version"]),
                "accepted_at": metadata.get("terms_accepted_at"),
            }
        ]
    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        # Deux premiers passages simultanés : le second relit le premier.
        return await db.users.find_one({"email": email}), False
    user_doc["_id"] = result.inserted_id
    return user_doc, True


@router.post("/session")
async def open_supabase_session(
    request: Request, response: Response, background_tasks: BackgroundTasks
):
    """Échange un jeton Supabase (en-tête Bearer) contre la session du site.

    Le jeton est vérifié, le compte Mongo relié (ou créé), puis posé dans le
    même cookie httpOnly que l'ancienne session : tout le reste du site
    (pricing.html, paiements, quotas) fonctionne sans changement. À rappeler
    à chaque rafraîchissement du jeton par le client Supabase.
    """
    if not supabase_auth.is_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non disponible")
    db = _require_db()
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    # Peut récupérer les clés publiques du projet (réseau) : hors boucle.
    payload = await run_in_threadpool(supabase_auth.decode_token, token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée"
        )

    user_doc = await db.users.find_one({"supabase_id": payload["sub"]})
    if not user_doc:
        user_doc, created = await _link_or_create_supabase_user(db, request, payload)
        if created:
            background_tasks.add_task(send_welcome_email, user_doc["email"], user_doc["name"])

    remaining = int(payload["exp"] - datetime.now(timezone.utc).timestamp())
    _set_session_cookie(response, token, max_age=max(remaining, 0))
    return _public_user(user_doc)


# ── Droits RGPD : export et suppression du compte ───────────────────────────


@router.get("/account/export")
async def export_account(request: Request):
    """Toutes les données personnelles du compte, en JSON (RGPD art. 15 et 20)."""
    db = _require_db()
    user = await get_current_user(request)
    uid = user["_id"]
    profile = {k: v for k, v in user.items() if k != "password_hash"}
    data = {
        "compte": profile,
        "achats": await db.purchases.find({"user_id": uid}).to_list(length=None),
        "tentatives_de_paiement": await db.payment_attempts.find({"user_id": uid}).to_list(
            length=None
        ),
        "cles_api": await db.api_keys.find({"user_id": str(uid)}, {"key_hash": 0}).to_list(
            length=None
        ),
        "messages_de_contact": await db.contact_messages.find({"email": user["email"]}).to_list(
            length=None
        ),
    }
    from bson import ObjectId

    return JSONResponse(
        jsonable_encoder(data, custom_encoder={ObjectId: str}),
        headers={"Content-Disposition": 'attachment; filename="mes-donnees-zlecaf.json"'},
    )


@router.delete("/account")
async def delete_account(request: Request, response: Response):
    """Supprime le compte et ses données personnelles (RGPD art. 17,
    exigence App Store / Google Play).

    Ordre : abonnements Stripe résiliés, puis identité Supabase, puis données
    Mongo — si une étape externe échoue, rien n'est effacé et le client peut
    réessayer. Les achats sont conservés anonymisés (obligations comptables).
    """
    db = _require_db()
    user = await get_current_user(request)
    uid = user["_id"]

    subscription_ids = {user.get("subscription_id")} if user.get("subscription_id") else set()
    purchases = await db.purchases.find({"user_id": uid}).to_list(length=None)
    subscription_ids |= {
        p["stripe_subscription_id"]
        for p in purchases
        if p.get("stripe_subscription_id") and p.get("status") != "canceled"
    }
    from services import stripe_service

    for subscription_id in subscription_ids:
        try:
            await run_in_threadpool(stripe_service.cancel_subscription, subscription_id)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Suppression de compte: résiliation Stripe échouée (%s)", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Résiliation de l'abonnement impossible pour le moment, réessayez.",
            )

    if user.get("supabase_id"):
        try:
            await supabase_auth.delete_admin_user(user["supabase_id"])
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.error("Suppression de compte: suppression Supabase échouée (%s)", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Suppression impossible pour le moment, réessayez.",
            )

    await db.api_keys.delete_many({"user_id": str(uid)})
    await db.purchases.update_many({"user_id": uid}, {"$set": {"user_id": None}})
    await db.payment_attempts.delete_many({"user_id": uid})
    await db.usage_counters.delete_many({"user_id": uid})
    await db.login_attempts.delete_many({"identifier": user["email"]})
    await db.contact_messages.delete_many({"email": user["email"]})
    await db.users.delete_one({"_id": uid})

    await logout(response)
    return {"message": "Compte supprimé"}
