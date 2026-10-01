from dataclasses import dataclass
from enum import Enum

class AreaKind(str, Enum):
    CONCOURSE = "concourse"
    PLATFORM = "platform"

@dataclass
class PatrolArea:
    id: str
    area_kind: AreaKind
    beacon_id: str