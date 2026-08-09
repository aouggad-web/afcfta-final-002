"""
Routes de facturation — abonnements Stripe (international) et Chargily (Algérie)
================================================================================

Monté sous `api_router` (préfixe `/api`), donc URLs effectives :
  POST /api/billing/checkout          — crée un paiement (auth session JWT)
  POST /api/billing/portal            — ouvre le Customer Portal Stripe (auth session JWT)
  GET  /api/billing/subscription      — état de l'abonnement courant (auth session JWT)
  POST /api/billing/webhook           — événements Stripe (auth par signature, pas de JWT)
  POST /api/billing/chargily/webhook  — événements Chargily (auth par signature HMAC)

L'accès n'est **jamais** accordé sur la redirection de succès : seul le webhook
signé fait foi. Le routage par pays est explicite (choix de l'utilisateur, pas
de géo-IP) : `billing_country == "DZ"` part vers Chargily (CIB/Edahabia, DZD),
tout le reste vers Stripe (USD). Si Chargily n'est pas activé
(`CHARGILY_ENABLED`), la branche algérienne répond 501.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Literal, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from services import chargily_service, stripe_service
from services.email_service import send_email
from starlette.concurrency import run_in_threadpool

from .user_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])

_db = None


def set_database(database) -> None:
    global _db
    _db = database


def _require_db():
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de données indisponible.",
        )
    return _db


def _success_url() -> str:
    return os.environ.get("BILLING_SUCCESS_URL", "https://afcfta-zlecaf.com/merci")


def _cancel_url() -> str:
    return os.environ.get("BILLING_CANCEL_URL", "https://afcfta-zlecaf.com/tarifs")


class CheckoutPayload(BaseModel):
    plan: Literal["starter", "pro", "business"]
    cycle: Literal["monthly", "annual"] = "monthly"
    billing_country: Optional[str] = None  # ISO-2 ; "DZ" → Chargily (Phase 2)


@router.post("/checkout")
async def create_checkout(payload: CheckoutPayload, request: Request):
    """Crée une session Stripe Checkout pour l'utilisateur connecté."""
    db = _require_db()
    user = await get_current_user(request)

    country = (payload.billing_country or "").strip().upper()
    if country == "DZ":
        return await _checkout_chargily(db, user, payload)

    price_id = stripe_service.resolve_price_id(payload.plan, payload.cycle)

    customer_id = await run_in_threadpool(
        stripe_service.get_or_create_customer,
        user.get("email", ""),
        user.get("name", ""),
        user.get("stripe_customer_id"),
    )
    if not user.get("stripe_customer_id"):
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"stripe_customer_id": customer_id}},
        )

    metadata = {
        "user_id": str(user["_id"]),
        "plan": payload.plan,
        "cycle": payload.cycle,
    }
    checkout_url = await run_in_threadpool(
        lambda: stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=_success_url(),
            cancel_url=_cancel_url(),
            client_reference_id=str(user["_id"]),
            metadata=metadata,
        )
    )
    return {"url": checkout_url}


async def _checkout_chargily(db, user, payload: "CheckoutPayload"):
    """Branche Algérie : paiement local via Chargily (CIB / Edahabia, DZD)."""
    if not chargily_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Paiement local (Algérie) bientôt disponible via Chargily.",
        )
    amount_dzd = chargily_service.resolve_amount_dzd(payload.plan, payload.cycle)
    metadata = {
        "user_id": str(user["_id"]),
        "plan": payload.plan,
        "cycle": payload.cycle,
    }
    checkout_url = await run_in_threadpool(
        lambda: chargily_service.create_checkout(
            amount_dzd=amount_dzd,
            success_url=_success_url(),
            failure_url=_cancel_url(),
            description=f"Abonnement ZLECAf {payload.plan} ({payload.cycle})",
            metadata=metadata,
        )
    )
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"payment_provider": "chargily", "billing_country": "DZ"}},
    )
    return {"url": checkout_url}


@router.post("/portal")
async def open_portal(request: Request):
    """Ouvre le Customer Portal Stripe pour gérer/annuler l'abonnement."""
    _require_db()
    user = await get_current_user(request)
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun abonnement associé à ce compte.",
        )
    portal_url = await run_in_threadpool(
        lambda: stripe_service.create_portal_session(
            customer_id=customer_id,
            return_url=_cancel_url(),
        )
    )
    return {"url": portal_url}


@router.get("/subscription")
async def get_subscription(request: Request):
    """Renvoie l'état d'abonnement de l'utilisateur (pour le tableau de bord)."""
    _require_db()
    user = await get_current_user(request)
    return {
        "tier": user.get("subscription_tier", "free"),
        "status": user.get("subscription_status"),
        "cycle": user.get("subscription_cycle"),
        "current_period_end": user.get("subscription_current_end"),
        "payment_provider": user.get("payment_provider"),
    }


# ── Webhook ────────────────────────────────────────────────────────────────


async def _update_user_by_id(user_id: str, fields: dict) -> None:
    db = _require_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        logger.warning("Webhook: user_id invalide dans metadata: %r", user_id)
        return
    await db.users.update_one({"_id": oid}, {"$set": fields})


async def _update_user_by_customer(customer_id: str, fields: dict) -> None:
    db = _require_db()
    await db.users.update_one({"stripe_customer_id": customer_id}, {"$set": fields})


def _period_end(sub: dict) -> Optional[datetime]:
    ts = sub.get("current_period_end")
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


async def _email_user(user_id: Optional[str], subject: str, body: str) -> None:
    """Envoi best-effort : ne bloque jamais le traitement du webhook."""
    if not user_id:
        return
    db = _require_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)}, {"email": 1})
    except Exception:
        return
    if user and user.get("email"):
        try:
            await run_in_threadpool(send_email, user["email"], subject, body)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Webhook: envoi email échoué: %s", exc)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Reçoit les événements Stripe (signature vérifiée, idempotent)."""
    db = _require_db()
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe_service.construct_event(payload, sig)
    except ValueError as exc:
        logger.warning("Webhook rejeté: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    event_id = event.get("id") if isinstance(event, dict) else event["id"]
    event_type = event.get("type") if isinstance(event, dict) else event["type"]
    data_obj = event["data"]["object"]

    # Idempotence : l'index unique sur event_id absorbe les rejeux Stripe.
    try:
        await db.payment_events.insert_one(
            {
                "event_id": event_id,
                "type": event_type,
                "received_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError:
        return {"status": "already_processed"}

    if event_type == "checkout.session.completed":
        meta = data_obj.get("metadata") or {}
        await _update_user_by_id(
            meta.get("user_id", ""),
            {
                "subscription_tier": meta.get("plan", "free"),
                "subscription_status": "active",
                "subscription_cycle": meta.get("cycle"),
                "subscription_id": data_obj.get("subscription"),
                "stripe_customer_id": data_obj.get("customer"),
                "payment_provider": "stripe",
            },
        )
        await _email_user(
            meta.get("user_id"),
            "Votre abonnement ZLECAf est actif",
            "Merci — votre abonnement est désormais actif. "
            "Vous pouvez le gérer à tout moment depuis votre tableau de bord.",
        )

    elif event_type == "customer.subscription.updated":
        meta = data_obj.get("metadata") or {}
        fields = {
            "subscription_status": data_obj.get("status"),
            "subscription_current_end": _period_end(data_obj),
        }
        if meta.get("plan"):
            fields["subscription_tier"] = meta["plan"]
        await _update_user_by_customer(data_obj.get("customer", ""), fields)

    elif event_type == "customer.subscription.deleted":
        await _update_user_by_customer(
            data_obj.get("customer", ""),
            {"subscription_tier": "free", "subscription_status": "canceled"},
        )

    elif event_type == "invoice.payment_failed":
        await _update_user_by_customer(
            data_obj.get("customer", ""),
            {"subscription_status": "past_due"},
        )

    return {"status": "ok"}


@router.post("/chargily/webhook")
async def chargily_webhook(request: Request):
    """Webhook Chargily (Algérie) — signature HMAC vérifiée, idempotent.

    Chargily fonctionne par paiements ponctuels : un paiement réussi active le
    plan pour la période achetée. Le renouvellement se fait par un nouveau
    paiement (pas d'abonnement récurrent côté passerelle).
    """
    db = _require_db()
    payload = await request.body()
    signature = request.headers.get("signature")

    try:
        event = chargily_service.verify_and_parse(payload, signature)
    except ValueError as exc:
        logger.warning("Webhook Chargily rejeté: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    event_id = event.get("id") or ""
    event_type = event.get("type") or ""
    data_obj = event.get("data") or {}

    try:
        await db.payment_events.insert_one(
            {
                "event_id": f"chargily:{event_id}",
                "type": event_type,
                "received_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError:
        return {"status": "already_processed"}

    meta = data_obj.get("metadata") or {}
    # metadata peut revenir sous forme de liste selon la version de l'API.
    if isinstance(meta, list):
        meta = meta[0] if meta and isinstance(meta[0], dict) else {}
    user_id = meta.get("user_id", "")

    if event_type == "checkout.paid":
        await _update_user_by_id(
            user_id,
            {
                "subscription_tier": meta.get("plan", "free"),
                "subscription_status": "active",
                "subscription_cycle": meta.get("cycle"),
                "payment_provider": "chargily",
                "billing_country": "DZ",
            },
        )
        await _email_user(
            user_id,
            "Votre abonnement ZLECAf est actif",
            "Merci — votre paiement a été confirmé et votre abonnement est actif.",
        )

    elif event_type in ("checkout.failed", "checkout.canceled", "checkout.expired"):
        # Aucun accès accordé : on journalise sans dégrader un abonnement déjà actif.
        logger.info("Chargily: paiement non abouti (%s) pour user_id=%s", event_type, user_id)

    return {"status": "ok"}
