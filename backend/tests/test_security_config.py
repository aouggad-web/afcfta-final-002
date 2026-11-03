"""Garde-fous des secrets au démarrage (constat E3 de l'audit de sécurité)."""

import asyncio
import logging

import pytest
from security_config import (
    est_valeur_exemple,
    imposer_jwt_secret,
    probleme_jwt_secret,
    probleme_mot_de_passe_admin,
)
from services.user_auth_service import hash_password, verify_password

SOLIDE = "Zx8-sentinelle-de-test-non-secrete-48-caracteres-!!"


@pytest.mark.parametrize(
    "valeur",
    [
        "your-jwt-secret-min-32-chars",
        "CHANGEZ-MOI-32-caracteres-minimum",
        "change-me-strong-password",
        "CHANGEZ-MOI-mot-de-passe-fort",
    ],
)
def test_les_valeurs_d_exemple_du_depot_sont_reconnues(valeur):
    assert est_valeur_exemple(valeur)


def test_jwt_secret():
    assert probleme_jwt_secret(None) is None  # absent : comptes déjà en 503
    assert probleme_jwt_secret(SOLIDE) is None
    assert "exemple" in probleme_jwt_secret("your-jwt-secret-min-32-chars")
    assert "trop court" in probleme_jwt_secret("a" * 31)


def test_mot_de_passe_admin():
    assert probleme_mot_de_passe_admin("Un-vrai-mot-de-passe-2026") is None
    assert "exemple" in probleme_mot_de_passe_admin("change-me-strong-password")
    assert "trop court" in probleme_mot_de_passe_admin("court")


def test_production_refuse_un_jwt_secret_faible():
    with pytest.raises(RuntimeError, match="JWT_SECRET refusé"):
        imposer_jwt_secret(
            {"APP_ENV": "production", "JWT_SECRET": "CHANGEZ-MOI-32-caracteres-minimum"}
        )
    imposer_jwt_secret({"APP_ENV": "production", "JWT_SECRET": SOLIDE})  # accepté


def test_production_signale_un_jwt_secret_court_sans_couper_le_service(caplog):
    with caplog.at_level(logging.CRITICAL):
        imposer_jwt_secret({"APP_ENV": "production", "JWT_SECRET": "a" * 20})
    assert "trop court" in caplog.text


def test_hors_production_un_jwt_secret_faible_est_signale_sans_bloquer(caplog):
    with caplog.at_level(logging.CRITICAL):
        imposer_jwt_secret({"JWT_SECRET": "court"})
    assert "JWT_SECRET refusé" in caplog.text


class _Users:
    def __init__(self, doc=None):
        self.doc = doc
        self.inserts = []

    async def find_one(self, query):
        return self.doc

    async def insert_one(self, doc):
        self.inserts.append(doc)

    async def update_one(self, query, update):
        self.doc = {**(self.doc or {}), **update["$set"]}


def _amorcer(monkeypatch, users, mot_de_passe):
    import server

    monkeypatch.setattr(server, "db", {"users": users})
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.invalid")
    monkeypatch.setenv("ADMIN_PASSWORD", mot_de_passe)
    asyncio.run(server._seed_admin_account())


def test_mot_de_passe_d_exemple_deja_en_service_verrouille_le_compte(monkeypatch):
    exemple = "change-me-strong-password"
    users = _Users({"email": "admin@example.invalid", "password_hash": hash_password(exemple)})
    _amorcer(monkeypatch, users, exemple)
    assert not verify_password(exemple, users.doc["password_hash"])  # plus de connexion possible


def test_mot_de_passe_d_exemple_n_amorce_pas_de_compte(monkeypatch):
    users = _Users(None)
    _amorcer(monkeypatch, users, "CHANGEZ-MOI-mot-de-passe-fort")
    assert users.inserts == []


def test_un_mot_de_passe_solide_deverrouille_le_compte(monkeypatch):
    nouveau = "Un-vrai-mot-de-passe-2026"
    users = _Users({"email": "admin@example.invalid", "password_hash": "!verrouille"})
    _amorcer(monkeypatch, users, nouveau)
    assert verify_password(nouveau, users.doc["password_hash"])


# ── Middlewares de sécurité obligatoires (constat M10) ──────────────────────


def test_server_installe_csp_csrf_et_limitation_de_debit():
    import server
    from middlewares import CSRFMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware

    installes = {m.cls for m in server.app.user_middleware}
    assert {SecurityHeadersMiddleware, CSRFMiddleware, RateLimitMiddleware} <= installes


def test_import_des_middlewares_n_est_pas_rattrape():
    """Un `try/except ImportError` autour de l'import laisserait démarrer l'API
    sans CSP, CSRF ni limitation de débit après un déploiement partiel."""
    import ast
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "server.py").read_text(encoding="utf-8")
    au_premier_niveau = [
        noeud
        for noeud in ast.parse(source).body
        if isinstance(noeud, ast.ImportFrom) and noeud.module == "middlewares"
    ]
    assert au_premier_niveau, "l'import des middlewares de sécurité doit rester obligatoire"
