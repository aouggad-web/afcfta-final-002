"""Tests de la correspondance ISIC Rev.4 <-> SH6 HS 2022 (module etl/isic4_hs6_correspondence)."""

from etl.isic4_hs6_correspondence import (
    coverage_stats,
    hs6_for_isic4,
    is_manufacturing_isic4,
    isic4_for_hs6,
)


def test_coverage_stats_sanity():
    """La couverture doit être stable et couvrir la majorité du SH6 manufacturier."""
    stats = coverage_stats()
    assert stats["hs_edition"].startswith("HS 2022")
    # Snapshot exact — change intentionnellement si les tables sources sont mises à jour.
    assert stats["total_hs6_mapped"] == 5595
    assert stats["hs6_mapped_to_manufacturing_isic4"] == 5014
    assert stats["hs6_with_multiple_isic4"] == 436
    assert len(stats["sources"]) == 3


def test_isic4_for_known_hs6_codes():
    """Cas de contrôle : quelques codes SH6 dont la classe ISIC4 est connue."""
    # HS 100630 (riz semi-blanchi/blanchi) -> ISIC 1061 Travail des grains
    assert isic4_for_hs6("100630") == ["1061"]
    # HS 220300 (bière de malt) -> ISIC 1103 (Fabrication de boissons à base de malt)
    assert isic4_for_hs6("220300") == ["1103"]
    # HS 300490 (autres médicaments préparés) -> division 21 pharmacie
    codes = isic4_for_hs6("300490")
    assert codes and all(c.startswith("21") for c in codes)


def test_isic4_for_hs6_accepts_dotted_form():
    """Le point séparateur du format SH n'est pas significatif."""
    assert isic4_for_hs6("1006.30") == isic4_for_hs6("100630")


def test_isic4_for_hs6_unknown_returns_empty_list():
    assert isic4_for_hs6("999999") == []


def test_hs6_for_isic4_covers_expected_sectors():
    """Chaque grande classe manufacturière doit avoir au moins un SH6 associé."""
    assert len(hs6_for_isic4("1050")) > 0  # Produits laitiers
    assert len(hs6_for_isic4("2910")) > 0  # Véhicules automobiles
    assert len(hs6_for_isic4("2100")) > 0  # Pharmacie
    assert hs6_for_isic4("9999") == []


def test_is_manufacturing_isic4_range():
    assert is_manufacturing_isic4("1010") is True
    assert is_manufacturing_isic4("2910") is True
    assert is_manufacturing_isic4("3320") is True
    assert is_manufacturing_isic4("0111") is False  # agriculture
    assert is_manufacturing_isic4("4520") is False  # commerce
    assert is_manufacturing_isic4("") is False
    assert is_manufacturing_isic4("ab12") is False


def test_round_trip_isic4_to_hs6_to_isic4():
    """Tout SH6 renvoyé par hs6_for_isic4(X) doit inclure X dans son propre mapping ISIC4."""
    for isic in ("1050", "1061", "1103", "2100", "2910"):
        hs_codes = hs6_for_isic4(isic)
        assert hs_codes, f"No HS6 mapped to {isic}"
        for hs in hs_codes[:10]:
            assert isic in isic4_for_hs6(hs), f"{isic} not in isic4_for_hs6({hs})"


def test_cpc_code_with_multiple_isic4_is_not_dropped():
    """
    Régression : la table source CPC21<->ISIC4 n'est pas 1:1 — le code CPC
    "01270" apparaît sur deux lignes avec ISIC4 "0113" et "0230". SH 0709.51
    est mappé à ce CPC ; les deux classes ISIC4 doivent apparaître, pas
    seulement la dernière lue.
    """
    codes = isic4_for_hs6("070951")
    assert "0113" in codes
    assert "0230" in codes


def test_is_manufacturing_isic4_rejects_malformed_codes():
    """Un code non-4-chiffres ne doit jamais être classé manufacturier, même
    si ses 2 premiers caractères tombent dans la plage 10-33."""
    assert is_manufacturing_isic4("10") is False
    assert is_manufacturing_isic4("1010x") is False
    assert is_manufacturing_isic4("101") is False
    assert is_manufacturing_isic4("10100") is False


def test_returned_lists_are_copies_not_cache_aliases():
    """Muter la liste retournée ne doit pas corrompre les appels suivants."""
    hs_codes = hs6_for_isic4("1050")
    original_length = len(hs_codes)
    hs_codes.append("999999")
    hs_codes.clear()
    assert len(hs6_for_isic4("1050")) == original_length

    isic_codes = isic4_for_hs6("100630")
    original = list(isic_codes)
    isic_codes.append("9999")
    isic_codes.clear()
    assert isic4_for_hs6("100630") == original
