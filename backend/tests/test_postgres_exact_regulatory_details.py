"""Execute provider SQL against isolated relational contract fixtures.

ZZZ and sentinel rows are test-only, never tariff data for the application.
SQLite exercises the queries; live PostgreSQL integration remains separate.
"""

import sqlite3

import pytest
from services.postgres_tariff_service import PostgresTariffService


@pytest.fixture
def provider():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE commodities (id INTEGER, country_iso3 TEXT, hs6 TEXT,
          national_code TEXT, description_fr TEXT, description_en TEXT,
          total_npf_pct REAL, total_zlecaf_pct REAL);
        CREATE TABLE measures (commodity_id INTEGER, measure_type TEXT, code TEXT,
          name_fr TEXT, rate_pct REAL, is_zlecaf_applicable INTEGER, zlecaf_rate_pct REAL);
        CREATE TABLE requirements (commodity_id INTEGER, requirement_type TEXT,
          code TEXT, document_fr TEXT, is_mandatory INTEGER, issuing_authority TEXT);
        INSERT INTO commodities VALUES
          (1,'ZZZ','000000','00000001','A','A',99,88),
          (2,'ZZZ','000000','00000002','B','B',77,66),
          (3,'YYY','000000','00000001','Other country','Other',55,44);
        INSERT INTO measures VALUES
          (1,'CUSTOMS_DUTY','DD','Duty A',10,1,2),
          (1,'VAT','TVA','VAT A',20,0,NULL),
          (2,'CUSTOMS_DUTY','DD','Duty B',30,0,NULL),
          (3,'CUSTOMS_DUTY','DD','Other country',40,0,NULL);
        INSERT INTO requirements VALUES
          (1,'DOC','A','Document A',1,'Authority A'),
          (2,'DOC','B','Document B',1,'Authority B'),
          (3,'DOC','C','Document C',1,'Authority C');
    """
    )
    service = PostgresTariffService.__new__(PostgresTariffService)
    service._execute_query = lambda query, params=None: [
        dict(row) for row in db.execute(query, params or {}).fetchall()
    ]
    yield service, db
    db.close()


def test_exact_position_does_not_mix_siblings_or_countries(provider):
    service, _ = provider
    result = service.get_regulatory_details("zzz", "0000.00.01")
    assert result["national_code"] == "00000001"
    assert {m["name"] for m in result["measures"]} == {"Duty A", "VAT A"}
    assert [r["code"] for r in result["requirements"]] == ["A"]
    assert result["taxes"] == {"dd_rate": 10, "vat_rate": 20, "zlecaf_rate": 2}


def test_ambiguous_hs6_is_not_arbitrarily_resolved(provider):
    service, _ = provider
    result = service.get_regulatory_details("ZZZ", "000000")
    assert result["success"] is False
    assert result["error_detail"]["code"] == "NATIONAL_POSITION_SELECTION_REQUIRED"
    assert "measures" not in result


def test_missing_national_position_does_not_fall_back_to_sibling(provider):
    service, _ = provider
    result = service.get_regulatory_details("ZZZ", "00000099")
    assert result["success"] is False
    assert "measures" not in result


def test_single_child_can_be_resolved(provider):
    service, _ = provider
    result = service.get_regulatory_details("YYY", "000000")
    assert result["national_code"] == "00000001"
    assert result["taxes"]["vat_rate"] is None
    assert result["taxes"]["zlecaf_rate"] is None


@pytest.mark.parametrize("rate", [None, 0])
def test_missing_rate_and_documented_zero_remain_distinct(provider, rate):
    service, db = provider
    db.execute("UPDATE measures SET rate_pct=? WHERE commodity_id=1 AND code='DD'", (rate,))
    result = service.get_regulatory_details("ZZZ", "00000001")
    assert result["taxes"]["dd_rate"] == rate


def test_multiple_duties_do_not_turn_into_a_single_rate(provider):
    service, db = provider
    db.execute("INSERT INTO measures VALUES (1,'CUSTOMS_DUTY','DD2','Conditional',40,0,NULL)")
    result = service.get_regulatory_details("ZZZ", "00000001")
    assert result["taxes"]["dd_rate"] is None
