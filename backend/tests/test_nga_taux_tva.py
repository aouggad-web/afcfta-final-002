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


def test_ni_la_recherche_ni_l_autre_porte_ne_servent_ces_taux(monkeypatch):
    """La recherche par mot-clé et GET /authentic-tariffs/calculate lisent la
    collecte brute : la TVA à 17,5 % n'y est ni affichée, ni comptée dans un
    total, ni liquidée. Une position ordinaire garde ses 7,5 %."""
    from services import authentic_tariff_service as svc

    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    ligne = next(r for r in svc.search_tariff_lines("NGA", "1605580000") if r.get("national_code") == "1605580000")
    assert ligne["tva_rate"] is None and ligne["total_rate"] is None
    assert svc.search_tariff_lines("NGA", "Bolting cloth")  # un taux absent ne fait plus planter la recherche

    refus = svc.calculate_import_taxes("NGA", "1605580000", 10000)
    assert refus["error_detail"]["missing_or_non_ad_valorem_taxes"] == ["TVA"]
    assert next(
        r for r in svc.search_tariff_lines("NGA", "1605100000") if r.get("national_code") == "1605100000"
    )["tva_rate"] == 7.5


def test_la_ligne_tarifaire_et_le_detail_des_taxes_ne_servent_pas_ces_taux(monkeypatch):
    """GET /authentic-tariffs/country/NGA/line/… et /taxes/… lisent la ligne
    ETL, PostgreSQL ou collectée : le taux n'y figure plus, ni dans le total."""
    import asyncio

    from routes import authentic_tariffs
    from services import authentic_tariff_service as svc

    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    ligne = asyncio.run(authentic_tariffs.get_tariff_line_endpoint("NGA", "160558", "fr"))["tariff_line"]
    assert ligne["vat_rate"] is None and ligne["total_taxes_pct"] is None
    taxes = asyncio.run(authentic_tariffs.get_taxes_detail_endpoint("NGA", "252510", "fr"))["taxes"]
    assert [t["rate"] for t in taxes if t["tax"] == "VAT"] == [None]
    assert svc.get_tariff_line("NGA", "160510")["vat_rate"] == 7.5

    class PostgreSQL:
        def get_regulatory_details(self, *_):
            return {"success": True, "measures": [{"code": "VAT", "rate": 17.5}], "taxes": {"vat_rate": 17.5}}

        def get_country_info(self, *_):
            return {}

        def get_sub_positions(self, *_):
            return []

    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: PostgreSQL())
    ligne = svc.get_tariff_line("NGA", "1605580000")
    assert ligne["vat_rate"] is None and [t["rate"] for t in ligne["taxes_detail"]] == [None]
