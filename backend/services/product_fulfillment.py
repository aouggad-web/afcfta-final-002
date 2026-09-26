"""
Livraison des produits hors formule (API, options, rapports, formation)
======================================================================

Appelé par les webhooks de paiement (`routes/billing.py`) une fois le paiement
confirmé — jamais sur la redirection de succès.

- Plans API (`api_request_quota` dans `pricing.PRODUCTS`) : livrés
  automatiquement — une clé API est créée avec son quota mensuel et envoyée
  par email. Elle est désactivée quand l'abonnement Stripe prend fin ; côté
  Chargily (paiement ponctuel), elle porte une date d'expiration.
- Autres produits : achat enregistré, email de confirmation au client et
  notification à l'équipe, qui livre à la main (rapport PDF, session de
  formation, accès à la certification…).

Chaque achat est tracé dans la collection `purchases`.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import pricing
from bson import ObjectId
from services.email_service import send_email
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# Période couverte par un paiement Chargily d'un produit mensuel.
CHARGILY_PERIOD_DAYS = 30

# Statuts Stripe d'abonnement pour lesquels le produit n'est plus fourni.
_ENDED_STATUSES = frozenset({"canceled", "unpaid", "incomplete_expired"})


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    # Mongo renvoie des datetimes naïfs (UTC) — même précaution qu'ailleurs.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _email(to: Optional[str], subject: str, body: str) -> None:
    """Envoi best-effort : un email raté ne doit jamais faire échouer la livraison."""
    if not to:
        return
    try:
        await run_in_threadpool(send_email, to, subject, body)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Livraison produit: envoi email échoué: %s", exc)


async def _create_api_key(db, user: dict, product_id: str, expires_at) -> tuple:
    """Crée la clé API d'un plan API. Retourne (id du document, clé en clair)."""
    entry = pricing.product(product_id)
    raw_key = "afcfta_" + secrets.token_urlsafe(32)
    doc = {
        "key_hash": _hash_key(raw_key),
        "name": f"{entry['label']} — {user.get('email', '')}",
        "owner": user.get("email", ""),
        # Le tier des clés gouverne le quota IA (auth.AI_TIER_QUOTAS) : un plan
        # API vendu n'inclut pas d'IA au-delà du niveau gratuit.
        "tier": "free",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user["_id"]),
        "product": product_id,
        "request_quota": entry["api_request_quota"],
    }
    if expires_at is not None:
        doc["expires_at"] = expires_at
    result = await db["api_keys"].insert_one(doc)
    return result.inserted_id, raw_key


async def activate(
    db,
    *,
    user_id: str,
    product_id: str,
    provider: str,
    subscription_id: Optional[str] = None,
) -> None:
    """Livre un produit payé. Lève UnknownProduct pour un id hors catalogue."""
    entry = pricing.product(product_id)
    try:
        oid = ObjectId(user_id)
    except Exception:
        logger.warning("Livraison produit: user_id invalide dans metadata: %r", user_id)
        return
    user = await db.users.find_one({"_id": oid}, {"email": 1, "name": 1})
    if not user:
        logger.warning("Livraison produit: utilisateur %s introuvable", user_id)
        return

    now = datetime.now(timezone.utc)
    period_end = None
    if provider == "chargily" and entry["recurring"]:
        # Renouvellement : on prolonge l'achat en cours à partir de sa fin, pour
        # ne pas faire perdre les jours déjà payés.
        current = await db.purchases.find_one(
            {"user_id": oid, "product": product_id, "provider": "chargily", "status": "active"}
        )
        current_end = _as_utc(current.get("period_end")) if current else None
        if current and current_end and current_end > now:
            period_end = current_end + timedelta(days=CHARGILY_PERIOD_DAYS)
            await db.purchases.update_one(
                {"_id": current["_id"]}, {"$set": {"period_end": period_end}}
            )
            if current.get("api_key_id"):
                await db["api_keys"].update_one(
                    {"_id": current["api_key_id"]}, {"$set": {"expires_at": period_end}}
                )
            await _email(
                user.get("email"),
                f"Renouvellement confirmé — {entry['label']}",
                f"Merci — votre {entry['label']} est prolongé jusqu'au "
                f"{period_end.strftime('%d/%m/%Y')}.",
            )
            return
        period_end = now + timedelta(days=CHARGILY_PERIOD_DAYS)

    api_key_id, raw_key = None, None
    if entry.get("api_request_quota"):
        api_key_id, raw_key = await _create_api_key(db, user, product_id, period_end)

    await db.purchases.insert_one(
        {
            "user_id": oid,
            "product": product_id,
            "provider": provider,
            "status": "active",
            "created_at": now,
            "period_end": period_end,
            "stripe_subscription_id": subscription_id,
            "api_key_id": api_key_id,
        }
    )

    lines = [f"Merci — votre achat « {entry['label']} » est confirmé."]
    if raw_key:
        lines += [
            f"Votre clé API : {raw_key}",
            f"Quota : {entry['api_request_quota']:,} requêtes par mois".replace(",", " ")
            + ". Envoyez-la dans l'en-tête X-API-Key de vos requêtes.",
            "Conservez-la en lieu sûr : elle ne vous sera plus renvoyée.",
        ]
    else:
        lines.append("Notre équipe vous contacte sous 48 h ouvrées pour la livraison.")
    if period_end:
        lines.append(f"Valable jusqu'au {period_end.strftime('%d/%m/%Y')}.")
    await _email(user.get("email"), f"Votre achat ZLECAf — {entry['label']}", "\n\n".join(lines))

    if not raw_key:
        await _email(
            os.environ.get("SAAS_SMTP_USER", ""),
            f"Commande à livrer — {entry['label']}",
            f"Client : {user.get('name', '')} <{user.get('email', '')}>\n"
            f"Produit : {entry['label']} ({product_id})\nPaiement : {provider}",
        )


async def update_stripe_subscription(db, subscription_id: str, status: str) -> None:
    """Répercute l'état d'un abonnement Stripe de produit sur l'achat et sa clé."""
    if not subscription_id:
        return
    fields = {"status": "canceled" if status in _ENDED_STATUSES else status}
    purchase = await db.purchases.find_one({"stripe_subscription_id": subscription_id})
    if not purchase:
        return
    await db.purchases.update_one({"_id": purchase["_id"]}, {"$set": fields})
    if status in _ENDED_STATUSES and purchase.get("api_key_id"):
        await db["api_keys"].update_one(
            {"_id": purchase["api_key_id"]}, {"$set": {"active": False}}
        )


async def is_product_subscription(db, subscription_id: Optional[str]) -> bool:
    if not subscription_id:
        return False
    return await db.purchases.find_one({"stripe_subscription_id": subscription_id}) is not None
