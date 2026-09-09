"""
Service Stripe — abonnements ZLECAf (Phase 1)
=============================================

Encapsule le SDK Stripe pour les abonnements. Aucune donnée de carte ne
transite par notre backend : on crée des sessions Stripe Checkout hébergées et
on réagit aux webhooks signés.

La clé API est lue **au moment de l'appel** (pas à l'import) pour que les routes
qui ne parlent pas à Stripe (branche Chargily 501, refus d'auth 401, signature
de webhook invalide) restent testables sans configuration.

Grille (source de vérité côté serveur) : les identifiants de prix `price_…`
proviennent des variables d'environnement `STRIPE_PRICE_<PLAN>_<M|Y>`, jamais du
navigateur. Le front n'envoie qu'un couple (plan, cycle) logique.
"""

from __future__ import annotations

import os

import stripe
from fastapi import HTTPException, status

# (plan, cycle) → nom de la variable d'environnement portant le price_id.
_PRICE_ENV = {
    ("starter", "monthly"): "STRIPE_PRICE_STARTER_M",
    ("starter", "annual"): "STRIPE_PRICE_STARTER_Y",
    ("pro", "monthly"): "STRIPE_PRICE_PRO_M",
    ("pro", "annual"): "STRIPE_PRICE_PRO_Y",
    ("business", "monthly"): "STRIPE_PRICE_BUSINESS_M",
    ("business", "annual"): "STRIPE_PRICE_BUSINESS_Y",
}


def _require_api_key() -> None:
    """Positionne stripe.api_key depuis l'environnement, ou 503 si absente."""
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paiement indisponible (STRIPE_SECRET_KEY non configurée).",
        )
    stripe.api_key = key


def resolve_price_id(plan: str, cycle: str) -> str:
    """Traduit (plan, cycle) en price_id Stripe via l'environnement.

    400 si le couple est inconnu, 503 si la variable d'env n'est pas renseignée.
    """
    env_name = _PRICE_ENV.get((plan, cycle))
    if env_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan/cycle inconnu : {plan}/{cycle}.",
        )
    price_id = os.environ.get(env_name)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tarif non configuré ({env_name}).",
        )
    return price_id


def get_or_create_customer(email: str, name: str, existing_id: str | None) -> str:
    """Retourne l'id du Customer Stripe, en le créant si nécessaire.

    Appel bloquant : à exécuter via run_in_threadpool depuis une route async.
    """
    _require_api_key()
    if existing_id:
        return existing_id
    customer = stripe.Customer.create(
        email=email,
        name=name or None,
        metadata={"app": "zlecaf"},
    )
    return customer.id


def create_checkout_session(
    *,
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    client_reference_id: str,
    metadata: dict,
) -> str:
    """Crée une Checkout Session d'abonnement et retourne son URL hébergée."""
    _require_api_key()
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=client_reference_id,
        subscription_data={"metadata": metadata},
        metadata=metadata,
        allow_promotion_codes=True,
    )
    return session.url


def create_portal_session(*, customer_id: str, return_url: str) -> str:
    """Crée une session du Customer Portal (gérer/annuler l'abonnement)."""
    _require_api_key()
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def construct_event(payload: bytes, sig_header: str | None):
    """Vérifie la signature du webhook et retourne l'événement Stripe.

    Lève ValueError si la signature est absente/invalide ou le secret manquant —
    la route transforme cela en 400.
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET non configurée.")
    if not sig_header:
        raise ValueError("En-tête Stripe-Signature manquant.")
    try:
        return stripe.Webhook.construct_event(payload, sig_header, secret)
    except stripe.error.SignatureVerificationError as exc:  # type: ignore[attr-defined]
        raise ValueError(f"Signature webhook invalide : {exc}") from exc
