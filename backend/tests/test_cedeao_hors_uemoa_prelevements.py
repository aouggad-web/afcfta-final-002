"""Gambie, Liberia, Sierra Leone : sans la redevance statistique ni
l'assiette de TVA recopiées du tarif béninois ; TVA/GST sur la valeur en douane
et tous les droits et taxes (IVAT Act 2012 s.171 ;
Revenue Code s.1004(d) ; GST Act 2009 s.26). Fiche :
CEDEAO_hors_UEMOA_prelevements_2026-10-12.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, calculer

SOCLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
PAYS = ("GMB", "LBR", "SLE")

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(SOCLE_DIR, f"{iso}.json")) for iso in PAYS),
    reason="socle absent (gitignoré)",
)


def _positions(iso):
    with open(os.path.join(SOCLE_DIR, f"{iso}.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, origine=None):
    position, _ = exoneration_origine.appliquer(position, origine)
    r = calculer(position, 10000, devise_position="XXX")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


@pytest.mark.parametrize("iso", PAYS)
def test_ni_redevance_statistique_ni_assiette_beninoise(iso):
    for position in _positions(iso).values():
        codes = [d["code"] for d in position["droits"]]
        assert "RS" not in codes
        assert codes[-1] == "TVA"
        tva = next(d for d in position["droits"] if d["code"] == "TVA")
        assert tva["assiette"] == "CIF+TOUS_SAUF_TVA"
        assert tva["source"] == "fiche CEDEAO_hors_UEMOA_prelevements_2026-10-12.json"


@pytest.mark.parametrize(
    "iso, taux_tva, attendus",
    [
        ("GMB", 15.0, {"PCC": 50.0, "FT": 155.0, "PUA": 20.0}),
        ("LBR", 12.0, {"PCC": 50.0, "CUF": 150.0}),
        ("SLE", 15.0, {"PCC": 50.0, "PUA": 20.0}),
    ],
)
def test_tva_sur_tous_les_droits_origine_tierce(iso, taux_tva, attendus):
    """Chevaux reproducteurs (DD 5 %), CIF 10 000, origine Chine."""
    etat, lignes = _lignes(_positions(iso)["0101210000"], "CHN")
    assert etat == COMPLET
    assert {c: lignes[c]["montant"] for c in attendus} == attendus
    base = 10000 + 500 + sum(attendus.values())
    assert lignes["TVA"]["base"] == base
    assert lignes["TVA"]["montant"] == pytest.approx(base * taux_tva / 100)


@pytest.mark.parametrize("iso", ("GMB", "SLE"))
def test_prelevement_ua_retire_pour_une_origine_africaine(iso):
    _, lignes = _lignes(_positions(iso)["0101210000"], "MAR")
    assert "PUA" not in lignes


@pytest.mark.parametrize(
    "iso, origine, attendus, base_tva",
    [
        ("GMB", "CHN", {"DD": 500.0, "PCC": 50.0, "FT": 155.0, "PUA": 20.0}, 10725.0),
        ("GMB", "NGA", {"DD": 500.0, "FT": 155.0}, 10655.0),
        ("LBR", "CHN", {"DD": 500.0, "PCC": 50.0, "CUF": 150.0}, 10700.0),
        ("SLE", "MAR", {"DD": 500.0, "PCC": 50.0}, 10550.0),
    ],
)
def test_ancien_chemin_suit_le_socle(iso, origine, attendus, base_tva):
    """/authentic-tariffs : sans redevance statistique, TVA/GST de la loi sur
    tous les droits, prélèvements nationaux, exonérations selon l'origine."""
    from services.authentic_tariff_service import calculate_import_taxes

    r = calculate_import_taxes(iso, "0101210000", 10000, origin_country=origine)
    etapes = {e["code"]: e for e in r["calculation_steps"]}
    assert {c: e["amount"] for c, e in etapes.items() if c != "TVA"} == attendus
    assert etapes["TVA"]["base_value"] == base_tva
    assert etapes["TVA"]["rate_pct"] == {"GMB": 15.0, "LBR": 12.0, "SLE": 15.0}[iso]
