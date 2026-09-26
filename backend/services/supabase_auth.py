"""
Supabase Auth — vérification des jetons et appels d'administration
==================================================================

Actif uniquement si `SUPABASE_URL` est renseignée ; sinon toutes les fonctions
se comportent comme si Supabase n'existait pas et l'ancien système de comptes
(`routes/user_auth.py`, JWT HS256 maison) reste seul en place.

- Les jetons d'accès Supabase sont signés par des clés asymétriques (ES256 /
  RS256) publiées en JWKS par le projet : aucun secret n'est nécessaire pour
  les vérifier. Les clés sont mises en cache (rotation rare).
- Les appels d'administration (lire un utilisateur, le supprimer) exigent
  `SUPABASE_SECRET_KEY`, qui ne doit exister que côté serveur.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
import jwt

logger = logging.getLogger(__name__)

_JWKS_LIFESPAN_SECONDS = 6 * 3600
_ADMIN_TIMEOUT = 10.0

_jwk_client: Optional[jwt.PyJWKClient] = None
_jwk_url: Optional[str] = None


def is_enabled() -> bool:
    return bool(os.environ.get("SUPABASE_URL"))


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/")


def _jwks() -> jwt.PyJWKClient:
    global _jwk_client, _jwk_url
    url = f"{_base_url()}/auth/v1/.well-known/jwks.json"
    if _jwk_client is None or _jwk_url != url:
        _jwk_client = jwt.PyJWKClient(url, cache_jwk_set=True, lifespan=_JWKS_LIFESPAN_SECONDS)
        _jwk_url = url
    return _jwk_client


def decode_token(token: str) -> Optional[dict]:
    """Payload d'un jeton d'accès Supabase valide, ou None.

    Ne lève jamais : un jeton invalide, expiré, d'un autre projet ou un
    ancien jeton maison (HS256) donne simplement None.
    """
    if not is_enabled() or not token:
        return None
    try:
        algorithm = jwt.get_unverified_header(token).get("alg")
    except jwt.PyJWTError:
        return None
    if algorithm not in ("ES256", "RS256"):
        # Nos anciens jetons de session sont en HS256 : pas pour Supabase.
        return None
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=f"{_base_url()}/auth/v1",
        )
    except jwt.PyJWTError as exc:
        logger.debug("Jeton Supabase refusé: %s", type(exc).__name__)
        return None
    if not payload.get("sub") or not payload.get("email"):
        return None
    return payload


def _admin_headers() -> dict:
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SECRET_KEY non configurée")
    headers = {"apikey": key}
    # Les nouvelles clés secrètes (sb_secret_…) passent seulement par `apikey` ;
    # l'ancienne clé service_role est un JWT attendu aussi en Authorization.
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def get_admin_user(user_id: str) -> dict:
    """Fiche utilisateur côté Supabase (dont `email_confirmed_at`)."""
    async with httpx.AsyncClient(timeout=_ADMIN_TIMEOUT) as client:
        resp = await client.get(
            f"{_base_url()}/auth/v1/admin/users/{user_id}", headers=_admin_headers()
        )
    resp.raise_for_status()
    return resp.json()


async def delete_admin_user(user_id: str) -> None:
    async with httpx.AsyncClient(timeout=_ADMIN_TIMEOUT) as client:
        resp = await client.delete(
            f"{_base_url()}/auth/v1/admin/users/{user_id}", headers=_admin_headers()
        )
    if resp.status_code != 404:  # déjà supprimé : rien à faire
        resp.raise_for_status()
