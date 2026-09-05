"""
Admin API key management routes
POST   /api/admin/keys          — create a new key  (admin)
GET    /api/admin/keys          — list all keys      (admin)
DELETE /api/admin/keys/{key_id} — revoke a key       (admin)
GET    /api/admin/keys/verify   — verify current key (any valid key)
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Annotated, Optional

from auth import get_db, require_admin, require_auth, resolve_ai_quota
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/admin/keys", tags=["Admin: API Keys"])

VALID_TIERS = ("free", "basic", "pro", "admin", "standard")


class CreateKeyRequest(BaseModel):
    name: str
    owner: str
    tier: str = "free"
    monthly_quota: Optional[int] = None  # overrides the tier's default AI quota


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


@router.get("/verify")
async def verify_key(key_doc: Annotated[dict, Depends(require_auth)]):
    """Verify the calling key and return its metadata (hash excluded).

    Unlike plain data routes, this endpoint must not accept the public
    passthrough that require_auth grants when MongoDB is unconfigured or
    (under PUBLIC_DATA_ACCESS) when no key is supplied — verifying a key only
    makes sense for an actual key, so reject those contexts explicitly.
    """
    if key_doc.get("no_db"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication database is not configured",
        )
    if key_doc.get("tier") == "public":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    tier = key_doc.get("tier")
    return {
        "valid": True,
        "name": key_doc.get("name"),
        "owner": key_doc.get("owner"),
        "tier": tier,
        "created_at": key_doc.get("created_at"),
        "ai_monthly_quota": resolve_ai_quota(tier, key_doc.get("monthly_quota")),
        "ai_usage_this_period": key_doc.get("usage_count", 0),
        "ai_usage_period": key_doc.get("usage_period"),
    }


@router.get("")
async def list_keys(key_doc: Annotated[dict, Depends(require_admin)]):
    """List all API keys (hash excluded)."""
    db = get_db()
    cursor = db["api_keys"].find({}, {"key_hash": 0})
    keys = await cursor.to_list(length=None)
    for k in keys:
        k["id"] = str(k.pop("_id"))
    return {"keys": keys, "count": len(keys)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_key(
    body: CreateKeyRequest,
    key_doc: dict = Depends(require_admin),
):
    """Create a new API key. The raw key is returned once; store it safely."""
    if body.tier not in VALID_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tier must be one of: {', '.join(VALID_TIERS)}",
        )
    db = get_db()
    raw_key = "afcfta_" + secrets.token_urlsafe(32)
    doc = {
        "key_hash": _hash_key(raw_key),
        "name": body.name,
        "owner": body.owner,
        "tier": body.tier,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.monthly_quota is not None:
        doc["monthly_quota"] = body.monthly_quota
    await db["api_keys"].insert_one(doc)
    return {
        "raw_key": raw_key,
        "name": body.name,
        "owner": body.owner,
        "tier": body.tier,
        "ai_monthly_quota": resolve_ai_quota(body.tier, body.monthly_quota),
        "note": "Store this key securely — it will not be shown again.",
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    key_doc: dict = Depends(require_admin),
):
    """Soft-delete (deactivate) an API key by its MongoDB ObjectId."""
    db = get_db()
    try:
        oid = ObjectId(key_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid key_id format",
        )
    result = await db["api_keys"].update_one({"_id": oid}, {"$set": {"active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
