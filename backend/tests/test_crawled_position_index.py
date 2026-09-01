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


def test_search_handles_raw_tax_lists_and_returns_position_provenance(monkeypatch, tmp_path):
    raw_taxes = [
        {"code": "GENERAL", "name": "General Customs Duty", "rate_pct": 10},
        {"code": "VAT", "name": "Value Added Tax", "rate_pct": 15},
        {"code": "AfCFTA", "name": "AfCFTA rate", "rate_pct": 2},
        {"code": "SADC", "name": "SADC preferential rate", "rate_pct": 4},
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
    assert result["tva_rate"] == 15
    assert result["source"] == "South African Revenue Service"
    assert result["source_url"] == "https://sars.example/tariff.pdf"
    assert (
        result["effective_rate"]
        == service.compute_tax_cascade(100, {"DD": 10, "TVA": 15}, "ZAF")["effective_rate_pct"]
    )
    assert service.load_crawled_position_index("ZAF")["01012100"]["taxes"] == raw_taxes


def test_search_handles_scalar_tax_maps(monkeypatch, tmp_path):
    raw_taxes = {"DD": 20.0, "TVA": 18.0, "PCC": 0.5}
    _write_crawled(
        tmp_path,
        "GIN",
        {
            "positions": [
                {
                    "code_clean": "7612900000",
                    "designation": "Récipients en aluminium",
                    "taxes": raw_taxes,
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)

    result = service.search_tariff_lines("GIN", "7612900000", limit=1)[0]

    assert result["dd_rate"] == 20
    assert result["tva_rate"] == 18
    assert (
        result["effective_rate"]
        == service.compute_tax_cascade(100, raw_taxes, "GIN")["effective_rate_pct"]
    )
    assert service.load_crawled_position_index("GIN")["7612900000"]["taxes"] == raw_taxes


def test_search_merges_postgres_with_missing_crawled_rows(monkeypatch, tmp_path):
    class PartialProvider:
        def search_commodities(self, *_args, **_kwargs):
            return [
                {
                    "hs6": "010121",
                    "code": "0101210010",
                    "description": "Position PostgreSQL",
                    "dd_rate": 5,
                }
            ]

    _write_crawled(
        tmp_path,
        "GHA",
        {
            "positions": [
                {
                    "code_clean": "0101210010",
                    "designation": "Doublon collecté",
                    "taxes": {"DD": 99},
                },
                {
                    "code_clean": "0101210090",
                    "designation": "Position collectée manquante",
                    "taxes": {"DD": 20},
                },
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: PartialProvider())
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)

    results = service.search_tariff_lines("GHA", "010121", limit=10)

    assert [result["national_code"] for result in results] == ["0101210010", "0101210090"]
    assert results[0]["source"] == "postgres"
    assert results[0]["dd_rate"] == 5
    assert results[1]["dd_rate"] == 20


def test_search_uses_etl_rates_when_crawled_position_has_no_tax_fields(monkeypatch, tmp_path):
    tariff_data = {
        "tariff_lines": [
            {
                "hs6": "010129",
                "vat_rate": 16,
                "sub_positions": [
                    {
                        "code": "01012900",
                        "dd": 25,
                        "description_fr": "Autres chevaux",
                    }
                ],
            }
        ]
    }
    _write_crawled(
        tmp_path,
        "KEN",
        {
            "positions": [
                {
                    "code_clean": "01012900",
                    "designation": "Other horses",
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: tariff_data)

    result = service.search_tariff_lines("KEN", "01012900", limit=1)[0]

    assert result["dd_rate"] == 25
    assert result["tva_rate"] == 16


def test_search_keeps_missing_duty_unresolved(monkeypatch, tmp_path):
    tariff_data = {
        "tariff_lines": [
            {
                "hs6": "010121",
                "vat_rate": 15,
                "sub_positions": [],
            }
        ]
    }
    _write_crawled(
        tmp_path,
        "ETH",
        {
            "positions": [
                {
                    "code_clean": "01012100000",
                    "designation": "Chevaux reproducteurs",
                    "taxes": {"TVA": {"rate": 15}},
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: tariff_data)

    result = service.search_tariff_lines("ETH", "01012100000", limit=1)[0]

    assert result["dd_rate"] is None
    assert result["duty_status"] == "UNAVAILABLE"


def test_search_keeps_existing_etl_hs6_priority(monkeypatch, tmp_path):
    etl_line = {
        "hs6": "010121",
        "description_fr": "Ligne SH6 ETL existante",
        "dd_rate": 5,
        "vat_rate": 15,
        "source": "ETL existant",
        "sub_positions": [],
    }
    _write_crawled(
        tmp_path,
        "ZAF",
        {
            "positions": [
                {
                    "code_clean": "010121",
                    "designation": "Crawled HS6 must not shadow ETL",
                    "taxes": [{"code": "GENERAL", "name": "General duty", "rate_pct": 99}],
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(
        service,
        "load_country_tariffs",
        lambda *_args: {"tariff_lines": [etl_line]},
    )

    result = service.search_tariff_lines("ZAF", "010121", limit=1)[0]

    assert result["dd_rate"] == 5
    assert result["source"] == "ETL existant"


def test_real_repository_regression_formats_are_consumed(monkeypatch):
    gha = service.load_crawled_position_index("GHA")
    ken = service.load_crawled_position_index("KEN")
    zaf = service.load_crawled_position_index("ZAF")

    assert len(gha) >= 6_000  # tariff_lines[].sub_positions[]
    assert len(ken) >= 5_900  # positions[]
    assert len(zaf) >= 8_500  # positions[] with mixed code lengths
    assert "0101210000" in gha
    assert "01012100" in ken
    assert isinstance(zaf["010121"]["taxes"], list)

    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)
    gin_result = service.search_tariff_lines("GIN", "7612900000", limit=1)[0]
    nga_result = service.search_tariff_lines("NGA", "0101210000", limit=1)[0]

    assert gin_result["dd_rate"] == 20
    assert gin_result["tva_rate"] == 18
    assert nga_result["dd_rate"] == 5
    assert nga_result["tva_rate"] == 7.5


def test_crawled_index_cache_is_bounded_to_recent_countries():
    for position in range(service._CRAWLED_INDEX_CACHE_MAX_COUNTRIES + 1):
        service._cache_crawled_position_index(f"X{position}", {str(position): {}})

    assert len(service._crawled_index_cache) == service._CRAWLED_INDEX_CACHE_MAX_COUNTRIES
    assert "X0" not in service._crawled_index_cache


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


@pytest.mark.parametrize(
    "iso3, raw_taxes",
    [
        ("CIV", {"DD": 99.0, "TVA": 99.0}),
        (
            "NGA",
            [
                {"code": "ID", "name": "Import Duty", "rate_pct": 99.0},
                {"code": "VAT", "name": "Value Added Tax", "rate_pct": 99.0},
            ],
        ),
    ],
)
def test_calculator_keeps_etl_rates_for_new_scalar_and_list_schemas(
    monkeypatch, tmp_path, iso3, raw_taxes
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
                "code": "0101210000",
                "dd": 5,
                "description_fr": "Chevaux reproducteurs",
            }
        ],
        "administrative_formalities": [],
    }
    _write_crawled(
        tmp_path,
        iso3,
        {
            "positions": [
                {
                    "code_clean": "0101210000",
                    "designation": "Chevaux reproducteurs",
                    "taxes": raw_taxes,
                }
            ]
        },
    )
    monkeypatch.setattr(service, "CRAWLED_DIR", str(tmp_path))
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: dict(parent_line))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: {})
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)

    result = service.calculate_import_taxes(iso3, "0101210000", 1_000)

    assert result["rates"]["dd_rate_pct"] == 5
    assert result["rates"]["vat_rate_pct"] == 14
    assert result["taxes_detail"]["DD"]["rate"] == 20
    assert result["taxes_detail"]["TVA"]["rate"] == 14
