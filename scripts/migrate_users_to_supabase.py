#!/usr/bin/env python3
"""
Transfert des comptes existants (MongoDB) vers Supabase Auth
============================================================

Pour chaque utilisateur Mongo sans `supabase_id` :
  1. crée l'utilisateur dans Supabase avec le MÊME mot de passe (le hachage
     bcrypt existant est importé tel quel : personne n'a à le réinitialiser) ;
  2. enregistre l'identifiant Supabase dans `users.supabase_id`.

Rien n'est supprimé de MongoDB : en cas de problème, l'ancien système de
connexion continue de fonctionner. Relancer le script ne crée pas de doublon
(les comptes déjà reliés sont ignorés, un email déjà présent dans Supabase est
simplement relié).

Variables d'environnement : MONGO_URL, DB_NAME (défaut « afcfta »),
SUPABASE_URL, SUPABASE_SECRET_KEY.

Usage :
  python scripts/migrate_users_to_supabase.py            # à blanc : n'écrit rien
  python scripts/migrate_users_to_supabase.py --apply    # transfert réel
  --require-confirmation : les comptes transférés devront confirmer leur email
                           (par défaut ils sont considérés confirmés)
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

_TIMEOUT = 20.0


def _admin_headers(secret_key: str) -> dict:
    headers = {"apikey": secret_key}
    if not secret_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {secret_key}"
    return headers


def _existing_supabase_ids(client: httpx.Client) -> dict:
    """email → id de tous les utilisateurs Supabase (pagination admin)."""
    ids, page = {}, 1
    while True:
        resp = client.get("/auth/v1/admin/users", params={"page": page, "per_page": 1000})
        resp.raise_for_status()
        users = resp.json().get("users", [])
        for user in users:
            if user.get("email"):
                ids[user["email"].lower()] = user["id"]
        if len(users) < 1000:
            return ids
        page += 1


def migrate(users, client: httpx.Client, *, apply: bool, require_confirmation: bool) -> dict:
    """Transfère les comptes. `users` : collection pymongo (ou équivalent)."""
    stats = {"a_transferer": 0, "crees": 0, "relies": 0, "erreurs": 0}
    known = None  # chargé seulement si un email existe déjà côté Supabase

    for doc in users.find({"supabase_id": {"$exists": False}}):
        email = (doc.get("email") or "").strip().lower()
        if not email:
            continue
        stats["a_transferer"] += 1
        if not apply:
            print(f"  [à blanc] {email}")
            continue

        body = {
            "email": email,
            "email_confirm": not require_confirmation,
            "user_metadata": {"name": doc.get("name", "")},
        }
        if str(doc.get("password_hash", "")).startswith("$2"):
            body["password_hash"] = doc["password_hash"]

        resp = client.post("/auth/v1/admin/users", json=body)
        if resp.status_code < 300:
            supabase_id = resp.json()["id"]
            stats["crees"] += 1
        elif resp.status_code == 422 and "email_exists" in resp.text:
            if known is None:
                known = _existing_supabase_ids(client)
            supabase_id = known.get(email)
            if not supabase_id:
                print(f"  ERREUR {email} : déjà présent dans Supabase mais introuvable")
                stats["erreurs"] += 1
                continue
            stats["relies"] += 1
        else:
            print(f"  ERREUR {email} : {resp.status_code} {resp.text[:200]}")
            stats["erreurs"] += 1
            continue

        users.update_one({"_id": doc["_id"]}, {"$set": {"supabase_id": supabase_id}})
        print(f"  OK {email} → {supabase_id}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--apply", action="store_true", help="effectuer le transfert")
    parser.add_argument("--require-confirmation", action="store_true")
    args = parser.parse_args()

    missing = [
        v for v in ("MONGO_URL", "SUPABASE_URL", "SUPABASE_SECRET_KEY") if not os.environ.get(v)
    ]
    if missing:
        print("Variables manquantes : " + ", ".join(missing))
        return 2

    from pymongo import MongoClient

    users = MongoClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "afcfta")]["users"]
    with httpx.Client(
        base_url=os.environ["SUPABASE_URL"].rstrip("/"),
        headers=_admin_headers(os.environ["SUPABASE_SECRET_KEY"]),
        timeout=_TIMEOUT,
    ) as client:
        print("Mode :", "TRANSFERT RÉEL" if args.apply else "à blanc (rien n'est écrit)")
        stats = migrate(
            users, client, apply=args.apply, require_confirmation=args.require_confirmation
        )
    print(
        f"\nComptes à transférer : {stats['a_transferer']} · créés : {stats['crees']} · "
        f"reliés : {stats['relies']} · erreurs : {stats['erreurs']}"
    )
    return 1 if stats["erreurs"] else 0


if __name__ == "__main__":
    sys.exit(main())
