from services.tariff_enrichment_service import get_country_enrichment

ACTIVE_PARTNER_RATES = {
    "CMR": "17.5%",
    "KEN": "16%",
    "RWA": "18%",
    "TZA": "18%",
    "ZAF": "15%",
}


def test_five_active_partners_publish_source_bound_current_vat():
    for country, expected_standard_rate in ACTIVE_PARTNER_RATES.items():
        enrichment = get_country_enrichment(country)
        tax = enrichment["consumption_tax"]

        assert tax["status"] == "DOCUMENTED", country
        assert tax["as_of"] == enrichment["as_of"], country
        assert any(record["rate"] == expected_standard_rate for record in tax["rates"])
        assert tax["source_ids"], country
        assert set(tax["source_ids"]) <= {
            source["source_id"] for source in enrichment["traceability_sources"]
        }, country


def test_kenya_expired_and_repealed_vat_records_are_not_published():
    tax = get_country_enrichment("KEN")["consumption_tax"]
    published = tax["rates"] + tax["exemptions"] + tax["zero_rated"]

    assert tax["as_of"] == "2026-07-29"
    assert tax["omitted_historical_records"] == 89
    assert all(record.get("legal_status") not in {"REPEALED", "EXPIRED"} for record in published)
    assert all(
        not record.get("effective_to") or tax["as_of"] <= record["effective_to"]
        for record in published
    )
    assert {
        "VAT-TEMP8-27101220",
        "VAT-TEMP8-27101922",
        "VAT-TEMP8-27101931",
    }.isdisjoint({record["record_id"] for record in published})


def test_unavailable_tunisia_vat_remains_fail_closed():
    tax = get_country_enrichment("TUN")["consumption_tax"]

    assert tax["status"] == "NOT_AVAILABLE"
    assert tax["rates"] == []
    assert tax["exemptions"] == []
    assert tax["zero_rated"] == []
    assert tax["source_ids"] == []
