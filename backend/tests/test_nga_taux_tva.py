"""Nigéria : la TVA est à 7,5 % (s.148) ou à 0 % (s.187) ; un autre taux collecté
au portail n'est servi par aucun chemin de calcul. Fiche : NGA_taux_TVA_2026-10-08.json."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "NGA.json")
besoin_socle = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _tva(position):
    return next(d for d in position["droits"] if d["code"] == "TVA")


@besoin_socle
@pytest.mark.parametrize("code, collecte", [("1605580000", "17,5"), ("2525100000", "1")])
def test_un_taux_de_tva_inconnu_de_la_loi_reste_a_completer(positions, code, collecte):
    tva = _tva(positions[code])
    assert tva["taux"] is None
    assert f"Taux de TVA collecté au portail : {collecte} %." in tva["note"]
    assert calculer(positions[code], 1000, devise_position="NGN")["npf"]["etat"] != COMPLET


@besoin_socle
def test_seuls_7_5_et_0_sont_servis(positions):
    taux = {_tva(p).get("taux") for p in positions.values() if any(d["code"] == "TVA" for d in p["droits"])}
    assert taux - {None} == {7.5, 0.0}


def test_l_autre_chemin_ne_sert_pas_non_plus_ces_taux():
    """normalize_nga alimente l'autre chemin de calcul et la recherche par
    mot-clé : la même règle s'y applique, la valeur collectée restant lisible."""
    chemin = Path(__file__).resolve().parents[2] / "scripts" / "normalize_crawled.py"
    spec = importlib.util.spec_from_file_location("normalize_crawled_tva", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    normalisees = module.normalize_nga(
        {
            "positions": [
                {"code_clean": "1605580000", "taxes": [{"code": "VAT", "rate_pct": 17.5, "raw_value": "17.5%"}]},
                {"code_clean": "0101210000", "taxes": [{"code": "VAT", "rate_pct": 7.5, "raw_value": "7.5%"}]},
            ]
        },
        "NGA",
    )
    tva = {p["national_code"]: next(t for t in p["taxes"] if t["code"] == "TVA") for p in normalisees}
    assert tva["1605580000"]["rate_pct"] is None and tva["1605580000"]["raw_value"] == "17.5%"
    assert "Nigeria Tax Act 2025" in tva["1605580000"]["note"]
    assert tva["0101210000"]["rate_pct"] == 7.5


