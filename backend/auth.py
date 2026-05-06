"""
AfCFTA API-key authentication
==============================
Two FastAPI dependencies are exported:
  require_auth  — any valid active key (standard or admin)
  require_admin — admin-tier keys only

Wire the database before first request:
    from auth import set_database
    set_database(db)
"""

import hashlib
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status


# ---------------------------------------------------------------------------
# Database handle (injected at startup via set_database)
# ---------------------------------------------------------------------------

_db = None


def set_database(database) -> None:
    global _db
    _db = database


def get_db():
    return _db


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

async def require_auth(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> dict:
    """Validate X-API-Key header; return the key document on success.
    
    When MongoDB is not configured (optional), all requests are allowed through
    with a public-tier context — tariff data is public information.
    """
    if _db is None:
        return {"tier": "public", "no_db": True}
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    doc = await _db["api_keys"].find_one(
        {"key_hash": _hash_key(x_api_key), "active": True}
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return doc


async def require_admin(
    key_doc: Annotated[dict, Depends(require_auth)],
) -> dict:
    """Require admin-tier API key."""
    if key_doc.get("tier") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin tier required",
        )
    return key_doc
