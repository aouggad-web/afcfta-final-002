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
    }
    compteurs = {k: 0 for k in ("taux_indisponibles", "droits_specifiques", "assiettes_indisponibles",
                                "assiettes_source", "assiettes_table")}
    bs._droit_douane_rdc(positions, compteurs)
    for position in positions.values():
        dd = position["droits"][0]
        assert dd["taux"] is None
        assert dd["note"] == bs.NOTE_DD_COD
        assert dd["libelle"] == "Droit de douane"
        assert not {"specifique", "compose", "regle_composee", "expression_brute"} & set(dd)
    assert positions["15111000"]["droits"][1]["taux"] == 16.0
    assert compteurs["taux_indisponibles"] == 2


@avec_socle
def test_aucun_droit_de_douane_rdc_n_est_liquide():
    with open(SOCLE_COD, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code in ("15111000", "25232900", "02011000", "72111400"):
        lignes = {ligne["code"]: ligne for ligne in calculer(positions[code], 1000.0)["npf"]["lignes"]}
        assert lignes["DD"]["statut"] != "CALCULE", code
    assert all(d["taux"] is None for p in positions.values() for d in p["droits"] if d["code"] == "DD")


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


def test_le_tarif_collecte_ne_sert_pas_le_tec_eac_comme_droit_rdc():
    """backend/data/tariffs/COD_tariffs.json (servi par /api/tariff-data/COD) :
    aucun droit de douane, ni à la ligne ni à la sous-position."""
    with open(os.path.join(BACKEND, "data", "tariffs", "COD_tariffs.json"), encoding="utf-8") as f:
        donnees = json.load(f)
    lignes = donnees["tariff_lines"]
    assert all(ligne["dd_rate"] is None and ligne["total_taxes_pct"] is None for ligne in lignes)
    assert all(sp["dd"] is None for ligne in lignes for sp in ligne["sub_positions"])
    assert all(t["rate"] is None for ligne in lignes for t in ligne["taxes_detail"] if t["tax"] == "CET")
    assert donnees["summary"]["dd_rate_range"] == {"min": None, "max": None, "avg": None}


def test_le_resume_par_chapitre_tolere_un_droit_indisponible():
    import asyncio

    spec = importlib.util.spec_from_file_location("routes_tariff_data_cod", os.path.join(BACKEND, "routes", "tariff_data.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    resume = asyncio.run(module.get_country_tariff_summary("COD"))
    chapitre = resume["by_chapter"]["25"]
    assert chapitre["dd_min"] is None and chapitre["dd_avg"] is None and chapitre["tariff_lines"] > 0
