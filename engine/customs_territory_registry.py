"""Load and query dated customs-territory memberships."""

import json
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from engine.schemas.customs_territory import CustomsTerritory, TerritoryMembership


class CustomsTerritoryRegistry:
    def __init__(
        self,
        territories: Iterable[CustomsTerritory],
        memberships: Iterable[TerritoryMembership],
    ):
        self.territories = {item.territory_id: item for item in territories}
        self.memberships = list(memberships)

    @classmethod
    def from_path(cls, path: Path) -> "CustomsTerritoryRegistry":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            (CustomsTerritory(**row) for row in payload.get("customs_territories", [])),
            (TerritoryMembership(**row) for row in payload.get("territory_memberships", [])),
        )

    def territory_ids_for(self, country_iso3: str, on_date: date) -> list[str]:
        country = country_iso3.strip().upper()
        memberships = [
            item
            for item in self.memberships
            if item.country_iso3.upper() == country and item.is_active(on_date)
        ]
        memberships.sort(key=lambda item: self.territories[item.territory_id].priority)
        return [item.territory_id for item in memberships]

    def tariff_territory_for(
        self, country_iso3: str, on_date: date
    ) -> Optional[CustomsTerritory]:
        candidates = [
            self.territories[territory_id]
            for territory_id in self.territory_ids_for(country_iso3, on_date)
            if self.territories[territory_id].tariff_authority
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.priority)
        best_priority = candidates[0].priority
        if sum(item.priority == best_priority for item in candidates) > 1:
            return None
        return candidates[0]
