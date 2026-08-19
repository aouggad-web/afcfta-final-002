"""
Service Chargily Pay — abonnements ZLECAf en Algérie (Phase 2)
=============================================================

Chargily Pay (v2) est la passerelle algérienne (CIB / Edahabia). Contrairement
à Stripe, elle facture en **DZD uniquement** et fonctionne par paiements
ponctuels : on crée un « checkout » hébergé et on réagit à un webhook signé
(HMAC-SHA256 du corps brut avec la clé secrète).

Comme pour Stripe, l'autorité sur les montants est **côté serveur** : les prix
en dinars proviennent de la grille unique `pricing.py` (une variable
d'environnement `CHARGILY_PRICE_<PLAN>_<M|Y>` peut surcharger un montant sans
redéploiement), jamais du navigateur.

La clé API est lue **au moment de l'appel** pour que les branches non-réseau
(Chargily désactivé, signature invalide) restent testables sans configuration.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time

import httpx
import pricing
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_DEFAULT_API_BASE = "https://pay.chargily.net/api/v2"
# Nombre total de tentatives réseau pour créer un checkout (1 essai + retries).
_CHECKOUT_ATTEMPTS = 3
# Délai de base du backoff exponentiel entre deux tentatives (secondes).
_CHECKOUT_BACKOFF = 0.5


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
    """Traduit (plan, cycle) en montant DZD via la grille unique `pricing.py`.

    400 si le couple est inconnu, 503 si une surcharge d'environnement est
    invalide ou sous le minimum Chargily. Contrairement à l'ancienne version,
    l'absence de surcharge n'échoue plus : on retombe sur le défaut revu.
    """
    try:
        return pricing.dzd_amount(plan, cycle)
    except pricing.UnknownPlanCycle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan/cycle inconnu : {plan}/{cycle}.",
        )
    except pricing.InvalidPrice as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


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
    url = f"{_api_base()}/checkouts"
    headers = {"Authorization": f"Bearer {key}"}

    # Retry uniquement les échecs transitoires (réseau + 5xx). Un 4xx est une
    # erreur définitive (montant/clé invalides) et ne doit jamais être rejoué.
    last_detail = "Chargily injoignable."
    for attempt in range(1, _CHECKOUT_ATTEMPTS + 1):
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=20)
        except httpx.HTTPError as exc:
            last_detail = f"Chargily injoignable : {exc}"
        else:
            if resp.status_code < 400:
                data = resp.json()
                checkout_url = data.get("checkout_url")
                if not checkout_url:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Réponse Chargily sans checkout_url.",
                    )
                return checkout_url
            if resp.status_code < 500:
                # Erreur cliente définitive : ne pas rejouer.
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Chargily a refusé la création du paiement ({resp.status_code}).",
                )
            last_detail = f"Chargily indisponible ({resp.status_code})."

        if attempt < _CHECKOUT_ATTEMPTS:
            logger.warning(
                "Chargily checkout: tentative %d/%d échouée (%s) — retry",
                attempt,
                _CHECKOUT_ATTEMPTS,
                last_detail,
            )
            time.sleep(_CHECKOUT_BACKOFF * (2 ** (attempt - 1)))

    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=last_detail)


def verify_and_parse(payload: bytes, signature_header: str | None) -> dict:
    """Vérifie la signature HMAC du webhook Chargily et retourne l'événement.

    Lève ValueError si la signature est absente/invalide ou le secret manquant —
    la route transforme cela en 400.
    """
    secret = os.environ.get("CHARGILY_WEBHOOK_SECRET") or os.environ.get("CHARGILY_SECRET_KEY")
    if not secret:
        raise ValueError(
            "Aucun secret de signature : renseignez CHARGILY_WEBHOOK_SECRET "
            "(ou à défaut CHARGILY_SECRET_KEY)."
        )
    if not signature_header:
        raise ValueError("En-tête signature manquant.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise ValueError("Signature webhook invalide.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Corps de webhook illisible : {exc}") from exc
