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
tout le reste vers Stripe (EUR). Si Chargily n'est pas activé
(`CHARGILY_ENABLED`), la branche algérienne répond 501.
"""

from __future__ import annotations

import ipaddress
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import pricing
from bson import ObjectId
from entitlements import all_tier_entitlements
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from services import chargily_service, geo_service, stripe_service
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
    # Retour post-paiement : par défaut on renvoie sur pricing.html avec un
    # marqueur, plutôt que sur des routes /merci /tarifs qui n'existent pas
    # côté frontend (SPA sans routage par URL → 404 au rafraîchissement).
    # Un paramètre de requête fonctionne toujours et laisse la page afficher
    # le bon message d'état.
    return os.environ.get(
        "BILLING_SUCCESS_URL",
        "https://afcfta-zlecaf.com/pricing.html?checkout=success",
    )


def _cancel_url() -> str:
    return os.environ.get(
        "BILLING_CANCEL_URL",
        "https://afcfta-zlecaf.com/pricing.html?checkout=cancel",
    )


class CheckoutPayload(BaseModel):
    plan: Literal["starter", "pro", "business"]
    cycle: Literal["monthly", "annual"] = "monthly"
    billing_country: Optional[str] = None  # ISO-2 ; "DZ" → Chargily (Phase 2)


def resolve_provider(request: Request, user: dict, declared_country: Optional[str]) -> dict:
    """Décide du prestataire de paiement et dit si le choix est verrouillé.

    Règle : une IP détectée en Algérie impose Chargily (contrôle des changes),
    quel que soit le pays déclaré par le navigateur — la valeur envoyée par le
    client n'est qu'une préférence, jamais une autorité.

    Dérogation : `billing_stripe_exemption: true` sur le document utilisateur
    (posée manuellement par le support) rend la main à l'utilisateur, pour les
    cas légitimes — Algérien en déplacement, expatrié, VPN d'entreprise.

    Si le pays n'est pas détectable (aucune source géo configurée, IP privée),
    on retombe sur le choix explicite de l'utilisateur plutôt que de bloquer.
    """
    detected = geo_service.country_from_request(request)
    declared = (declared_country or "").strip().upper() or None
    exempt = bool(user.get("billing_stripe_exemption"))

    if detected == "DZ" and not exempt:
        return {"provider": "chargily", "country": "DZ", "locked": True, "detected": detected}
    if declared == "DZ":
        return {"provider": "chargily", "country": "DZ", "locked": False, "detected": detected}
    return {
        "provider": "stripe",
        "country": declared or detected,
        "locked": False,
        "detected": detected,
    }


@router.get("/geo-diagnostic")
async def geo_diagnostic(request: Request):
    """Diagnostic de la détection de pays, vu du backend.

    Répond à la question « que laisse passer l'ingress de l'hébergeur ? » sans
    attendre le support : appelez cette route depuis l'extérieur et lisez ce que
    le backend voit réellement. Ne révèle que des informations sur la requête de
    l'appelant lui-même.
    """
    xff = request.headers.get("x-forwarded-for", "")

    # L'adresse vue par la couche ASGI est une IP d'infrastructure (pod, ingress).
    # Seul son *caractère* privé/public a une valeur de diagnostic — savoir si la
    # couche réseau voit un hop interne plutôt que le client. On expose donc ce
    # booléen et jamais l'adresse elle-même, qui renseignerait sur la topologie.
    asgi_host = request.client.host if request.client else None
    asgi_is_private = None
    if asgi_host:
        try:
            asgi_is_private = ipaddress.ip_address(asgi_host).is_private
        except ValueError:
            asgi_is_private = None

    return {
        "client_ip": geo_service.client_ip(request),
        "detected_country": geo_service.country_from_request(request),
        "cloudflare_trusted": geo_service.cloudflare_is_trusted(request),
        "geoip_db_configured": bool(os.environ.get("GEOIP_DB_PATH")),
        # Relais de confiance pris en compte pour extraire l'IP du visiteur.
        # Si `client_ip` ci-dessus ne correspond pas à votre adresse publique
        # réelle, ajustez TRUSTED_PROXY_HOPS et rappelez cette route.
        "trusted_proxy_hops": geo_service.trusted_proxy_hops(),
        "headers_seen": {
            "cf_ipcountry": request.headers.get("cf-ipcountry") is not None,
            "cf_connecting_ip": request.headers.get("cf-connecting-ip") is not None,
            "x_edge_secret": request.headers.get("x-edge-secret") is not None,
            "x_forwarded_for_hops": len([h for h in xff.split(",") if h.strip()]),
        },
        "asgi_client_is_private": asgi_is_private,
    }


@router.get("/pricing")
async def get_pricing():
    """Grille tarifaire publique (source unique `pricing.py`).

    Permet à la page de tarifs de consommer les prix EUR/DZD au lieu de les
    coder en dur, ce qui garantit qu'affichage, Stripe et Chargily restent
    cohérents. Aucune authentification : les prix sont publics.
    """
    return {
        "currencies": {"stripe": "EUR", "chargily": "DZD"},
        "plans": pricing.grid(),
    }


@router.get("/entitlements")
async def get_entitlements():
    """Ce que chaque formule débloque réellement (source unique `entitlements.py`).

    Permet à la page de tarifs de générer sa liste de fonctionnalités à partir
    du même modèle que celui qui gate les routes côté backend
    (`entitlement_guard.require_module`), au lieu d'une liste HTML codée en
    dur qui pourrait diverger. Aucune authentification : ce sont les règles
    des formules, pas les droits d'un utilisateur précis — le tier "free"
    inclus ici est celui d'un visiteur non connecté.
    """
    return {
        tier: {
            "daily_calculations": ent.daily_calculations,
            "monthly_country_profiles": ent.monthly_country_profiles,
            "export_formats": list(ent.export_formats),
            "api_access": ent.api_access,
            "api_monthly_quota": ent.api_monthly_quota,
            "seats_included": ent.seats_included,
            "modules": {
                module_id: {
                    "enabled": access.enabled,
                    "quota": access.quota,
                    "quota_period": access.quota_period,
                }
                for module_id, access in ent.modules.items()
            },
        }
        for tier, ent in all_tier_entitlements().items()
    }


@router.get("/payment-context")
async def payment_context(request: Request):
    """Contexte de paiement pour l'interface : prestataire imposé ou non.

    Permet au front de pré-sélectionner — et de verrouiller — le bon moyen de
    paiement avant même que l'utilisateur clique.
    """
    user = {}
    try:
        user = await get_current_user(request)
    except HTTPException:
        pass  # Visiteur non connecté : on renvoie quand même le contexte géo.
    ctx = resolve_provider(request, user, None)
    return {
        "provider": ctx["provider"],
        "country": ctx["country"],
        "locked": ctx["locked"],
        "currency": "DZD" if ctx["provider"] == "chargily" else "EUR",
    }


@router.post("/checkout")
async def create_checkout(payload: CheckoutPayload, request: Request):
    """Crée un paiement pour l'utilisateur connecté (Stripe ou Chargily)."""
    db = _require_db()
    user = await get_current_user(request)

    ctx = resolve_provider(request, user, payload.billing_country)
    signals = geo_service.collect_signals(request, user)
    logger.info(
        "Checkout: user=%s plan=%s provider=%s locked=%s detected=%s mismatch=%s",
        user.get("_id"),
        payload.plan,
        ctx["provider"],
        ctx["locked"],
        signals.get("detected_country"),
        signals.get("country_mismatch"),
    )

    if ctx["provider"] == "chargily":
        return await _checkout_chargily(db, user, payload, signals)

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
    await _record_attempt(db, user, payload, "stripe", signals)
    return {"url": checkout_url}


async def _record_attempt(db, user, payload, provider: str, signals: dict) -> None:
    """Trace la tentative de paiement et ses signaux géo, pour audit.

    Best-effort : une écriture d'audit ne doit jamais faire échouer un paiement.
    Les IP sont des données personnelles — prévoir une purge périodique de cette
    collection selon votre politique de rétention.
    """
    try:
        await db.payment_attempts.insert_one(
            {
                "user_id": user.get("_id"),
                "plan": payload.plan,
                "cycle": payload.cycle,
                "provider": provider,
                "declared_country": (payload.billing_country or "").strip().upper() or None,
                "created_at": datetime.now(timezone.utc),
                **signals,
            }
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Audit tentative de paiement non enregistré: %s", exc)


async def _checkout_chargily(db, user, payload: "CheckoutPayload", signals: dict):
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
    # Aucune écriture sur le document utilisateur ici : tant que le paiement
    # n'est pas confirmé, rien n'est acquis. `payment_provider` et
    # `billing_country` sont posés par le webhook sur `checkout.paid`, comme
    # côté Stripe. La tentative reste tracée dans `payment_attempts`.
    await _record_attempt(db, user, payload, "chargily", signals)
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


# Libellés FR des formules, pour le corps des emails transactionnels
# uniquement — la page pricing (frontend) a sa propre source pour l'affichage.
_PLAN_LABELS = {"starter": "Starter", "pro": "Pro", "business": "Business"}
_CYCLE_LABELS = {"monthly": "mensuel", "annual": "annuel"}


def _plan_label(plan: Optional[str]) -> str:
    return _PLAN_LABELS.get(plan or "", plan or "votre formule")


def _amount_line(plan: Optional[str], cycle: Optional[str], *, currency: str) -> str:
    """Ligne de montant pour le corps d'un email, à partir de la grille
    tarifaire serveur (`pricing.py`) plutôt que du payload webhook — évite de
    dépendre de champs qui varient selon le fournisseur/la version d'API et
    reste garanti cohérent avec ce qui a été facturé au checkout."""
    if plan not in pricing.PLANS or cycle not in pricing.CYCLES:
        return ""
    try:
        if currency == "eur":
            return f"Montant : {pricing.eur_amount(plan, cycle)} €"
        return f"Montant : {pricing.dzd_amount(plan, cycle)} DZD"
    except (pricing.UnknownPlanCycle, pricing.InvalidPrice):
        return ""


def _period_end_line(period_end: Optional[datetime]) -> str:
    if not period_end:
        return ""
    return f"Prochaine échéance : {period_end.strftime('%d/%m/%Y')}"


async def _send_email_best_effort(email: Optional[str], subject: str, body: str) -> None:
    """Envoi best-effort : ne bloque jamais le traitement du webhook."""
    if not email:
        return
    try:
        await run_in_threadpool(send_email, email, subject, body)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Webhook: envoi email échoué: %s", exc)


async def _email_user(user_id: Optional[str], subject: str, body: str) -> None:
    if not user_id:
        return
    db = _require_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)}, {"email": 1})
    except Exception:
        return
    if user:
        await _send_email_best_effort(user.get("email"), subject, body)


async def _user_by_customer(customer_id: str) -> Optional[dict]:
    """Récupère le document utilisateur AVANT que le webhook ne le mette à
    jour — nécessaire pour que l'email d'échec/annulation puisse encore
    mentionner la formule que l'utilisateur est en train de perdre."""
    if not customer_id:
        return None
    db = _require_db()
    return await db.users.find_one(
        {"stripe_customer_id": customer_id},
        {"email": 1, "subscription_tier": 1, "subscription_cycle": 1},
    )


async def _claim_event(db, event_key: str, event_type: str) -> bool:
    """Réserve un événement pour traitement unique. False s'il est déjà pris.

    L'index unique sur `event_id` transforme deux livraisons concurrentes du même
    événement en une seule réservation gagnante — les autres reçoivent
    DuplicateKeyError et sont ignorées.
    """
    try:
        await db.payment_events.insert_one(
            {
                "event_id": event_key,
                "type": event_type,
                "received_at": datetime.now(timezone.utc),
            }
        )
        return True
    except DuplicateKeyError:
        return False


async def _release_event(db, event_key: str) -> None:
    """Annule la réservation d'un événement dont le traitement a échoué.

    Sans cela, un handler qui lève après la réservation marquerait l'événement
    « traité » à tort : le rejeu du fournisseur (livraison at-least-once)
    tomberait sur « déjà traité » et l'utilisateur qui a payé ne serait jamais
    activé. En libérant la réservation, on laisse le rejeu refaire le travail.
    """
    try:
        await db.payment_events.delete_one({"event_id": event_key})
    except Exception as exc:  # pragma: no cover - best effort
        logger.error(
            "CRITIQUE: réservation d'événement %s non libérée après échec (%s) — "
            "l'événement pourrait ne jamais être rejoué.",
            event_key,
            exc,
        )


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
    if not await _claim_event(db, event_id, event_type):
        return {"status": "already_processed"}

    # En cas d'échec du traitement, on libère la réservation pour que le rejeu
    # Stripe refasse le travail au lieu de le sauter en « déjà traité ».
    try:
        if event_type == "checkout.session.completed":
            meta = data_obj.get("metadata") or {}
            plan = meta.get("plan", "free")
            cycle = meta.get("cycle")
            await _update_user_by_id(
                meta.get("user_id", ""),
                {
                    "subscription_tier": plan,
                    "subscription_status": "active",
                    "subscription_cycle": cycle,
                    "subscription_id": data_obj.get("subscription"),
                    "stripe_customer_id": data_obj.get("customer"),
                    "payment_provider": "stripe",
                },
            )
            lines = [
                f"Merci — votre abonnement {_plan_label(plan)} "
                f"({_CYCLE_LABELS.get(cycle, cycle or '')}) est désormais actif.",
                _amount_line(plan, cycle, currency="eur"),
                "Vous pouvez le gérer à tout moment depuis votre tableau de bord.",
            ]
            await _email_user(
                meta.get("user_id"),
                "Votre abonnement ZLECAf est actif",
                "\n\n".join(line for line in lines if line),
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
            customer_id = data_obj.get("customer", "")
            user = await _user_by_customer(customer_id)
            await _update_user_by_customer(
                customer_id,
                {"subscription_tier": "free", "subscription_status": "canceled"},
            )
            if user:
                plan = user.get("subscription_tier")
                await _send_email_best_effort(
                    user.get("email"),
                    "Votre abonnement ZLECAf a été résilié",
                    f"Votre abonnement {_plan_label(plan)} a été résilié — vous repassez "
                    "à la formule Free. Vous pouvez vous réabonner à tout moment depuis "
                    "votre tableau de bord.",
                )

        elif event_type == "invoice.payment_failed":
            customer_id = data_obj.get("customer", "")
            user = await _user_by_customer(customer_id)
            await _update_user_by_customer(customer_id, {"subscription_status": "past_due"})
            if user:
                plan = user.get("subscription_tier")
                amount_cents = data_obj.get("amount_due")
                amount_line = (
                    f"Montant impayé : {amount_cents / 100:.2f} €"
                    if isinstance(amount_cents, (int, float))
                    else ""
                )
                lines = [
                    f"Le paiement de votre abonnement {_plan_label(plan)} a échoué.",
                    amount_line,
                    "Merci de mettre à jour votre moyen de paiement depuis votre tableau "
                    "de bord pour éviter une interruption d'accès.",
                ]
                await _send_email_best_effort(
                    user.get("email"),
                    "Échec du paiement de votre abonnement ZLECAf",
                    "\n\n".join(line for line in lines if line),
                )
    except Exception:
        await _release_event(db, event_id)
        raise

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

    # Événements Chargily préfixés pour ne jamais collisionner avec ceux de Stripe.
    event_key = f"chargily:{event_id}"
    if not await _claim_event(db, event_key, event_type):
        return {"status": "already_processed"}

    try:
        meta = data_obj.get("metadata") or {}
        # metadata peut revenir sous forme de liste selon la version de l'API.
        if isinstance(meta, list):
            meta = meta[0] if meta and isinstance(meta[0], dict) else {}
        user_id = meta.get("user_id", "")

        if event_type == "checkout.paid":
            plan = meta.get("plan", "free")
            cycle = meta.get("cycle")
            # Chargily n'a pas de notion d'abonnement récurrent (cf. docstring
            # ci-dessus) — un paiement ne couvre que la période réellement
            # achetée. Sans date de fin explicite, le resolver
            # d'entitlements.py traiterait une subscription_current_end
            # absente comme « toujours en cours » et accorderait un accès
            # payant permanent depuis un seul paiement.
            paid_days = 365 if cycle == "annual" else 30
            period_end = datetime.now(timezone.utc) + timedelta(days=paid_days)
            await _update_user_by_id(
                user_id,
                {
                    "subscription_tier": plan,
                    "subscription_status": "active",
                    "subscription_cycle": cycle,
                    "subscription_current_end": period_end,
                    "payment_provider": "chargily",
                    "billing_country": "DZ",
                },
            )
            lines = [
                f"Merci — votre paiement pour la formule {_plan_label(plan)} "
                f"({_CYCLE_LABELS.get(cycle, cycle or '')}) a été confirmé et votre "
                "abonnement est actif.",
                _amount_line(plan, cycle, currency="dzd"),
                _period_end_line(period_end),
            ]
            await _email_user(
                user_id,
                "Votre abonnement ZLECAf est actif",
                "\n\n".join(line for line in lines if line),
            )

        elif event_type in ("checkout.failed", "checkout.canceled", "checkout.expired"):
            # Aucun accès accordé : on journalise sans dégrader un abonnement actif.
            logger.info("Chargily: paiement non abouti (%s) pour user_id=%s", event_type, user_id)
            if event_type == "checkout.failed":
                await _email_user(
                    user_id,
                    "Échec de votre paiement ZLECAf",
                    "Votre paiement via Chargily n'a pas pu être confirmé. Aucun montant "
                    "n'a été prélevé pour cet abonnement — vous pouvez réessayer depuis "
                    "la page tarifs.",
                )
    except Exception:
        await _release_event(db, event_key)
        raise

    return {"status": "ok"}
