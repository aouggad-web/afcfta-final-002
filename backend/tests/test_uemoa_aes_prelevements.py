"""UEMOA et AES : PCS à 0,8 % (acte additionnel n° 01/2019/CCEG/UEMOA) ; PC-AES
dont sont exclues les marchandises originaires de l'AES et de l'UEMOA
(décision du 28/03/2025, art. 1er et 4) ; Burkina Faso : taxes sur les boissons,
le café et le thé, les noix de colas, et TVA sur la valeur en douane + tous les
droits et taxes de porte (CGI art. 310, 4°) ; Niger : exonérations de TVA de la
loi de finances 2026 (CGI art. 322 nouveau).
Fiches : UEMOA_AES_PCS_PC-AES_2026-10-11.json, BFA_prelevements_TVA_2026-10-11.json,
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


def test_cola_pays_tiers(bfa):
    """Cola, origine Maroc : DD 20 % : 200 ; RS 10 ; PCS 8 ; PC-AES 5 ; taxe 10 % sur
    1 223 ; TVA 18 % sur la valeur et tous ces droits."""
    etat, lignes = _calcul(bfa["0802700000"], "MAR")
    assert etat == "COMPLET"
    assert lignes["TNC"]["base"] == 1223.0 and lignes["TNC"]["montant"] == 122.3
    assert lignes["TVA"]["base"] == 1345.3


def test_cola_origine_uemoa_sans_pcs_ni_pc_aes(bfa):
    etat, lignes = _calcul(bfa["0802700000"], "SEN")
    assert "PCS" not in lignes and "PC-AES" not in lignes
    assert lignes["TNC"]["base"] == 1210.0 and lignes["TVA"]["base"] == 1331.0
    assert etat == "COMPLET"


def test_cafe_taxe_12(bfa):
    etat, lignes = _calcul(bfa["0901211000"], "MAR")
    assert lignes["TCT"]["taux_pct"] == 12.0 and etat == "COMPLET"


def test_boisson_energisante_50_et_biere_sans_taux(bfa):
    _, lignes = _calcul(bfa["2202991000"], "MAR")
    assert lignes["TSB"]["taux_pct"] == 50.0
    etat, lignes = _calcul(bfa["2203001000"], "MAR")
    assert lignes["TSB"]["montant"] is None and etat != "COMPLET"


def test_eaux_et_vinaigres_exoneres_de_la_taxe(bfa):
    for code in ("2201101000", "2209001000"):
        assert "TSB" not in {d["code"] for d in bfa[code]["droits"]}


def test_droits_du_tec_2022(bfa):
    dd = {c: next(d["taux"] for d in bfa[c]["droits"] if d["code"] == "DD") for c in ("0701900000", "0703100000", "1511100000")}
    assert dd == {"0701900000": 35.0, "0703100000": 35.0, "1511100000": 10.0}


def test_niger_tva_exoneree(ner):
    tva = lambda code: next(d["taux"] for d in ner[code]["droits"] if d["code"] == "TVA")  # noqa: E731
    assert tva("1001110000") == 0.0
    assert tva("9022140000") == 0.0
    assert tva("9402109000") == 19.0
    assert tva("1006301000") is None
