"""Lot 1A — fail-closed checks for MAR/TUN/DZA administrative formalities.

These tests replace historical assertions that required generic document codes or
minimum document coverage without a source bound to each tariff line. They do
not add or infer any formality. Empty coverage remains an acceptable and
explicitly honest state until official, line-scoped evidence is available.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWLED_ROOT = REPO_ROOT / "backend" / "data" / "crawled"


def _lines(country: str) -> list[dict]:
    payload = json.loads(
        (CRAWLED_ROOT / f"{country}_tariffs.json").read_text(encoding="utf-8")
    )
    for key in ("positions", "sub_positions", "tariff_lines"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    raise AssertionError(f"{country}: no supported tariff-line collection")


def _formalities(country: str):
    for line in _lines(country):
        entries = line.get("administrative_formalities", [])
        assert isinstance(entries, list), (
            f"{country}: administrative_formalities must be a list when present"
        )
        for entry in entries:
            assert isinstance(entry, dict), f"{country}: formality entry must be an object"
            yield entry


def _assert_all_published_formalities_are_source_bound(country: str) -> None:
    required = {"source_id", "legal_reference", "verification_status"}
    for entry in _formalities(country):
        missing = {field for field in required if not entry.get(field)}
        assert not missing, (
            f"{country}/{entry.get('code', '?')}: published formality lacks "
            f"source binding fields {sorted(missing)}"
        )


def _assert_code_is_source_bound_if_present(country: str, code: str) -> None:
    for entry in _formalities(country):
        if entry.get("code") != code:
            continue
        assert entry.get("source_id"), f"{country}/{code}: missing source_id"
        assert entry.get("legal_reference"), f"{country}/{code}: missing legal_reference"
        assert entry.get("verification_status"), (
            f"{country}/{code}: missing verification_status"
        )


def test_mar_published_formalities_are_source_bound_or_absent():
    _assert_all_published_formalities_are_source_bound("MAR")


def test_tun_published_formalities_are_source_bound_or_absent():
    _assert_all_published_formalities_are_source_bound("TUN")


def test_dza_published_formalities_are_source_bound_or_absent():
    _assert_all_published_formalities_are_source_bound("DZA")


def test_mar_veterinary_code_is_not_accepted_without_source_binding():
    _assert_code_is_source_bound_if_present("MAR", "C01")


def test_tun_veterinary_code_is_not_accepted_without_source_binding():
    _assert_code_is_source_bound_if_present("TUN", "102")


def test_mar_pharma_code_is_not_accepted_without_source_binding():
    _assert_code_is_source_bound_if_present("MAR", "C04")


def test_tun_pharma_code_is_not_accepted_without_source_binding():
    _assert_code_is_source_bound_if_present("TUN", "103")


def test_formality_absence_is_schema_safe_and_never_replaced_by_a_placeholder():
    for country in ("MAR", "TUN", "DZA"):
        lines = _lines(country)
        assert lines, f"{country}: tariff data must remain readable"
        for line in lines:
            assert isinstance(line, dict), f"{country}: tariff line must be an object"
            entries = line.get("administrative_formalities", [])
            assert isinstance(entries, list)
            assert all(entry not in (None, "", 0) for entry in entries)
