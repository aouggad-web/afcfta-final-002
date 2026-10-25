"""Namibie : préférence ZLECAf de sa General Note O (GN 390/2024, GN 229/2025)
aux taux de la colonne AfCFTA du tarif commun SACU le plus à jour (socle).
Fiche : NAM_zlecaf_2026-10-25.json."""

import importlib.util
import os
import sys
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle
from services.zlecaf_schedule_nam import DATES_ENTREE_NAM, nam_partner_active

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

socle_present = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "NAM.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_zlecaf_nam_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_zlecaf_nam_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, origine, code, quantite=None):
    demande = {"destination": "NAM", "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
               "devise_cif": "NAD", "origine": origine}
    if quantite is not None:
        demande["quantite"] = quantite
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    corps = reponse.json()
    lignes = {ligne["code"]: ligne for ligne in (corps.get("preference") or {}).get("lignes", [])}
    return corps["preference_zlecaf"], lignes


def test_origines_de_la_general_note_o():
    """Note O.6 : à partir de la publication de l'avis qui inscrit l'État."""
    assert set(DATES_ENTREE_NAM) == {"DZA", "CMR", "EGY", "GHA", "KEN", "RWA", "TUN", "GMB"}
    assert not nam_partner_active("KEN", date(2024, 12, 19))
    assert nam_partner_active("KEN", date(2024, 12, 20))
    assert not nam_partner_active("GMB", date(2025, 9, 3))
    assert nam_partner_active("GMB", date(2025, 9, 4))
    assert not nam_partner_active("NGA", date(2026, 10, 25))


@socle_present
def test_colonne_afcfta_du_tarif_sacu_le_plus_a_jour(client):
    """85.39.21.45 : 8 % au tarif SACU de 2026 (12 % au GN 391/2024 namibien,
    arrêté en 2024)."""
    regime, lignes = _calcul(client, "KEN", "85392145")
    assert regime["statut"] == "APPLIED"
    assert "General Note O" in regime["note"]
    assert lignes["DD"]["taux_pct"] == 8.0


@socle_present
def test_gambie_inscrite_par_le_gn_229_2025(client):
    regime, _ = _calcul(client, "GMB", "85392145")
    assert regime["statut"] == "APPLIED"


@socle_present
def test_origine_hors_general_note_o_au_npf(client):
    regime, _ = _calcul(client, "NGA", "85392145")
    assert regime["statut"] == "PENDING_PARTNER"
    assert not regime["applique"]


@socle_present
def test_origine_sacu_en_union_douaniere(client):
    regime, _ = _calcul(client, "ZAF", "85392145")
    assert regime["regime"] == "UNION_DOUANIERE"
