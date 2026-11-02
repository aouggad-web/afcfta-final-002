"""GZALE à l'importation en Algérie : franchise du seul droit de douane pour
les origines arabes africaines, retenue seulement quand elle est plus
favorable que la ZLECAf (fiche DZA_GZALE_2026-11-02.json)."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle
from services.preference import (
    GZALE_ORIGINES_DZA,
    _choisir_gzale_ou_zlecaf,
    taux_preferentiels,
)

besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)


def _position(dd, daps):
    return {"droits": [{"code": "DD", "taux": dd}, {"code": "DAPS", "taux": daps}, {"code": "TVA", "taux": 19}]}


ZLECAF_REFUSEE = {"applique": False, "regime": "ZLECAF", "statut": "NOT_AVAILABLE", "note": "non activé", "taux": {}}


def test_les_origines_sont_les_membres_africains_de_la_zone():
    assert GZALE_ORIGINES_DZA == {"EGY", "LBY", "MAR", "SDN", "TUN"}


def test_origine_arabe_sans_zlecaf_recoit_la_franchise_du_seul_droit_de_douane():
    r = _choisir_gzale_ou_zlecaf(_position(30, 70), "DZA", "MAR", ZLECAF_REFUSEE)
    assert r["applique"] is True
    assert r["regime"] == "GZALE"
    assert r["taux"] == {"DD": {"taux": 0.0}}  # DAPS et TVA restent dus
    assert "516/DGD/D042.21" in r["perimetre"]["DD"]
    assert "certificat d'origine" in r["note"]
    assert r["zlecaf"]["statut"] == "NOT_AVAILABLE"
    assert "8 avril 2019" in r["note"]  # DAPS porté par la position : dû, et pourquoi


def test_sans_daps_la_reserve_daps_n_est_pas_dite():
    r = _choisir_gzale_ou_zlecaf(_position(30, 0), "DZA", "LBY", ZLECAF_REFUSEE)
    assert r["regime"] == "GZALE"
    assert "DAPS" not in r["note"]


@pytest.mark.parametrize("origine", ["MRT", "FRA", "COM", None])
def test_hors_zone_la_decision_zlecaf_passe_telle_quelle(origine):
    assert _choisir_gzale_ou_zlecaf(_position(30, 0), "DZA", origine, ZLECAF_REFUSEE) is ZLECAF_REFUSEE


def test_hors_algerie_rien_ne_change():
    assert _choisir_gzale_ou_zlecaf(_position(30, 0), "TUN", "MAR", ZLECAF_REFUSEE) is ZLECAF_REFUSEE


def test_la_zlecaf_exonerant_le_daps_l_emporte_sur_la_gzale():
    zlecaf = {"applique": True, "regime": "ZLECAF", "statut": "APPLIED", "note": "482/2024",
              "taux": {"DD": {"taux": 0.0}, "DAPS": {"taux": 0.0}}}
    r = _choisir_gzale_ou_zlecaf(_position(30, 70), "DZA", "TUN", zlecaf)
    assert r["regime"] == "ZLECAF"
    assert r["taux"] == zlecaf["taux"]
    assert "zone arabe (GZALE) est aussi ouverte" in r["note"]


def test_la_gzale_l_emporte_sur_un_demantelement_zlecaf_inacheve():
    zlecaf = {"applique": True, "regime": "ZLECAF", "statut": "APPLIED", "note": "482/2024",
              "taux": {"DD": {"taux": 3.0}}}
    r = _choisir_gzale_ou_zlecaf(_position(5, 0), "DZA", "TUN", zlecaf)
    assert r["regime"] == "GZALE"
    assert r["taux"] == {"DD": {"taux": 0.0}}
    assert "moins favorable" in r["note"]


def test_a_egalite_la_zlecaf_est_conservee():
    zlecaf = {"applique": True, "regime": "ZLECAF", "statut": "APPLIED", "note": "",
              "taux": {"DD": {"taux": 0.0}}}
    assert _choisir_gzale_ou_zlecaf(_position(5, 0), "DZA", "EGY", zlecaf)["regime"] == "ZLECAF"


# ── Sur le socle ──────────────────────────────────────────────────────────────
@besoin_socle
@pytest.mark.parametrize("origine", sorted(GZALE_ORIGINES_DZA - {"EGY", "TUN"}))
def test_socle_origine_hors_zlecaf_au_droit_de_douane_nul(origine):
    position, _ = socle.position("DZA", "0204501100")
    r = taux_preferentiels(position, "DZA", origine, "0204501100")
    assert r["regime"] == "GZALE"
    assert r["taux"] == {"DD": {"taux": 0.0}}


@besoin_socle
def test_socle_tunisie_garde_la_zlecaf_qui_exonere_aussi_le_daps():
    position, _ = socle.position("DZA", "0204501100")
    r = taux_preferentiels(position, "DZA", "TUN", "0204501100")
    assert r["regime"] == "ZLECAF"
    assert r["taux"]["DAPS"] == {"taux": 0.0}


@pytest.fixture
def client():
    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_gzale", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_gzale"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


@besoin_socle
def test_route_maroc_vers_algerie_nomme_la_gzale_et_garde_le_daps(client):
    reponse = client.post(
        "/calcul",
        json={"destination": "DZA", "origine": "MAR", "code_sh": "0204501100", "valeur_cif": 100000},
    )
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["regime_commercial"]["regime"] == "GZALE"
    assert corps["preference_zlecaf"]["applique"] is False
    assert corps["preference_zlecaf"]["statut"] == "REGIME_GZALE"
    lignes = {ligne["code"]: ligne for ligne in corps["preference"]["lignes"]}
    assert lignes["DD"]["montant"] == 0
    assert lignes["DAPS"]["montant"] == 70000
