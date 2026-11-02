"""Value objects for patrol coverage and the overdue log (MET-B-007)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from src.domain.patrol_area import AreaKind


class CoverageStatus(StrEnum):
    """Whether an area or station is within its patrol deadline."""

    COMPLIANT = "compliant"
    OVERDUE = "overdue"


@dataclass(frozen=True)
class AreaReference:
    """Identify a patrol area; ``station_id`` is None for unassigned areas."""

    station_id: str | None
    area_id: str
    kind: AreaKind


@dataclass(frozen=True)
class TimeSpan:
    """A closed time range ``[start, end]`` during which an area is covered."""

    start: datetime
    end: datetime

    def touches(self, other: TimeSpan) -> bool:
        """Return True if the spans overlap or share an endpoint."""
        if self.end < other.start:
            return False
        if other.end < self.start:
            return False
        return True

    def merge(self, other: TimeSpan) -> TimeSpan:
        """Return the smallest span covering both, or raise ValueError if apart."""
        if not self.touches(other):
            raise ValueError("Cannot merge non-touching spans")
        return TimeSpan(
            start=min(self.start, other.start), end=max(self.end, other.end)
        )


@dataclass(frozen=True)
class StewardPatrolInterval:
    """One visit by a steward's device to a beacon.

    ``ended_at`` is None while the steward is still at the beacon.
    """

    android_id: UUID
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None

    def is_patrolling(self) -> bool:
        """Return True if the visit has not ended yet."""
        return self.ended_at is None

    def patrol_duration(self, now: datetime) -> timedelta:
        """Return how long the visit lasted, or has lasted so far at ``now``."""
        if self.ended_at is not None:
            return self.ended_at - self.started_at
        return now - self.started_at

    def qualifies_as_patrolled(
        self, min_qualifying_duration: timedelta, now: datetime
    ) -> bool:
        """Return True if the visit lasted at least ``min_qualifying_duration``."""
        return self.patrol_duration(now) >= min_qualifying_duration

    def qualified_as_patrolled_at(self, min_qualifying_duration: timedelta) -> datetime:
        """Return when the visit reaches the minimum qualifying duration."""
        return self.started_at + min_qualifying_duration

    def patrol_span(
        self,
        min_qualifying_duration: timedelta,
        time_until_next_needed_patrol: timedelta,
        now: datetime,
    ) -> TimeSpan | None:
        """Return the span this visit keeps the area covered, or None.

        The span starts when the visit qualified and ends
        ``time_until_next_needed_patrol`` after the visit ended, or after
        ``now`` if it is still ongoing. Visits that do not qualify cover
        nothing.
        """
        if not self.qualifies_as_patrolled(min_qualifying_duration, now):
            return None
        return TimeSpan(
            start=self.qualified_as_patrolled_at(min_qualifying_duration),
            end=(self.ended_at or now) + time_until_next_needed_patrol,
        )


@dataclass(frozen=True)
class OverdueEpisode:
    """A period an area went unpatrolled; ``cleared_at`` is None while ongoing."""

    overdue_at: datetime
    cleared_at: datetime | None

    def is_open(self) -> bool:
        """Return True if the area is still overdue."""
        return self.cleared_at is None

    def duration(self, now: datetime) -> timedelta:
        """Return how long the area was overdue, or has been so far at ``now``."""
        if self.cleared_at is not None:
            return self.cleared_at - self.overdue_at
        return now - self.overdue_at


@dataclass(frozen=True)
class AreaCoverageReport:
    """Patrol coverage of one area as of ``as_of``."""

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
        """Return when the area becomes (or became) overdue.

        None while the area is covered, or when it has never been covered and
        there is no shift start to count from.
        """
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
        """Return how far ``as_of`` is past ``overdue_at``; negative if before it."""
        if self.overdue_at is None:
            return None
        return self.as_of - self.overdue_at

    @property
    def coverage_status(self) -> CoverageStatus:
        """Return OVERDUE once ``as_of`` is past ``overdue_at``.

        An area that is not covered and has no ``overdue_at`` is OVERDUE.
        """
        if self.covered_now:
            return CoverageStatus.COMPLIANT
        if self.overdue_at is None or self.as_of > self.overdue_at:
            return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        """Return the fields that make up the area's visible state."""
        return (
            self.covered_now,
            self.last_covered_at,
            self.coverage_status,
            self.current_steward_ids,
        )


@dataclass(frozen=True)
class StationCoverageReport:
    """Coverage of all patrol areas at one station."""

    station_id: str
    areas: tuple[AreaCoverageReport, ...]

    def areas_of(self, kind: AreaKind) -> tuple[AreaCoverageReport, ...]:
        """Return the station's areas of the given kind."""
        return tuple(area for area in self.areas if area.area.kind == kind)

    @property
    def coverage_status(self) -> CoverageStatus:
        """Return OVERDUE if any area at the station is overdue."""
        for _area in self.areas:
            if _area.coverage_status == CoverageStatus.OVERDUE:
                return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        """Return the visible state of every area, in area ID order."""
        sorted_areas = sorted(self.areas, key=lambda a: a.area.area_id)
        return tuple(area.state() for area in sorted_areas)


@dataclass(frozen=True)
class OverdueDetected:
    """Overdue log entry recording that an area became overdue."""

    area: AreaReference
    overdue_at: datetime
    detected_at: datetime
    last_covered_at: datetime | None
    source: str

    @property
    def stable_entry_id(self) -> str:
        """Return an ID that is the same each time this episode is detected."""
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:DETECTED"


@dataclass(frozen=True)
class OverdueCleared:
    """Overdue log entry recording that an overdue area was patrolled again."""

    area: AreaReference
    overdue_at: datetime
    cleared_at: datetime
    source: str

    @property
    def stable_entry_id(self) -> str:
        """Return an ID that is the same each time this clearance is seen."""
        datestring = self.overdue_at.isoformat()
        return f"{self.area.station_id}:{self.area.area_id}:{datestring}:CLEARED"

    def overdue_for(self) -> timedelta:
        """Return how long the area was overdue."""
        return self.cleared_at - self.overdue_at
