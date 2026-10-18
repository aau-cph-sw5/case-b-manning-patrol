"""
Value objects for patrol coverage and the overdue log (MET-B-007)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from src.models.patrol_area import AreaKind, PatrolArea


# Whether an area, or a whole station, has been patrolled within the window.
class CoverageStatus(StrEnum):
    COMPLIANT = "compliant"
    OVERDUE = "overdue"


# Identifies one patrol area. Key for area coverage and for overdue log entries.
@dataclass(frozen=True)
class AreaRef:
    station_id: str | None
    area_id: str
    kind: AreaKind

    @staticmethod
    def from_patrol_area(area: PatrolArea) -> AreaRef:
        return AreaRef(area.station_id, area.area_id, area.area_kind)


# A span of time during which an area counts as covered.
@dataclass(frozen=True)
class CoveredTimeSpan:
    start: datetime
    end: datetime

    def touches(self, other: CoveredTimeSpan) -> bool:
        if self.end < other.start:
            return False
        if other.end < self.start:
            return False
        return True

    def merge(self, other: CoveredTimeSpan) -> CoveredTimeSpan:
        if not self.touches(other):
            raise ValueError("Cannot merge non-touching spans")
        return CoveredTimeSpan(
            start=min(self.start, other.start), end=max(self.end, other.end)
        )


# One steward's presence at one beacon: a CONNECT and the DISCONNECT or STOP that
# closed it. ended_at is None while the visit is still open.
@dataclass(frozen=True)
class PresenceInterval:
    android_id: str
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None

    def is_open(self) -> bool:
        return self.ended_at is None

    def duration(self, now: datetime) -> timedelta:
        if self.ended_at is not None:
            return self.ended_at - self.started_at
        return now - self.started_at

    def qualifies(self, min_duration: timedelta, now: datetime) -> bool:
        return self.duration(now) >= min_duration

    def qualified_at(self, min_duration: timedelta) -> datetime:
        return self.started_at + min_duration

    def covered_span(
        self,
        min_duration: timedelta,
        window: timedelta,
        now: datetime,
    ) -> CoveredTimeSpan | None:
        if not self.qualifies(min_duration, now):
            return None
        return CoveredTimeSpan(
            start=self.qualified_at(min_duration),
            end=(self.ended_at or now) + window,
        )


@dataclass(frozen=True)
class OverdueEpisode:
    overdue_at: datetime
    cleared_at: datetime | None

    def is_open(self) -> bool:
        return self.cleared_at is None

    def duration(self, now: datetime) -> timedelta:
        if self.cleared_at is not None:
            return self.cleared_at - self.overdue_at
        return now - self.overdue_at


@dataclass(frozen=True)
class AreaCoverage:
    area: AreaRef
    last_covered_at: datetime | None
    covered_now: bool
    baseline: datetime | None
    current_steward_ids: frozenset[str]
    episodes: tuple[OverdueEpisode, ...]
    window: timedelta
    as_of: datetime

    @property
    def overdue_at(self) -> datetime | None:
        if self.covered_now:
            return None

        if self.last_covered_at is None and self.baseline is None:
            return None

        if self.last_covered_at is None and self.baseline is not None:
            return self.baseline + self.window

        if self.last_covered_at is not None and self.baseline is None:
            return self.last_covered_at + self.window

        return None

    @property
    def overdue_by(self) -> timedelta | None:
        if self.overdue_at is None:
            return None
        return datetime.now() - self.overdue_at

    @property
    def status(self) -> CoverageStatus:
        if self.overdue_at is None:
            return CoverageStatus.COMPLIANT
        if self.as_of > self.overdue_at:
            return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        return (
            self.covered_now,
            self.last_covered_at,
            self.status,
            self.current_steward_ids,
        )


@dataclass(frozen=True)
class StationCoverage:
    station_id: str
    areas: tuple[AreaCoverage, ...]

    def areas_of(self, kind: AreaKind) -> tuple[AreaCoverage, ...]:
        return tuple(area for area in self.areas if area.area.kind == kind)

    @property
    def status(self) -> CoverageStatus:
        coverage_status = CoverageStatus.COMPLIANT
        for _area in self.areas:
            if _area.status == CoverageStatus.OVERDUE:
                coverage_status = CoverageStatus.OVERDUE
                break
        return coverage_status

    def state(self) -> tuple:
        sorted_areas = sorted(self.areas, key=lambda a: a.area.area_id)
        return tuple(area.state() for area in sorted_areas)


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
    def entry_id(self) -> str:
        """A stable id for this entry, the same every time it is computed.

        uuid5 of (station_id, area_id, overdue_at, "DETECTED") with one fixed
        namespace. The tracker compares it with the ids already in the log, so
        a repeated refresh or a restart never logs the same episode twice. Two
        different episodes have different overdue_at values, so different ids.
        """
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:DETECTED"


# Log entry: an overdue episode for an area was cleared. Append-only.
# Storage schema is open (ADR-0008).
@dataclass(frozen=True)
class OverdueCleared:
    area: AreaRef
    overdue_at: datetime
    cleared_at: datetime
    source: str

    @property
    def entry_id(self) -> str:
        """A stable id for this entry, the same every time it is computed.

        uuid5 of (station_id, area_id, overdue_at, "CLEARED") with the same
        namespace as OverdueDetected. Shares overdue_at with the matching
        DETECTED entry, so the pair can be found, but never the same id.
        """
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:CLEARED"

    def overdue_for(self) -> timedelta:
        """How long the area was overdue in total

        cleared_at - overdue_at. Computed from the two stored timestamps
        instead of being stored, so it can never disagree with them.
        """
        return self.cleared_at - self.overdue_at
