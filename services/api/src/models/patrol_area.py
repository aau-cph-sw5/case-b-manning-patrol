from dataclasses import dataclass
from enum import StrEnum


class AreaKind(StrEnum):
    CONCOURSE = "concourse"
    PLATFORM = "platform"


@dataclass
class PatrolArea:
    id: str
    area_kind: AreaKind
    beacon_id: str
