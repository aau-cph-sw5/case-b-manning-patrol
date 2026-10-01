from dataclasses import dataclass
from .patrol_area import AreaKind, PatrolArea


@dataclass
class Station:
    id: str 
    name: str
    line_ids: list[str] 
    patrol_areas: list[PatrolArea]

    # This function returns the PatrolArea object that matches the given kind, or None if no match is found
    # kind gets the value of the AreaKind enum, e.g. AreaKind.CONCOURSE or AreaKind.PLATFORM
    def area(self, kind: AreaKind) -> PatrolArea | None:
            for a in self.patrol_areas:
                if a.area_kind == kind:
                    return a
            return None
