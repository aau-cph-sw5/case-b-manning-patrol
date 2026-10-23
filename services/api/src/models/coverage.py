"""
Value objects for patrol coverage and the overdue log (MET-B-007)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from src.models.patrol_area import AreaKind, PatrolArea


class CoverageStatus(StrEnum):
    COMPLIANT = "compliant"
    OVERDUE = "overdue"


@dataclass(frozen=True)
class AreaReference:
    station_id: str | None
    area_id: str
    kind: AreaKind

    @staticmethod
    def from_patrol_area(area: PatrolArea) -> AreaReference:
        return AreaReference(area.station_id, area.area_id, area.area_kind)


@dataclass(frozen=True)
class TimeSpan:
    start: datetime
    end: datetime

    def touches(self, other: TimeSpan) -> bool:
        if self.end < other.start:
            return False
        if other.end < self.start:
            return False
        return True

    def merge(self, other: TimeSpan) -> TimeSpan:
        if not self.touches(other):
            raise ValueError("Cannot merge non-touching spans")
        return TimeSpan(
            start=min(self.start, other.start), end=max(self.end, other.end)
        )


@dataclass(frozen=True)
class StewardPatrolInterval:
    android_id: UUID
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None

    def is_patrolling(self) -> bool:
        return self.ended_at is None

    def patrol_duration(self, now: datetime) -> timedelta:
        if self.ended_at is not None:
            return self.ended_at - self.started_at
        return now - self.started_at

    def qualifies_as_patrolled(
        self, min_qualifying_duration: timedelta, now: datetime
    ) -> bool:
        return self.patrol_duration(now) >= min_qualifying_duration

    def qualified_as_patrolled_at(self, min_qualifying_duration: timedelta) -> datetime:
        return self.started_at + min_qualifying_duration

    def patrol_span(
        self,
        min_qualifying_duration: timedelta,
        time_until_next_needed_patrol: timedelta,
        now: datetime,
    ) -> TimeSpan | None:
        if not self.qualifies_as_patrolled(min_qualifying_duration, now):
            return None
        return TimeSpan(
            start=self.qualified_as_patrolled_at(min_qualifying_duration),
            end=(self.ended_at or now) + time_until_next_needed_patrol,
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
class AreaCoverageReport:
    area: AreaReference
    last_covered_at: datetime | None
    covered_now: bool
    shift_start_time: datetime | None
    current_steward_ids: frozenset[UUID]
    episodes: tuple[OverdueEpisode, ...]
    time_until_next_needed_patrol: timedelta
    as_of: datetime

    @property
    def overdue_at(self) -> datetime | None:
        if self.covered_now:
            return None
        elif self.last_covered_at is None and self.shift_start_time is not None:
            return self.shift_start_time + self.time_until_next_needed_patrol
        elif self.last_covered_at is not None and self.shift_start_time is not None:
            return (
                max(self.last_covered_at, self.shift_start_time)
                + self.time_until_next_needed_patrol
            )
        elif self.last_covered_at is not None and self.shift_start_time is None:
            return self.last_covered_at + self.time_until_next_needed_patrol
        else:
            return None

    @property
    def overdue_by(self) -> timedelta | None:
        if self.overdue_at is None:
            return None
        return self.as_of - self.overdue_at

    @property
    def coverage_status(self) -> CoverageStatus:
        if self.covered_now:
            return CoverageStatus.COMPLIANT
        if self.overdue_at is None or self.as_of > self.overdue_at:
            return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        return (
            self.covered_now,
            self.last_covered_at,
            self.coverage_status,
            self.current_steward_ids,
        )


@dataclass(frozen=True)
class StationCoverageReport:
    station_id: str
    areas: tuple[AreaCoverageReport, ...]

    def areas_of(self, kind: AreaKind) -> tuple[AreaCoverageReport, ...]:
        return tuple(area for area in self.areas if area.area.kind == kind)

    @property
    def coverage_status(self) -> CoverageStatus:
        for _area in self.areas:
            if _area.coverage_status == CoverageStatus.OVERDUE:
                return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        sorted_areas = sorted(self.areas, key=lambda a: a.area.area_id)
        return tuple(area.state() for area in sorted_areas)


@dataclass(frozen=True)
class OverdueDetected:
    area: AreaReference
    overdue_at: datetime
    detected_at: datetime
    last_covered_at: datetime | None
    source: str

    @property
    def stable_entry_id(self) -> str:
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:DETECTED"


@dataclass(frozen=True)
class OverdueCleared:
    area: AreaReference
    overdue_at: datetime
    cleared_at: datetime
    source: str

    @property
    def stable_entry_id(self) -> str:
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:CLEARED"

    def overdue_for(self) -> timedelta:
        return self.cleared_at - self.overdue_at
