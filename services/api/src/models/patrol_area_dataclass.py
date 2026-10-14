from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class AreaKind(StrEnum):
    CONCOURSE = "concourse"
    PLATFORM = "platform"


@dataclass
class PatrolArea:
    area_id: str
    area_kind: AreaKind
    beacon_id: UUID
