"""UEMOA et AES : PCS à 0,8 % (acte additionnel n° 01/2019/CCEG/UEMOA) ; PC-AES
dont sont exclues les marchandises originaires de l'AES et de l'UEMOA
(décision du 28/03/2025, art. 1er et 4) ; Burkina Faso : droits du TEC 2022 ;
Niger : exonérations de TVA de la loi de finances 2026 (CGI art. 322 nouveau).
Fiches : UEMOA_AES_PCS_PC-AES_2026-10-11.json, BFA_droits_TEC_2026-10-11.json,
NER_TVA_exonerations_LF2026_2026-10-11.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE_DIR, "BFA.json")), reason="socle absent (gitignoré)"
)


def _positions(iso):
    with open(os.path.join(SOCLE_DIR, f"{iso}.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


@pytest.fixture(scope="module")
def bfa():
    return _positions("BFA")


@pytest.fixture(scope="module")
def ner():
    return _positions("NER")


def _calcul(position, origine=None):
    position, _ = exoneration_origine.appliquer(position, origine)
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


@pytest.mark.parametrize("iso", ["BFA", "NER", "BEN", "TGO", "GNB"])
def test_pcs_a_0_8(iso):
    positions = _positions(iso)
    assert {d["taux"] for p in positions.values() for d in p["droits"] if d["code"] == "PCS"} == {0.8}


@pytest.mark.parametrize(
    "origine, retires",
    [("NER", ["PCS", "PC-AES"]), ("SEN", ["PCS", "PC-AES"]), ("GHA", []), ("MAR", []), (None, [])],
)
def test_pc_aes_selon_l_origine(bfa, origine, retires):
    _, exonerations = exoneration_origine.appliquer(bfa["0802700000"], origine)
    assert [e["code"] for e in exonerations] == retires


def test_pc_aes_retire_de_la_base_de_tva(bfa):
    """Cola, origine Sénégal (UEMOA) : ni PCS ni PC-AES, et la base de la TVA les omet ;
    origine Maroc : les deux sont dus et entrent dans la base."""
    _, tiers = _calcul(bfa["0802700000"], "MAR")
    etat, uemoa = _calcul(bfa["0802700000"], "SEN")
    assert {"PCS", "PC-AES"} <= set(tiers) and not {"PCS", "PC-AES"} & set(uemoa)
    assert tiers["TVA"]["base"] - uemoa["TVA"]["base"] > 13.0
    assert etat == "COMPLET"


def test_droits_du_tec_2022(bfa):
    dd = {c: next(d["taux"] for d in bfa[c]["droits"] if d["code"] == "DD") for c in ("0701900000", "0703100000", "1511100000")}
    assert dd == {"0701900000": 35.0, "0703100000": 35.0, "1511100000": 10.0}


def test_niger_tva_exoneree(ner):
    tva = lambda code: next(d["taux"] for d in ner[code]["droits"] if d["code"] == "TVA")  # noqa: E731
    assert tva("1001110000") == 0.0
    assert tva("9022140000") == 0.0
    assert tva("9402109000") == 19.0
    assert tva("1006301000") is None
