"""
Tests du signal d'assemblage par proxy d'intrants (services/manufacturing_proxy_service.py).

Contexte : FAOSTAT/USGS/UNIDO ne mesurent pas de production physique pour les
biens d'équipement électroménager (réfrigérateurs, téléviseurs...) — le module
Opportunités perdait tout ancrage réel sur ce segment. Ce service dérive un
signal INDIRECT d'assemblage local à partir des importations réelles (OEC/UN
Comtrade) du composant-clé (compresseurs, modules d'affichage), jamais présenté
comme une production mesurée.

Tests purs : les appels réseau (real_trade_service / oec_service) sont
monkeypatchés — aucun appel API réel.
"""

import asyncio
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import manufacturing_proxy_service as proxy_mod  # noqa: E402


def test_list_proxy_chapters_covers_fridges_ac_and_tv():
    chapters = proxy_mod.list_proxy_chapters()
    hs_codes = {c["hs_code"] for c in chapters}
    assert {"8418", "8415", "8528"} <= hs_codes


def test_match_proxy_accepts_hs6_and_hs4():
    assert proxy_mod._match_proxy("841821") == (
        "8418",
        proxy_mod._INPUT_PROXY_CHAPTERS["8418"],
    )
    assert proxy_mod._match_proxy("8528") == (
        "8528",
        proxy_mod._INPUT_PROXY_CHAPTERS["8528"],
    )


def test_match_proxy_returns_none_for_uncovered_hs():
    assert proxy_mod._match_proxy("010121") is None
    assert proxy_mod._match_proxy("") is None
    assert proxy_mod._match_proxy(None) is None


def test_estimate_assembly_signal_unmapped_hs_returns_unavailable():
    result = asyncio.run(proxy_mod.estimate_assembly_signal("MAR", "0101"))
    assert result == {
        "available": False,
        "reason": "no_proxy_mapping",
        "hs_code": "0101",
    }


def test_estimate_assembly_signal_uses_real_input_imports(monkeypatch):
    async def fake_country_imports(iso3, hs6, year=2024):
        assert hs6 == "841430"
        return {
            "available": True,
            "import_value_usd": 12_500_000.0,
            "hs_code": hs6,
            "year": 2023,
            "source": "OEC / BACI",
        }

    async def fake_top_importers(hs6, year):
        return {
            "hs_code": hs6,
            "year": year,
            "data": [
                {"country_iso3": "EGY", "country_name": "Égypte", "import_value": 40_000_000},
                {"country_iso3": "MAR", "country_name": "Maroc", "import_value": 12_500_000},
                {"country_iso3": "TUN", "country_name": "Tunisie", "import_value": 3_000_000},
            ],
            "source": "OEC/BACI",
        }

    monkeypatch.setattr(
        proxy_mod.real_trade_service, "get_country_product_imports", fake_country_imports
    )
    monkeypatch.setattr(proxy_mod.oec_service, "get_top_african_importers", fake_top_importers)

    result = asyncio.run(proxy_mod.estimate_assembly_signal("MAR", "8418"))
    assert result["available"] is True
    assert result["method"] == "input_proxy_estimate"
    assert result["hs_code"] == "8418"
    assert "methodology" in result and "PAS une production mesurée" in result["methodology"]

    signal = result["input_signals"][0]
    assert signal["input_hs6"] == "841430"
    assert signal["country_import_usd"] == 12_500_000.0
    assert signal["continental_ranking"]["rank"] == 2
    assert signal["continental_ranking"]["total_countries"] == 3
    assert signal["continental_ranking"]["top_importers"][0]["country_iso3"] == "EGY"


def test_estimate_assembly_signal_no_imports_observed(monkeypatch):
    async def fake_country_imports(iso3, hs6, year=2024):
        return {"available": False}

    monkeypatch.setattr(
        proxy_mod.real_trade_service, "get_country_product_imports", fake_country_imports
    )

    result = asyncio.run(proxy_mod.estimate_assembly_signal("SYC", "8528"))
    assert result["available"] is False
    assert result["input_signals"][0]["country_import_usd"] is None
    assert result["input_signals"][0]["continental_ranking"] == {"available": False}


def test_shared_compressor_input_covers_both_fridges_and_ac():
    fridge = proxy_mod._INPUT_PROXY_CHAPTERS["8418"]["inputs"][0]["hs6"]
    ac = proxy_mod._INPUT_PROXY_CHAPTERS["8415"]["inputs"][0]["hs6"]
    assert fridge == ac == "841430"
