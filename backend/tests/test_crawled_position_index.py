"""Non-regression tests for national-position coverage adapters."""

import json

import pytest
from services import authentic_tariff_service as service


@pytest.fixture(autouse=True)
def clear_crawled_cache():
    service._crawled_index_cache.clear()
    yield
    service._crawled_index_cache.clear()


def _write_crawled(tmp_path, iso3, payload):
    target = tmp_path / f"{iso3}_tariffs.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def test_loads_legacy_root_sub_positions_without_changing_tariff_columns(monkeypatch, tmp_path):
    taxes = {
        "DD": {"name": "Droit de douane", "rate": 15},
        "TVA": {"name": "TVA", "rate": 19},
    }
    _write_crawled(
        tmp_path,
        "DZA",
        {
            "source": "customs.example",
            "source_quality": "crawled_authentic",
            "sub_positions": [
                {
                    "hs_code": "01.01.211100",
                    "name": "Chevaux reproducteurs",
                    "taxes": taxes,
                }
            ],
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))

    position = service.load_crawled_position_index("DZA")["0101211100"]

    assert position["taxes"] == taxes
    assert position["source"] == "customs.example"
    assert position["source_quality"] == "crawled_authentic"


def test_loads_root_positions_and_preserves_raw_tax_list(monkeypatch, tmp_path):
    raw_taxes = [
        {"code": "GENERAL", "name": "General Customs Duty", "rate_pct": 10},
        {"code": "AfCFTA", "name": "AfCFTA rate", "rate_pct": 0},
        {"code": "SADC", "name": "SADC rate", "rate_pct": 0},
    ]
    _write_crawled(
        tmp_path,
        "ZAF",
        {
            "positions": [
                {
                    "code_clean": "01012100",
                    "designation": "Pure-bred breeding animals",
                    "taxes": raw_taxes,
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))

    position = service.load_crawled_position_index("ZAF")["01012100"]

    assert position["taxes"] == raw_taxes
    assert position["name"] == "Pure-bred breeding animals"


def test_loads_nested_tariff_line_sub_positions_without_indexing_parent(monkeypatch, tmp_path):
    _write_crawled(
        tmp_path,
        "GHA",
        {
            "source": "GRA / TEC CEDEAO",
            "tariff_lines": [
                {
                    "hs6": "010121",
                    "description_fr": "Chevaux vivants",
                    "dd_rate": 20,
                    "sub_positions": [
                        {
                            "code": "0101210000",
                            "dd": 5,
                            "description_fr": "Chevaux reproducteurs de race pure",
                        },
                        {"code": "0101210090", "dd": 20},
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))

    index = service.load_crawled_position_index("GHA")

    assert set(index) == {"0101210000", "0101210090"}
    assert index["0101210000"]["dd"] == 5
    assert index["0101210000"]["source"] == "GRA / TEC CEDEAO"
    assert "010121" not in index


def test_tariff_line_without_national_children_does_not_invent_positions(monkeypatch, tmp_path):
    _write_crawled(
        tmp_path,
        "AGO",
        {
            "tariff_lines": [
                {
                    "hs6": "010121",
                    "description_fr": "Chevaux vivants",
                    "dd_rate": 7.5,
                    "sub_positions": [],
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))

    assert service.load_crawled_position_index("AGO") == {}


def test_get_sub_positions_adds_only_missing_crawled_positions(monkeypatch, tmp_path):
    parent_line = {
        "hs6": "010121",
        "dd_rate": 20,
        "sub_positions": [
            {
                "code": "0101210010",
                "dd": 5,
                "description_fr": "Position déjà exploitée",
                "source": "ETL existant",
            }
        ],
    }
    _write_crawled(
        tmp_path,
        "GHA",
        {
            "source": "GRA",
            "tariff_lines": [
                {
                    "hs6": "010121",
                    "sub_positions": [
                        {"code": "0101210010", "dd": 99},
                        {
                            "code": "0101210090",
                            "dd": 20,
                            "description_fr": "Position retrouvée dans le crawl",
                        },
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: parent_line)
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)

    positions = service.get_sub_positions("GHA", "010121")
    by_code = {position["code"]: position for position in positions}

    assert set(by_code) == {"0101210010", "0101210090"}
    assert by_code["0101210010"]["dd_rate"] == 5
    assert by_code["0101210010"]["source"] == "ETL existant"
    assert by_code["0101210090"]["dd_rate"] == 20
    assert by_code["0101210090"]["source"] == "GRA"


def test_search_handles_raw_tax_lists_and_returns_position_provenance(monkeypatch, tmp_path):
    raw_taxes = [
        {"code": "GENERAL", "name": "General Customs Duty", "rate_pct": 10},
        {"code": "AfCFTA", "name": "AfCFTA rate", "rate_pct": 0},
    ]
    _write_crawled(
        tmp_path,
        "ZAF",
        {
            "positions": [
                {
                    "code_clean": "01012100",
                    "designation": "Pure-bred breeding animals",
                    "dd_rate": 10,
                    "taxes": raw_taxes,
                    "source": "South African Revenue Service",
                    "source_url": "https://sars.example/tariff.pdf",
                    "source_quality": "crawled_authentic",
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)

    result = service.search_tariff_lines("ZAF", "01012100", limit=1)[0]

    assert result["national_code"] == "01012100"
    assert result["dd_rate"] == 10
    assert result["source"] == "South African Revenue Service"
    assert result["source_url"] == "https://sars.example/tariff.pdf"
    assert service.load_crawled_position_index("ZAF")["01012100"]["taxes"] == raw_taxes


def test_real_repository_regression_formats_are_consumed():
    gha = service.load_crawled_position_index("GHA")
    ken = service.load_crawled_position_index("KEN")
    zaf = service.load_crawled_position_index("ZAF")

    assert len(gha) >= 6_000  # tariff_lines[].sub_positions[]
    assert len(ken) >= 5_900  # positions[]
    assert len(zaf) >= 8_500  # positions[] with mixed code lengths
    assert "0101210000" in gha
    assert "01012100" in ken
    assert isinstance(zaf["010121"]["taxes"], list)


def test_calculator_keeps_existing_etl_rate_for_newly_indexed_nested_position(
    monkeypatch, tmp_path
):
    parent_line = {
        "hs6": "010121",
        "description_fr": "Chevaux vivants",
        "description_en": "Live horses",
        "dd_rate": 20,
        "vat_rate": 14,
        "other_taxes_rate": 0,
        "taxes_detail": [
            {"tax": "DD", "rate": 20},
            {"tax": "TVA", "rate": 14},
        ],
        "sub_positions": [
            {
                "code": "01012100",
                "dd": 5,
                "description_fr": "Chevaux reproducteurs",
            }
        ],
        "administrative_formalities": ["Comportement existant conservé"],
    }
    _write_crawled(tmp_path, "AGO", {"tariff_lines": [parent_line]})
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: dict(parent_line))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: {})
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)

    result = service.calculate_import_taxes("AGO", "01012100", 1_000)

    assert result["rates"]["dd_rate_pct"] == 5
    assert result["sub_position"]["code"] == "01012100"
    assert result["administrative_formalities"] == ["Comportement existant conservé"]


def test_calculator_keeps_existing_root_sub_position_tax_precedence(monkeypatch, tmp_path):
    parent_line = {
        "hs6": "010121",
        "description_fr": "Chevaux vivants",
        "description_en": "Live horses",
        "dd_rate": 20,
        "vat_rate": 14,
        "other_taxes_rate": 0,
        "taxes_detail": [{"tax": "DD", "rate": 20}],
        "sub_positions": [],
        "administrative_formalities": [],
    }
    _write_crawled(
        tmp_path,
        "DZA",
        {
            "sub_positions": [
                {
                    "hs_code": "0101210010",
                    "name": "Chevaux reproducteurs",
                    "taxes": {"DD": {"name": "Droit de douane", "rate": 5}},
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: dict(parent_line))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: {})
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)

    result = service.calculate_import_taxes("DZA", "0101210010", 1_000)

    assert result["rates"]["dd_rate_pct"] == 5
