"""Tests du chargeur UNIDO IDSB/INDSTAT ISIC 4 chiffres (etl/isic4_idsb_data)."""

from unittest.mock import patch

from etl import isic4_idsb_data

_FAKE_RECORDS = [
    # MAR / ISIC 1010: output 2018 puis 2020 (=> 2020 est la dernière année, valeur 210)
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2018,
        "indicator_code": "100",
        "indicator_name": "Output",
        "value": 100.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2020,
        "indicator_code": "100",
        "indicator_name": "Output",
        "value": 210.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    # MAR / ISIC 1010: imports mondiales 2019 (une seule année)
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2019,
        "indicator_code": "101",
        "indicator_name": "Imports World",
        "value": 500.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    # MAR / ISIC 1010: INDSTAT Value added 2018
    {
        "dataset_code": "INDSTAT_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2018,
        "indicator_code": "20",
        "indicator_name": "Value added",
        "value": 42.0,
        "unit": "current_USD",
        "data_nature": "OFFICIAL_STATISTICS",
    },
    # MAR / ISIC 1050 (secteur différent, un seul indicateur)
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1050",
        "isic_description": "Dairy products",
        "year": 2022,
        "indicator_code": "107",
        "indicator_name": "Apparent Consumption",
        "value": 999.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    # KEN (second pays)
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "KEN",
        "country_name": "Kenya",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2021,
        "indicator_code": "104",
        "indicator_name": "Exports World",
        "value": 77.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    # Indicateur inconnu — doit être ignoré silencieusement
    {
        "dataset_code": "IDSB_R4",
        "country_iso3": "MAR",
        "country_name": "Morocco",
        "isic_code": "1010",
        "isic_description": "Processing/preserving of meat",
        "year": 2023,
        "indicator_code": "9999",
        "indicator_name": "Unknown metric",
        "value": 1.0,
        "unit": "current_USD",
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
]


def _patch_records():
    """Remplace le loader mémoïsé par notre jeu de test (et vide le cache)."""
    isic4_idsb_data._load_records.cache_clear()
    isic4_idsb_data.list_covered_countries.cache_clear()
    return patch.object(isic4_idsb_data, "_load_records", lambda: list(_FAKE_RECORDS))


def teardown_module(module):
    """Vide le cache après les tests pour ne pas polluer d'autres suites."""
    isic4_idsb_data._load_records.cache_clear()
    isic4_idsb_data.list_covered_countries.cache_clear()


def test_list_covered_countries_deduplicates_and_sorts():
    with _patch_records():
        isic4_idsb_data.list_covered_countries.cache_clear()
        assert isic4_idsb_data.list_covered_countries() == ["KEN", "MAR"]


def test_is_country_covered_case_insensitive():
    with _patch_records():
        isic4_idsb_data.list_covered_countries.cache_clear()
        assert isic4_idsb_data.is_country_covered("mar") is True
        assert isic4_idsb_data.is_country_covered("KEN") is True
        assert isic4_idsb_data.is_country_covered("ZWE") is False


def test_country_summary_picks_latest_year_per_indicator():
    with _patch_records():
        summary = isic4_idsb_data.get_country_isic4_summary("MAR")
    assert summary is not None
    assert summary["country_iso3"] == "MAR"
    assert summary["country_name"] == "Morocco"

    sectors = {s["isic4"]: s for s in summary["sectors"]}
    assert set(sectors) == {"1010", "1050"}

    ind = sectors["1010"]["indicators"]
    # Output: 2018 (100) puis 2020 (210) — l'année 2020 doit gagner
    assert ind["output_usd"] == {
        "value": 210.0,
        "unit": "current_USD",
        "year": 2020,
        "data_nature": "UNIDO_DERIVED_ESTIMATE",
    }
    # Imports World: 2019 seul
    assert ind["imports_world_usd"]["value"] == 500.0
    assert ind["imports_world_usd"]["year"] == 2019
    # Value added (INDSTAT): 2018 seul
    assert ind["value_added_usd"]["value"] == 42.0
    assert ind["value_added_usd"]["data_nature"] == "OFFICIAL_STATISTICS"
    # Un indicateur non mappé ne doit rien produire
    assert "9999" not in ind
    assert not any(k.endswith("9999") for k in ind)


def test_country_summary_returns_none_for_uncovered_country():
    with _patch_records():
        assert isic4_idsb_data.get_country_isic4_summary("ZWE") is None


def test_country_summary_is_sorted_by_isic_code():
    with _patch_records():
        summary = isic4_idsb_data.get_country_isic4_summary("MAR")
    codes = [s["isic4"] for s in summary["sectors"]]
    assert codes == sorted(codes)


def test_timeseries_returns_all_years_sorted_ascending():
    with _patch_records():
        ts = isic4_idsb_data.get_isic4_timeseries("MAR", "1010")
    assert ts is not None
    assert ts["isic4"] == "1010"
    output_series = ts["series"]["output_usd"]
    years = [p["year"] for p in output_series]
    assert years == sorted(years)  # ordre croissant
    assert years == [2018, 2020]  # exactement les années disponibles
    assert output_series[-1]["value"] == 210.0


def test_timeseries_none_for_unknown_pair():
    with _patch_records():
        assert isic4_idsb_data.get_isic4_timeseries("ZWE", "1010") is None
        assert isic4_idsb_data.get_isic4_timeseries("MAR", "9999") is None
