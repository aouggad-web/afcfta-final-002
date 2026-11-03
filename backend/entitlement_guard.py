"""FastAPI dependencies that enforce `entitlements.py` on real routes.

Bridges two systems that were previously disconnected:
  - the SaaS JWT session (`routes/user_auth.py`), which knows the caller's
    subscription tier
  - the X-API-Key system (`auth.py`), which currently gates the module
    routers (production, logistics, ...) but has no notion of a plan/tier

A caller with a valid JWT session is gated on their actual subscription tier.
A caller without one (API-key-only access, or no auth at all) is treated as
the "free" tier — `resolve_entitlements(None)` already resolves to free.

Appels sans session (audit E1) : les calculs sont comptés en mémoire par
visiteur (`require_calculations_quota`) ; l'API v2, le module Opportunités et
les exports de fichiers exigent une clé API valide (plans API vendus, clés
admin), déjà comptée par sa `request_quota` dans `auth.require_auth`.

Wire the database before first request, same pattern as `auth.py`/`billing.py`:
    from entitlement_guard import set_database
    set_database(db)
"""

from __future__ import annotations

import logging
from typing import Optional

from auth import require_auth
from bson import ObjectId
from bson.errors import InvalidId
from entitlements import Entitlements, ModuleAccess, resolve_entitlements
from fastapi import Depends, HTTPException, Request, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from services import geo_service, supabase_auth
from services.user_auth_service import decode_access_token

logger = logging.getLogger(__name__)

_db = None


def set_database(database) -> None:
    global _db
    _db = database


async def get_optional_subscriber(request: Request) -> Optional[dict]:
    """Best-effort resolution of the calling user from the JWT session cookie
    or bearer header. Never raises — an absent/invalid/expired token, a
    missing database, or an unknown user id all resolve to `None`, which
    `resolve_entitlements` treats as the free tier."""
    if _db is None:
        return None

    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None

    payload = decode_access_token(token)
    if payload:
        try:
            query = {"_id": ObjectId(payload["sub"])}
        except (InvalidId, TypeError, KeyError):
            return None
    else:
        # Session Supabase : le compte Mongo est relié par `supabase_id`.
        supabase_payload = supabase_auth.decode_token(token)
        if not supabase_payload:
            return None
        query = {"supabase_id": supabase_payload["sub"]}

    try:
        return await _db.users.find_one(query)
    except PyMongoError:
        # Motor connects lazily, so a Mongo outage first surfaces here
        # rather than at startup — this dependency promises never to
        # raise, so an unreachable database falls back to `None` (free
        # tier) rather than turning every session-cookie-bearing request
        # into an unstructured 500.
        return None


def _period_key(quota_period: str, user: dict) -> str:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    if quota_period == "day":
        return now.strftime("%Y-%m-%d")
    if quota_period == "month":
        return now.strftime("%Y-%m")
    # "cycle": the paid subscription period, keyed by its recorded end so a
    # renewal (new `subscription_current_end`) naturally starts a fresh
    # counter without any explicit reset job.
    end = user.get("subscription_current_end")
    return f"cycle:{end}"


async def check_and_increment_usage(user: dict, counter_id: str, access: ModuleAccess) -> bool:
    """Atomically increments the usage counter for (user, counter_id, current
    period) and returns whether the call is within quota. `access.quota is
    None` (unlimited) always returns True without touching the database.
    """
    if access.quota is None:
        return True
    if _db is None:
        # No database to count against. This is an operational outage, not
        # a subscriber hitting their cap — raising here (rather than
        # returning False, which callers turn into a 429 "quota_exceeded")
        # keeps the HTTP status and message honest about the actual cause,
        # so it doesn't get debugged as a billing/quota issue.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "entitlements_unavailable",
                "message": "Vérification des quotas indisponible (base de données non configurée).",
            },
        )

    period_key = _period_key(access.quota_period, user)
    key = {"user_id": user["_id"], "counter_id": counter_id, "period_key": period_key}

    # Two attempts: the second only runs if the first's insert_one lost a
    # first-of-the-period race (see below) — never because a real quota
    # denial should be retried.
    for _attempt in range(2):
        # Atomic "increment only if still under quota": the filter re-checks
        # `count < quota` as part of the same update, so concurrent requests
        # can't both read a stale count and both succeed past the limit.
        updated = await _db.usage_counters.find_one_and_update(
            {**key, "count": {"$lt": access.quota}},
            {"$inc": {"count": 1}},
            return_document=ReturnDocument.AFTER,
        )
        if updated is not None:
            return True

        # No document matched the filter above — either this is the first
        # call of the period (no document yet) or the quota is already
        # exhausted (document exists with count >= quota). These two cases
        # must NOT be conflated: unconditionally upserting here would let
        # every call past the quota re-create/no-op the same maxed-out
        # document and always return True, defeating the cap entirely. The
        # unique index on (user_id, counter_id, period_key) makes the
        # insert itself the atomic "does it already exist" check.
        try:
            await _db.usage_counters.insert_one({**key, "count": 1})
            return True
        except DuplicateKeyError:
            # Ambiguous: either the quota was genuinely already exhausted
            # (correctly deny), or another concurrent request created the
            # counter first — meaning THIS request's find_one_and_update
            # above ran too early (against a not-yet-existing document) and
            # was never actually checked against the now-real count. With a
            # quota > 1 the latter case still has room and must not be
            # denied as a false first-of-the-period 429, so loop once more
            # to re-run the conditional increment against the document that
            # now exists — this second find_one_and_update is the real
            # quota check for this request.
            continue

    return False


def _forbidden(tier: str, module_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "upgrade_required",
            "tier": tier,
            "module": module_id,
            "message": (
                f"Ce module n'est pas inclus dans la formule '{tier}'. "
                "Passez à une formule supérieure pour y accéder."
            ),
        },
    )


def _quota_exceeded(tier: str, module_id: str, access: ModuleAccess) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "quota_exceeded",
            "tier": tier,
            "module": module_id,
            "quota": access.quota,
            "quota_period": access.quota_period,
            "message": (
                f"Quota de la formule '{tier}' atteint ({access.quota}/"
                f"{access.quota_period}) pour ce module. Passez à une formule "
                "supérieure pour continuer."
            ),
        },
    )


def _cle_api(key_doc) -> bool:
    """Vrai pour un vrai document `api_keys` (plan API vendu ou clé admin), et
    non pour le contexte public que `require_auth` rend sans clé ou sans base."""
    return isinstance(key_doc, dict) and bool(key_doc.get("key_hash"))


def _reserve_aux_abonnements(module_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "upgrade_required",
            "tier": "anonymous",
            "module": module_id,
            "message": (
                "Ce module est réservé aux abonnements payants. Souscrivez un "
                "abonnement pour y accéder."
            ),
        },
    )


def require_module(module_id: str):
    """FastAPI dependency factory: gates a route on a subscriber's access to
    `module_id` per `entitlements.MODULES`, enforcing both the on/off switch
    and any usage quota for the resolved tier."""

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        access = ent.module(module_id)
        if not access.enabled:
            raise _forbidden(ent.tier, module_id)
        if access.quota is not None and user is not None:
            # Metering needs a stable identity to count against. An
            # unauthenticated caller (anonymous visitor, or an API-key-only
            # integration predating the SaaS accounts) has none — these
            # module routers were public/API-key-gated before entitlements
            # existed, so anonymous traffic keeps that prior behavior
            # (module on/off still enforced above, just not metered) rather
            # than being newly locked behind a login wall.
            ok = await check_and_increment_usage(user, module_id, access)
            if not ok:
                raise _quota_exceeded(ent.tier, module_id, access)
        return ent

    return _dependency


def require_paid_module(module_id: str, *, compter: bool = True):
    """`require_module` pour un module réservé aux abonnements payants (module
    Opportunités, « reports », refusé à la formule free — audit E1).

    Un abonné est traité par `require_module` (403 en free, quota sinon), ou,
    avec `compter=False`, par `require_module_enabled` (403 en free, sans
    décompte : écrans de consultation du même onglet, qui envoient beaucoup de
    requêtes). Un appel sans session est refusé (403 upgrade_required), sauf
    s'il porte une clé API valide, ou s'il n'y a pas de base (dev, workflow CI
    opportunites_module.yml) : le module reste alors ouvert comme avant."""

    module_dependency = (require_module if compter else require_module_enabled)(module_id)

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
        key_doc: dict = Depends(require_auth),
    ) -> Entitlements:
        if user is None:
            if _db is None or _cle_api(key_doc):
                return resolve_entitlements(None)
            raise _reserve_aux_abonnements(module_id)
        return await module_dependency(request=request, user=user)

    return _dependency


def require_module_enabled(module_id: str):
    """FastAPI dependency factory: gates a route on a subscriber's *access* to
    `module_id` (the tier on/off switch only), WITHOUT per-request metering.

    Use this for read-only reference/browse routers whose single UI view fans
    out to many GET requests (logistics ports + corridors + fees, statistics
    lookups, production tables, rules-of-origin chapters). Metering those
    per HTTP request — as `require_module` does — makes one screen load burn a
    whole day's/month's quota on the first visit (free logistics = 5/day, free
    stats = 20/month), so a signed-in free user gets "impossible to load"
    before doing anything. Quotas belong on genuine billable *actions* (one
    tariff calculation, one generated premium report), not on browsing
    reference data, so those still use the metered `require_module` /
    `require_calculations_quota`.

    The tier on/off switch is preserved: a module a tier does not grant at all
    (e.g. `tools` on free) still returns 403 here."""

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        access = ent.module(module_id)
        if not access.enabled:
            raise _forbidden(ent.tier, module_id)
        return ent

    return _dependency


def require_api_access():
    """FastAPI dependency for `Entitlements.api_access`/`api_monthly_quota`
    (currently only Business: unlocked, 1000 req/month) — a per-tier field,
    not a `MODULES` entry, same shape as `require_calculations_quota`.

    Gates the API v2 router for a signed-in SaaS subscriber (403 if their tier
    doesn't include API access, 429 past the monthly quota). Sans session
    (audit E1) : une clé API valide passe (plans API vendus, de tier « free »
    et sans session JWT, déjà comptés par leur `request_quota`) ; tout autre
    appel, base absente comprise, reçoit 403. FastAPI met `require_auth` en
    cache pour la requête : la clé n'est comptée qu'une fois, même avec le
    `_auth` du routeur.
    """

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
        key_doc: dict = Depends(require_auth),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        if user is None:
            if _cle_api(key_doc):
                return ent
            raise _forbidden(ent.tier, "api")
        if not ent.api_access:
            raise _forbidden(ent.tier, "api")
        if ent.api_monthly_quota is not None:
            access = ModuleAccess(enabled=True, quota=ent.api_monthly_quota, quota_period="month")
            ok = await check_and_increment_usage(user, "api", access)
            if not ok:
                raise _quota_exceeded(ent.tier, "api", access)
        return ent

    return _dependency


# Calculs des visiteurs sans session (audit E1) : comptés EN MÉMOIRE seulement,
# par clé de visiteur (`geo_service.cle_de_comptage` : IPv4, ou préfixe IPv6
# /64) et par jour UTC. Rien n'est écrit en base : aucune IP n'est conservée,
# comme le promet la politique de confidentialité. Le compteur est propre au
# processus : la production tourne avec un seul worker uvicorn (avec N workers,
# un visiteur aurait N fois le quota), et un redémarrage le remet à zéro.
_calculs_anonymes: dict[str, int] = {}
_jour_calculs_anonymes: Optional[str] = None
# Borne de la mémoire : au-delà, le visiteur le plus ancien est oublié. Tout
# vider rouvrirait le quota du jour pour tous dès qu'un client inonde le
# compteur de clés neuves.
_MAX_VISITEURS_ANONYMES = 100_000
_compteur_plein_signale = False


def _calcul_anonyme_autorise(cle: str, quota: int) -> bool:
    """Compte un calcul de `cle` pour aujourd'hui ; faux au-delà de `quota`.
    Sans `await` : sur la boucle asyncio, lecture et écriture ne s'entrelacent
    pas entre deux requêtes."""
    global _jour_calculs_anonymes, _compteur_plein_signale
    jour = _period_key("day", {})
    if jour != _jour_calculs_anonymes:
        _calculs_anonymes.clear()
        _jour_calculs_anonymes = jour
        _compteur_plein_signale = False
    elif len(_calculs_anonymes) >= _MAX_VISITEURS_ANONYMES and cle not in _calculs_anonymes:
        if not _compteur_plein_signale:  # une fois par jour, pas à chaque requête
            logger.warning(
                "Compteur des calculs anonymes plein (%d visiteurs) : les plus anciens sont oubliés.",
                len(_calculs_anonymes),
            )
            _compteur_plein_signale = True
        del _calculs_anonymes[next(iter(_calculs_anonymes))]
    compte = _calculs_anonymes.get(cle, 0)
    if compte >= quota:
        return False
    _calculs_anonymes[cle] = compte + 1
    return True


def _limite_anonyme_atteinte(quota: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "quota_exceeded",
            "tier": "anonymous",
            "module": "calculator",
            "quota": quota,
            "quota_period": "day",
            "message": (
                f"Limite de {quota} calculs par jour sans abonnement atteinte. "
                "Souscrivez un abonnement pour continuer."
            ),
        },
    )


def require_calculations_quota():
    """FastAPI dependency for the tariff calculator's `daily_calculations`
    limit — a per-tier field on `Entitlements`, not a `MODULES` entry.

    Sans session : le quota de la formule free, compté en mémoire par visiteur
    (voir `_calculs_anonymes`). Passent sans être comptés : une clé API valide
    (comptée par sa `request_quota`), l'absence de base (dev, CI) et un
    visiteur dont l'IP est inconnue (repli ouvert)."""

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
        key_doc: dict = Depends(require_auth),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        if user is None:
            if _db is None or _cle_api(key_doc):
                return ent
            if ent.daily_calculations is None:
                return ent
            cle = geo_service.cle_de_comptage(request)
            if cle is not None and not _calcul_anonyme_autorise(cle, ent.daily_calculations):
                raise _limite_anonyme_atteinte(ent.daily_calculations)
            return ent
        if ent.daily_calculations is None:
            return ent
        access = ModuleAccess(enabled=True, quota=ent.daily_calculations, quota_period="day")
        ok = await check_and_increment_usage(user, "calculator", access)
        if not ok:
            raise _quota_exceeded(ent.tier, "calculator", access)
        return ent

    return _dependency


def check_export_format(fmt: str, user: Optional[dict], key_doc) -> Entitlements:
    """Exige le format d'export `fmt` dans la formule (`export_formats`, audit
    E1) : 403 sinon. Un appel sans session passe avec une clé API valide ; sans
    clé, il est refusé comme la formule free (aucun format), base absente
    comprise."""
    ent = resolve_entitlements(user)
    if user is None and _cle_api(key_doc):
        return ent
    if fmt not in ent.export_formats:
        raise _forbidden(ent.tier, f"export_{fmt}")
    return ent


def require_export_format(fmt: str):
    """FastAPI dependency factory : `check_export_format` pour une route qui
    sert toujours le même format (`routers/export_router.py`)."""

    async def _dependency(
        user: Optional[dict] = Depends(get_optional_subscriber),
        key_doc: dict = Depends(require_auth),
    ) -> Entitlements:
        return check_export_format(fmt, user, key_doc)

    return _dependency
