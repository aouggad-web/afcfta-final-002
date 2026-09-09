"""Lot 1A — fail-closed checks for MAR/TUN/DZA administrative formalities.

These tests replace historical assertions that required generic document codes or
minimum document coverage without a source bound to each tariff line. They do
not add or infer any formality. Empty coverage remains an acceptable and
explicitly honest state until official, line-scoped evidence is available.
Each replacement is a guardrail, not evidence that a document exists.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWLED_ROOT = REPO_ROOT / "backend" / "data" / "crawled"


def _lines(country: str) -> list[dict]:
    payload = json.loads((CRAWLED_ROOT / f"{country}_tariffs.json").read_text(encoding="utf-8"))
    for key in ("positions", "sub_positions", "tariff_lines"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    raise AssertionError(f"{country}: no supported tariff-line collection")


def _assert_entry_is_source_bound(country: str, entry: dict) -> None:
    required = {"source_id", "legal_reference", "verification_status"}
    missing = {field for field in required if not entry.get(field)}
    code = entry.get("code", "?")
    message = (
        f"{country}/{code}: published formality lacks source binding fields " f"{sorted(missing)}"
    )
    assert not missing, message


def _assert_country_formality_contract(country: str) -> None:
    lines = _lines(country)
    assert lines, f"{country}: tariff data must remain readable"

    for line in lines:
        assert isinstance(line, dict), f"{country}: tariff line must be an object"
        entries = line.get("administrative_formalities", [])
        message = f"{country}: administrative_formalities must be a list when present"
        assert isinstance(entries, list), message
        for entry in entries:
            assert isinstance(entry, dict), f"{country}: formality entry must be an object"
            _assert_entry_is_source_bound(country, entry)


def _assert_code_contract(country: str, code: str) -> None:
    """Exercise the rejection contract even when the live dataset has no such code."""

    with pytest.raises(AssertionError, match="source_id"):
        _assert_entry_is_source_bound(country, {"code": code})

    for line in _lines(country):
        for entry in line.get("administrative_formalities", []):
            if entry.get("code") == code:
                _assert_entry_is_source_bound(country, entry)


def test_mar_published_formalities_are_source_bound_or_absent():
    _assert_country_formality_contract("MAR")


def test_tun_published_formalities_are_source_bound_or_absent():
    _assert_country_formality_contract("TUN")


def test_dza_published_formalities_are_source_bound_or_absent():
    _assert_country_formality_contract("DZA")


def test_mar_veterinary_code_is_not_accepted_without_source_binding():
    # Contract test: C01 is rejected unless a future official record is source-bound.
    _assert_code_contract("MAR", "C01")


def test_tun_veterinary_code_is_not_accepted_without_source_binding():
    # Contract test: 102 is rejected unless a future official record is source-bound.
    _assert_code_contract("TUN", "102")


def test_mar_pharma_code_is_not_accepted_without_source_binding():
    # Contract test: C04 is rejected unless a future official record is source-bound.
    _assert_code_contract("MAR", "C04")


def test_tun_pharma_code_is_not_accepted_without_source_binding():
    # Contract test: 103 is rejected unless a future official record is source-bound.
    _assert_code_contract("TUN", "103")


def test_formality_absence_is_schema_safe_and_never_replaced_by_a_placeholder():
    for country in ("MAR", "TUN", "DZA"):
        for line in _lines(country):
            entries = line.get("administrative_formalities", [])
            assert isinstance(entries, list)
            assert all(entry not in (None, "", 0) for entry in entries)
