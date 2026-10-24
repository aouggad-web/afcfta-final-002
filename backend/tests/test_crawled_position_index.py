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


def test_get_sub_positions_refreshes_existing_and_adds_collected_positions(monkeypatch, tmp_path):
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
    assert by_code["0101210010"]["dd_rate"] == 99
    assert by_code["0101210010"]["source"] == "GRA"
    assert by_code["0101210090"]["dd_rate"] == 20
    assert by_code["0101210090"]["source"] == "GRA"


def test_get_sub_positions_does_not_inherit_parent_duty_for_crawled_only_row(monkeypatch, tmp_path):
    _write_crawled(
        tmp_path,
        "ETH",
        {
            "positions": [
                {
                    "code_clean": "01012100000",
                    "designation": "Chevaux reproducteurs",
                    "taxes": {"TVA": {"rate": 15}, "WHR": {"rate": 3}},
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(
        service,
        "get_tariff_line",
        lambda *_args: {"hs6": "010121", "dd_rate": 35, "sub_positions": []},
    )
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)

    result = service.get_sub_positions("ETH", "010121")[0]

    assert result["dd_rate"] is None
    assert result["duty_status"] == "UNAVAILABLE"


def test_get_sub_positions_merges_postgres_with_missing_crawled_rows(monkeypatch, tmp_path):
    class PartialProvider:
        def get_sub_positions(self, *_args):
            return [
                {
                    "code": "0101210010",
                    "description_fr": "Position PostgreSQL",
                    "dd": 5,
                }
            ]

    _write_crawled(
        tmp_path,
        "GHA",
        {
            "positions": [
                {"code_clean": "0101210010", "designation": "Doublon", "dd": 99},
                {"code_clean": "0101210090", "designation": "Position manquante", "dd": 20},
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: PartialProvider())
    monkeypatch.setattr(
        service,
        "get_tariff_line",
        lambda *_args: {"hs6": "010121", "dd_rate": 20, "sub_positions": []},
    )
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)

    by_code = {
        position["code"]: position for position in service.get_sub_positions("GHA", "010121")
    }

    assert set(by_code) == {"0101210010", "0101210090"}
    assert by_code["0101210010"]["source"] == "postgres"
    assert by_code["0101210010"]["dd_rate"] == 5
    assert by_code["0101210090"]["dd_rate"] == 20


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


def test_crawled_index_cache_is_bounded_to_recent_countries():
    for position in range(service._CRAWLED_INDEX_CACHE_MAX_COUNTRIES + 1):
        service._cache_crawled_position_index(f"X{position}", {str(position): {}})

    assert len(service._crawled_index_cache) == service._CRAWLED_INDEX_CACHE_MAX_COUNTRIES
    assert "X0" not in service._crawled_index_cache


