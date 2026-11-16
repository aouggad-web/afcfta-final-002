"""Un chemin /api/... inconnu répond 404, jamais la page de l'application.

Contrôle de l'exploitation du 16/11/2026 : sur la préproduction, /api/docs et
/api/openapi.json (fermés en production) répondaient 200 avec la page HTML de
l'application, servie par le repli `serve_react` de server.py. Aucun schéma
n'était exposé, mais une route d'API absente doit se voir comme telle.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.mark.parametrize("chemin", ["/api/docs", "/api/openapi.json", "/api/inexistant/rien"])
def test_chemin_api_inconnu_repond_404(chemin):
    from server import app

    reponse = TestClient(app).get(chemin)

    assert reponse.status_code == 404, chemin
    assert "text/html" not in reponse.headers.get("content-type", "")


def test_api_sans_barre_finale_ne_rend_pas_la_page_de_l_application():
    """`/api` est la racine de l'API, pas une route inconnue : sans interface
    construite, FastAPI la redirige vers `/api/` (200) ; avec, le repli répond
    404. Dans les deux cas, jamais la page HTML de l'application."""
    from server import app

    reponse = TestClient(app).get("/api")

    assert reponse.status_code in (200, 404)
    assert "text/html" not in reponse.headers.get("content-type", "")
