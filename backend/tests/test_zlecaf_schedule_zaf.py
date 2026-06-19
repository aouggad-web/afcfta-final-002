"""
Tests des partenaires ZLECAf actifs à l'importation en Afrique du Sud
(newsletter AfCFTA, the dtic/SARS, mars 2026).
"""
from services.zlecaf_schedule_zaf import zaf_partner_active, ACTIVE_PARTNERS_ZAF


def test_named_implementing_country_is_active():
    assert zaf_partner_active("GHA") is True
    assert zaf_partner_active("dza") is True  # insensible à la casse


def test_sacu_member_not_counted_as_zlecaf_partner():
    # La SACU (Botswana, Lesotho, Namibie, Eswatini) échange avec l'Afrique
    # du Sud sous le régime SACU, pas sous la ZLECAf (FAQ explicite).
    for sacu_iso3 in ("BWA", "LSO", "NAM", "SWZ"):
        assert zaf_partner_active(sacu_iso3) is False


def test_non_listed_country_not_active():
    assert zaf_partner_active("SEN") is False


def test_active_partners_count():
    assert len(ACTIVE_PARTNERS_ZAF) == 14
