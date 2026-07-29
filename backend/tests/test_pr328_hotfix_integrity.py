from services.tariff_enrichment_service import get_country_enrichment


def test_burundi_vat_base_fails_closed_until_runtime_conflict_is_reconciled():
    tax = get_country_enrichment("BDI")["consumption_tax"]

    assert tax["standard_rate"] == 18.0
    assert tax["standard_rate_source_id"] == "BDI-OBR-VAT-AMEND-2020"
    assert tax["import_base"] is None
    assert tax["base_status"] == "NOT_AVAILABLE"


def test_equatorial_guinea_tax_claims_are_bound_to_specific_sources():
    tax = get_country_enrichment("GNQ")["consumption_tax"]

    assert tax["standard_rate_source_id"] == "GNQ-TAX-LAW-4-2004"
    assert tax["import_base_source_id"] == "GNQ-TAX-LAW-4-2004"

    reduced = {item["rate"]: item for item in tax["reduced_rates"]}
    assert reduced[6.0]["source_id"] == "GNQ-TAX-LAW-4-2004"
    assert reduced[5.0]["source_id"] == "GNQ-BUDGET-LAW-9-2025"
    assert reduced[0.0]["source_id"] == "GNQ-BUDGET-LAW-9-2025"
    assert reduced[5.0]["effective_from"] == "2026-01-01"
    assert reduced[0.0]["effective_from"] == "2026-01-01"


def test_priority_08_source_references_resolve_to_country_source_records():
    for country in ("BDI", "GNQ"):
        enrichment = get_country_enrichment(country)
        source_ids = {
            source["source_id"] for source in enrichment["traceability_sources"]
        }
        tax = enrichment["consumption_tax"]

        claim_source_ids = {
            value
            for key, value in tax.items()
            if key.endswith("_source_id") and value is not None
        }
        claim_source_ids.update(
            item["source_id"]
            for item in tax.get("reduced_rates", [])
            if item.get("source_id")
        )

        assert claim_source_ids
        assert claim_source_ids <= source_ids
