"""
Tests du proxy d'exportation (repli quand FAO/USGS/UNIDO ne couvrent pas un
produit dans le module Opportunités).

Demande utilisateur : « rajouter l'historique des exports du SH4/SH6 dans les
données de la production si elles ne sont pas répertoriées et rapatriées de FAO
et UNIDO ». Le proxy est construit à partir de l'historique OEC/BACI mais
étiqueté strictement comme un INDICE (borne basse), jamais une mesure de
production — avec un garde-fou réexport supplémentaire pour les hubs.

`build_export_proxy_capacity` est une fonction pure : ces tests ne font aucune
requête réseau, ils lui passent directement une réponse OEC synthétique.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import production_capacity_service as pcs  # noqa: E402


def _oec_history(**overrides):
    """Réponse OEC synthétique type get_country_hs6_history (exports croissants)."""
    base = {
        "country_iso3": "GHA",
        "country_name": "Ghana",
        "hs_code": "870380",
        "hs4_code": "8703",
        "level": "hs6",
        "match_level": "hs6",
        "currency": "USD",
        "has_data": True,
        "exports": [
            {"year": 2020, "trade_value": 1_000_000.0, "quantity": 500.0},
            {"year": 2021, "trade_value": 0, "quantity": 0, "no_data": True},
            {"year": 2022, "trade_value": 2_000_000.0, "quantity": 900.0},
            {"year": 2023, "trade_value": 4_000_000.0, "quantity": 1500.0},
        ],
    }
    base.update(overrides)
    return base


def test_proxy_built_from_export_history():
    r = pcs.build_export_proxy_capacity("870380", _oec_history())
    assert r["available"] is True
    assert r["is_proxy"] is True
    assert r["basis"] == "exports_proxy"
    # Dernière année valide = 2023 (l'année no_data 2021 est ignorée)
    assert r["latest_year"] == 2023
    assert r["latest_value"] == 4_000_000.0
    assert r["match_level"] == "HS6"
    assert r["source"]["institution"].startswith("OEC")
    # Série filtrée (3 années réelles, pas l'année no_data)
    assert [p["year"] for p in r["timeseries"]] == [2020, 2022, 2023]


def test_proxy_caveat_present_and_marks_lower_bound():
    r = pcs.build_export_proxy_capacity("870380", _oec_history())
    assert "PROXY" in r["proxy_caveat"]
    assert "BORNE BASSE" in r["proxy_caveat"]
    # Pas hub -> pas le caveat hub-spécifique (le caveat de base mentionne bien
    # les réexportations comme limite générale, ce n'est pas le caveat hub).
    assert "hub de réexportation" not in r["proxy_caveat"]
    assert r["is_reexport_hub"] is False


def test_cagr_computed_from_first_and_last_valid_year():
    r = pcs.build_export_proxy_capacity("870380", _oec_history())
    # 1M -> 4M sur 3 ans (2020->2023) : (4)^(1/3)-1 ≈ 58,7 %
    assert r["cagr_pct"] is not None
    assert 55.0 < r["cagr_pct"] < 62.0


def test_reexport_hub_adds_extra_caveat():
    hist = _oec_history(country_iso3="MUS", country_name="Maurice")
    r = pcs.build_export_proxy_capacity("870380", hist, is_reexport_hub=True)
    assert r["is_reexport_hub"] is True
    assert "réexportation" in r["proxy_caveat"]
    assert "origine ZLECAf" in r["proxy_caveat"]


def test_hs4_match_level_labelled():
    r = pcs.build_export_proxy_capacity("8703", _oec_history(match_level="hs4"))
    assert r["match_level"] == "HS4"


def test_no_export_data_is_unavailable():
    # has_data False
    r = pcs.build_export_proxy_capacity("870380", _oec_history(has_data=False))
    assert r["available"] is False
    assert r["reason"] == "no_export_data"


def test_error_history_is_unavailable():
    r = pcs.build_export_proxy_capacity("870380", {"error": "Country XXX not found"})
    assert r["available"] is False
    assert r["reason"] == "no_export_data"


def test_all_years_no_data_is_unavailable():
    hist = _oec_history(
        exports=[
            {"year": 2022, "trade_value": 0, "quantity": 0, "no_data": True},
            {"year": 2023, "trade_value": 0, "quantity": 0, "no_data": True},
        ]
    )
    # has_data True mais aucune valeur exploitable -> indisponible
    r = pcs.build_export_proxy_capacity("870380", hist)
    assert r["available"] is False
    assert r["reason"] == "no_export_data"


def test_none_history_is_unavailable():
    r = pcs.build_export_proxy_capacity("870380", None)
    assert r["available"] is False


def test_single_year_has_value_but_no_cagr():
    hist = _oec_history(exports=[{"year": 2023, "trade_value": 3_000_000.0, "quantity": 1000.0}])
    r = pcs.build_export_proxy_capacity("870380", hist)
    assert r["available"] is True
    assert r["latest_value"] == 3_000_000.0
    assert r["cagr_pct"] is None
