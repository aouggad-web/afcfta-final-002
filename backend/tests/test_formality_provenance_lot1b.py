"""Lot 1B — fail-closed contracts for Africa-wide regulatory claims.

The retired tests generalized documents, authorities, observations, or rates across
countries without line-scoped official evidence. These replacements never infer
coverage. They reject unsupported claims and validate any published formality that
is actually present in crawled data.
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


@lru_cache(maxsize=None)
def _lines(country: str) -> list[dict]:
    path = CRAWLED_ROOT / f"{country}_tariffs.json"
    if not path.exists():
        return []

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    payload = json.loads(raw)
    for key in ("positions", "sub_positions", "tariff_lines"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


@lru_cache(maxsize=1)
def _countries() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.name.removesuffix("_tariffs.json") for path in CRAWLED_ROOT.glob("*_tariffs.json")
        )
    )


def _assert_source_bound(country: str, claim: dict) -> None:
    missing = {field for field in SOURCE_FIELDS if not claim.get(field)}
    code = claim.get("code") or claim.get("tax") or "?"
    assert not missing, (
        f"{country}/{code}: published regulatory claim lacks source binding "
        f"fields {sorted(missing)}"
    )
    status = claim["verification_status"]
    status_message = f"{country}/{code}: invalid verification_status {status}"
    assert status in VALID_STATUSES, status_message


def _iter_formalities(country: str):
    for line in _lines(country):
        assert isinstance(line, dict), f"{country}: tariff line must be an object"
        entries = line.get("administrative_formalities", [])
        assert isinstance(
            entries, list
        ), f"{country}: administrative_formalities must be a list when present"
        for entry in entries:
            entry_message = f"{country}: formality entry must be an object"
            assert isinstance(entry, dict), entry_message
            yield entry


def _assert_country_formality_contract(country: str) -> None:
    for entry in _iter_formalities(country):
        _assert_source_bound(country, entry)


def _iter_structured_tax_claims(country: str):
    for line in _lines(country):
        assert isinstance(line, dict), f"{country}: tariff line must be an object"
        entries = line.get("taxes", [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            assert isinstance(entry, dict), f"{country}: tax entry must be an object"
            if "tax" in entry:
                yield entry


def _assert_code_contract(countries, code: str) -> None:
    country_label = ",".join(countries)
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(country_label, {"code": code})

    for country in countries:
        for entry in _iter_formalities(country):
            if entry.get("code") == code:
                _assert_source_bound(country, entry)


def _assert_regulatory_claim_contract(country: str, claim_code: str) -> None:
    with pytest.raises(AssertionError, match="source_id"):
        _assert_source_bound(country, {"tax": claim_code})

    for entry in _iter_structured_tax_claims(country):
        if entry.get("tax") == claim_code:
            _assert_source_bound(country, entry)

    _assert_source_bound(
        country,
        {
            "tax": claim_code,
            "source_id": "contract-fixture",
            "legal_reference": "contract-fixture",
            "verification_status": "UNVERIFIED",
        },
    )


# 01 — replaces universal multi-document coverage.
def test_africa_published_formalities_are_source_bound_or_absent():
    for country in _countries():
        _assert_country_formality_contract(country)


# 02-06 — generic document codes are contracts, never inferred defaults.
def test_pharmauth_is_rejected_without_source_binding():
    countries = (
        "NGA",
        "KEN",
        "ZAF",
        "ETH",
        "CMR",
        "GHA",
        "SEN",
        "TZA",
        "UGA",
    )
    _assert_code_contract(countries, "PHARMAUTH")


def test_vetcert_is_rejected_without_source_binding():
    countries = ("NGA", "KEN", "ZAF", "ETH", "CMR", "GHA", "SEN", "TZA")
    _assert_code_contract(countries, "VETCERT")


def test_phytocert_is_rejected_without_source_binding():
    _assert_code_contract(("NGA", "KEN", "ZAF", "ETH", "GHA"), "PHYTOCERT")


def test_energyauth_is_rejected_without_source_binding():
    countries = ("NGA", "AGO", "GAB", "COG", "GNQ", "LBY", "SDN")
    _assert_code_contract(countries, "ENERGYAUTH")


def test_armauth_is_rejected_without_source_binding():
    _assert_code_contract(("NGA", "KEN", "ZAF", "GHA", "EGY"), "ARMAUTH")


# 07-08 — empty coverage is honest; DZA is not forced into a historical code set.
def test_empty_formality_coverage_is_a_valid_fail_closed_state():
    assert list(_iter_formalities("__NO_DATA__")) == []


def test_dza_formalities_are_source_bound_or_absent():
    _assert_country_formality_contract("DZA")


# 09-12 — DRC/OCC claims require source binding per use case.
def test_cod_occdecl_is_rejected_without_source_binding():
    _assert_code_contract(("COD",), "OCCDECL")


def test_cod_pharma_claims_are_rejected_without_source_binding():
    _assert_code_contract(("COD",), "PHARMAUTH")
    _assert_code_contract(("COD",), "OCCDECL")


def test_cod_animal_claims_are_rejected_without_source_binding():
    _assert_code_contract(("COD",), "VETCERT")
    _assert_code_contract(("COD",), "OCCDECL")


def test_cod_vehicle_claims_are_rejected_without_source_binding():
    _assert_code_contract(("COD",), "STDCERT")
    _assert_code_contract(("COD",), "OCCDECL")


# 13-16 — national pre-import and inspection claims.
def test_nga_formm_is_rejected_without_source_binding():
    _assert_code_contract(("NGA",), "FORMM")


def test_egy_goeic_is_rejected_without_source_binding():
    _assert_code_contract(("EGY",), "GOEIC")


def test_eth_manufactured_ethpermit_is_rejected_without_source_binding():
    _assert_code_contract(("ETH",), "ETHPERMIT")


def test_eth_processed_food_ethpermit_is_rejected_without_source_binding():
    _assert_code_contract(("ETH",), "ETHPERMIT")


# 17-22 — ECTN is never generalized across CEMAC or all tariff lines.
def test_cemac_ectn_is_rejected_without_country_source_binding():
    _assert_code_contract(("CMR", "GAB", "CAF", "COG", "GNQ", "TCD"), "ECTN")


def test_gab_ectn_is_rejected_without_source_binding():
    _assert_code_contract(("GAB",), "ECTN")


def test_caf_ectn_is_rejected_without_source_binding():
    _assert_code_contract(("CAF",), "ECTN")


def test_cog_ectn_is_rejected_without_source_binding():
    _assert_code_contract(("COG",), "ECTN")


def test_gnq_ectn_is_rejected_without_source_binding():
    _assert_code_contract(("GNQ",), "ECTN")


def test_tcd_ectn_is_rejected_without_source_binding():
    _assert_code_contract(("TCD",), "ECTN")


# 23-29 — observations and parafiscal rates are source-bound claims, not constants.
def test_eth_sur_observation_requires_source_binding():
    _assert_regulatory_claim_contract("ETH", "SUR")


def test_cmr_tci_observation_requires_source_binding():
    _assert_regulatory_claim_contract("CMR", "TCI")


def test_mar_tpi_observation_requires_source_binding():
    _assert_regulatory_claim_contract("MAR", "TPI")


def test_mar_other_taxes_claim_requires_source_binding():
    _assert_regulatory_claim_contract("MAR", "TPI")


def test_ken_idf_rate_claim_requires_source_binding():
    _assert_regulatory_claim_contract("KEN", "IDF")


def test_eth_sur_rate_claim_requires_source_binding():
    _assert_regulatory_claim_contract("ETH", "SUR")


def test_gab_other_taxes_claim_requires_source_binding():
    _assert_regulatory_claim_contract("GAB", "TCI")
