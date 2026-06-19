"""
Tests du statut de ratification continental de l'Accord ZLECAf (newsletter
AfCFTA, the dtic/SARS, mars 2026).
"""
from services.zlecaf_membership_status import (
    ratification_status, is_party_to_agreement,
    STATUS_NOT_SIGNED, STATUS_SIGNED_NOT_RATIFIED, STATUS_RATIFIED,
)


def test_eritrea_not_signed():
    assert ratification_status("ERI") == STATUS_NOT_SIGNED
    assert is_party_to_agreement("ERI") is False


def test_four_signed_not_ratified_countries():
    for iso3 in ("BEN", "LBY", "SSD", "SDN"):
        assert ratification_status(iso3) == STATUS_SIGNED_NOT_RATIFIED
        assert is_party_to_agreement(iso3) is False


def test_default_country_is_ratified():
    for iso3 in ("DZA", "ZAF", "NGA", "MAR", "EGY"):
        assert ratification_status(iso3) == STATUS_RATIFIED
        assert is_party_to_agreement(iso3) is True


def test_case_insensitive_and_empty():
    assert ratification_status("eri") == STATUS_NOT_SIGNED
    assert ratification_status("") == STATUS_RATIFIED
