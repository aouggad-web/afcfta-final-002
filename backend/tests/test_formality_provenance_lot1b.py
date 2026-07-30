"""Lot 1B — fail-closed Africa-wide contracts for administrative claims.

These tests replace historical assertions that generalized documents, authorities,
observations, or rates across countries without line-scoped official evidence.
They never add or infer regulatory data. Empty coverage remains an honest state.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWLED_ROOT = REPO_ROOT / "backend" / "data" / "crawled"

REQUIRED_SOURCE_FIELDS = {"source_id", "legal_reference", "verification_status"}


def _lines(country: str) -> list[dict]:
    payload = json.loads(
        (CRAWLED_ROOT / f"{country}_tariffs.json").read_text(encoding="utf-8")
    )
    for key in ("positions", "sub_positions", "tariff_lines"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    raise AssertionError(f"{country}: no supported tariff-line collection")


def _assert_source_bound(country: str, entry: dict) -> None:
    assert isinstance(entry, dict), f"{country}: regulatory entry must be an object"
    missing = {field for field in REQUIRED_SOURCE_FIELDS if not entry.get(field)}
    code = entry.get("code", entry.get("name", "?"))
    assert not missing, (
        f"{country}/{code}: published regulatory claim lacks source fields "
        f"{sorted(missing)}"
    )


def _assert_country_contract(country: str) -> None:
    lines = _lines(country)
    assert lines, f"{country}: tariff data must remain readable"
    for line in lines:
        assert isinstance(line, dict), f"{country}: tariff line must be an object"
        entries = line.get("administrative_formalities", [])
        assert isinstance(entries, list), (
            f"{country}: administrative_formalities must be a list when present"
        )
        for entry in entries:
            _assert_source_bound(country, entry)


def _assert_code_contract(country: str, code: str) -> None:
    """Reject an unsupported code and validate any matching live record."""
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(country, {"code": code})

    for line in _lines(country):
        for entry in line.get("administrative_formalities", []):
            if entry.get("code") == code:
                _assert_source_bound(country, entry)


COUNTRY_CONTRACTS = [
    "NGA",
    "KEN",
    "ZAF",
    "ETH",
    "GHA",
    "CMR",
    "SEN",
]


@pytest.mark.parametrize("country", COUNTRY_CONTRACTS)
def test_country_formalities_are_source_bound_or_absent(country):
    _assert_country_contract(country)


CODE_CONTRACTS = [
    ("NGA", "PHARMAUTH"),
    ("KEN", "VETCERT"),
    ("ZAF", "STDCERT"),
    ("ETH", "ETHPERMIT"),
    ("CMR", "PHARMAUTH"),
    ("COD", "OCCDECL"),
    ("NGA", "FORMM"),
    ("EGY", "GOEIC"),
    ("GAB", "ECTN"),
    ("CAF", "ECTN"),
    ("COG", "ECTN"),
    ("GNQ", "ECTN"),
    ("TCD", "ECTN"),
    ("DZA", "910"),
    ("MAR", "910"),
]


@pytest.mark.parametrize(
    ("country", "code"),
    CODE_CONTRACTS,
    ids=[f"{country}-{code}" for country, code in CODE_CONTRACTS],
)
def test_regulatory_code_is_rejected_without_source_binding(country, code):
    _assert_code_contract(country, code)


OBSERVATION_CONTRACTS = [
    ("ETH", "SUR"),
    ("CMR", "TCI"),
    ("MAR", "TPI"),
    ("KEN", "IDF"),
    ("GAB", "other_taxes"),
    ("MAR", "other_taxes"),
    ("ETH", "other_taxes"),
]


@pytest.mark.parametrize(
    ("country", "claim"),
    OBSERVATION_CONTRACTS,
    ids=[f"{country}-{claim}" for country, claim in OBSERVATION_CONTRACTS],
)
def test_observation_or_rate_claim_requires_explicit_provenance(country, claim):
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(country, {"name": claim})


# 7 country contracts + 15 code contracts + 7 observation/rate contracts = 29 cases.
