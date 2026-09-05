"""Tests unitaires du module `regional_blocs` : résolution des unions douanières
(libre circulation, recalcul 0 %) et des zones de libre-échange (conditionnel,
sans recalcul). Couvre l'auto-échange, les blocs chevauchants et la
normalisation des codes ISO."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.regional_blocs import (
    CUSTOMS_UNION_NAMES,
    CUSTOMS_UNIONS,
    FREE_TRADE_AREAS,
    FTA_NAMES,
    same_customs_union,
    shared_free_trade_areas,
)

# ── Unions douanières ───────────────────────────────────────────────────────


def test_same_customs_union_sacu():
    assert same_customs_union("BWA", "ZAF") == "SACU"


def test_same_customs_union_uemoa():
    assert same_customs_union("BEN", "SEN") == "UEMOA"


def test_same_customs_union_eac():
    assert same_customs_union("KEN", "UGA") == "EAC"


def test_same_customs_union_cemac():
    assert same_customs_union("CMR", "GAB") == "CEMAC"


def test_no_shared_customs_union_returns_none():
    # ZAF (SACU) vs EGY (aucune union douanière commune).
    assert same_customs_union("ZAF", "EGY") is None


def test_customs_union_self_trade_is_none():
    assert same_customs_union("ZAF", "ZAF") is None


def test_customs_union_empty_input_is_none():
    assert same_customs_union("", "ZAF") is None
    assert same_customs_union("ZAF", None) is None


def test_customs_union_normalizes_case_and_whitespace():
    assert same_customs_union(" zaf ", "bwa") == "SACU"


# ── Zones de libre-échange (conditionnelles) ────────────────────────────────


def test_shared_fta_comesa():
    # ERI et EGY partagent le COMESA mais aucune union douanière.
    assert same_customs_union("ERI", "EGY") is None
    assert shared_free_trade_areas("ERI", "EGY") == ["COMESA"]


def test_shared_fta_self_trade_is_empty():
    assert shared_free_trade_areas("EGY", "EGY") == []


def test_shared_fta_empty_when_no_common_area():
    # ZAF (SADC) vs EGY (COMESA) : aucune ZLE commune.
    assert shared_free_trade_areas("ZAF", "EGY") == []


# ── Blocs chevauchants : l'union douanière prime, la ZLE reste signalée ──────


def test_overlap_sacu_members_also_share_sadc():
    """ZAF/BWA : union douanière SACU ET zone de libre-échange SADC."""
    assert same_customs_union("ZAF", "BWA") == "SACU"
    assert shared_free_trade_areas("ZAF", "BWA") == ["SADC"]


def test_overlap_uemoa_members_also_share_ecowas():
    """BEN/SEN : union douanière UEMOA ET zone de libre-échange CEDEAO."""
    assert same_customs_union("BEN", "SEN") == "UEMOA"
    assert shared_free_trade_areas("BEN", "SEN") == ["ECOWAS"]


def test_eswatini_multi_bloc_membership():
    """SWZ appartient à SACU, SADC et COMESA : la résolution dépend du partenaire."""
    # Avec ZAF (SACU + SADC) : union douanière SACU, ZLE SADC.
    assert same_customs_union("SWZ", "ZAF") == "SACU"
    assert shared_free_trade_areas("SWZ", "ZAF") == ["SADC"]
    # Avec KEN (EAC + COMESA) : aucune union douanière commune, ZLE COMESA.
    assert same_customs_union("SWZ", "KEN") is None
    assert shared_free_trade_areas("SWZ", "KEN") == ["COMESA"]


# ── Cohérence des tables (codes ↔ libellés) ─────────────────────────────────


def test_every_customs_union_has_a_name():
    assert set(CUSTOMS_UNIONS) == set(CUSTOMS_UNION_NAMES)


def test_every_fta_has_a_name():
    assert set(FREE_TRADE_AREAS) == set(FTA_NAMES)
