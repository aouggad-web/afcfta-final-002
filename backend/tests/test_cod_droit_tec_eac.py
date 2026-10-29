"""RDC : le socle ne sert pas le TEC EAC 2022 comme droit de douane. La RDC
ne l'applique pas (fiche COD_application_2026-09-27.json) ; son barème DGDA
n'est pas obtenu, le droit est donc indisponible."""

import importlib.util
import json
import os

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
