"""
Tests for the industrial intelligence service.

Focus: the curated knowledge base must
- match operational champions by HS product (longest-prefix wins),
- surface forward-looking megaprojects as a "High Growth" signal,
- cross-reference megaprojects with the real projets_structurants data,
- fail closed (empty result) for unknown countries/products.

No network, no mocking needed — the KB and projects files ship in the repo.
"""

from services import industrial_intelligence_service as ii


def test_kb_loads_and_algeria_present():
    assert ii.has_intelligence("DZA") is True
    assert ii.has_intelligence("dza") is True  # case-insensitive
    profile = ii.get_country_intelligence("DZA")
    assert profile is not None
    assert profile.get("champions")


def test_operational_champion_matched_by_hs():
    # Urea -> Sorfert/AOA (engrais azotés)
    m = ii.match_for_hs("DZA", "310210")
    assert m["available"] is True
    assert m["signal"] == "Established"
    assert m["champion"] is not None
    assert "Sorfert" in m["champion"]["name"]
    assert m["future_capacity"] is None


def test_champion_transformation_pathway_exposed():
    # The strategic card needs input -> process -> output to render.
    champ = ii.match_for_hs("DZA", "852872")["champion"]  # TVs -> Condor
    assert champ is not None
    assert "Condor" in champ["name"]
    assert champ.get("input_source")
    assert champ.get("process")
    assert champ.get("output_product")


def test_future_megaproject_signals_high_growth_with_detail():
    # Iron ore -> Gara Djebilet (a forward-looking structuring project).
    m = ii.match_for_hs("DZA", "260111")
    assert m["signal"] == "High Growth"
    fut = m["future_capacity"]
    assert fut is not None
    assert fut["linked_project"] == "Mine de Fer Gara Djebilet - Phase de Production"
    # Cross-referenced with the real projets_structurants_afrique data.
    assert "project_detail" in fut
    assert fut["project_detail"].get("titre") == fut["linked_project"]


def test_phosphate_future_capacity_matches():
    # Natural phosphate 2510 -> Bled El Hadba integrated phosphate project.
    m = ii.match_for_hs("DZA", "251010")
    assert m["signal"] == "High Growth"
    assert m["future_capacity"]["linked_project"] == (
        "Projet Phosphate Intégré (PPI) - Bled El Hadba"
    )


def test_unknown_country_and_product_fail_closed():
    m_country = ii.match_for_hs("XXX", "310210")
    assert m_country["available"] is False
    assert m_country["champion"] is None
    assert m_country["future_capacity"] is None

    m_product = ii.match_for_hs("DZA", "999999")
    assert m_product["available"] is False
    assert m_product["signal"] is None


def test_priority_commodities_deduped():
    items = ii.priority_commodities("DZA")
    assert items
    codes = [it["hs_code"] for it in items]
    assert len(codes) == len(set(codes))  # no duplicate HS codes
    # Both established and high-growth commodities appear.
    signals = {it["signal"] for it in items}
    assert "Established" in signals
    assert "High Growth" in signals
