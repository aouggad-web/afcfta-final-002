import json
from pathlib import Path

from services.tariff_enrichment_service import get_country_enrichment

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATHS = (
    REPO_ROOT / "data" / "regional-18" / "tariff_enrichment_registry.json",
    REPO_ROOT / "data" / "west-africa-15" / "tariff_enrichment_registry.json",
    REPO_ROOT / "data" / "algeria-active-3" / "tariff_enrichment_registry.json",
)


def _configured_countries():
    for registry_path in REGISTRY_PATHS:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        yield from registry["countries"].items()


def _source_ids(vat_data):
    return sorted(
        {
            record["source_id"]
            for collection in ("vat_rates", "vat_exemptions", "vat_zero_rated")
            for record in vat_data.get(collection, [])
            if record.get("source_id")
        }
    )


def test_published_vat_records_expose_their_traceability_source_ids():
    checked = 0
    for country, configured in _configured_countries():
        vat_measure_path = configured.get("vat_measure_path")
        if not vat_measure_path:
            continue

        enrichment = get_country_enrichment(country)
        tax = enrichment["consumption_tax"]
        vat_data = json.loads((REPO_ROOT / vat_measure_path).read_text(encoding="utf-8"))
        expected = _source_ids(vat_data) if configured["vat_status"] != "NOT_AVAILABLE" else []

        assert tax["source_ids"] == expected, country
        assert set(tax["source_ids"]) <= {
            source["source_id"] for source in enrichment["traceability_sources"]
        }, country
        checked += 1

    assert checked == 18


def test_unavailable_vat_does_not_expose_unpublished_measure_sources():
    tunisia = get_country_enrichment("TUN")

    assert tunisia["vat_status"] == "NOT_AVAILABLE"
    assert tunisia["consumption_tax"]["rates"] == []
    assert tunisia["consumption_tax"]["source_ids"] == []
