from dataclasses import dataclass

from .patrol_area import PatrolArea


@dataclass
class Station:
    id: str  # Change this
    lines: list[str]  # Change this
    patrol_areas: list[PatrolArea]
