"""
Service Chargily Pay — abonnements ZLECAf en Algérie (Phase 2)
=============================================================

Chargily Pay (v2) est la passerelle algérienne (CIB / Edahabia). Contrairement
à Stripe, elle facture en **DZD uniquement** et fonctionne par paiements
ponctuels : on crée un « checkout » hébergé et on réagit à un webhook signé
(HMAC-SHA256 du corps brut avec la clé secrète).

Comme pour Stripe, l'autorité sur les montants est **côté serveur** : les prix
en dinars proviennent des variables d'environnement `CHARGILY_PRICE_<PLAN>_<M|Y>`
(entiers en DZD), jamais du navigateur.

La clé API est lue **au moment de l'appel** pour que les branches non-réseau
(Chargily désactivé, signature invalide) restent testables sans configuration.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os

import httpx
from fastapi import HTTPException, status

# (plan, cycle) → variable d'environnement portant le montant en DZD (entier).
_PRICE_ENV = {
    ("starter", "monthly"): "CHARGILY_PRICE_STARTER_M",
    ("starter", "annual"): "CHARGILY_PRICE_STARTER_Y",
    ("pro", "monthly"): "CHARGILY_PRICE_PRO_M",
    ("pro", "annual"): "CHARGILY_PRICE_PRO_Y",
    ("business", "monthly"): "CHARGILY_PRICE_BUSINESS_M",
    ("business", "annual"): "CHARGILY_PRICE_BUSINESS_Y",
}

_DEFAULT_API_BASE = "https://pay.chargily.net/api/v2"


def is_enabled() -> bool:
    return os.environ.get("CHARGILY_ENABLED", "false").lower() == "true"


def _api_base() -> str:
    return os.environ.get("CHARGILY_API_BASE", _DEFAULT_API_BASE).rstrip("/")


def _secret_key() -> str:
    key = os.environ.get("CHARGILY_SECRET_KEY")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paiement local indisponible (CHARGILY_SECRET_KEY non configurée).",
        )
    return key


def resolve_amount_dzd(plan: str, cycle: str) -> int:
    """Traduit (plan, cycle) en montant DZD via l'environnement.

    400 si le couple est inconnu, 503 si la variable d'env manque ou est invalide.
    """
    env_name = _PRICE_ENV.get((plan, cycle))
    if env_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan/cycle inconnu : {plan}/{cycle}.",
        )
    raw = os.environ.get(env_name)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tarif local non configuré ({env_name}).",
        )
    try:
        amount = int(raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tarif local invalide ({env_name}={raw!r}).",
        )
    if amount < 75:  # minimum imposé par Chargily
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tarif local sous le minimum Chargily (75 DZD) : {env_name}.",
        )
    return amount


def create_checkout(
    *,
    amount_dzd: int,
    success_url: str,
    failure_url: str,
    description: str,
    metadata: dict,
) -> str:
    """Crée un checkout Chargily et retourne son URL hébergée.

    Appel bloquant : à exécuter via run_in_threadpool depuis une route async.
    """
    key = _secret_key()
    payload = {
        "amount": amount_dzd,
        "currency": "dzd",
        "success_url": success_url,
        "failure_url": failure_url,
        "description": description,
        "locale": "fr",
        "metadata": metadata,
    }
    try:
        resp = httpx.post(
            f"{_api_base()}/checkouts",
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Chargily injoignable : {exc}",
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Chargily a refusé la création du paiement ({resp.status_code}).",
        )
    data = resp.json()
    url = data.get("checkout_url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse Chargily sans checkout_url.",
        )
    return url


def verify_and_parse(payload: bytes, signature_header: str | None) -> dict:
    """Vérifie la signature HMAC du webhook Chargily et retourne l'événement.

    Lève ValueError si la signature est absente/invalide ou le secret manquant —
    la route transforme cela en 400.
    """
    secret = os.environ.get("CHARGILY_WEBHOOK_SECRET") or os.environ.get("CHARGILY_SECRET_KEY")
    if not secret:
        raise ValueError("CHARGILY_WEBHOOK_SECRET non configurée.")
    if not signature_header:
        raise ValueError("En-tête signature manquant.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise ValueError("Signature webhook invalide.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Corps de webhook illisible : {exc}") from exc
