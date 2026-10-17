"""
Value objects for patrol coverage and the overdue log (MET-B-007)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from src.models.patrol_area import AreaKind
from src.services.coverage.models.area_coverage import AreaCoverage
from src.services.coverage.models.area_ref import AreaRef


# Whether an area, or a whole station, has been patrolled within the window.
class CoverageStatus(StrEnum):
    COMPLIANT = "compliant"
    OVERDUE = "overdue"


# Coverage of one station: one AreaCoverage per patrol area of the station.
@dataclass(frozen=True)
class StationCoverage:
    station_id: str
    areas: tuple[AreaCoverage, ...]

    def areas_of(self, kind: AreaKind) -> tuple[AreaCoverage, ...]:
        """The station's areas of one kind, for example all its platforms.

        A station can have several areas of the same kind (two platforms at an
        interchange), each with its own result. That is why this returns a
        tuple instead of a single platform or concourse field.
        """
        return self.areas

    @property
    def status(self) -> CoverageStatus:
        """Whether the station as a whole is COMPLIANT or OVERDUE.

        OVERDUE as soon as any of its areas is OVERDUE, because every area must
        be patrolled. Derived from the areas, so the station can never disagree
        with them.
        """
        raise NotImplementedError

    def state(self) -> tuple:
        """The value that decides whether this station must be published again.

        The state() of each area, ordered by area_id so the order the areas
        were loaded in does not matter. When any area's state changes, the
        whole station is pushed to the dashboard.
        """
        raise NotImplementedError


# Log entry: the system saw an area become overdue. Append-only.
# Storage schema is open (ADR-0008).
@dataclass(frozen=True)
class OverdueDetected:
    area: AreaRef
    overdue_at: datetime
    detected_at: datetime
    last_covered_at: datetime | None
    source: str

    @property
    def entry_id(self) -> UUID:
        """A stable id for this entry, the same every time it is computed.

        uuid5 of (station_id, area_id, overdue_at, "DETECTED") with one fixed
        namespace. The tracker compares it with the ids already in the log, so
        a repeated refresh or a restart never logs the same episode twice. Two
        different episodes have different overdue_at values, so different ids.
        """
        raise NotImplementedError


# Log entry: an overdue episode for an area was cleared. Append-only.
# Storage schema is open (ADR-0008).
@dataclass(frozen=True)
class OverdueCleared:
    area: AreaRef
    overdue_at: datetime
    cleared_at: datetime
    source: str

    @property
    def entry_id(self) -> UUID:
        """A stable id for this entry, the same every time it is computed.

        uuid5 of (station_id, area_id, overdue_at, "CLEARED") with the same
        namespace as OverdueDetected. Shares overdue_at with the matching
        DETECTED entry, so the pair can be found, but never the same id.
        """
        raise NotImplementedError

    @property
    def overdue_for(self) -> timedelta:
        """How long the area was overdue in total.

        cleared_at - overdue_at. Computed from the two stored timestamps
        instead of being stored, so it can never disagree with them.
        """
        raise NotImplementedError
