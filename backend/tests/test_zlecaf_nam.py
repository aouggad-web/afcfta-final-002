"""Namibie : préférence ZLECAf de sa General Note O (GN 390/2024, GN 229/2025)
aux taux de la colonne AfCFTA de son tarif (GN 391/2024, GN 174/2026).
Fiche : NAM_zlecaf_2026-10-25.json."""

import importlib.util
import json
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


def _script(nom):
    spec = importlib.util.spec_from_file_location(f"{nom}_zlecaf_nam_test", os.path.join(RACINE, "scripts", f"{nom}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
def test_taux_du_tarif_namibien_et_non_sud_africain(client):
    """85.39.21.45 : 12 % au GN 391/2024, 8 % dans la colonne sud-africaine de 2026."""
    regime, lignes = _calcul(client, "KEN", "85392145")
    assert regime["statut"] == "APPLIED"
    assert "GN 391/2024" in regime["note"]
    assert lignes["DD"]["taux_pct"] == 12.0


@socle_present
def test_origine_hors_general_note_o_au_npf(client):
    regime, _ = _calcul(client, "NGA", "85392145")
    assert regime["statut"] == "PENDING_PARTNER"
    assert not regime["applique"]


@socle_present
def test_origine_sacu_en_union_douaniere(client):
    regime, _ = _calcul(client, "ZAF", "85392145")
    assert regime["regime"] == "UNION_DOUANIERE"


@socle_present
def test_amendement_gn_174_2026(client):
    """0307.32.20 : 10 %, ligne insérée par le GN 174/2026."""
    _, lignes = _calcul(client, "EGY", "03073220")
    assert lignes["DD"]["taux_pct"] == 10.0


@socle_present
def test_ligne_namibienne_non_subdivisee(client):
    """2710.19 n'est pas subdivisée au GN 391/2024 : 6,6c/li sur 2710.19.30."""
    _, lignes = _calcul(client, "TUN", "27101930", quantite=1000)
    assert lignes["DD"]["montant"] == pytest.approx(66.0)


@socle_present
def test_plancher_de_la_note_o_3(client):
    """5208.41 : 31,2 % en colonne AfCFTA, 22 % au droit général."""
    _, lignes = _calcul(client, "GMB", "520841")
    assert lignes["DD"]["taux_pct"] == 22.0


@socle_present
@pytest.mark.parametrize("code", ["19019010", "08045011"])
def test_preference_non_tracee(client, code):
    """Formule « less » (1901.90.10) ; ligne sud-africaine qu'aucune ligne
    namibienne ne couvre (0804.50.11)."""
    regime, _ = _calcul(client, "KEN", code, quantite=10)
    assert regime["statut"] == "PREFERENCE_NON_TRACEE"


@socle_present
def test_compose_sans_regle_non_liquide(client):
    _, lignes = _calcul(client, "KEN", "020110", quantite=100)
    assert lignes["DD"]["statut"] == "REGLE_COMPOSEE_NON_ETABLIE"


def test_lecture_des_expressions():
    colonne_afcfta_nam = _script("build_socle").colonne_afcfta_nam
    assert colonne_afcfta_nam("free") == {"taux": 0.0}
    assert colonne_afcfta_nam("13,2%") == {"taux": 13.2}
    plafond = colonne_afcfta_nam("270c/kg with a maximum of 57,6%")
    assert plafond["specifique"]["montant"] == pytest.approx(2.7) and plafond["plafond_ad_valorem_pct"] == 57.6
    compose = colonne_afcfta_nam("40% or 240c/kg")
    assert compose["compose"] and "regle_composee" not in compose
    assert colonne_afcfta_nam("6% or 33c/kg less 54%")["taux"] is None


def test_le_script_reproduit_la_colonne_afcfta():
    script = _script("extraire_zlecaf_nam")
    with open(script.SORTIE, encoding="utf-8") as f:
        assert script.colonne_afcfta() == json.load(f)
