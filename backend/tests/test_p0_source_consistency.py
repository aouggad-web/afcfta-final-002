"""Audit regressions using the repository's collected tariff positions."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import currencies.service as currency_service
import pytest
ROOT = Path(__file__).resolve().parents[2]
_MODULE_PATH = ROOT / "scripts" / "normalize_crawled.py"
_spec = importlib.util.spec_from_file_location("normalize_crawled", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
normalize_gha_canonical = _mod.normalize_gha_canonical


@pytest.fixture(autouse=True)
def local_sources(monkeypatch):
    monkeypatch.setattr(currency_service, "get_by_country", lambda _: None)


# L'Algérie ne se calcule plus que par `POST /calcul` : ses deux cas y sont tenus.
def test_dza_collected_duty_agrees_in_listing_rate_and_amount():
    from routes.calcul import DemandeCalcul, calcul

    result = calcul(
        DemandeCalcul(destination="DZA", origine="SEN", code_sh="2201101100", valeur_cif=1000)
    )
    dd = next(l for l in result["npf"]["lignes"] if l["code"] == "DD")
    assert dd["taux_pct"] == 30
    assert dd["montant"] == 300


def test_dza_missing_duty_does_not_produce_complete_total():
    """Chapitre 98 du tarif algérien — « Effets personnels » : hors importation
    commerciale, aucun droit de douane n'y est perçu (T.C.S et PRCT le sont).
    L'absence de droit y est cohérente, et non lacunaire — la ligne exerce
    quand même le chemin qu'il faut tenir : un droit absent ne devient ni 0 ni
    exception. Le cas algérien était auparavant 1001110000, blé dur de semence :
    un droit que le MIROIR conformepro.dz ne publiait pas, alors que l'e-service
    DGD le donne à 0,00 %. Le cas est reporté sur une position dont la source
    PRIMAIRE elle-même ne publie aucun droit."""
    from routes.calcul import DemandeCalcul, calcul

    result = calcul(
        DemandeCalcul(destination="DZA", origine="SEN", code_sh="9810100000", valeur_cif=1000)
    )
    assert result["npf"]["etat"] == "PARTIEL"
    assert "DD" in {m["code"] for m in result["npf"]["manques"]}


def test_ghana_normalization_preserves_all_national_children_and_zero_duties():
    data = json.loads((ROOT / "backend/data/crawled/GHA_tariffs.json").read_text())
    original = copy.deepcopy(data)
    positions = normalize_gha_canonical(data, "GHA")
    expected = {p["code"]: p for line in data["tariff_lines"] for p in line["sub_positions"]}
    assert len(positions) == len(expected) == 6129
    assert {p["national_code"] for p in positions} == set(expected)
    for position in positions:
        taxes = position["taxes"]
        duty = next(t for t in taxes if t["code"] == "DD")
        assert duty["rate_pct"] == expected[position["national_code"]]["dd"]
        assert sum(t.get("is_vat", False) for t in taxes) == 1
    assert data == original
