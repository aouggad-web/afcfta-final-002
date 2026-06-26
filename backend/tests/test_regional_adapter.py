"""
Tests de l'adaptateur de bloc régional (propagation du TEC/TDC).

Sans réseau : la source (le tarif extérieur commun) provient des États membres
déjà présents dans data/crawled. Vérifie que le droit de douane commun est
préservé, que la TVA devient nationale, et que le résultat est authentique.
"""

import pytest
from tariff_crawl.adapters.regional import (
    NATIONAL_ONLY,
    _swap_vat,
    build_regional_file,
    deferred_national,
    find_gaps,
)
from tariff_crawl.canonical import validate_authenticity
from tariff_crawl.manifest import Provenance


def test_swap_vat_keeps_duty_changes_only_vat():
    pos = {
        "code": "0101.21.00.00",
        "taxes": {"DD": 10.0, "PCS": 1.0, "TVA": 18.0},
        "taxes_detail": [
            {"tax_code": "DD", "rate": 10.0},
            {"tax_code": "TVA", "rate": 18.0},
        ],
    }
    out = _swap_vat(pos, 15.0)
    assert out["taxes"]["DD"] == 10.0  # droit commun inchangé
    assert out["taxes"]["PCS"] == 1.0  # prélèvement communautaire inchangé
    assert out["taxes"]["TVA"] == 15.0  # TVA -> taux national
    assert out["taxes_detail"][1]["rate"] == 15.0
    # l'original n'est pas muté
    assert pos["taxes"]["TVA"] == 18.0


def test_ghana_is_deferred_to_national_crawl():
    assert "GHA" in NATIONAL_ONLY
    assert "GHA" not in find_gaps("ECOWAS")


@pytest.mark.parametrize(
    "iso,bloc,expected_vat",
    [
        ("GNB", "ECOWAS", 17.0),
        ("LBR", "ECOWAS", 10.0),
        ("GNQ", "CEMAC", 15.0),
    ],
)
def test_build_regional_file_authentic_and_national_vat(iso, bloc, expected_vat):
    doc, issues = build_regional_file(iso, bloc)
    assert not issues, issues
    assert doc["source_quality"] == Provenance.REGIONAL_CET.value
    assert doc["stats"]["sub_positions"] > 0

    ok, _ = validate_authenticity(doc)
    assert ok

    # La TVA de toute position porte le taux national du pays cible.
    key = "positions" if "positions" in doc else "sub_positions"
    sample = doc[key][50]
    vat = sample["taxes"].get("TVA", sample["taxes"].get("VAT"))
    assert vat == expected_vat


def test_regional_file_has_explicit_source_and_provenance():
    doc, _ = build_regional_file("CPV", "ECOWAS")
    assert "CEDEAO" in doc["source"]
    assert doc["source_url"]
    assert doc["derived_from"] == "BEN"
