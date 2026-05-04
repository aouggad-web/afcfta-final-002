#!/usr/bin/env python3
"""
Migration: Create api_keys collection indexes
=============================================
Run once after deploying auth.py to ensure key lookups are fast and unique.

    python migrations/add_api_keys_indexes.py

Environment variables (same as the main app):
    MONGO_URL    / MONGODB_URI — MongoDB connection string
    DB_NAME      / MONGODB_DB  — database name (default: afcfta)
"""

import asyncio
import os
import sys


async def migrate() -> None:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except ImportError:
        print("ERROR: motor is not installed. Run: pip install motor", file=sys.stderr)
        sys.exit(1)

    uri = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME") or os.getenv("MONGODB_DB", "afcfta")

    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    print(f"Connected to MongoDB: {uri} / {db_name}")

    # Unique index on key_hash for O(1) lookups during auth
    await db["api_keys"].create_index("key_hash", unique=True)
    print("  [ok] api_keys.key_hash (unique)")

    # Compound index for admin dashboard listing by tier/status
    await db["api_keys"].create_index([("active", 1), ("tier", 1)])
    print("  [ok] api_keys.(active, tier)")

    # Ensure rate-limit counter docs are quickly accessible by _id
    await db["rate_limit_counters"].create_index("_id")
    print("  [ok] rate_limit_counters._id")

    client.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
