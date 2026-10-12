from dataclasses import dataclass

from .patrol_area import AreaKind, PatrolArea


@dataclass
class Station:
    id: str
    name: str
    line_ids: list[str]
    patrol_areas: list[PatrolArea]

    # Returns the PatrolArea matching the given kind, or None if no match is found.
    # kind is an AreaKind value, e.g. AreaKind.CONCOURSE or AreaKind.PLATFORM.
    def area(self, kind: AreaKind) -> PatrolArea | None:
        for a in self.patrol_areas:
            if a.area_kind == kind:
                return a
        return None
