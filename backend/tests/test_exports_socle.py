"""L'export CSV du socle (backend/data/exports/socle/) reste celui du socle.

Le SaaS ne les sert à aucune formule (seul le compte admin les télécharge,
si ADMIN_ACCES_ILLIMITE est activé) ; leur manifeste donne le nombre de
positions affiché par le module Outils. Un socle reconstruit — ou un moteur modifié, qui change le
total pour 100 CAF — sans réexport décrirait un tarif qui n'est plus celui du
calculateur. Remède : relancer
``python3 scripts/exporter_tarifs_socle.py`` (après ``build_socle.py``).
"""

import hashlib
import importlib.util
import io
import json
import os
import sys
import zipfile
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
sys.path.insert(0, BACKEND)

from routes.tariff_data import router  # noqa: E402

EXPORTS = os.path.join(BACKEND, "data", "exports", "socle")
REMEDE = "relancer python3 scripts/exporter_tarifs_socle.py"


def _json(chemin):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _empreinte(chemin):
    with open(chemin, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


EXPORTS_PAYS = _json(os.path.join(EXPORTS, "MANIFESTE.json"))["pays"]
SOCLE_PAYS = _json(os.path.join(BACKEND, "socle", "MANIFESTE.json"))["pays"]


def test_chaque_pays_du_socle_a_son_export():
    attendus = {cc for cc, e in SOCLE_PAYS.items() if e["compteurs"]["positions"]}
    assert set(EXPORTS_PAYS) == attendus, REMEDE


@pytest.mark.parametrize("cc", sorted(EXPORTS_PAYS))
def test_l_export_est_tire_du_socle_versionne(cc):
    entree = EXPORTS_PAYS[cc]
    assert entree["socle_sha256"] == SOCLE_PAYS[cc]["socle_sha256"], f"{cc} : {REMEDE} {cc}"
    assert entree["sha256"] == _empreinte(os.path.join(EXPORTS, entree["fichier"]))
    assert entree["notes_sha256"] == _empreinte(os.path.join(EXPORTS, entree["fichier_notes"]))


def test_le_reexport_redonne_les_fichiers_archives(tmp_path):
    """Même socle, même moteur : mêmes octets. Tourne là où le socle est
    construit (la CI le construit avant pytest)."""
    construits = [cc for cc in EXPORTS_PAYS if os.path.exists(os.path.join(BACKEND, "socle", f"{cc}.json"))]
    if not construits:
        pytest.skip("socle non construit (python3 scripts/build_socle.py)")

    spec = importlib.util.spec_from_file_location("exporter_tarifs_socle", os.path.join(REPO, "scripts", "exporter_tarifs_socle.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPORT_DIR = str(tmp_path)

    ecarts = []
    for cc in construits:
        entree = module.exporter(cc, {"pays": SOCLE_PAYS}, le=date.fromisoformat(EXPORTS_PAYS[cc]["date_reference"]))
        if (entree["sha256"], entree["notes_sha256"]) != (EXPORTS_PAYS[cc]["sha256"], EXPORTS_PAYS[cc]["notes_sha256"]):
            ecarts.append(cc)
    assert not ecarts, f"{REMEDE} {' '.join(ecarts)}"


def _client(quota=False, utilisateur=None):
    """Client du routeur seul. Le quota « tools » (abonnement, base de
    données) est neutralisé, sauf ``quota=True`` qui le laisse s'appliquer.
    ``utilisateur`` est la session vue par l'application (aucune par défaut)."""
    from entitlement_guard import get_optional_subscriber
    from routes.tariff_data import _tools_metered

    app = FastAPI()
    app.include_router(router)
    if not quota:
        app.dependency_overrides[_tools_metered[0].dependency] = lambda: None
    app.dependency_overrides[get_optional_subscriber] = lambda: utilisateur
    return TestClient(app)


ADMIN = {"email": "admin@exemple.invalid", "role": "admin"}


@pytest.fixture
def admin(monkeypatch):
    """Client du compte admin, accès illimité activé (cas d'Emergent)."""
    monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", "true")
    return _client(utilisateur=ADMIN)


def test_la_liste_ne_donne_que_le_nombre_de_positions(monkeypatch):
    monkeypatch.delenv("ADMIN_ACCES_ILLIMITE", raising=False)
    corps = _client().get("/tariff-data/download/list").json()
    assert corps["count"] == len(EXPORTS_PAYS)
    assert corps["telechargement"] is False
    cog = next(c for c in corps["countries"] if c["code"] == "COG")
    assert cog["positions"] == EXPORTS_PAYS["COG"]["positions"]
    # Aucun lien ni aucune taille de fichier : rien n'est téléchargeable.
    assert set(cog) == {"code", "name", "positions", "collecte", "devise"}


TELECHARGEMENTS = [
    "/tariff-data/download-zip/COG",
    "/tariff-data/download-json/COG",
    "/tariff-data/download-region-zip/cemac",
]


@pytest.mark.parametrize("chemin", TELECHARGEMENTS)
@pytest.mark.parametrize(
    "reglage, utilisateur",
    [
        (None, None),  # anonyme
        ("true", {"email": "pro@exemple.invalid", "role": "user"}),  # abonné
        (None, ADMIN),  # admin, accès illimité désactivé (défaut)
        ("false", ADMIN),
    ],
)
def test_aucune_formule_ne_telecharge_les_tarifs(monkeypatch, chemin, reglage, utilisateur):
    """Décision du responsable produit (03/11/2026) : aucun téléchargement de
    tarif, pour aucune formule ni aucun pays."""
    if reglage is None:
        monkeypatch.delenv("ADMIN_ACCES_ILLIMITE", raising=False)
    else:
        monkeypatch.setenv("ADMIN_ACCES_ILLIMITE", reglage)
    reponse = _client(utilisateur=utilisateur).get(chemin)
    assert reponse.status_code == 403
    assert reponse.json()["detail"]["error"] == "downloads_disabled"


def test_les_lignes_tarifaires_paginees_ne_sont_plus_servies(admin):
    assert admin.get("/tariff-data/COG").status_code == 404


def test_l_admin_recoit_les_liens_de_telechargement(admin):
    corps = admin.get("/tariff-data/download/list").json()
    assert corps["telechargement"] is True
    cog = next(c for c in corps["countries"] if c["code"] == "COG")
    assert cog["download_url"] == "/tariff-data/download-zip/COG"
    assert cog["json_download_url"] == "/tariff-data/download-json/COG"
    assert cog["total_size_kb"] > 0


def test_le_zip_porte_le_tarif_et_ses_notes(admin):
    reponse = admin.get("/tariff-data/download-zip/cog")
    assert reponse.status_code == 200
    with zipfile.ZipFile(io.BytesIO(reponse.content)) as zf:
        assert sorted(zf.namelist()) == ["COG_NPF.csv", "COG_NPF_notes.csv"]
        entete = zf.read("COG_NPF.csv").decode("utf-8-sig").splitlines()[0]
    assert entete.startswith("Position;Désignation;Chapitre;Unité;DD ")


def test_le_zip_d_un_groupe_porte_les_exports_de_ses_pays(admin):
    reponse = admin.get("/tariff-data/download-region-zip/cemac")
    assert reponse.status_code == 200
    with zipfile.ZipFile(io.BytesIO(reponse.content)) as zf:
        noms = zf.namelist()
    assert "CEMAC_+_RDC_+_STP/Congo_COG/COG_NPF.csv" in noms
    assert all(n.endswith(("_NPF.csv", "_NPF_notes.csv")) for n in noms)


def test_un_pays_sans_export_est_refuse(admin):
    assert admin.get("/tariff-data/download-zip/DJI").status_code == 404
    assert admin.get("/tariff-data/download-zip/..%2F..%2Fetc").status_code == 404


def test_le_json_reprend_le_csv_archive(admin):
    """Le JSON se lit sur le CSV archivé : un réexport du tarif le met à jour
    sans autre étape."""
    corps = admin.get("/tariff-data/download-json/cog").json()
    assert corps["pays"] == "COG"
    assert corps["socle_sha256"] == EXPORTS_PAYS["COG"]["socle_sha256"]
    assert len(corps["positions"]) == EXPORTS_PAYS["COG"]["positions"]
    assert [p["code"] for p in corps["prelevements"]][:2] == ["DD", "TCI"]
    cheval = next(p for p in corps["positions"] if p["position"] == "01011010")
    assert cheval["droits"]["DD"] == 5.0
    assert cheval["total_pour_100_caf"] == 28.7  # CIA 0,2 % comprise
    assert cheval["etat"] == "COMPLET"
    assert all(n in corps["notes"] for n in cheval["notes"])


def test_le_json_garde_les_formes_publiees_et_les_restrictions(admin):
    zaf = admin.get("/tariff-data/download-json/ZAF").json()
    primates = next(p for p in zaf["positions"] if p["position"] == "020830")
    assert primates["droits"]["DD"] == "8c/kg"
    assert primates["total_pour_100_caf"] is None
    lby = admin.get("/tariff-data/download-json/LBY").json()
    biere = next(p for p in lby["positions"] if p["position"] == "220300")
    assert biere["restrictions"] == ["Importation interdite (NPF et Ligue arabe)"]


def test_les_anciens_csv_par_chapitres_ne_sont_plus_servis():
    """Les CSV de l'ancien collecteur (``<ISO>_NPF_chXX-YY.csv``) ne portaient
    pas les corrections du socle : ils ont été retirés, et rien ne les
    régénère."""
    exports = os.path.dirname(EXPORTS)
    assert [f for f in os.listdir(exports) if f.endswith(".csv")] == []
    assert _client().get("/tariff-data/download/COG/01-10").status_code == 404


def test_chaque_export_annonce_ses_colonnes():
    for cc, entree in EXPORTS_PAYS.items():
        with open(os.path.join(EXPORTS, entree["fichier"]), encoding="utf-8-sig") as f:
            entete = f.readline().rstrip("\n").split(";")
        assert len(entete) == 4 + len(entree["colonnes"]) + 5, cc
