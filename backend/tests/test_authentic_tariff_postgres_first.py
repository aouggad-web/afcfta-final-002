import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import authentic_tariff_service as svc


class _PostgresProviderSuccess:
    def get_regulatory_details(self, country_iso3, hs6):
        return {
            "success": True,
            "description": "Produit test PostgreSQL",
            "taxes": {"dd_rate": 5.0, "zlecaf_rate": 0.0},
            "measures": [
                {
                    "code": "DD",
                    "name": "Droits de Douane",
                    "rate": 5.0,
                    "zlecaf_applicable": True,
                    "zlecaf_rate": 0.0,
                },
                {
                    "code": "TVA",
                    "name": "TVA",
                    "rate": 20.0,
                    "zlecaf_applicable": False,
                    "zlecaf_rate": None,
                },
            ],
            "requirements": [{"code": "DOC1", "document": "Facture"}],
        }

    def get_country_info(self, country_iso3):
        return {"vat_rate": 20.0, "total_positions": 10, "chapters_covered": 2}

    def get_sub_positions(self, country_iso3, hs6, language="fr"):
        return [
            {
                "code": f"{hs6}0010",
                "digits": 10,
                "description_fr": "Sous-position PostgreSQL",
                "description_en": "PostgreSQL sub-position",
                "dd": 5.0,
            }
        ]


class _PostgresProviderMiss:
    def get_regulatory_details(self, country_iso3, hs6):
        return {"success": False}

    def get_country_info(self, country_iso3):
        return {"vat_rate": 19.0}

    def get_sub_positions(self, country_iso3, hs6, language="fr"):
        return []


@pytest.fixture(autouse=True)
def reset_postgres_provider_cache():
    svc._postgres_provider_cache = None


def test_get_tariff_line_prefers_postgres(monkeypatch):
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: _PostgresProviderSuccess())
    monkeypatch.setattr(
        svc,
        "load_country_tariffs",
        lambda iso3: {
            "tariff_lines": [{"hs6": "180100", "dd_rate": 30.0, "description_fr": "ETL"}]
        },
    )

    line = svc.get_tariff_line("MAR", "180100")

    assert line is not None
    assert line["data_source"] == "postgres"
    assert line["dd_rate"] == 5.0
    assert line["description_fr"] == "Produit test PostgreSQL"


def test_get_tariff_line_falls_back_to_etl(monkeypatch):
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: _PostgresProviderMiss())
    etl_line = {"hs6": "180100", "dd_rate": 25.0, "description_fr": "ETL line"}
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: {"tariff_lines": [etl_line]})

    line = svc.get_tariff_line("MAR", "180100")

    assert line == etl_line
    assert line["dd_rate"] == 25.0


def test_get_sub_positions_prefers_postgres(monkeypatch):
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: _PostgresProviderSuccess())
    monkeypatch.setattr(svc, "load_crawled_position_index", lambda _iso3: {})
    monkeypatch.setattr(svc, "load_nomenclature_map", lambda _iso3: None)

    positions = svc.get_sub_positions("MAR", "180100")

    assert len(positions) == 1
    assert positions[0]["source"] == "postgres"
    assert positions[0]["dd_rate"] == 5.0


def test_calculate_import_taxes_uses_postgres_when_etl_unavailable(monkeypatch):
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: _PostgresProviderSuccess())
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: None)
    monkeypatch.setattr(
        svc,
        "load_crawled_position_index",
        lambda iso3: {"1801000010": {"taxes": {"DD": {"rate": 99.0}}}},
    )

    result = svc.calculate_import_taxes("MAR", "1801000010", 1000.0)

    assert "error" not in result
    assert result["rates"]["dd_rate_pct"] == 5.0
    assert result["sub_position"]["code"] == "1801000010"
