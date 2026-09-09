"""Regression guards for unknown customs-duty handling.

Missing DD must remain ``None``/``UNAVAILABLE`` on every public tariff path.
A source-provided ``0.0`` remains a real, payable zero rate.
"""

from services import authentic_tariff_service as service


class _RegulatoryProvider:
    def __init__(self, dd_rate=None, sub_positions=None):
        self.dd_rate = dd_rate
        self.sub_positions = sub_positions or []

    def get_regulatory_details(self, *_args):
        return {
            "success": True,
            "description": "Test position",
            "taxes": {"dd_rate": self.dd_rate},
            "measures": [],
            "requirements": [],
        }

    def get_country_info(self, *_args):
        return {"vat_rate": 18}

    def get_sub_positions(self, *_args):
        return self.sub_positions


class _SearchProvider:
    def __init__(self, dd_rate_marker):
        self.dd_rate_marker = dd_rate_marker

    def search_commodities(self, *_args, **_kwargs):
        row = {
            "hs6": "010121",
            "code": "0101210010",
            "description": "Test search row",
        }
        if self.dd_rate_marker != "MISSING":
            row["dd_rate"] = self.dd_rate_marker
        return [row]


def test_get_tariff_line_postgres_missing_dd_stays_unavailable(monkeypatch):
    provider = _RegulatoryProvider(
        dd_rate=None,
        sub_positions=[{"code": "0101210010", "description_fr": "Sans DD"}],
    )
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: provider)

    line = service.get_tariff_line("GIN", "010121")

    assert line["dd_rate"] is None
    assert line["duty_status"] == "UNAVAILABLE"
    assert line["sub_positions"][0]["dd"] is None
    assert line["sub_positions"][0]["dd_rate"] is None
    assert line["sub_positions"][0]["duty_status"] == "UNAVAILABLE"


def test_get_tariff_line_postgres_verified_zero_remains_payable(monkeypatch):
    provider = _RegulatoryProvider(
        dd_rate=0.0,
        sub_positions=[{"code": "0101210010", "dd": 0.0}],
    )
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: provider)

    line = service.get_tariff_line("GIN", "010121")

    assert line["dd_rate"] == 0.0
    assert line["duty_status"] == "PAYABLE"
    assert line["sub_positions"][0]["dd_rate"] == 0.0
    assert line["sub_positions"][0]["duty_status"] == "PAYABLE"


def test_direct_postgres_search_missing_dd_stays_unavailable(monkeypatch):
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: _SearchProvider("MISSING"))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)

    result = service.search_tariff_lines("GIN", "010121", limit=1)[0]

    assert result["dd_rate"] is None
    assert result["duty_status"] == "UNAVAILABLE"


def test_direct_postgres_search_verified_zero_remains_payable(monkeypatch):
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: _SearchProvider(0.0))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)

    result = service.search_tariff_lines("GIN", "010121", limit=1)[0]

    assert result["dd_rate"] == 0.0
    assert result["duty_status"] == "PAYABLE"


def test_etl_search_missing_dd_is_normalized(monkeypatch):
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_crawled_position_index", lambda *_args: {})
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)
    monkeypatch.setattr(
        service,
        "load_country_tariffs",
        lambda *_args: {
            "tariff_lines": [
                {
                    "hs6": "010121",
                    "description_fr": "Ligne ETL sans DD",
                    "sub_positions": [],
                }
            ]
        },
    )

    result = service.search_tariff_lines("GIN", "010121", limit=1)[0]

    assert result["dd_rate"] is None
    assert result["duty_status"] == "UNAVAILABLE"


def test_nomenclature_search_without_duty_is_unavailable(monkeypatch):
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_crawled_position_index", lambda *_args: {})
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: None)
    monkeypatch.setattr(
        service,
        "load_nomenclature_map",
        lambda *_args: {"0101210099": "Nomenclature sans tarif"},
    )

    result = service.search_tariff_lines("GIN", "0101210099", limit=1)[0]

    assert result["dd_rate"] is None
    assert result["duty_status"] == "UNAVAILABLE"


def test_calculator_fails_closed_when_dd_is_unknown(monkeypatch):
    line = {
        "hs6": "010121",
        "description_fr": "Ligne sans DD",
        "description_en": "Line without duty",
        "dd_rate": None,
        "duty_status": "UNAVAILABLE",
        "source": "postgres",
        "data_source": "postgres",
        "sub_positions": [],
    }
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: dict(line))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: {})

    result = service.calculate_import_taxes("GIN", "010121", 1000)

    assert result["calculation_status"] == "CALCULATION_UNAVAILABLE"
    assert result["duty_status"] == "UNAVAILABLE"
    assert result["rates"]["dd_rate_pct"] is None
    assert "npf_calculation" not in result


def test_calculator_accepts_verified_zero_duty(monkeypatch):
    line = {
        "hs6": "010121",
        "description_fr": "Ligne à droit nul",
        "description_en": "Zero-duty line",
        "dd_rate": 0.0,
        "duty_status": "PAYABLE",
        "vat_rate": 0.0,
        "other_taxes_rate": 0.0,
        "taxes_detail": [],
        "sub_positions": [],
        "administrative_formalities": [],
    }
    monkeypatch.setattr(service, "get_tariff_line", lambda *_args: dict(line))
    monkeypatch.setattr(service, "load_country_tariffs", lambda *_args: {})
    monkeypatch.setattr(service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(service, "load_nomenclature_map", lambda *_args: None)
    monkeypatch.setattr(service, "load_crawled_position_index", lambda *_args: {})

    result = service.calculate_import_taxes("GIN", "010121", 1000)

    assert "error" not in result
    assert result["rates"]["dd_rate_pct"] == 0.0
    assert result["npf_calculation"]["total_to_pay"] == 1000
