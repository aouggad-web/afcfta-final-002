from services.tariff_enrichment_service import get_country_enrichment

EXPECTED_MEASURE_COUNTS = {
    "CMR": 17,
    "KEN": 144,
    "RWA": 7,
    "TZA": 6,
}


def test_other_tax_inventories_are_source_bound_and_date_filtered():
    for country, expected_count in EXPECTED_MEASURE_COUNTS.items():
        enrichment = get_country_enrichment(country)
        inventory = enrichment["other_import_taxes"]

        assert inventory["status"] == enrichment["other_taxes_status"], country
        assert inventory["as_of"] == enrichment["as_of"], country
        assert len(inventory["measures"]) == expected_count, country
        assert inventory["source_ids"], country
        assert set(inventory["source_ids"]) <= {
            source["source_id"] for source in enrichment["traceability_sources"]
        }, country
        assert all(
            record.get("legal_status") not in {"REPEALED", "EXPIRED"}
            for record in inventory["measures"]
        ), country


def test_records_without_explicit_hs_codes_cannot_be_auto_attached():
    for country in EXPECTED_MEASURE_COUNTS:
        measures = get_country_enrichment(country)["other_import_taxes"]["measures"]
        assert all(
            record["automatic_product_specific_hs_attachment_allowed"]
            == bool(record.get("hs_codes_explicit"))
            for record in measures
        ), country


def test_kenya_export_reference_table_is_not_published_as_import_tax():
    inventory = get_country_enrichment("KEN")["other_import_taxes"]

    assert inventory["omitted_historical_records"] == 2
    assert "export_levy_reference_only" not in {
        record["collection"] for record in inventory["measures"]
    }
    assert all(
        record["source_record_path"]
        in {
            "data/kenya/excise_measures.json",
            "data/kenya/import_levies.json",
        }
        for record in inventory["measures"]
    )
