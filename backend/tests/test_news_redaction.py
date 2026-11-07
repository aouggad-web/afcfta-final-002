"""Rédacteur en chef des actualités (décision de l'exploitant du 07/11/2026) :
validation préalable, épingles de 7 jours, masquage, règles de blocage,
articles manuels et illustrations copiées sur notre serveur."""

import sys
from datetime import timedelta
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import auth  # noqa: E402
import entitlement_guard  # noqa: E402
from routes import news as news_routes  # noqa: E402
from services import news_images  # noqa: E402
from services import news_redaction  # noqa: E402
from services.user_auth_service import create_access_token  # noqa: E402

# ── Fausse base Mongo, juste ce que la rédaction utilise ────────────────────


def _correspond(doc, filtre):
    for cle, attendu in filtre.items():
        if isinstance(attendu, dict) and "$exists" in attendu:
            if (cle in doc) != attendu["$exists"]:
                return False
        elif doc.get(cle) != attendu:
            return False
    return True


class _Curseur:
    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, length=None):
        return list(self._docs)


class _Resultat:
    def __init__(self, n):
        self.deleted_count = n


class _Collection:
    def __init__(self, docs=()):
        self.docs = [dict(d) for d in docs]

    def find(self, filtre=None, projection=None):
        return _Curseur([dict(d) for d in self.docs if _correspond(d, filtre or {})])

    async def find_one(self, filtre):
        return next((dict(d) for d in self.docs if _correspond(d, filtre)), None)

    async def insert_one(self, doc):
        doc = dict(doc)
        doc.setdefault("_id", ObjectId())
        self.docs.append(doc)

    async def update_one(self, filtre, maj, upsert=False):
        doc = next((d for d in self.docs if _correspond(d, filtre)), None)
        if doc is None:
            if not upsert:
                return
            doc = {k: v for k, v in filtre.items() if not isinstance(v, dict)}
            self.docs.append(doc)
        doc.update(maj.get("$set", {}))
        for cle in maj.get("$unset", {}):
            doc.pop(cle, None)

    async def delete_one(self, filtre):
        for i, d in enumerate(self.docs):
            if _correspond(d, filtre):
                del self.docs[i]
                return _Resultat(1)
        return _Resultat(0)


ADMIN = {"_id": ObjectId(), "email": "admin@exemple.invalid", "role": "admin"}
ABONNE = {
    "_id": ObjectId(),
    "email": "pro@exemple.invalid",
    "subscription_tier": "pro",
    "subscription_status": "active",
}


class _FausseBase:
    def __init__(self):
        self.users = _Collection([ADMIN, ABONNE])
        self.news_redaction = _Collection()
        self.news_regles = _Collection()
        self.news_images = _Collection()


def _article(n, **extra):
    return {
        "id": f"a{n}",
        "title": f"Titre {n} sur le commerce",
        "summary": f"Résumé {n}",
        "link": f"https://presse.exemple/{n}",
        "source": "Agence Ecofin",
        "category": "Commerce",
        "region": "Afrique",
        "country": None,
        "published_at": f"2026-11-0{n}T08:00:00",
        **extra,
    }


COLLECTE = [_article(1), _article(2), _article(3, source="Source Douteuse")]


@pytest.fixture(autouse=True)
def base(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secret-de-test")
    db = _FausseBase()
    auth.set_database(db)
    entitlement_guard.set_database(db)

    async def fausse_collecte(force_refresh=False):
        return {"last_update": "2026-11-07T08:00:00", "articles": [dict(a) for a in COLLECTE]}

    monkeypatch.setattr(news_routes, "get_news", fausse_collecte)

    # Aucun appel réseau dans les tests : par défaut, aucune image trouvée.
    async def aucune_image(lien_article=None, lien_image=None):
        raise news_images.ImageRefusee("aucune image d'aperçu dans la page")

    monkeypatch.setattr(news_images, "recuperer", aucune_image)
    yield db
    auth.set_database(None)
    entitlement_guard.set_database(None)


@pytest.fixture(scope="module")
def app():
    api = APIRouter(prefix="/api")
    api.include_router(news_routes.router)
    application = FastAPI()
    application.include_router(api)
    return application


def _client(app, qui=None):
    client = TestClient(app)
    if qui is not None:
        client.cookies.set("access_token", create_access_token(str(qui["_id"]), qui["email"]))
    return client


def _publics(app):
    return [a["id"] for a in _client(app).get("/api/news").json()["articles"]]


# ── Validation préalable ─────────────────────────────────────────────────────


def test_rien_n_est_affiche_sans_validation(app):
    reponse = _client(app).get("/api/news").json()
    assert reponse["mode"] == "redaction"
    assert reponse["articles"] == []
    assert _client(app).get("/api/news/by-region").json()["articles_by_region"] == {}


def test_sans_base_le_fil_reste_automatique(app):
    auth.set_database(None)
    assert _publics(app) == ["a1", "a2", "a3"]


def test_la_file_montre_les_articles_collectes_non_decides(app):
    etat = _client(app, ADMIN).get("/api/news/redaction").json()
    assert [a["id"] for a in etat["a_valider"]] == ["a1", "a2", "a3"]


@pytest.mark.parametrize("qui", [None, ABONNE])
def test_la_redaction_est_reservee_au_compte_admin(app, qui):
    client = _client(app, qui)
    assert client.get("/api/news/redaction").status_code == 403
    for chemin, corps in [
        ("/api/news/redaction/decision", {"id": "a1", "action": "publier"}),
        ("/api/news/redaction/publier-tout", None),
        ("/api/news/redaction/epingle", {"id": "a1"}),
        ("/api/news/redaction/regles", {"type": "mot", "valeur": "fraude"}),
        (
            "/api/news/redaction/manuel",
            {"title": "Titre", "link": "https://a.b/c", "source": "Moi"},
        ),
        ("/api/news/redaction/image", {"id": "a1"}),
    ]:
        assert client.post(chemin, json=corps).status_code == 403, chemin
    assert _publics(app) == []


def test_publier_puis_masquer_puis_retablir(app):
    admin = _client(app, ADMIN)
    assert admin.post("/api/news/redaction/decision", json={"id": "a2", "action": "publier"}).json()
    assert _publics(app) == ["a2"]
    admin.post("/api/news/redaction/decision", json={"id": "a2", "action": "masquer"})
    assert _publics(app) == []
    etat = admin.get("/api/news/redaction").json()
    assert [a["id"] for a in etat["masques"]] == ["a2"]
    admin.post("/api/news/redaction/decision", json={"id": "a2", "action": "retablir"})
    assert _publics(app) == ["a2"]


def test_un_article_ecarte_quitte_la_file_et_peut_y_revenir(app):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "ecarter"})
    etat = admin.get("/api/news/redaction").json()
    assert "a1" not in [a["id"] for a in etat["a_valider"]]
    assert [a["id"] for a in etat["ecartes"]] == ["a1"]
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "retablir"})
    assert "a1" in [a["id"] for a in admin.get("/api/news/redaction").json()["a_valider"]]
    assert _publics(app) == []


def test_un_article_ecarte_retabli_revient_meme_sorti_de_la_collecte(app, monkeypatch):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "ecarter"})

    async def collecte_suivante(force_refresh=False):
        return {"last_update": None, "articles": [dict(COLLECTE[1])]}

    monkeypatch.setattr(news_routes, "get_news", collecte_suivante)
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "retablir"})
    file = admin.get("/api/news/redaction").json()["a_valider"]
    assert [a["id"] for a in file] == ["a1", "a2"]
    assert file[0]["title"] == "Titre 1 sur le commerce"
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "publier"})
    assert _publics(app) == ["a1"]


def test_les_identifiants_a_tirets_des_projets_structurants_sont_acceptes(app, monkeypatch):
    projet = _article(4, id="dz-project-gara-djebilet")

    async def collecte(force_refresh=False):
        return {"last_update": None, "articles": [projet]}

    monkeypatch.setattr(news_routes, "get_news", collecte)
    admin = _client(app, ADMIN)
    for action in ("publier", "masquer", "retablir"):
        reponse = admin.post(
            "/api/news/redaction/decision",
            json={"id": "dz-project-gara-djebilet", "action": action},
        )
        assert reponse.status_code == 200, action
    assert admin.post("/api/news/redaction/epingle", json={"id": "dz-project-gara-djebilet"}).json()
    assert _publics(app) == ["dz-project-gara-djebilet"]
    assert admin.get("/api/news/images/dz-project-gara-djebilet").status_code == 404
    assert admin.get("/api/news/images/a%2F..").status_code in (404, 422)


def test_un_article_publie_reste_affiche_apres_la_collecte_suivante(app, monkeypatch):
    _client(app, ADMIN).post("/api/news/redaction/decision", json={"id": "a1", "action": "publier"})

    async def collecte_vide(force_refresh=False):
        return {"last_update": None, "articles": []}

    monkeypatch.setattr(news_routes, "get_news", collecte_vide)
    articles = _client(app).get("/api/news").json()["articles"]
    assert [a["id"] for a in articles] == ["a1"]
    assert articles[0]["title"] == "Titre 1 sur le commerce"


def test_publier_tout_vide_la_file(app):
    admin = _client(app, ADMIN)
    assert admin.post("/api/news/redaction/publier-tout").json()["publies"] == 3
    assert admin.get("/api/news/redaction").json()["a_valider"] == []
    assert sorted(_publics(app)) == ["a1", "a2", "a3"]


def test_article_inconnu_et_action_invalide(app):
    admin = _client(app, ADMIN)
    assert (
        admin.post(
            "/api/news/redaction/decision", json={"id": "zz", "action": "publier"}
        ).status_code
        == 404
    )
    assert (
        admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "x"}).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/news/redaction/decision", json={"id": {"$ne": 1}, "action": "publier"}
        ).status_code
        == 422
    )


# ── Épingles ─────────────────────────────────────────────────────────────────


def test_l_epingle_place_l_article_en_tete_pour_sept_jours(app, base):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/publier-tout")
    admin.post("/api/news/redaction/epingle", json={"id": "a1"})
    articles = _client(app).get("/api/news").json()["articles"]
    assert articles[0]["id"] == "a1" and articles[0]["pinned"] is True
    doc = next(d for d in base.news_redaction.docs if d["_id"] == "a1")
    duree = doc["epingle_jusqua"] - news_redaction._maintenant()
    assert timedelta(days=6, hours=23) < duree <= timedelta(days=7)


def test_l_epingle_expire_seule(app, base):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/publier-tout")
    admin.post("/api/news/redaction/epingle", json={"id": "a1"})
    doc = next(d for d in base.news_redaction.docs if d["_id"] == "a1")
    doc["epingle_jusqua"] = news_redaction._maintenant() - timedelta(seconds=1)
    articles = _client(app).get("/api/news").json()["articles"]
    assert articles[0]["id"] == "a3" and not any(a["pinned"] for a in articles)


def test_epingler_un_article_de_la_file_le_publie(app):
    _client(app, ADMIN).post("/api/news/redaction/epingle", json={"id": "a2"})
    assert _publics(app) == ["a2"]


def test_ordre_de_la_une(app):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/publier-tout")
    for article_id in ("a1", "a2", "a3"):
        admin.post("/api/news/redaction/epingle", json={"id": article_id})
    assert _publics(app) == ["a1", "a2", "a3"]
    admin.post("/api/news/redaction/une", json={"ids": ["a3", "a1", "a2"]})
    assert _publics(app) == ["a3", "a1", "a2"]
    admin.post("/api/news/redaction/epingle", json={"id": "a3", "epingler": False})
    assert _publics(app) == ["a1", "a2", "a3"]


# ── Règles de blocage ────────────────────────────────────────────────────────


def test_bloquer_une_source(app):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/regles", json={"type": "source", "valeur": "source douteuse"})
    etat = admin.get("/api/news/redaction").json()
    assert [a["id"] for a in etat["a_valider"]] == ["a1", "a2"]
    assert admin.post("/api/news/redaction/publier-tout").json()["publies"] == 2


def test_bloquer_un_mot_entier_retire_aussi_un_article_deja_publie(app):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/publier-tout")
    admin.post("/api/news/redaction/regles", json={"type": "mot", "valeur": "Titre 2"})
    assert sorted(_publics(app)) == ["a1", "a3"]
    regle = admin.get("/api/news/redaction").json()["regles"][0]
    assert admin.delete(f"/api/news/redaction/regles/{regle['id']}").json() == {"ok": True}
    assert sorted(_publics(app)) == ["a1", "a2", "a3"]
    assert admin.delete("/api/news/redaction/regles/pas-un-id").status_code == 404


def test_un_mot_ne_bloque_pas_un_morceau_de_mot():
    regle = {"type": "mot", "valeur": "or"}
    assert not news_redaction.bloque([regle], {"title": "Le commerce progresse"})
    assert news_redaction.bloque([regle], {"title": "Le cours de l'or monte"})


# ── Articles ajoutés à la main ───────────────────────────────────────────────


def test_article_manuel_publie_directement_et_jamais_bloque(app):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/regles", json={"type": "source", "valeur": "Moi"})
    reponse = admin.post(
        "/api/news/redaction/manuel",
        json={
            "title": "Lancement du corridor Alger-Lagos",
            "summary": "Annonce officielle.",
            "link": "https://www.exemple.dz/annonce",
            "source": "Moi",
        },
    ).json()
    articles = _client(app).get("/api/news").json()["articles"]
    assert [a["id"] for a in articles] == [reponse["id"]]
    assert articles[0]["manuel"] is True and articles[0]["link"] == "https://www.exemple.dz/annonce"


@pytest.mark.parametrize(
    "lien",
    ["javascript:alert(1)", "data:text/html,x", "//exemple.dz/x", "ftp://exemple.dz/x", "https://"],
)
def test_article_manuel_lien_web_seulement(app, lien):
    reponse = _client(app, ADMIN).post(
        "/api/news/redaction/manuel", json={"title": "Titre", "link": lien, "source": "Moi"}
    )
    assert reponse.status_code == 422


# ── Illustrations ────────────────────────────────────────────────────────────

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 100


def test_image_copiee_servie_seulement_une_fois_l_article_publie(app, monkeypatch):
    vus = {}

    async def fausse_recuperation(lien_article=None, lien_image=None):
        vus["lien"] = lien_article
        return {"type": "image/jpeg", "donnees": JPEG, "origine": "https://presse.exemple/i.jpg"}

    monkeypatch.setattr(news_images, "recuperer", fausse_recuperation)
    admin = _client(app, ADMIN)
    assert admin.post("/api/news/redaction/image", json={"id": "a1"}).json() == {"ok": True}
    assert vus["lien"] == "https://presse.exemple/1"
    etat = admin.get("/api/news/redaction").json()
    assert etat["a_valider"][0]["has_image"] is True
    assert admin.get("/api/news/images/a1").status_code == 200
    assert _client(app).get("/api/news/images/a1").status_code == 404

    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "publier"})
    reponse = _client(app).get("/api/news/images/a1")
    assert reponse.status_code == 200 and reponse.content == JPEG
    assert reponse.headers["content-type"] == "image/jpeg"
    assert reponse.headers["x-content-type-options"] == "nosniff"
    assert _client(app).get("/api/news").json()["articles"][0]["has_image"] is True

    admin.post("/api/news/redaction/image/retirer", json={"id": "a1"})
    assert _client(app).get("/api/news/images/a1").status_code == 404


def test_image_refusee_message_au_redacteur(app, monkeypatch):
    async def refus(lien_article=None, lien_image=None):
        raise news_images.ImageRefusee("aucune image d'aperçu dans la page")

    monkeypatch.setattr(news_images, "recuperer", refus)
    reponse = _client(app, ADMIN).post("/api/news/redaction/image", json={"id": "a1"})
    assert reponse.status_code == 422
    assert reponse.json()["detail"]["error"] == "image_refusee"


@pytest.mark.parametrize(
    "lien",
    [
        "file:///etc/passwd",
        "gopher://exemple.dz/",
        "http://127.0.0.1/x.jpg",
        "http://10.0.0.5/x.jpg",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/x.jpg",
        "https://exemple.dz:8443/x.jpg",
        "javascript:alert(1)",
    ],
)
def test_liens_refuses_avant_toute_connexion(lien):
    with pytest.raises(news_images.ImageRefusee):
        news_images.verifier_lien(lien)


def test_un_nom_d_hote_passe_la_forme_le_resolveur_le_juge():
    assert (
        news_images.verifier_lien("https://presse.exemple/a.jpg") == "https://presse.exemple/a.jpg"
    )


@pytest.mark.parametrize(
    "adresses",
    [["10.1.2.3"], ["127.0.0.1"], ["93.184.216.34", "192.168.1.1"], ["::1"], []],
)
def test_resolveur_refuse_toute_adresse_non_publique(monkeypatch, adresses):
    import asyncio

    async def fausse_resolution(self, host, port=0, family=0):
        return [{"host": a, "port": port, "family": family} for a in adresses]

    monkeypatch.setattr(news_images.DefaultResolver, "resolve", fausse_resolution)

    async def essai():
        resolveur = news_images._ResolveurPublic()
        try:
            await resolveur.resolve("hote.exemple", 443)
        finally:
            await resolveur.close()

    with pytest.raises(OSError):
        asyncio.run(essai())


def test_resolveur_accepte_une_adresse_publique(monkeypatch):
    import asyncio

    async def fausse_resolution(self, host, port=0, family=0):
        return [{"host": "93.184.216.34", "port": port, "family": family}]

    monkeypatch.setattr(news_images.DefaultResolver, "resolve", fausse_resolution)

    async def essai():
        resolveur = news_images._ResolveurPublic()
        try:
            return await resolveur.resolve("hote.exemple", 443)
        finally:
            await resolveur.close()

    assert asyncio.run(essai())[0]["host"] == "93.184.216.34"


def _jpeg(largeur, hauteur, exif=True):
    import io

    from PIL import Image

    image = Image.new("RGB", (largeur, hauteur), (200, 120, 40))
    sortie = io.BytesIO()
    if exif:
        donnees_exif = Image.Exif()
        donnees_exif[0x010F] = "Fabricant secret"  # Make
        image.save(sortie, format="JPEG", exif=donnees_exif)
    else:
        image.save(sortie, format="JPEG")
    return sortie.getvalue()


def test_vignette_reduite_reencodee_sans_metadonnees():
    import io

    from PIL import Image

    original = _jpeg(2000, 1200)
    assert b"Fabricant secret" in original
    vignette = news_images.vignette(original)
    assert b"Fabricant secret" not in vignette
    with Image.open(io.BytesIO(vignette)) as image:
        assert image.format == "WEBP"
        assert image.size == (320, 192)
    assert len(vignette) < len(original)


def test_une_petite_image_n_est_pas_agrandie():
    import io

    from PIL import Image

    with Image.open(io.BytesIO(news_images.vignette(_jpeg(100, 80, exif=False)))) as image:
        assert image.size == (100, 80)


def test_faux_jpeg_et_bombe_refuses(monkeypatch):
    with pytest.raises(news_images.ImageRefusee):
        news_images.vignette(b"\xff\xd8\xff" + b"pas une image")
    monkeypatch.setattr(news_images, "PIXELS_MAX", 1000)
    with pytest.raises(news_images.ImageRefusee):
        news_images.vignette(_jpeg(100, 100, exif=False))


def test_formats_acceptes():
    assert news_images.type_image(JPEG) == "image/jpeg"
    assert news_images.type_image(b"\x89PNG\r\n\x1a\n....") == "image/png"
    assert news_images.type_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert news_images.type_image(b"<svg onload=alert(1)>") is None
    assert news_images.type_image(b"GIF89a") is None


def test_image_d_apercu_trouvee_dans_la_page():
    page = """<html><head>
      <meta name="twitter:image" content="https://cdn.exemple/tw.jpg">
      <meta content="/img/une.jpg?a=1&amp;b=2" property="og:image" />
    </head></html>"""
    assert (
        news_images.image_dans_la_page(page, "https://presse.exemple/article/1")
        == "https://presse.exemple/img/une.jpg?a=1&b=2"
    )
    assert (
        news_images.image_dans_la_page(
            "<meta property='og:image' content='javascript:x'>", "https://a.b/"
        )
        is None
    )


# ── Recherche automatique de l'image à la publication ───────────────────────


@pytest.fixture
def images_trouvees(monkeypatch):
    demandes = []

    async def trouvee(lien_article=None, lien_image=None):
        demandes.append(lien_article)
        return {"type": "image/webp", "donnees": b"RIFF....WEBP", "origine": lien_article}

    monkeypatch.setattr(news_images, "recuperer", trouvee)
    return demandes


def test_publier_cherche_l_image_aussitot(app, images_trouvees):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "publier"})
    assert images_trouvees == ["https://presse.exemple/1"]
    assert _client(app).get("/api/news").json()["articles"][0]["has_image"] is True
    # Déjà illustré : pas de seconde recherche.
    admin.post("/api/news/redaction/epingle", json={"id": "a1"})
    assert images_trouvees == ["https://presse.exemple/1"]


def test_tout_publier_cherche_toutes_les_images(app, images_trouvees):
    _client(app, ADMIN).post("/api/news/redaction/publier-tout")
    assert sorted(images_trouvees) == [f"https://presse.exemple/{n}" for n in (1, 2, 3)]


def test_ecarter_ne_cherche_pas_d_image(app, images_trouvees):
    _client(app, ADMIN).post("/api/news/redaction/decision", json={"id": "a1", "action": "ecarter"})
    assert images_trouvees == []


def test_sans_image_trouvee_l_article_reste_publie(app):
    admin = _client(app, ADMIN)
    reponse = admin.post("/api/news/redaction/decision", json={"id": "a1", "action": "publier"})
    assert reponse.json() == {"ok": True}
    articles = _client(app).get("/api/news").json()["articles"]
    assert [a["id"] for a in articles] == ["a1"] and articles[0]["has_image"] is False


def test_chercher_les_images_manquantes_des_articles_deja_publies(app, base, images_trouvees):
    admin = _client(app, ADMIN)
    admin.post("/api/news/redaction/publier-tout")
    base.news_images.docs = [d for d in base.news_images.docs if d["_id"] != "a2"]
    images_trouvees.clear()
    assert admin.post("/api/news/redaction/images-manquantes").json() == {
        "ok": True,
        "recherches": 1,
    }
    assert images_trouvees == ["https://presse.exemple/2"]
    assert _client(app).post("/api/news/redaction/images-manquantes").status_code == 403
