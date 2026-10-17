from __future__ import annotations

# Identifies one patrol area. Key for area coverage and for overdue log entries.
from pydantic.dataclasses import dataclass

from src.models.patrol_area import AreaKind, PatrolArea


@dataclass(frozen=True)
class AreaRef:
    station_id: str | None
    area_id: str
    kind: AreaKind

    @staticmethod
    def from_patrol_area(area: PatrolArea) -> AreaRef:
        return AreaRef(area.station_id, area.area_id, area.area_kind)
