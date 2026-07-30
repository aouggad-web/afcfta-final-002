"""Lot 1C — provenance contracts for IMPDEC, code 910, and platforms.

Country identity or customs-platform metadata never proves that a regulatory code
applies. IMPDEC and 910 may be absent. When published, they must be linked to an
identified source, a legal reference, and a canonical verification status.
"""

import json
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWLED_ROOT = REPO_ROOT / "backend" / "data" / "crawled"
SOURCE_FIELDS = {"source_id", "legal_reference", "verification_status"}
VALID_STATUSES = {
    "DOCUMENTED",
    "PARTIAL",
    "UNVERIFIED",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
}


@lru_cache(maxsize=1)
def _countries() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.name.removesuffix("_tariffs.json")
            for path in CRAWLED_ROOT.glob("*_tariffs.json")
        )
    )


@lru_cache(maxsize=None)
def _lines(country: str) -> list[dict]:
    path = CRAWLED_ROOT / f"{country}_tariffs.json"
    if not path.exists():
        return []

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []

    for key in ("positions", "sub_positions", "tariff_lines"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _assert_source_bound(country: str, entry: dict) -> None:
    missing = {field for field in SOURCE_FIELDS if not entry.get(field)}
    code = entry.get("code", "?")
    assert not missing, (
        f"{country}/{code}: published formality lacks source binding fields "
        f"{sorted(missing)}"
    )
    status = entry["verification_status"]
    assert status in VALID_STATUSES, (
        f"{country}/{code}: invalid verification_status {status}"
    )


def _iter_code_entries(country: str, code: str):
    for line in _lines(country):
        assert isinstance(line, dict), f"{country}: tariff line must be an object"
        formalities = line.get("administrative_formalities", [])
        assert isinstance(formalities, list), (
            f"{country}: administrative_formalities must be a list when present"
        )
        for entry in formalities:
            assert isinstance(entry, dict), (
                f"{country}: formality entry must be an object"
            )
            if entry.get("code") == code:
                yield entry


def _assert_code_contract(countries, code: str) -> None:
    label = ",".join(countries)
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(label, {"code": code})

    _assert_source_bound(
        label,
        {
            "code": code,
            "source_id": "contract-fixture",
            "legal_reference": "contract-fixture",
            "verification_status": "UNVERIFIED",
        },
    )

    for country in countries:
        for entry in _iter_code_entries(country, code):
            _assert_source_bound(country, entry)


def _assert_country_code_pair(country: str) -> None:
    _assert_code_contract((country,), "910")
    _assert_code_contract((country,), "IMPDEC")


# 01-06 — neither 910 nor IMPDEC is inferred from the country alone.
def test_eth_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("ETH")


def test_sdn_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("SDN")


def test_stp_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("STP")


def test_nga_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("NGA")


def test_ken_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("KEN")


def test_zaf_910_and_impdec_are_source_bound_if_present():
    _assert_country_code_pair("ZAF")


# 07 — IMPDEC is not a universal default across crawled country files.
def test_all_crawled_impdec_entries_are_source_bound_or_absent():
    _assert_code_contract(_countries(), "IMPDEC")


# 08-10 — national code 910 is not legitimised without official evidence.
def test_dza_910_is_source_bound_if_present():
    _assert_code_contract(("DZA",), "910")


def test_mar_910_is_source_bound_if_present():
    _assert_code_contract(("MAR",), "910")


def test_tun_910_is_source_bound_if_present():
    _assert_code_contract(("TUN",), "910")


# 11 — a software platform label is metadata, not regulatory provenance.
def test_customs_platform_metadata_does_not_prove_impdec_applicability():
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(
            "GHA",
            {
                "code": "IMPDEC",
                "customs_platform": "GCNET",
            },
        )

    non_asycuda = ("GHA", "NGA", "KEN", "TZA", "ZAF")
    _assert_code_contract(non_asycuda, "IMPDEC")
