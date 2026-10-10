"""Libye : aucun texte trouvé ne fonde la « Port Services Tax » à 4 % ni la
« Production Tax » à 2 % ; le socle les sert sans taux. Fiche :
LBY_TSP_TP_taux_2026-10-10.json."""

import json
import os

import pytest
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "LBY.json"
)
besoin_socle = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


@besoin_socle
def test_tsp_et_tp_sont_servies_sans_taux_avec_leur_motif(positions):
    lignes = [d for p in positions.values() for d in p["droits"] if d["code"] in ("TSP", "TP")]
    assert len(lignes) == 2 * len(positions)
    assert all(d.get("taux") is None for d in lignes)
    assert all("n° 393/2025" in d["note"] for d in lignes if d["code"] == "TSP")
    assert all("loi n° 19/1992" in d["note"] for d in lignes if d["code"] == "TP")


@besoin_socle
def test_le_moteur_ne_sert_aucun_taux_pour_tsp_et_tp(positions):
    r = calculer(positions["01012100"], 10000, devise_position="LYD")
    lignes = {ligne["code"]: ligne for ligne in r["npf"]["lignes"]}
    assert r["npf"]["etat"] != COMPLET
    assert lignes["DD"]["montant"] == pytest.approx(500.0)
    assert lignes["TSP"]["taux_pct"] is None and lignes["TP"]["taux_pct"] is None
    assert "n° 393/2025" in lignes["TSP"]["note"]
    assert {"TSP", "TP"} <= {m["code"] for m in r["npf"]["manques"]}
