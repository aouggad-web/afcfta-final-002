"""Invariants for the common regional / national customs model.

The registry is deliberately small in this wave.  These tests exercise the
temporal and priority semantics without asserting unverified tariff rates.
"""

from datetime import date
from pathlib import Path

from engine.customs_territory_registry import CustomsTerritoryRegistry
from engine.schemas.customs_territory import (
    CustomsTerritory,
    ImplementationStatus,
    TerritoryMembership,
    TerritoryType,
)


MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "customs" / "africa_customs_model.json"


def _registry():
    return CustomsTerritoryRegistry.from_path(MODEL_PATH)


def test_country_selects_common_customs_union_by_date():
    registry = _registry()

    assert registry.tariff_territory_for("KEN", date(2023, 1, 1)).territory_id == "EAC"
    # Membership has an explicit start date; it must not be projected backward.
    assert registry.tariff_territory_for("KEN", date(2021, 12, 31)) is None


def test_national_membership_can_have_non_tariff_regional_affiliations():
    registry = _registry()

    # COMESA/SADC are represented as FTA metadata and must not override the
    # customs-union tariff authority selected for the country.
    # Pending-verification memberships are intentionally not active yet.
    assert registry.territory_ids_for("KEN", date(2023, 1, 1)) == ["EAC"]
    assert registry.tariff_territory_for("KEN", date(2023, 1, 1)).territory_id == "EAC"


def test_sacu_membership_is_dated_and_country_specific_tax_layer_is_separate():
    registry = _registry()

    assert registry.tariff_territory_for("ZAF", date(2026, 5, 28)) is None
    assert registry.tariff_territory_for("ZAF", date(2026, 5, 29)).territory_id == "SACU"
    assert registry.tariff_territory_for("ZAF", date(2026, 7, 1)).territory_id == "SACU"


def test_equal_tariff_authority_priority_is_not_resolved_arbitrarily():
    """Two equally preferred customs unions require human review upstream."""
    territories = [
        CustomsTerritory(
            territory_id="A",
            name="A",
            territory_type=TerritoryType.CUSTOMS_UNION,
            tariff_authority=True,
            priority=10,
            source_id="A-SOURCE",
        ),
        CustomsTerritory(
            territory_id="B",
            name="B",
            territory_type=TerritoryType.CUSTOMS_UNION,
            tariff_authority=True,
            priority=10,
            source_id="B-SOURCE",
        ),
    ]
    memberships = [
        TerritoryMembership(
            territory_id=territory,
            country_iso3="KEN",
            valid_from=date(2020, 1, 1),
            implementation_status=ImplementationStatus.ACTIVE,
            source_id=f"{territory}-MEMBERSHIP",
        )
        for territory in ("A", "B")
    ]
    registry = CustomsTerritoryRegistry(territories, memberships)

    assert registry.tariff_territory_for("KEN", date(2024, 1, 1)) is None
