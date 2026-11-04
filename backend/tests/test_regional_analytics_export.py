"""Export de l'analyse régionale (/api/regional-analytics/export) : injection
de formules de tableur (audit M5).

Le secteur, recopié dans chaque ligne, n'accepte plus que les valeurs connues ;
les cellules texte du classeur et du CSV de repli sont neutralisées.
"""

import io
import sys
from pathlib import Path

import openpyxl
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth import require_auth  # noqa: E402
from dashboard.export_services import ExportService  # noqa: E402
from routes import regional_analytics  # noqa: E402

FORMULE = '=HYPERLINK("https://exemple.invalid","x")'


@pytest.fixture
def client():
    """Routeur monté sous /api, appelé avec une clé API admin : l'accès par
    formule est testé dans test_acces_par_formule.py."""

    async def _cle_admin():
        return {"key_hash": "empreinte-de-test", "tier": "admin", "active": True}

    api = APIRouter(prefix="/api")
    api.include_router(regional_analytics.router)
    app = FastAPI()
    app.include_router(api)
    app.dependency_overrides[require_auth] = _cle_admin
    return TestClient(app)


def _formules(contenu_xlsx):
    classeur = openpyxl.load_workbook(io.BytesIO(contenu_xlsx))
    return [
        cellule.coordinate
        for feuille in classeur.worksheets
        for ligne in feuille.iter_rows()
        for cellule in ligne
        if cellule.data_type == "f"
    ]


def test_export_regional_refuse_un_secteur_inconnu(client):
    for format_ in ("excel", "json"):
        reponse = client.get(
            "/api/regional-analytics/export", params={"format": format_, "sector": FORMULE}
        )
        assert reponse.status_code == 422
        assert "general" in reponse.json()["detail"]
        assert "agriculture" in reponse.json()["detail"]


@pytest.mark.parametrize("secteur", ["general", "agriculture"])
def test_export_regional_accepte_les_secteurs_connus(client, secteur):
    reponse = client.get("/api/regional-analytics/export", params={"sector": secteur})

    assert reponse.status_code == 200
    assert _formules(reponse.content) == []


def test_classeur_n_ecrit_aucune_formule():
    donnees = {"opportunities": [{"country": FORMULE, "sector": "@x", "investment_score": 0.5}]}

    contenu = ExportService().export_investment_analysis_excel(donnees)

    assert _formules(contenu) == []
    feuille = openpyxl.load_workbook(io.BytesIO(contenu)).active
    assert feuille["B5"].value == "'" + FORMULE


def test_csv_de_repli_neutralise_les_cellules_texte():
    donnees = {
        "opportunities": [
            {
                "country": "=1+1",
                "sector": "@x",
                "investment_score": 0.5,
                "grade": "-A",
                "recommendation": "+b",
            }
        ]
    }

    lignes = ExportService._csv_fallback(donnees).decode().splitlines()

    assert lignes[1] == "'=1+1,'@x,0.500,'-A,'+b"
