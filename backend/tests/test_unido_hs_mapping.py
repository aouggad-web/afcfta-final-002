"""
Tests for the UNIDO ISIC (Rev.4) -> HS product mapping.

Guarantees the mapping stays coherent (well-formed HS4 codes, every ISIC
division present in the UNIDO data is covered, and the forward/inverse lookups
agree), so the discovery engine can rely on it.
"""

from services import unido_hs_mapping as m


def test_every_unido_isic_division_is_mapped():
    """Chaque division ISIC présente dans les données UNIDO a une correspondance."""
    from production_data import get_manufacturing_production

    present = {str(r["isic_code"]) for r in get_manufacturing_production() if r.get("isic_code")}
    missing = present - set(m.ISIC_HS)
    assert not missing, f"Divisions ISIC UNIDO sans mapping SH: {sorted(missing)}"


def test_all_hs4_codes_are_wellformed():
    for isic, block in m.ISIC_HS.items():
        for hs4, label in block["hs4"].items():
            assert hs4.isdigit() and len(hs4) == 4, f"{isic}: SH4 mal formé {hs4!r}"
            assert label, f"{isic}/{hs4}: libellé vide"


def test_each_division_has_transformation_narrative():
    for isic in m.ISIC_HS:
        t = m.transformation_for_isic(isic)
        assert t["input"] and t["process"], f"{isic}: intrant/procédé manquant"
        assert t["isic_label_fr"] and t["isic_label_en"]


def test_forward_and_inverse_lookup_agree():
    # Sucre (1701) -> division 10 (alimentaire) ; ciment (2523) -> 23.
    assert "10" in m.isic_for_hs("170199")
    assert "23" in m.isic_for_hs("252310")
    # Récepteurs TV (8528) -> électronique (26) ; urée (3102) -> chimie (20).
    assert "26" in m.isic_for_hs("852872")
    assert "20" in m.isic_for_hs("310210")
    # Chaque SH4 catalogué retrouve sa division.
    for isic, block in m.ISIC_HS.items():
        for hs4 in block["hs4"]:
            assert isic in m.isic_for_hs(hs4)


def test_hs2_fallback_when_no_exact_hs4():
    # 7299 (SH4 acier non catalogué) doit retomber sur la division 24 via le
    # chapitre 72.
    assert "24" in m.isic_for_hs("729900")


def test_non_manufacturable_product_has_no_isic():
    # Minerai de fer brut (2601) est extractif : aucune division manufacturière.
    assert m.isic_for_hs("260111") == []


def test_product_label_resolves():
    assert m.product_label("252310") == "Ciment (y compris clinker)"
    assert m.product_label("690800") == "Carreaux céramiques vernissés (faïence)"
    assert m.product_label("999999") is None
