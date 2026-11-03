"""Verrouillage après échecs de connexion, par appareil connu (constat M4 de
l'audit de sécurité).

Un navigateur qui s'est déjà connecté à un compte reçoit un cookie d'appareil
signé : ses échecs sont comptés à part et ne verrouillent que lui. Les autres
tentatives partagent le compteur du compte (5 échecs, 15 minutes). Aucune
adresse IP n'est utilisée ni conservée.
"""

import bcrypt
import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes import user_auth
from starlette.responses import Response

EMAIL = "victime@example.com"
BON = "Bon-mot-de-passe-2026"


class _Collection:
    """Collection Mongo minimale en mémoire (égalité simple)."""

    def __init__(self):
        self.docs = []

    def _trouve(self, query):
        return next((d for d in self.docs if all(d.get(k) == v for k, v in query.items())), None)

    async def find_one(self, query, projection=None):
        doc = self._trouve(query)
        return dict(doc) if doc else None

    async def find_one_and_update(self, query, update, upsert=False, return_document=None):
        doc = self._trouve(query)
        if doc is None and upsert:
            doc = {**query, **update.get("$setOnInsert", {})}
            self.docs.append(doc)
        for k, v in update.get("$inc", {}).items():
            doc[k] = doc.get(k, 0) + v
        return dict(doc)

    async def update_one(self, query, update):
        doc = self._trouve(query)
        if doc:
            doc.update(update.get("$set", {}))

    async def delete_one(self, query):
        doc = self._trouve(query)
        if doc:
            self.docs.remove(doc)


class _DB:
    def __init__(self):
        self.users = _Collection()
        self.login_attempts = _Collection()


def _compte(email):
    # bcrypt à coût minimal : seul le verrouillage est testé ici.
    empreinte = bcrypt.hashpw(BON.encode(), bcrypt.gensalt(4)).decode()
    return {
        "_id": ObjectId(),
        "email": email,
        "name": "V",
        "role": "user",
        "password_hash": empreinte,
    }


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "sentinelle-de-test-non-secrete-" + "x" * 32)
    base = _DB()
    base.users.docs.append(_compte(EMAIL))
    user_auth.set_database(base)
    yield base
    user_auth.set_database(None)


@pytest.fixture
def app(db):
    app = FastAPI()
    app.include_router(user_auth.router)
    return app


def _connexion(client, email=EMAIL, mot_de_passe=BON):
    return client.post("/auth/login", json={"email": email, "password": mot_de_passe})


def _echecs(client, n=5, email=EMAIL):
    return [_connexion(client, email, "faux").status_code for _ in range(n)]


def test_un_navigateur_connu_n_est_pas_verrouille_par_un_tiers(app):
    victime = TestClient(app)
    assert _connexion(victime).status_code == 200

    tiers = TestClient(app)
    assert _echecs(tiers) == [401] * 5
    assert _connexion(tiers).status_code == 429
    assert _connexion(victime).status_code == 200


def test_sans_cookie_appareil_cinq_echecs_verrouillent_meme_avec_le_bon_mot_de_passe(app):
    client = TestClient(app)
    assert _echecs(client) == [401] * 5
    reponse = _connexion(client)
    assert reponse.status_code == 429
    assert "15 minutes" in reponse.json()["detail"]


def test_un_navigateur_connu_ne_verrouille_que_lui_meme(app):
    connu = TestClient(app)
    assert _connexion(connu).status_code == 200
    assert _echecs(connu) == [401] * 5
    assert _connexion(connu).status_code == 429
    assert _connexion(TestClient(app)).status_code == 200


def test_cookie_appareil_d_un_autre_compte_est_ignore(app, db):
    db.users.docs.append(_compte("autre@example.com"))
    client = TestClient(app)
    assert _connexion(client, "autre@example.com").status_code == 200
    assert _echecs(client) == [401] * 5
    assert _connexion(TestClient(app)).status_code == 429


def test_cookie_appareil_falsifie_est_ignore(app):
    client = TestClient(app)
    client.cookies.set(user_auth.DEVICE_COOKIE, "nonce." + "0" * 64)
    assert _echecs(client) == [401] * 5
    assert _connexion(TestClient(app)).status_code == 429


def test_message_identique_que_le_compte_existe_ou_non(app):
    client = TestClient(app)
    inconnu = _connexion(client, "inconnu@example.com", "faux")
    connu = _connexion(client, EMAIL, "faux")
    assert (inconnu.status_code, inconnu.json()) == (connu.status_code, connu.json())

    _echecs(client, 4, "inconnu@example.com")
    _echecs(client, 4)
    verrou_inconnu = _connexion(client, "inconnu@example.com", "faux")
    verrou_connu = _connexion(client)
    assert verrou_inconnu.status_code == verrou_connu.status_code == 429
    assert verrou_inconnu.json() == verrou_connu.json()


def test_succes_remet_le_compteur_a_zero(app, db):
    client = TestClient(app)
    assert _echecs(client, 4) == [401] * 4
    assert _connexion(client).status_code == 200
    assert db.login_attempts.docs == []
    # Même chose sous le compteur de l'appareil, désormais connu.
    assert _echecs(client, 4) == [401] * 4
    assert _connexion(client).status_code == 200
    assert db.login_attempts.docs == []


def test_la_deconnexion_garde_le_cookie_appareil(app):
    victime = TestClient(app)
    assert _connexion(victime).status_code == 200
    deconnexion = victime.post("/auth/logout")
    assert not any(
        user_auth.DEVICE_COOKIE in entete for entete in deconnexion.headers.get_list("set-cookie")
    )
    assert _echecs(TestClient(app)) == [401] * 5
    assert _connexion(victime).status_code == 200


def test_sans_jwt_secret_le_cookie_appareil_est_ignore(app, db, monkeypatch):
    client = TestClient(app)
    assert _connexion(client).status_code == 200
    monkeypatch.setenv("JWT_SECRET", "")
    assert _echecs(client) == [401] * 5
    assert [d["identifier"] for d in db.login_attempts.docs] == [EMAIL]


@pytest.mark.parametrize("https", [True, False])
def test_cookie_appareil_memes_attributs_que_la_session(monkeypatch, https):
    monkeypatch.setenv("JWT_SECRET", "sentinelle-de-test-non-secrete-" + "x" * 32)
    monkeypatch.setattr(user_auth, "_COOKIE_SECURE", https)
    reponse = Response()
    user_auth._set_session_cookie(reponse, "jeton")
    user_auth._set_device_cookie(reponse, EMAIL)
    session, appareil = [v.decode() for k, v in reponse.raw_headers if k == b"set-cookie"]

    def attributs(entete):
        # Durée de vie mise à part : le cookie d'appareil survit à la session.
        return {a.strip().lower() for a in entete.split(";")[1:] if "max-age" not in a.lower()}

    assert appareil.startswith(f"{user_auth.DEVICE_COOKIE}=")
    assert attributs(appareil) == attributs(session)
    assert "httponly" in attributs(appareil)
    assert ("partitioned" in attributs(appareil)) is https
    assert EMAIL not in appareil
