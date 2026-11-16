"""Accès sans abonnement (audit E1, décision de l'exploitant du 09/11/2026).

- Sans compte : seul le tableau de bord d'accueil est consultable ; calculs
  et modules de consultation renvoient 401 « login_required ».
- Compte sans abonnement (formule free, e-mail validé) : 2 calculs par mois,
  5 recherches distinctes par module de consultation et par mois.
- /api/reports/* (module Opportunités) : réservé aux abonnements payants ;
  les diagnostics /reports/health et /reports/oec-health restent publics.
- /api/v2/* : refusé sans clé API valide.
- Exports de fichiers (décision de l'exploitant du 06/11/2026) : le PDF est
  accordé à toutes les formules ; CSV et Excel ne le sont à aucune, réservés au
  compte admin connecté.

Une clé API valide (plans API vendus, clés admin) garde l'accès sans session,
sauf aux exports CSV et Excel : aucune clé n'y passe, même admin.
Sans base (dev, CI), calculs et rapports restent ouverts ; l'API v2 et les
exports de fichiers, non.

Hermétique : base Mongo en mémoire, vrai routeur `/api` (routes.register_routes)
ou sonde montée avec les mêmes dépendances que la production.
"""

import asyncio
import hashlib
import io
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import auth  # noqa: E402
import entitlement_guard  # noqa: E402
import routes  # noqa: E402
from routers import export_router  # noqa: E402
from routes import user_auth  # noqa: E402
from services.user_auth_service import create_access_token  # noqa: E402

from backend.tests.routes_effectives import routes_api  # noqa: E402

CLE_VENDUE = "cle-plan-api-vendu"
CLE_ADMIN = "cle-admin"


def _hash(cle):
    return hashlib.sha256(cle.encode()).hexdigest()


class _Compteurs:
    """usage_counters : find_one_and_update avec `$lt`, insert_one unique."""

    def __init__(self):
        self.docs = {}

    @staticmethod
    def _cle(doc):
        return (str(doc["user_id"]), doc["counter_id"], doc["period_key"])

    async def find_one_and_update(self, filtre, maj, return_document=None):
        doc = self.docs.get(self._cle(filtre))
        if doc is None or doc["count"] >= filtre["count"]["$lt"]:
            return None
        doc["count"] += maj["$inc"]["count"]
        return dict(doc)

    async def insert_one(self, doc):
        if self._cle(doc) in self.docs:
            raise DuplicateKeyError("doublon")
        self.docs[self._cle(doc)] = dict(doc)


class _Utilisateurs:
    def __init__(self, utilisateurs):
        self._par_id = {u["_id"]: u for u in utilisateurs}

    async def find_one(self, filtre):
        return self._par_id.get(filtre.get("_id"))


class _ClesApi:
    """api_keys : recherche par empreinte, comptage `request_quota`."""

    def __init__(self, docs):
        self.docs = {d["key_hash"]: d for d in docs}

    async def find_one(self, filtre):
        doc = self.docs.get(filtre["key_hash"])
        return dict(doc) if doc and doc["active"] == filtre["active"] else None

    async def find_one_and_update(self, filtre, maj, return_document=None):
        for doc in self.docs.values():
            if doc["_id"] != filtre["_id"]:
                continue
            if "request_period" in filtre and doc.get("request_period") != filtre["request_period"]:
                return None
            for champ, n in maj.get("$inc", {}).items():
                doc[champ] = doc.get(champ, 0) + n
            doc.update(maj.get("$set", {}))
            return dict(doc)
        return None


class _Douane:
    """customs_data, pour les exports de routers/export_router.py."""

    DOC = {
        "country_code": "KE",
        "imported_at": "2026-01-01",
        "tariffs": {"tariff_lines": [{"hs_code": "010110", "customs_duty": "10%", "vat": "16%"}]},
    }

    async def find_one(self, filtre, sort=None):
        return dict(self.DOC, country_code=filtre["country_code"])

    def find(self, filtre):
        return self

    def sort(self, *a, **k):
        return self

    async def to_list(self, length=None):
        return [dict(self.DOC)]


class _Recherches:
    """recherches_modules : un document par (compte, module, mois)."""

    def __init__(self):
        self.docs = {}

    async def find_one(self, filtre):
        await asyncio.sleep(0)  # laisse passer les requêtes simultanées
        doc = self.docs.get(filtre["_id"])
        return dict(doc) if doc else None

    async def insert_one(self, doc):
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("doublon")
        self.docs[doc["_id"]] = {**doc, "termes": list(doc["termes"])}

    async def update_one(self, filtre, maj):
        doc = self.docs.get(filtre["_id"])
        if doc is None or doc["termes"] != filtre["termes"]:
            return SimpleNamespace(matched_count=0)
        doc["termes"].extend(maj["$push"]["termes"]["$each"])
        return SimpleNamespace(matched_count=1)


class _FausseBase:
    def __init__(self, utilisateurs=()):
        self.users = _Utilisateurs(utilisateurs)
        self.usage_counters = _Compteurs()
        self.api_keys = _ClesApi(
            [
                {
                    "_id": ObjectId(),
                    "key_hash": _hash(CLE_VENDUE),
                    "tier": "free",
                    "active": True,
                    "request_quota": 5000,
                },
                {"_id": ObjectId(), "key_hash": _hash(CLE_ADMIN), "tier": "admin", "active": True},
            ]
        )
        self.customs_data = _Douane()
        self.recherches_modules = _Recherches()

    def __getitem__(self, nom):
        return getattr(self, nom)


def _abonne(formule):
    return {
        "_id": ObjectId(),
        "email": f"{formule}@exemple.invalid",
        "subscription_tier": formule,
        "subscription_status": "active",
    }


ABONNES = {formule: _abonne(formule) for formule in ("free", "starter", "pro", "business")}
# Compte admin amorcé (server.py) : rôle admin, aucune formule.
ADMIN = {"_id": ObjectId(), "email": "admin@exemple.invalid", "role": "admin"}


@pytest.fixture(autouse=True)
def base(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secret-de-test")
    # L'IP du visiteur est l'adresse du pair (voir _client) : aucun relais ni
    # en-tête Cloudflare à croire.
    for nom in ("TRUSTED_PROXY_CIDRS", "TRUST_CLOUDFLARE_HEADERS", "CLOUDFLARE_EDGE_SECRET"):
        monkeypatch.delenv(nom, raising=False)
    db = _FausseBase([*ABONNES.values(), ADMIN])
    auth.set_database(db)
    entitlement_guard.set_database(db)
    export_router.init_db(db)
    yield db
    auth.set_database(None)
    entitlement_guard.set_database(None)
    export_router.init_db(None)


@pytest.fixture(scope="module")
def app_api():
    """Le vrai routeur /api, composé comme dans server.py (sans middlewares)."""
    api = APIRouter(prefix="/api")
    routes.register_routes(api)
    app = FastAPI()
    app.include_router(api)
    return app


def _app_calcul():
    """Sonde montée avec les dépendances du vrai POST /api/calcul."""
    sonde = APIRouter()

    @sonde.post("/calcul")
    async def calcul():
        return {"ok": True}

    api = APIRouter(prefix="/api")
    api.include_router(sonde, dependencies=routes._auth + routes._calculator_entitlement)
    app = FastAPI()
    app.include_router(api)
    return app


def _client(app, ip=None, abonne=None, cle=None):
    """Client HTTP ; `ip` est l'adresse du pair TCP vue par l'application."""
    if ip is not None:
        app_seule = app

        async def app(scope, receive, send):
            if scope["type"] == "http":
                scope = dict(scope, client=(ip, 40000))
            await app_seule(scope, receive, send)

    client = TestClient(app)
    if abonne is not None:
        client.cookies.set("access_token", create_access_token(str(abonne["_id"]), abonne["email"]))
    if cle is not None:
        client.headers["X-API-Key"] = cle
    return client


def _statuts(client, n, methode="post", chemin="/api/calcul"):
    return [getattr(client, methode)(chemin).status_code for _ in range(n)]


# ── Calculateur : aucun sans compte, 2 par mois sans abonnement ────────────


def test_calcul_sans_compte_demande_la_connexion():
    reponse = _client(_app_calcul(), ip="41.200.1.1").post("/api/calcul")

    assert reponse.status_code == 401
    detail = reponse.json()["detail"]
    assert detail["error"] == "login_required"
    assert detail["module"] == "calculator"


def test_calcul_sans_base_reste_ouvert():
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _statuts(_client(_app_calcul(), ip="41.200.1.1"), 3) == [200] * 3


def test_calcul_cle_api_valide_passe_sans_compte(base):
    client = _client(_app_calcul(), ip="41.200.1.1", cle=CLE_VENDUE)

    assert _statuts(client, 3) == [200] * 3
    assert base.api_keys.docs[_hash(CLE_VENDUE)]["request_count"] == 3


def test_calcul_compte_sans_abonnement_deux_par_mois_puis_invitation(base):
    client = _client(_app_calcul(), abonne=ABONNES["free"])

    assert _statuts(client, 2) == [200, 200]
    detail = client.post("/api/calcul").json()["detail"]
    assert (detail["error"], detail["tier"], detail["quota"], detail["quota_period"]) == (
        "quota_exceeded", "free", 2, "month")
    (cle,) = base.usage_counters.docs
    assert cle[1] == "calculator" and len(cle[2]) == 7  # « AAAA-MM » : compteur du mois


def test_calcul_abonne_payant_garde_son_quota_du_jour():
    assert _statuts(_client(_app_calcul(), abonne=ABONNES["starter"]), 3) == [200] * 3


# ── Fiche réglementaire (onglet Réglementation du calculateur) ──────────────
# Règle 2 de la décision d'accès du 09/11/2026 : un compte inscrit sans
# abonnement a 5 recherches par module et par mois. La fiche d'une position est
# le module « reglementation » ; un pays et un produit cherchés comptent chacun
# une recherche, comme dans les autres modules.


def _fiche(client, pays, code):
    return client.get(f"/api/consultation/{pays}/position/{code}")


def test_fiche_reglementation_demande_la_connexion(app_api, base):
    reponse = _fiche(_client(app_api), "DZA", "0201101100")

    assert reponse.status_code == 401
    detail = reponse.json()["detail"]
    assert (detail["error"], detail["module"]) == ("login_required", "reglementation")
    assert base.recherches_modules.docs == {}


def test_la_fiche_est_la_seule_route_de_consultation_comptee(app_api):
    """Les routes que le calculateur partage restent hors quota : leur usage est
    compté au calcul, et les compter ici ferait échouer le calcul d'un compte
    gratuit avant son premier résultat."""
    gardees = {
        route.path
        for route in routes_api(app_api)
        if route.path.startswith("/api/consultation/") and _porte(route, "require_module_consultation.")
    }
    assert gardees == {"/api/consultation/{iso3}/position/{code}"}
    toutes = {route.path for route in routes_api(app_api) if route.path.startswith("/api/consultation/")}
    assert {
        "/api/consultation/{iso3}/sous-positions/{hs6}",
        "/api/consultation/{iso3}/recherche",
        "/api/consultation/{iso3}/formalites/{code}",
    } <= toutes


# Les routes que le calculateur partage : connexion exigée, rien de décompté.
ROUTES_PARTAGEES = [
    "/api/consultation/DZA/sous-positions/020110",
    "/api/consultation/DZA/recherche?q=veaux",
    "/api/consultation/DZA/formalites/0201101100",
    "/api/calcul/pays",
]


@pytest.mark.parametrize("chemin", ROUTES_PARTAGEES)
def test_routes_partagees_demandent_la_connexion(app_api, chemin):
    reponse = _client(app_api).get(chemin)

    assert reponse.status_code == 401
    detail = reponse.json()["detail"]
    assert (detail["error"], detail["module"]) == ("login_required", "calculator")


@pytest.mark.parametrize("chemin", ROUTES_PARTAGEES)
def test_routes_partagees_ne_comptent_rien_pour_un_compte_gratuit(app_api, base, chemin):
    """Les compter ferait échouer un calcul gratuit avant son premier résultat."""
    client = _client(app_api, abonne=ABONNES["free"])

    statuts = {client.get(chemin).status_code for _ in range(8)}

    assert statuts.isdisjoint({401, 403, 429})
    assert base.recherches_modules.docs == {}
    assert base.usage_counters.docs == {}


@pytest.mark.parametrize("chemin", ROUTES_PARTAGEES)
def test_routes_partagees_cle_api_valide_et_absence_de_base(app_api, base, chemin):
    assert _client(app_api, cle=CLE_VENDUE).get(chemin).status_code != 401
    assert base.recherches_modules.docs == {}

    entitlement_guard.set_database(None)
    auth.set_database(None)
    assert _client(app_api).get(chemin).status_code != 401


def test_chaque_route_partagee_porte_la_garde_de_connexion_et_aucune_garde_comptee(app_api):
    partagees = {
        route.path: route
        for route in routes_api(app_api)
        if route.path in {
            "/api/consultation/{iso3}/sous-positions/{hs6}",
            "/api/consultation/{iso3}/recherche",
            "/api/consultation/{iso3}/formalites/{code}",
            "/api/calcul/pays",
        }
    }
    assert len(partagees) == 4
    for chemin, route in partagees.items():
        assert _porte(route, "require_login."), chemin
        assert not _porte(route, "require_module_consultation."), chemin
        assert not _porte(route, "require_calculations_quota."), chemin


def test_fiche_reglementation_cinq_recherches_par_mois_puis_invitation(app_api, base):
    client = _client(app_api, abonne=ABONNES["free"])

    assert _fiche(client, "DZA", "0201101100").status_code != 429  # DZA et le code : 2 sur 5
    assert _fiche(client, "DZA", "0201101100").status_code != 429  # revoir ne compte pas
    assert _fiche(client, "DZA", "0201101900").status_code != 429  # un produit nouveau : 3 sur 5
    assert _fiche(client, "MAR", "0101210000").status_code != 429  # MAR et le code : 5 sur 5

    reponse = _fiche(client, "DZA", "0201102000")  # un sixième terme
    assert reponse.status_code == 429
    detail = reponse.json()["detail"]
    assert (detail["error"], detail["tier"], detail["module"], detail["quota"], detail["quota_period"]) == (
        "quota_exceeded", "free", "reglementation", 5, "month")
    (doc,) = base.recherches_modules.docs.values()
    assert doc["module"] == "reglementation"
    assert sorted(doc["termes"]) == sorted(["DZA", "0201101100", "0201101900", "MAR", "0101210000"])


def test_fiche_reglementation_l_origine_est_une_option_de_la_meme_recherche(app_api, base):
    """Le pays d'origine précise la recherche d'un produit, il n'en ouvre pas une
    autre : les mêmes pays et produit, avec ou sans origine, comptent une fois."""
    client = _client(app_api, abonne=ABONNES["free"])

    for origine in (None, "TUN", "KEN", "MAR", "GHA", "ZAF"):
        reponse = client.get("/api/consultation/DZA/position/0201101100", params={"origine": origine} if origine else None)
        assert reponse.status_code != 429, origine
    (doc,) = base.recherches_modules.docs.values()
    assert sorted(doc["termes"]) == ["0201101100", "DZA"]


@pytest.mark.parametrize("formule", ["starter", "pro", "business"])
def test_fiche_reglementation_sans_limite_en_formule_payante(app_api, base, formule):
    client = _client(app_api, abonne=ABONNES[formule])

    statuts = [_fiche(client, "DZA", f"02011011{i:02d}").status_code for i in range(8)]
    assert not {401, 403, 429} & set(statuts)
    assert base.recherches_modules.docs == {}


def test_fiche_reglementation_a_son_propre_compteur(app_api, base):
    # Cinq recherches épuisées dans le module Production n'ôtent rien à la fiche.
    production = _client(_app_consultation("production"), abonne=ABONNES["free"])
    for pays in ("DZA", "MAR", "TUN", "EGY", "NGA"):
        assert production.get(f"/api/sonde/{pays}").status_code == 200
    assert production.get("/api/sonde/KEN").status_code == 429

    assert _fiche(_client(app_api, abonne=ABONNES["free"]), "DZA", "0201101100").status_code != 429
    assert {doc["module"] for doc in base.recherches_modules.docs.values()} == {"production", "reglementation"}


def test_fiche_reglementation_cle_api_valide_passe_sans_compte(app_api, base):
    reponse = _fiche(_client(app_api, cle=CLE_VENDUE), "DZA", "0201101100")

    assert reponse.status_code != 401
    assert base.recherches_modules.docs == {}
    assert base.api_keys.docs[_hash(CLE_VENDUE)]["request_count"] == 1


def test_fiche_reglementation_sans_base_reste_ouverte(app_api):
    # Développement et CI : aucun Mongo, appels anonymes.
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _fiche(_client(app_api), "DZA", "0201101100").status_code not in (401, 403, 429)


def test_fiche_reglementation_le_compte_admin_passe_sans_rien_decompter(app_api, base, monkeypatch):
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    admin = _client(app_api, abonne=ADMIN)

    statuts = [_fiche(admin, "DZA", f"02011011{i:02d}").status_code for i in range(8)]
    assert not {401, 403, 429} & set(statuts)
    assert base.recherches_modules.docs == {}


# ── Modules de consultation : connexion, puis 5 recherches par mois ─────────


def _app_consultation(module="production"):
    """Sonde avec la garde des modules de consultation."""
    sonde = APIRouter()

    @sonde.get("/sonde")
    async def liste():
        return {"ok": True}

    @sonde.get("/sonde/{country_iso3}")
    async def fiche(country_iso3: str, lang: str = "fr", year: int = 2024):
        return {"ok": True}

    api = APIRouter(prefix="/api")
    api.include_router(
        sonde,
        dependencies=routes._auth + [Depends(entitlement_guard.require_module_consultation(module))],
    )
    app = FastAPI()
    app.include_router(api)
    return app


def test_consultation_sans_compte_demande_la_connexion():
    reponse = _client(_app_consultation()).get("/api/sonde/DZA")

    assert reponse.status_code == 401
    assert reponse.json()["detail"]["error"] == "login_required"


@pytest.mark.parametrize(
    "chemin",
    ["/api/production/macro/DZA", "/api/logistics/ports", "/api/rules-of-origin/stats",
     "/api/country-profile/DZA", "/api/statistics/trade-performance"],
)
def test_vrais_modules_fermes_sans_compte(app_api, chemin):
    reponse = _client(app_api).get(chemin)

    assert reponse.status_code == 401, chemin
    assert reponse.json()["detail"]["error"] == "login_required"


def test_tableau_de_bord_reste_public(app_api):
    # Données du tableau de bord d'accueil servies par le routeur Statistiques.
    assert _client(app_api).get("/api/statistics/afreximbank-atr2026").status_code != 401


def test_cinq_recherches_par_mois_puis_invitation(base):
    client = _client(_app_consultation(), abonne=ABONNES["free"])

    # Ouvrir le module (listes générales) ne compte pas.
    assert _statuts(client, 3, "get", "/api/sonde") == [200] * 3
    for pays in ("DZA", "MAR", "TUN", "EGY", "NGA"):
        assert client.get(f"/api/sonde/{pays}").status_code == 200
    # Revoir un pays déjà cherché, même avec d'autres options, ne compte pas.
    assert client.get("/api/sonde/DZA?lang=en&year=2023").status_code == 200

    reponse = client.get("/api/sonde/KEN")
    assert reponse.status_code == 429
    detail = reponse.json()["detail"]
    assert (detail["error"], detail["tier"], detail["module"], detail["quota"], detail["quota_period"]) == (
        "quota_exceeded", "free", "production", 5, "month")
    (doc,) = base.recherches_modules.docs.values()
    assert doc["termes"] == ["DZA", "MAR", "TUN", "EGY", "NGA"]


def test_recherches_comptees_par_module(base):
    client_prod = _client(_app_consultation("production"), abonne=ABONNES["free"])
    client_log = _client(_app_consultation("logistics"), abonne=ABONNES["free"])
    for pays in ("DZA", "MAR", "TUN", "EGY", "NGA"):
        client_prod.get(f"/api/sonde/{pays}")

    assert client_log.get("/api/sonde/KEN").status_code == 200


def test_formules_payantes_sans_limite_de_recherches(base):
    client = _client(_app_consultation(), abonne=ABONNES["starter"])

    assert all(client.get(f"/api/sonde/P{i}").status_code == 200 for i in range(8))
    assert base.recherches_modules.docs == {}


def test_termes_de_recherche():
    from starlette.requests import Request

    requete = Request({
        "type": "http", "method": "GET", "path": "/x/dza", "headers": [],
        "query_string": b"hs_code=0901&lang=en&page=2&q=cafe",
        "path_params": {"country_iso3": "dza"},
    })
    assert entitlement_guard.termes_de_recherche(requete) == ["0901", "CAFE", "DZA"]


def test_parametre_de_requete_homonyme_ne_masque_pas_le_chemin(base):
    client = _client(_app_consultation(), abonne=ABONNES["free"])
    for pays in ("DZA", "MAR", "TUN", "EGY", "NGA"):
        client.get(f"/api/sonde/{pays}")

    assert client.get("/api/sonde/KEN?country_iso3=").status_code == 429
    assert client.get("/api/sonde/KEN?country_iso3=DZA").status_code == 429


def test_recherches_simultanees_ne_depassent_pas_le_quota(base):
    utilisateur = ABONNES["free"]
    acces = entitlement_guard.resolve_entitlements(utilisateur).module("production")

    async def scenario():
        await entitlement_guard.compter_recherches(utilisateur, "production", ["A", "B", "C", "D"], acces)
        return await asyncio.gather(*(
            entitlement_guard.compter_recherches(utilisateur, "production", [terme], acces)
            for terme in ("E", "F", "G")
        ))

    assert sorted(asyncio.run(scenario())) == [False, False, True]
    (doc,) = base.recherches_modules.docs.values()
    assert len(doc["termes"]) == 5


# ── Module Opportunités : réservé aux abonnements payants ───────────────────


def test_rapports_refuses_a_un_anonyme(app_api, base):
    reponse = _client(app_api).get("/api/reports/macro/NGA")

    assert reponse.status_code == 403
    detail = reponse.json()["detail"]
    assert detail["error"] == "upgrade_required"
    assert detail["tier"] == "anonymous"
    assert "abonnements payants" in detail["message"]
    assert base.usage_counters.docs == {}


def test_rapports_refuses_a_un_abonne_free(app_api):
    reponse = _client(app_api, abonne=ABONNES["free"]).get("/api/reports/macro/NGA")

    assert reponse.status_code == 403
    assert reponse.json()["detail"]["error"] == "upgrade_required"


def test_rapports_ouverts_aux_formules_payantes_et_comptes(app_api):
    client = _client(app_api, abonne=ABONNES["starter"])  # 10 rapports par jour

    assert _statuts(client, 10, "get", "/api/reports/macro/NGA") == [200] * 10
    assert client.get("/api/reports/macro/NGA").status_code == 429


def test_rapports_cle_api_valide_acceptee_et_comptee_une_fois(app_api, base):
    reponse = _client(app_api, cle=CLE_VENDUE).get("/api/reports/macro/NGA")

    assert reponse.status_code == 200
    assert base.api_keys.docs[_hash(CLE_VENDUE)]["request_count"] == 1


def test_rapports_sans_base_restent_ouverts(app_api):
    # Workflow CI opportunites_module.yml : aucun Mongo, appels anonymes.
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _client(app_api).get("/api/reports/macro/NGA").status_code == 200


def test_diagnostics_rapports_restent_publics_et_hors_quota(app_api, base):
    assert _client(app_api).get("/api/reports/health").status_code == 200
    assert base.usage_counters.docs == {}

    controles = {
        route.path: _porte(route, "require_paid_module.")
        for route in routes_api(app_api)
        if route.path.startswith("/api/reports/")
    }
    assert controles.pop("/api/reports/health") is False
    assert controles.pop("/api/reports/oec-health") is False
    assert controles and all(controles.values())


# ── Sous-onglets de l'onglet Opportunités : abonnement payant, sans décompte ─

_SOUS_ONGLETS = ("/api/substitution/", "/api/strategic/", "/api/industrie-nationale/")


def test_sous_onglets_opportunites_portent_le_controle_d_abonnement(app_api):
    routes_sous_onglets = [
        route
        for route in routes_api(app_api)
        if route.path.startswith(_SOUS_ONGLETS)
    ]

    assert {r.path.split("/")[2] for r in routes_sous_onglets} == {
        "substitution",
        "strategic",
        "industrie-nationale",
    }
    for route in routes_sous_onglets:
        assert _porte(route, "require_paid_module."), route.path


def test_l_application_ne_sert_aucune_copie_non_controlee_des_sous_onglets():
    """server.py incluait une seconde fois le routeur de substitution, sans le
    contrôle d'abonnement. La copie contrôlée, incluse en premier, servait les
    requêtes ; un simple changement d'ordre aurait ouvert l'onglet à tous.
    Vérifié sur l'application réelle, pas sur `app_api`."""
    from server import app

    routes_sous_onglets = [r for r in routes_api(app) if r.path.startswith(_SOUS_ONGLETS)]

    assert routes_sous_onglets
    for route in routes_sous_onglets:
        assert _porte(route, "require_paid_module."), route.path


def test_sous_onglets_refuses_a_un_anonyme_et_au_free(app_api, base):
    anonyme = _client(app_api).get("/api/substitution/countries")
    free = _client(app_api, abonne=ABONNES["free"]).get("/api/substitution/countries")

    assert anonyme.status_code == 403
    assert anonyme.json()["detail"]["tier"] == "anonymous"
    assert free.status_code == 403
    assert free.json()["detail"]["error"] == "upgrade_required"


def test_sous_onglets_ouverts_aux_formules_payantes_sans_decompte(app_api, base):
    # Starter a 10 rapports par jour : la consultation ne doit pas les user.
    client = _client(app_api, abonne=ABONNES["starter"])

    assert _statuts(client, 12, "get", "/api/substitution/countries") == [200] * 12
    assert base.usage_counters.docs == {}
    assert client.get("/api/reports/macro/NGA").status_code == 200


def test_sous_onglets_cle_api_et_absence_de_base(app_api):
    assert _client(app_api, cle=CLE_VENDUE).get("/api/substitution/countries").status_code == 200
    entitlement_guard.set_database(None)
    auth.set_database(None)
    assert _client(app_api).get("/api/substitution/countries").status_code == 200


# ── Compte admin : tous les modules, aucun quota ────────────────────────────


def test_le_compte_admin_passe_partout_sans_rien_decompter(app_api, base, monkeypatch):
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    admin = _client(app_api, abonne=ADMIN)

    assert admin.get("/api/reports/macro/NGA").status_code == 200
    assert admin.get("/api/substitution/countries").status_code == 200
    assert admin.get("/api/v2/analytics/dashboard").status_code == 200
    assert admin.get("/api/export/tariffs/excel?countries=KE").status_code == 200
    assert base.usage_counters.docs == {}
    # Téléchargement des tarifs : réservé à ce compte.
    assert admin.get("/api/tariff-data/download-json/COG").status_code == 200


def test_sans_le_reglage_le_compte_admin_n_a_aucun_privilege(app_api, monkeypatch):
    monkeypatch.delenv("ADMIN_ACCES_ILLIMITE", raising=False)
    admin = _client(app_api, abonne=ADMIN)

    assert admin.get("/api/reports/macro/NGA").status_code == 403
    assert admin.get("/api/tariff-data/download-json/COG").status_code == 403
    assert admin.get("/api/export/tariffs/csv?country=KE").status_code == 403
    assert admin.get("/api/export/tariffs/excel?countries=KE").status_code == 403


# ── API v2 : clé API valide ou session Business ─────────────────────────────


def test_api_v2_refuse_un_anonyme(app_api):
    reponse = _client(app_api).get("/api/v2/analytics/dashboard")

    assert reponse.status_code == 403
    assert reponse.json()["detail"]["error"] == "upgrade_required"


def test_api_v2_accepte_une_cle_vendue_comptee_une_seule_fois(app_api, base):
    # `require_auth` figure deux fois (routeur et garde) : FastAPI le met en
    # cache pour la requête, la clé n'est donc décomptée qu'une fois.
    reponse = _client(app_api, cle=CLE_VENDUE).get("/api/v2/analytics/dashboard")

    assert reponse.status_code == 200
    assert base.api_keys.docs[_hash(CLE_VENDUE)]["request_count"] == 1


def test_api_v2_session_inchangee_pro_refuse_business_accepte(app_api):
    pro = _client(app_api, abonne=ABONNES["pro"]).get("/api/v2/analytics/dashboard")
    business = _client(app_api, abonne=ABONNES["business"]).get("/api/v2/analytics/dashboard")

    assert pro.status_code == 403
    assert business.status_code == 200


def test_api_v2_sans_base_refusee(app_api):
    # Contrairement aux calculs et aux rapports : sans base, aucune clé n'est
    # vérifiable, donc aucun appel n'est admis.
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _client(app_api).get("/api/v2/analytics/dashboard").status_code == 403


# ── Exports de fichiers : le format doit figurer dans la formule ────────────

# Décision de l'exploitant du 06/11/2026 : CSV et Excel réservés au compte
# admin connecté, dans tous les modules ; le PDF accordé à toutes les formules.
EXPORTS_RESERVES = {
    "/api/export/tariffs/csv?country=KE": "csv",
    "/api/export/comparison/csv?countries=KE,TZ": "csv",
    "/api/export/tariffs/excel?countries=KE": "excel",
    "/api/regional-analytics/export?format=excel": "excel",
}
EXPORT_PDF = "/api/regional-analytics/export?format=pdf"


@pytest.mark.parametrize("chemin", EXPORTS_RESERVES)
@pytest.mark.parametrize("formule", ABONNES)
def test_csv_et_excel_refuses_a_toutes_les_formules(app_api, chemin, formule):
    # Business comprise, et le refus n'invite pas à changer de formule.
    reponse = _client(app_api, abonne=ABONNES[formule]).get(chemin)

    assert reponse.status_code == 403
    detail = reponse.json()["detail"]
    assert detail["error"] == "export_disabled"
    assert detail["module"] == f"export_{EXPORTS_RESERVES[chemin]}"
    nom = {"csv": "CSV", "excel": "Excel"}[EXPORTS_RESERVES[chemin]]
    assert detail["message"] == f"L'export {nom} n'est proposé dans aucune formule."


@pytest.mark.parametrize("chemin", EXPORTS_RESERVES)
def test_csv_et_excel_accordes_au_compte_admin_connecte(app_api, chemin, monkeypatch):
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")

    assert _client(app_api, abonne=ADMIN).get(chemin).status_code == 200


@pytest.mark.parametrize("chemin", EXPORTS_RESERVES)
def test_csv_et_excel_refuses_sans_session_meme_avec_une_cle_admin(app_api, chemin, monkeypatch):
    # Comme le téléchargement des tarifs : la session admin, aucune clé.
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    for cle in (None, CLE_VENDUE, CLE_ADMIN):
        reponse = _client(app_api, cle=cle).get(chemin)
        assert reponse.status_code == 403, cle
        assert reponse.json()["detail"]["error"] == "export_disabled"


@pytest.mark.parametrize("formule", ABONNES)
def test_pdf_accorde_a_toutes_les_formules(app_api, formule):
    reponse = _client(app_api, abonne=ABONNES[formule]).get(EXPORT_PDF)

    assert reponse.status_code == 200
    assert reponse.headers["content-disposition"].endswith(".pdf")


def test_pdf_accorde_au_compte_admin_connecte(app_api, monkeypatch):
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")

    assert _client(app_api, abonne=ADMIN).get(EXPORT_PDF).status_code == 200


def test_pdf_refuse_a_l_anonyme_sauf_cle_api(app_api):
    anonyme = _client(app_api).get(EXPORT_PDF)

    assert anonyme.status_code == 403
    assert anonyme.json()["detail"]["tier"] == "anonymous"
    assert _client(app_api, cle=CLE_VENDUE).get(EXPORT_PDF).status_code == 200


def test_export_sans_base_refuse(app_api):
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _client(app_api).get("/api/export/tariffs/csv?country=KE").status_code == 403
    assert _client(app_api).get(EXPORT_PDF).status_code == 403


def test_rapport_de_validation_reserve_a_l_admin(app_api):
    chemin = "/api/export/validation-report/json"

    assert _client(app_api, abonne=ABONNES["business"]).get(chemin).status_code == 403
    assert _client(app_api, cle=CLE_VENDUE).get(chemin).status_code == 403
    assert _client(app_api, cle=CLE_ADMIN).get(chemin).status_code == 200


def test_export_regional_excel_par_defaut_json_libre(app_api):
    chemin = "/api/regional-analytics/export"
    anonyme = _client(app_api)

    # Sans format : excel, réservé à l'admin.
    assert _client(app_api, abonne=ABONNES["business"]).get(chemin).status_code == 403
    assert anonyme.get(chemin).status_code == 403
    assert anonyme.get(chemin, params={"format": "json"}).status_code == 200


def test_export_regional_excel_de_l_admin_est_un_xlsx(app_api, monkeypatch):
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    reponse = _client(app_api, abonne=ADMIN).get("/api/regional-analytics/export")

    assert io.BytesIO(reponse.content).read(2) == b"PK"  # xlsx


def test_la_session_donne_au_navigateur_ses_formats_d_export(app_api, base, monkeypatch):
    """GET /api/auth/me : le navigateur masque ses boutons d'export CSV, JSON et
    Excel d'après `export_formats` (le PDF seul pour toutes les formules)."""
    monkeypatch.setattr(user_auth, "_db", base)
    formats = {
        formule: _client(app_api, abonne=abonne).get("/api/auth/me").json()["export_formats"]
        for formule, abonne in ABONNES.items()
    }
    assert formats == {formule: ["pdf"] for formule in ABONNES}
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    me = _client(app_api, abonne=ADMIN).get("/api/auth/me").json()
    assert me["export_formats"] == ["csv", "excel", "pdf"]


def _porte(route, prefixe):
    """La route dépend-elle d'une dépendance dont le nom commence par `prefixe` ?"""
    pile = list(route.dependant.dependencies)
    while pile:
        dependance = pile.pop()
        if getattr(dependance.call, "__qualname__", "").startswith(prefixe):
            return True
        pile.extend(dependance.dependencies)
    return False


def test_chaque_export_de_fichier_porte_un_controle(app_api):
    exports = [
        route
        for route in routes_api(app_api)
        if (
            route.path.startswith("/api/export/") or route.path == "/api/regional-analytics/export"
        )
    ]

    assert len(exports) == 5
    for route in exports:
        assert any(
            _porte(route, prefixe)
            for prefixe in ("require_export_format.", "_format_d_export", "require_admin")
        ), route.path
