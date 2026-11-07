"""Accès sans abonnement (audit E1) : ce qu'un visiteur sans session obtient.

- POST /api/calcul (et /api/calcul/export) : 10 calculs par jour et par
  visiteur, comptés en mémoire seulement, jamais en base.
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

import hashlib
import io
import logging
import sys
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import APIRouter, FastAPI
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
    entitlement_guard._calculs_anonymes.clear()
    yield db
    auth.set_database(None)
    entitlement_guard.set_database(None)
    export_router.init_db(None)
    entitlement_guard._calculs_anonymes.clear()


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


# ── Calculateur : 10 calculs par jour sans abonnement, en mémoire ──────────


def test_calcul_anonyme_limite_a_dix_par_jour_puis_429():
    client = _client(_app_calcul(), ip="41.200.1.1")

    assert _statuts(client, 10) == [200] * 10
    reponse = client.post("/api/calcul")

    assert reponse.status_code == 429
    detail = reponse.json()["detail"]
    assert detail["error"] == "quota_exceeded"
    assert detail["tier"] == "anonymous"
    assert "Souscrivez un abonnement" in detail["message"]


def test_calcul_deux_visiteurs_ont_deux_compteurs():
    app = _app_calcul()
    assert _statuts(_client(app, ip="41.200.1.1"), 11)[-1] == 429

    assert _statuts(_client(app, ip="41.200.1.2"), 1) == [200]


def test_calcul_adresses_ipv6_d_un_meme_slash64_partagent_le_compteur():
    app = _app_calcul()
    for i in range(10):
        assert _client(app, ip=f"2a01:e0a:1:2::{i + 1:x}").post("/api/calcul").status_code == 200

    assert _client(app, ip="2a01:e0a:1:2::ff").post("/api/calcul").status_code == 429
    assert _client(app, ip="2a01:e0a:1:3::1").post("/api/calcul").status_code == 200


def test_calcul_visiteur_sans_ip_identifiable_n_est_pas_bloque():
    # Pair privé, sans relais : `cle_de_comptage` rend None (repli ouvert).
    assert _statuts(_client(_app_calcul(), ip="10.0.0.7"), 12) == [200] * 12


def test_calcul_sans_base_reste_ouvert():
    entitlement_guard.set_database(None)
    auth.set_database(None)

    assert _statuts(_client(_app_calcul(), ip="41.200.1.1"), 12) == [200] * 12


def test_calcul_cle_api_valide_n_est_pas_comptee_sur_le_quota_du_visiteur(base):
    client = _client(_app_calcul(), ip="41.200.1.1", cle=CLE_VENDUE)

    assert _statuts(client, 12) == [200] * 12
    assert base.api_keys.docs[_hash(CLE_VENDUE)]["request_count"] == 12
    assert entitlement_guard._calculs_anonymes == {}


def test_calcul_anonyme_n_ecrit_rien_en_base(base):
    _statuts(_client(_app_calcul(), ip="41.200.1.1"), 11)

    assert base.usage_counters.docs == {}
    assert entitlement_guard._calculs_anonymes == {"41.200.1.1": 10}


def test_calcul_abonne_free_garde_son_propre_quota_en_base(base):
    app = _app_calcul()
    assert _statuts(_client(app, ip="41.200.1.1"), 11)[-1] == 429

    # Même IP, mais une session : le compteur de l'abonné, pas celui de l'IP.
    abonne = _client(app, ip="41.200.1.1", abonne=ABONNES["free"])
    assert _statuts(abonne, 10) == [200] * 10
    assert abonne.post("/api/calcul").json()["detail"]["tier"] == "free"
    assert len(base.usage_counters.docs) == 1


def test_compteur_anonyme_repart_de_zero_quand_le_jour_change():
    entitlement_guard._calculs_anonymes["41.200.1.1"] = 10
    entitlement_guard._jour_calculs_anonymes = "2000-01-01"

    assert _client(_app_calcul(), ip="41.200.1.1").post("/api/calcul").status_code == 200
    assert entitlement_guard._calculs_anonymes == {"41.200.1.1": 1}


def test_compteur_anonyme_borne_en_memoire(monkeypatch, caplog):
    monkeypatch.setattr(entitlement_guard, "_MAX_VISITEURS_ANONYMES", 3)
    app = _app_calcul()
    for ip in ("41.0.0.1", "41.0.0.2", "41.0.0.3"):
        _client(app, ip=ip).post("/api/calcul")

    monkeypatch.setattr(entitlement_guard, "_compteur_plein_signale", False)
    with caplog.at_level(logging.WARNING, logger="entitlement_guard"):
        assert _client(app, ip="41.0.0.4").post("/api/calcul").status_code == 200
        assert _client(app, ip="41.0.0.5").post("/api/calcul").status_code == 200

    # Le plus ancien est oublié, les autres gardent leur compte : le quota du
    # jour ne se rouvre pas pour tous. Une seule alerte.
    assert entitlement_guard._calculs_anonymes == {"41.0.0.3": 1, "41.0.0.4": 1, "41.0.0.5": 1}
    assert caplog.text.count("les plus anciens sont oubliés") == 1


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
