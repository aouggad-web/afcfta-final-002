"""Tests hors-ligne du script ETL de rafraîchissement des cours mondiaux."""

import os
import sys

import pytest

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from etl import update_world_market_prices as etl  # noqa: E402


def _chart_payload(price, market_time=1783000000, currency="USD", symbol="CC=F"):
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": price,
                        "regularMarketTime": market_time,
                        "currency": currency,
                        "symbol": symbol,
                    }
                }
            ]
        }
    }


def test_parse_chart_response_extracts_price_and_market_date():
    q = etl.parse_chart_response(_chart_payload(5877.16))
    assert q["price"] == 5877.16
    assert q["as_of"] == "2026-07-02"  # dérivée du timestamp de l'API, pas de l'horloge locale
    assert q["currency"] == "USD"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"chart": {"result": []}},
        _chart_payload(None),
        _chart_payload(-1),
        _chart_payload(5877.16, market_time=None),
    ],
)
def test_parse_chart_response_rejects_unusable_payloads(payload):
    with pytest.raises(ValueError):
        etl.parse_chart_response(payload)


def test_build_entry_converts_cocoa_tonnes_to_usd_per_kg():
    spec = etl.SYMBOLS["CC=F"]
    quote = {"price": 5877.16, "as_of": "2026-07-08", "currency": "USD"}
    entry = etl.build_entry("CC=F", spec, quote)
    assert entry["hs"] == "1801"
    assert entry["usd_per_kg"] == pytest.approx(5.87716)
    assert entry["raw_quote"] == "5877.16 USD/tonne"
    assert entry["as_of"] == "2026-07-08"
    assert "Yahoo Finance" in entry["source"]


def test_build_entry_converts_coffee_cents_per_lb():
    # ICE Coffee C est coté en CENTS/lb — Yahoo le signale via currency="USd".
    spec = etl.SYMBOLS["KC=F"]
    quote = {"price": 315.24, "as_of": "2026-07-08", "currency": "USd"}
    entry = etl.build_entry("KC=F", spec, quote)
    assert entry["usd_per_kg"] == pytest.approx(6.9499, abs=1e-3)
    assert entry["raw_quote"] == "315.24 ¢/lb"


def test_build_entry_uses_currency_field_not_symbol_guess_for_cents_scale():
    # Le bug corrigé : NE PAS supposer l'échelle cents/dollars par contrat.
    # Même unité physique (lb), même symbole -> résultat x100 selon la
    # devise réellement renvoyée par l'API pour CETTE cotation précise.
    spec = etl.SYMBOLS["HG=F"]
    cents_quote = {"price": 605.75, "as_of": "2026-07-08", "currency": "USd"}
    dollars_quote = {"price": 6.0575, "as_of": "2026-07-08", "currency": "USD"}
    cents_entry = etl.build_entry("HG=F", spec, cents_quote)
    dollars_entry = etl.build_entry("HG=F", spec, dollars_quote)
    assert cents_entry["usd_per_kg"] == pytest.approx(dollars_entry["usd_per_kg"], rel=1e-9)
    assert cents_entry["raw_quote"] == "605.75 ¢/lb"
    assert dollars_entry["raw_quote"] == "6.0575 USD/lb"


def test_build_entry_rejects_implausible_conversion():
    # Si l'API changeait d'unité (ex. cacao coté en ¢ au lieu de USD/tonne),
    # la conversion sortirait des bornes et doit être REJETÉE, pas écrite.
    spec = etl.SYMBOLS["CC=F"]
    quote = {"price": 587716.0, "as_of": "2026-07-08", "currency": "USD"}
    with pytest.raises(ValueError, match="vraisemblance"):
        etl.build_entry("CC=F", spec, quote)


def test_build_entry_rejects_unexpected_currency():
    spec = etl.SYMBOLS["GC=F"]
    quote = {"price": 4110.6, "as_of": "2026-07-09", "currency": "EUR"}
    with pytest.raises(ValueError, match="devise"):
        etl.build_entry("GC=F", spec, quote)


def test_every_symbol_has_plausibility_bounds():
    for spec in etl.SYMBOLS.values():
        assert spec["hs"] in etl.PLAUSIBILITY_USD_PER_KG
        assert spec["physical_unit"] in etl._PHYSICAL_UNITS


def test_symbols_target_hs_codes_known_to_the_backend():
    from services import shipment_estimator as se

    for spec in etl.SYMBOLS.values():
        assert spec["hs"] in se._WORLD_MARKET_BENCHMARKS, (
            f"SH {spec['hs']} rafraîchi par l'ETL mais absent des benchmarks statiques "
            "du backend — le repli daté n'existerait pas"
        )
