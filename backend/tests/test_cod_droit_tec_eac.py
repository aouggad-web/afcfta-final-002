"""RDC : le socle ne sert pas le TEC EAC 2022 comme droit de douane. La RDC
ne l'applique pas (fiche COD_application_2026-09-27.json) ; son barème DGDA
n'est pas obtenu, le droit est donc indisponible."""

import importlib.util
import json
import os
import sys

import pytest

from services import socle
from services.calcul import calculer

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACINE = os.path.dirname(BACKEND)
SOCLE_COD = os.path.join(socle.SOCLE_DIR, "COD.json")
avec_socle = pytest.mark.skipif(not os.path.exists(SOCLE_COD), reason="socle absent (gitignoré)")


def _constructeur():
    spec = importlib.util.spec_from_file_location(
        "build_socle_cod_test", os.path.join(RACINE, "scripts", "build_socle.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_le_droit_lu_au_tec_eac_est_retire():
    """Le taux du TEC EAC est retiré partout ; la loi de finances 2026 (annexe XV) en fixe un pour certaines positions."""
    bs = _constructeur()
    positions = {
        "15111000": {"droits": [
            {"code": "DD", "famille": "droit", "taux": 0.0, "assiette": "CIF"},
            {"code": "TVA", "famille": "tva", "taux": 16.0, "assiette": "CIF+DD"},
        ]},
        "10061000": {"droits": [
            {"code": "DD", "famille": "droit", "taux": 75.0, "assiette": "CIF",
             "specifique": {"montant": 345.0}, "compose": True, "regle_composee": "LE_PLUS_ELEVE",
             "expression_brute": "75% or $345/MT whichever is higher"},
        ]},
        "31023000": {"droits": [{"code": "DD", "famille": "droit", "taux": 0.0, "assiette": "CIF"}]},
    }
    compteurs = {k: 0 for k in ("taux_indisponibles", "droits_specifiques", "assiettes_indisponibles",
                                "assiettes_source", "assiettes_table")}
    bs._droit_douane_rdc(positions, compteurs)
    for position in positions.values():
        assert not {"specifique", "compose", "regle_composee", "expression_brute"} & set(position["droits"][0])
    huile = positions["15111000"]["droits"][0]
    assert huile["taux"] == 10.0 and "25/060" in huile["note"] and huile["source"] == bs._SOURCE_DD_COD_LF2026
    assert positions["10061000"]["droits"][0]["taux"] is None
    assert positions["10061000"]["droits"][0]["note"] == bs.NOTE_DD_COD
    # Nitrate d'ammonium : 5 % pour les engrais, 20 % pour les explosifs ; la position ne les distingue pas.
    nitrate = positions["31023000"]["droits"][0]
    assert nitrate["taux"] is None and "5 %" in nitrate["note"] and "20 %" in nitrate["note"]
    assert positions["15111000"]["droits"][1]["taux"] == 16.0
    assert compteurs["taux_indisponibles"] == 2


@avec_socle
def test_droit_de_douane_rdc_seulement_ou_la_loi_de_finances_le_fixe():
    """Taux servi là où le projet de LF 2025 et l'annexe XV (supprimée) de la LF 2026 concordent ; la loi
    rectificative 2026 remet en application les annexes de la LF 2025, dont le texte adopté n'est pas lu."""
    with open(SOCLE_COD, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code, montant in (("15111000", 100.0), ("72111400", 200.0), ("09052000", 50.0), ("40122000", 100.0),
                          ("04072100", 200.0)):
        lignes = {ligne["code"]: ligne for ligne in calculer(positions[code], 1000.0)["npf"]["lignes"]}
        assert lignes["DD"]["montant"] == pytest.approx(montant), code
        # La TVA (16 % de CIF + DD) redevient liquidable.
        assert lignes["TVA"]["montant"] == pytest.approx(0.16 * (1000.0 + montant)), code
    # Taux que seule l'annexe 2026, supprimée, portait ; texte contradictoire ; ligne nationale plus fine ; 72.10
    # (10 % au projet 2025, 20 % en 2026).
    for code in ("25232900", "10061000", "31023000", "73061100", "72109000", "25181000", "25182000", "39191000",
                 "73063000", "72082600", "36020000", "72104900"):
        lignes = {ligne["code"]: ligne for ligne in calculer(positions[code], 1000.0)["npf"]["lignes"]}
        assert lignes["DD"]["statut"] != "CALCULE", code
    assert "supprimée" in next(d for d in positions["73063000"]["droits"] if d["code"] == "DD")["note"]
    avec_taux = [c for c, p in positions.items() for d in p["droits"] if d["code"] == "DD" and d["taux"] is not None]
    assert 40 < len(avec_taux) < 120


@avec_socle
def test_tva_reduite_des_produits_de_la_loi_rectificative_a_etablir():
    """LFR 2026, art. 13 : 8 % « aux acquisitions et ventes » des viandes, du riz, du sucre… ; à l'importation, le
    texte ne tranche pas : la TVA reste à établir, même quand le droit de douane est connu."""
    with open(SOCLE_COD, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    viande = {ligne["code"]: ligne for ligne in calculer(positions["02011000"], 1000.0)["npf"]["lignes"]}
    assert viande["DD"]["montant"] == pytest.approx(200.0) and viande["TVA"]["statut"] != "CALCULE"
    for code in ("10063000", "04021000"):
        tva = next(d for d in positions[code]["droits"] if d["code"] == "TVA")
        assert tva["taux"] is None and "8 %" in tva["note"], code


def test_preference_rdc_eac_sans_libre_circulation():
    """Kenya → RDC : la libre circulation EAC n'est pas servie, et la note le dit."""
    from services.preference import taux_preferentiels

    position = {"droits": [{"code": "DD", "famille": "droit", "taux": None, "assiette": "CIF"}]}
    resultat = taux_preferentiels(position, "COD", "KEN", "15111000")
    assert resultat.get("regime") != "UNION_DOUANIERE" and resultat["union_non_effective"] == "COD"
    assert "n'applique pas le tarif extérieur commun" in resultat["note"]


@avec_socle
def test_route_annonce_que_la_rdc_n_applique_pas_le_tec():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    spec = importlib.util.spec_from_file_location("routes_calcul_cod", os.path.join(BACKEND, "routes", "calcul.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_cod"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)
    for origine in ("KEN", "CHN"):
        corps = client.post("/calcul", json={"destination": "COD", "code_sh": "15111000", "valeur_cif": 1000,
                                             "origine": origine}).json()
        assert corps["union_non_effective"]["pays"] == "COD", origine
        assert corps["regime_commercial"].get("statut") != "LIBRE_CIRCULATION", origine
    corps = client.post("/calcul", json={"destination": "KEN", "code_sh": "15111000", "valeur_cif": 1000,
                                         "origine": "UGA"}).json()
    assert "union_non_effective" not in corps
