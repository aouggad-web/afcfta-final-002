"""Tests hors-ligne de l'ETL de rafraîchissement du fret vraquier (proxy BDRY)."""

import json
import os
import sys
import tempfile

import pytest

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import logistics_bulk_fees_data as bulk  # noqa: E402
from etl import update_bulk_freight_indices as etl  # noqa: E402


def _chart_payload(current, closes, market_time=1783000000):
    """Réponse chart Yahoo minimale : cours courant + série de clôtures."""
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": current,
                        "regularMarketTime": market_time,
                        "symbol": "BDRY",
                    },
                    "indicators": {"quote": [{"close": closes}]},
                }
            ]
        }
    }


# ── compute_multiplier : facteur = niveau / référence ────────────────────────
def test_compute_multiplier_ratio_to_baseline():
    assert etl.compute_multiplier(15.0, 10.0) == 1.5
    assert etl.compute_multiplier(10.0, 10.0) == 1.0


@pytest.mark.parametrize("bad_level", [0, -1, None, "x"])
def test_compute_multiplier_rejects_bad_levels(bad_level):
    with pytest.raises(ValueError):
        etl.compute_multiplier(bad_level, 10.0)


@pytest.mark.parametrize("factor", [5.0, 0.1])
def test_compute_multiplier_rejects_out_of_bounds(factor):
    with pytest.raises(ValueError, match="vraisemblance"):
        etl.compute_multiplier(10.0 * factor, 10.0)


# ── parse_chart_series : extraction cours + série ────────────────────────────
def test_parse_chart_series_extracts_current_and_closes():
    s = etl.parse_chart_series(_chart_payload(12.0, [10.0, 11.0, None, 12.0]))
    assert s["current"] == 12.0
    assert s["as_of"] == "2026-07-02"  # dérivée du timestamp API, pas de l'horloge locale
    assert s["closes"] == [10.0, 11.0, 12.0]  # None filtré


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"chart": {"result": []}},
        _chart_payload(None, [10.0]),
        _chart_payload(-1, [10.0]),
        _chart_payload(12.0, [10.0], market_time=None),
    ],
)
def test_parse_chart_series_rejects_unusable(payload):
    with pytest.raises(ValueError):
        etl.parse_chart_series(payload)


# ── compute_market_factor : cours courant vs moyenne glissante ───────────────
def test_compute_market_factor_uses_series_average_as_baseline():
    closes = [10.0] * 40  # moyenne 10
    info = etl.compute_market_factor({"current": 15.0, "as_of": "2026-07-14", "closes": closes})
    assert info["factor"] == 1.5  # 15 / 10
    assert info["baseline"] == 10.0
    assert info["window_points"] == 40
    assert info["as_of"] == "2026-07-14"


def test_compute_market_factor_rejects_short_series():
    with pytest.raises(ValueError, match="trop courte"):
        etl.compute_market_factor({"current": 12.0, "as_of": "2026-07-14", "closes": [10.0, 11.0]})


def test_compute_market_factor_rejects_out_of_bounds():
    # Cours courant 5x la moyenne → facteur 5, hors bornes → rejeté.
    closes = [10.0] * 40
    with pytest.raises(ValueError, match="vraisemblance"):
        etl.compute_market_factor({"current": 50.0, "as_of": "2026-07-14", "closes": closes})


# ── build_*_entry : provenance ───────────────────────────────────────────────
def test_build_static_entry_is_dated_and_neutral():
    entry = etl.build_static_entry("panamax")
    assert entry["multiplier"] == 1.0
    assert entry["as_of"] == "moyenne 2024"
    assert "Baltic" in entry["source"]
    assert entry["proxy"] == etl.MARKET_PROXY_NAME


def test_build_live_entry_carries_proxy_provenance():
    info = {
        "factor": 1.5,
        "current": 15.0,
        "baseline": 10.0,
        "as_of": "2026-07-14",
        "window_points": 250,
    }
    entry = etl.build_live_entry("capesize", info)
    assert entry["multiplier"] == 1.5
    assert entry["as_of"] == "2026-07-14"
    assert entry["proxy_level"] == 15.0
    assert entry["proxy_baseline_12m"] == 10.0
    assert "BDRY" in entry["source"]
    assert "pas l'indice" in entry["source"].lower()  # étiquetage honnête du proxy


# ── build_payload : live appliqué à toutes les classes vs repli statique ─────
def test_build_payload_live_applies_factor_to_all_classes():
    info = {
        "factor": 1.5,
        "current": 15.0,
        "baseline": 10.0,
        "as_of": "2026-07-14",
        "window_points": 250,
    }
    payload = etl.build_payload(info)
    mults = payload["vessel_class_multipliers"]
    assert set(mults) == set(etl.VESSEL_CLASSES)
    assert all(m["multiplier"] == 1.5 for m in mults.values())
    assert payload["_meta"]["is_live"] is True


def test_build_payload_static_when_no_factor():
    payload = etl.build_payload(None)
    mults = payload["vessel_class_multipliers"]
    assert set(mults) == set(etl.VESSEL_CLASSES)
    assert all(m["multiplier"] == 1.0 for m in mults.values())
    assert payload["_meta"]["is_live"] is False


def test_fetch_market_factor_reads_local_json_seam(monkeypatch):
    # Le chemin BDRY_CHART_JSON permet un test hors-réseau bout-en-bout.
    payload = _chart_payload(15.0, [10.0] * 40)
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(payload, fh)
    fh.close()
    monkeypatch.setenv("BDRY_CHART_JSON", fh.name)
    try:
        info = etl.fetch_market_factor()
        assert info is not None
        assert info["factor"] == 1.5
    finally:
        os.unlink(fh.name)


def test_fetch_market_factor_returns_none_on_bad_source(monkeypatch):
    monkeypatch.setenv("BDRY_CHART_JSON", "/nonexistent/bdry.json")
    assert etl.fetch_market_factor() is None


def test_every_class_is_known_to_backend():
    for cls in etl.VESSEL_CLASSES:
        assert cls in bulk.VESSEL_CLASSES


# ── Backend : lecture fail-soft de fret_vraquier.json (contrat inchangé) ─────
def _write_json(obj):
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(obj, fh)
    fh.close()
    return fh.name


def test_backend_loads_valid_multipliers():
    path = _write_json(
        {"vessel_class_multipliers": {"capesize": {"multiplier": 1.5, "as_of": "2026-07-14"}}}
    )
    try:
        ov = bulk._load_freight_overrides(path)
        assert ov["capesize"]["multiplier"] == 1.5
    finally:
        os.unlink(path)


def test_backend_ignores_out_of_bounds_multiplier():
    # Critère d'acceptation : une entrée live invalide n'écrase jamais le statique.
    path = _write_json(
        {"vessel_class_multipliers": {"capesize": {"multiplier": 10.0, "as_of": "x"}}}
    )
    try:
        assert "capesize" not in bulk._load_freight_overrides(path)
    finally:
        os.unlink(path)


@pytest.mark.parametrize("bad_mult", [0, -1, "1.2", True, None])
def test_backend_ignores_non_numeric_or_nonpositive(bad_mult):
    path = _write_json(
        {"vessel_class_multipliers": {"panamax": {"multiplier": bad_mult, "as_of": "x"}}}
    )
    try:
        assert "panamax" not in bulk._load_freight_overrides(path)
    finally:
        os.unlink(path)


def test_backend_corrupt_file_falls_back_to_static():
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    fh.write("{ not valid json")
    fh.close()
    try:
        assert bulk._load_freight_overrides(fh.name) == {}
    finally:
        os.unlink(fh.name)


def test_backend_missing_file_falls_back_to_static():
    assert bulk._load_freight_overrides("/nonexistent/path/fret_vraquier.json") == {}


def test_multiplier_scales_modeled_rate():
    base = bulk.model_bulk_freight_usd_per_t(4000, "capesize")
    bulk._FREIGHT_OVERRIDES["capesize"] = {"multiplier": 1.5, "as_of": "2026-07-14"}
    try:
        scaled = bulk.model_bulk_freight_usd_per_t(4000, "capesize")
        assert scaled > base
        assert scaled == pytest.approx(base * 1.5, rel=0.02)
    finally:
        del bulk._FREIGHT_OVERRIDES["capesize"]


def test_committed_seed_file_is_valid():
    ov = bulk._load_freight_overrides(bulk._FREIGHT_OVERRIDE_PATH)
    assert set(ov) == set(bulk.VESSEL_CLASSES)
    for cls, entry in ov.items():
        lo, hi = bulk._MULTIPLIER_BOUNDS
        assert lo <= entry["multiplier"] <= hi
        assert entry["as_of"]
        assert entry["source"]
