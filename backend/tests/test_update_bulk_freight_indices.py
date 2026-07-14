"""Tests hors-ligne de l'ETL de rafraîchissement des indices de fret vraquier (Lot D)."""

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


# ── ETL : calcul du multiplicateur ──────────────────────────────────────────
def test_compute_multiplier_ratio_to_baseline():
    # 1035 / 690 = 1,5
    assert etl.compute_multiplier(1035.0, 690.0) == 1.5
    assert etl.compute_multiplier(690.0, 690.0) == 1.0


@pytest.mark.parametrize("bad_level", [0, -1, None, "x"])
def test_compute_multiplier_rejects_bad_levels(bad_level):
    with pytest.raises(ValueError):
        etl.compute_multiplier(bad_level, 690.0)


@pytest.mark.parametrize("factor", [5.0, 0.1])
def test_compute_multiplier_rejects_out_of_bounds(factor):
    # Un niveau x5 ou /10 sort des bornes [0.3, 3.0] → rejeté, jamais borné en silence.
    with pytest.raises(ValueError, match="vraisemblance"):
        etl.compute_multiplier(690.0 * factor, 690.0)


def test_build_static_entry_is_dated_and_sourced():
    entry = etl.build_static_entry("panamax")
    assert entry["multiplier"] == 1.0
    assert entry["as_of"] == "moyenne 2024"
    assert "Baltic" in entry["source"]
    assert entry["index"].startswith("BPI")


def test_build_live_entry_carries_provenance():
    entry = etl.build_live_entry("capesize", 4125.0, "2026-07-14")
    assert entry["multiplier"] == 1.5  # 4125 / 2750
    assert entry["as_of"] == "2026-07-14"
    assert entry["index_level"] == 4125.0
    assert entry["baseline_2024"] == 2750.0
    assert "Baltic" in entry["source"]


# ── ETL : assemblage du payload (live valide vs repli statique) ──────────────
def test_build_payload_uses_static_when_no_live_levels():
    payload = etl.build_payload({})
    mults = payload["vessel_class_multipliers"]
    assert set(mults) == set(etl.VESSEL_INDICES)
    assert all(m["multiplier"] == 1.0 for m in mults.values())
    assert payload["_meta"]["classes_live"] == []


def test_build_payload_applies_valid_live_and_falls_back_on_invalid():
    live = {
        "supramax": {"level": 1845.0, "as_of": "2026-07-14"},  # 1845/1230 = 1.5 valide
        "capesize": {"level": 2750.0 * 9, "as_of": "2026-07-14"},  # x9 → hors bornes
    }
    payload = etl.build_payload(live)
    mults = payload["vessel_class_multipliers"]
    # Supramax live appliqué
    assert mults["supramax"]["multiplier"] == 1.5
    assert mults["supramax"]["as_of"] == "2026-07-14"
    # Capesize invalide → repli statique 1,0 (jamais le facteur douteux)
    assert mults["capesize"]["multiplier"] == 1.0
    assert mults["capesize"]["as_of"] == "moyenne 2024"
    assert "supramax" in payload["_meta"]["classes_live"]
    assert any("capesize" in f for f in payload["_meta"]["classes_failed_or_static"])


def test_every_class_has_index_and_baseline():
    for cls, spec in etl.VESSEL_INDICES.items():
        assert cls in bulk.VESSEL_CLASSES
        assert spec["baseline_2024"] > 0
        assert spec["index"]
        assert spec["source"]


# ── Backend : lecture fail-soft de fret_vraquier.json ───────────────────────
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
    # Critère d'acceptation Lot D : une entrée live invalide n'écrase jamais le statique.
    path = _write_json(
        {"vessel_class_multipliers": {"capesize": {"multiplier": 10.0, "as_of": "x"}}}
    )
    try:
        ov = bulk._load_freight_overrides(path)
        assert "capesize" not in ov
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
    # Le multiplicateur multiplie bien le tarif océanique modélisé.
    base = bulk.model_bulk_freight_usd_per_t(4000, "capesize")
    bulk._FREIGHT_OVERRIDES["capesize"] = {"multiplier": 1.5, "as_of": "2026-07-14"}
    try:
        scaled = bulk.model_bulk_freight_usd_per_t(4000, "capesize")
        # Au-dessus du plancher, le facteur 1,5 s'applique (tolérance d'arrondi).
        assert scaled > base
        assert scaled == pytest.approx(base * 1.5, rel=0.02)
    finally:
        del bulk._FREIGHT_OVERRIDES["capesize"]


def test_committed_seed_file_is_valid_and_neutral():
    # Le fichier versionné doit être lisible et neutre (seed 1,0 = statique).
    ov = bulk._load_freight_overrides(bulk._FREIGHT_OVERRIDE_PATH)
    assert set(ov) == set(bulk.VESSEL_CLASSES)
    for cls, entry in ov.items():
        assert entry["multiplier"] == 1.0
        assert entry["as_of"]
        assert entry["source"]
