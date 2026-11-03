"""L'export CSV du socle (backend/data/exports/socle/) reste celui du socle.

Le SaaS ne les sert plus (aucun téléchargement de tarif, quelle que soit la
formule), mais leur manifeste donne le nombre de positions affiché par le
module Outils. Un socle reconstruit — ou un moteur modifié, qui change le
total pour 100 CAF — sans réexport décrirait un tarif qui n'est plus celui du
calculateur. Remède : relancer
``python3 scripts/exporter_tarifs_socle.py`` (après ``build_socle.py``).
"""

import hashlib
import importlib.util
import json
import os
import sys
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


def _client(quota=False):
    """Client du routeur seul. Le quota « tools » (abonnement, base de
    données) est neutralisé, sauf ``quota=True`` qui le laisse s'appliquer."""
    from routes.tariff_data import _tools_metered

    app = FastAPI()
    app.include_router(router)
    if not quota:
        app.dependency_overrides[_tools_metered[0].dependency] = lambda: None
    return TestClient(app)


def test_la_liste_ne_donne_que_le_nombre_de_positions():
    corps = _client().get("/tariff-data/download/list").json()
    assert corps["count"] == len(EXPORTS_PAYS)
    cog = next(c for c in corps["countries"] if c["code"] == "COG")
    assert cog["positions"] == EXPORTS_PAYS["COG"]["positions"]
    # Aucun lien ni aucune taille de fichier : rien n'est téléchargeable.
    assert set(cog) == {"code", "name", "positions", "collecte", "devise"}


@pytest.mark.parametrize(
    "chemin",
    [
        "/tariff-data/download-zip/COG",
        "/tariff-data/download-json/COG",
        "/tariff-data/download-region-zip/cemac",
        "/tariff-data/COG",  # lignes tarifaires paginées
    ],
)
def test_aucun_tarif_n_est_plus_telechargeable(chemin):
    """Décision du responsable produit (03/11/2026) : aucun téléchargement de
    tarif, pour aucune formule ni aucun pays."""
    assert _client().get(chemin).status_code == 404


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
