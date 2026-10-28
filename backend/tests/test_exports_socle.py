"""L'export CSV du socle (backend/data/exports/socle/) reste celui du socle.

Le SaaS sert ces fichiers tels quels. Un socle reconstruit — ou un moteur
modifié, qui change le total pour 100 CAF — sans réexport servirait un tarif
qui n'est plus celui du calculateur. Remède : relancer
``python3 scripts/exporter_tarifs_socle.py`` (après ``build_socle.py``).
"""

import hashlib
import importlib.util
import io
import json
import os
import sys
import zipfile

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
        entree = module.exporter(cc, {"pays": SOCLE_PAYS})
        if (entree["sha256"], entree["notes_sha256"]) != (EXPORTS_PAYS[cc]["sha256"], EXPORTS_PAYS[cc]["notes_sha256"]):
            ecarts.append(cc)
    assert not ecarts, f"{REMEDE} {' '.join(ecarts)}"


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_la_liste_annonce_chaque_export():
    corps = _client().get("/tariff-data/download-socle/list").json()
    assert corps["count"] == len(EXPORTS_PAYS)
    cog = next(c for c in corps["countries"] if c["code"] == "COG")
    assert cog["positions"] == EXPORTS_PAYS["COG"]["positions"]
    assert cog["download_url"] == "/tariff-data/download-socle/COG"


def test_le_zip_porte_le_tarif_et_ses_notes():
    reponse = _client().get("/tariff-data/download-socle/cog")
    assert reponse.status_code == 200
    with zipfile.ZipFile(io.BytesIO(reponse.content)) as zf:
        assert sorted(zf.namelist()) == ["COG_NPF.csv", "COG_NPF_notes.csv"]
        entete = zf.read("COG_NPF.csv").decode("utf-8-sig").splitlines()[0]
    assert entete.startswith("Position;Désignation;Chapitre;Unité;DD ")


def test_un_pays_sans_export_est_refuse():
    assert _client().get("/tariff-data/download-socle/DJI").status_code == 404
    assert _client().get("/tariff-data/download-socle/..%2F..%2Fetc").status_code == 404
