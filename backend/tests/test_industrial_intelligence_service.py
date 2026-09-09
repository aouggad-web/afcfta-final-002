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
    # Urea -> Sorfert/AOA (engrais azotés). A value-added champion is a growth
    # opportunity under AfCFTA, so the display signal is "High Growth"; provenance
    # (operational) is carried by the champion's status field.
    m = ii.match_for_hs("DZA", "310210")
    assert m["available"] is True
    assert m["signal"] == "High Growth"
    assert m["champion"] is not None
    assert "Sorfert" in m["champion"]["name"]
    assert m["champion"]["status"] == "operational"
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


def test_autoderivation_covers_noncurated_countries():
    # Guinea (Simandou) -> iron ore; DRC -> copper/cobalt; Nigeria -> refined fuel.
    # None of these are hand-curated, yet their structuring projects must yield
    # forward-looking "High Growth" capacity.
    assert ii.is_curated("GIN") is False
    assert ii.has_intelligence("GIN") is True
    gin = ii.match_for_hs("GIN", "260111")  # iron ore
    assert gin["signal"] == "High Growth"
    assert gin["future_capacity"] is not None

    cod = ii.match_for_hs("COD", "260300")  # copper ore
    assert cod["signal"] == "High Growth"

    nga = ii.match_for_hs("NGA", "271000")  # refined petroleum
    assert nga["signal"] == "High Growth"


def test_autoderivation_ignores_pure_infrastructure():
    # A railway/port keyword must never be mistaken for a commodity
    # ("ferroviaire" must not match the \bfer\b iron-ore rule).
    from services.industrial_intelligence_service import _commodity_for_project

    assert _commodity_for_project("Transport Ferroviaire", "Ligne Ferroviaire") is None
    assert _commodity_for_project("Infrastructure Portuaire", "Port en eaux profondes") is None
    assert _commodity_for_project("Énergie - Hydraulique", "Barrage") is None
    # But a genuine mining sector maps.
    assert _commodity_for_project("Mines - Fer", "Mine de fer") is not None


def test_is_curated_vs_has_intelligence():
    assert ii.is_curated("DZA") is True
    assert ii.has_intelligence("DZA") is True
    # Unknown country: neither.
    assert ii.is_curated("XXX") is False
    assert ii.has_intelligence("XXX") is False


def test_major_economies_have_curated_flagship_champions():
    # Each big economy's verified flagship must match its signature product.
    cases = {
        "MAR": ("251010", "ocp"),  # phosphate rock -> OCP
        "NGA": ("271000", "dangote refinery"),  # refined petroleum -> Dangote Refinery
        "EGY": ("721420", "ezz"),  # rebars -> Ezz Steel
        "ZAF": ("080510", "agrume"),  # oranges -> citrus filière
    }
    for iso, (hs, needle) in cases.items():
        assert ii.is_curated(iso) is True, iso
        m = ii.match_for_hs(iso, hs)
        assert m["champion"] is not None, (iso, hs)
        assert needle in m["champion"]["name"].lower(), (iso, m["champion"]["name"])
        assert m["signal"] == "High Growth"


def test_priority_commodities_deduped():
    items = ii.priority_commodities("DZA")
    assert items
    codes = [it["hs_code"] for it in items]
    assert len(codes) == len(set(codes))  # no duplicate HS codes
    # All capacity-driven commodities carry the growth signal.
    signals = {it["signal"] for it in items}
    assert "High Growth" in signals
    assert "High Growth" in signals
