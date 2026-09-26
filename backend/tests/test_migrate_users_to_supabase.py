"""Tests du script de transfert des comptes vers Supabase (API Supabase simulée)."""

import importlib.util
import json
from pathlib import Path

import httpx

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_users_to_supabase.py"
_spec = importlib.util.spec_from_file_location("migrate_users_to_supabase", _SCRIPT)
migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migration)


class _Users:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query):
        return [d for d in self.docs if "supabase_id" not in d]

    def update_one(self, query, update):
        for d in self.docs:
            if d["_id"] == query["_id"]:
                d.update(update["$set"])


def _client(existing_emails=()):
    created = []

    def handler(request: httpx.Request):
        if request.method == "POST":
            body = json.loads(request.content)
            if body["email"] in existing_emails:
                return httpx.Response(422, json={"error_code": "email_exists"})
            created.append(body)
            return httpx.Response(200, json={"id": f"sb-{body['email']}"})
        users = [{"id": f"old-{e}", "email": e} for e in existing_emails]
        return httpx.Response(200, json={"users": users})

    client = httpx.Client(base_url="https://x.supabase.co", transport=httpx.MockTransport(handler))
    return client, created


def _docs():
    return [
        {"_id": 1, "email": "Alice@Example.com", "name": "Alice", "password_hash": "$2b$12$abc"},
        {"_id": 2, "email": "bob@example.com", "name": "Bob", "password_hash": "$2b$12$def"},
        {"_id": 3, "email": "deja@example.com", "supabase_id": "sb-deja"},
    ]


def test_dry_run_writes_nothing():
    docs = _docs()
    client, created = _client()
    stats = migration.migrate(_Users(docs), client, apply=False, require_confirmation=False)
    assert stats["a_transferer"] == 2
    assert not created and "supabase_id" not in docs[0]


def test_apply_imports_password_hash_and_links_accounts():
    docs = _docs()
    client, created = _client()
    stats = migration.migrate(_Users(docs), client, apply=True, require_confirmation=False)
    assert stats == {"a_transferer": 2, "crees": 2, "relies": 0, "erreurs": 0}
    assert created[0] == {
        "email": "alice@example.com",
        "email_confirm": True,
        "user_metadata": {"name": "Alice"},
        "password_hash": "$2b$12$abc",
    }
    assert docs[0]["supabase_id"] == "sb-alice@example.com"


def test_email_already_in_supabase_is_linked_not_duplicated():
    docs = _docs()
    client, created = _client(existing_emails=("bob@example.com",))
    stats = migration.migrate(_Users(docs), client, apply=True, require_confirmation=True)
    assert stats["relies"] == 1 and stats["crees"] == 1
    assert docs[1]["supabase_id"] == "old-bob@example.com"
    assert created[0]["email_confirm"] is False
