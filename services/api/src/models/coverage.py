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
    station_id: str
    area_id: str
    kind: AreaKind

    @staticmethod
    def from_patrol_area(area: PatrolArea) -> AreaRef:
        """Turn a PatrolArea row into the key that coverage uses.

        CoverageService calls this once per patrol area when it loads the areas.
        It copies station_id, area_id and area_kind into a frozen, hashable
        value, so the coverage rule never depends on the database model.
        PatrolArea.station_id may be None but AreaRef.station_id may not: agree
        with the caller whether that raises or the area is skipped.
        """
        raise NotImplementedError


# A span of time during which an area counts as covered.
@dataclass(frozen=True)
class CoveredTimeSpan:
    start: datetime
    end: datetime

    def touches(self, other: CoveredTimeSpan) -> bool:
        """Tell whether this span and another can be merged into one.

        True when they overlap, or when one ends exactly where the other starts.
        Touching spans leave no uncovered moment between them, so the area was
        never overdue there. CoverageWindow._union checks this before merge.
        """
        raise NotImplementedError

    def merge(self, other: CoveredTimeSpan) -> CoveredTimeSpan:
        """Combine two touching spans into one.

        Returns a span from the earlier start to the later end. Only call it
        when touches(other) is True: for spans with a gap between them, the
        result would wrongly cover the gap.
        """
        raise NotImplementedError


# One steward's presence at one beacon: a CONNECT and the DISCONNECT or STOP that
# closed it. ended_at is None while the visit is still open.
@dataclass(frozen=True)
class PresenceInterval:
    actor: str
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None

    def is_open(self) -> bool:
        """Tell whether the steward is still at the beacon.

        True when no DISCONNECT or STOP has closed the visit yet, which means
        ended_at is None. Open visits count towards current_steward_ids and are
        measured up to now.
        """
        raise NotImplementedError

    def duration(self, now: datetime) -> timedelta:
        """How long the steward has been, or was, at the beacon.

        ended_at - started_at for a closed visit. An open visit has no end yet,
        so it is measured up to now. now is passed in instead of read from the
        clock, so the result is repeatable (AC5).
        """
        raise NotImplementedError

    def qualifies(self, min_duration: timedelta, now: datetime) -> bool:
        """Tell whether the visit is long enough to count as a patrol.

        True when duration(now) is at least min_duration, the threshold for the
        area's kind (platform 4 s, concourse 10 min). A shorter visit, such as
        walking through, never counts. An open visit can cross the threshold
        while it is still going on, which is one reason for the clock tick.
        """
        raise NotImplementedError

    def qualified_at(self, min_duration: timedelta) -> datetime:
        """The moment the visit started to count as a patrol.

        started_at + min_duration. Coverage begins here, not at started_at,
        because before this moment the visit was not long enough yet. It is
        also the moment an overdue episode ends when this visit clears it.
        """
        raise NotImplementedError

    def covered_span(
        self,
        min_duration: timedelta,
        window: timedelta,
        now: datetime,
    ) -> CoveredTimeSpan | None:
        """The span of time this visit keeps the area covered.

        None if the visit does not qualify. Otherwise the span runs from
        qualified_at(min_duration) until (ended_at or now) + window: the area
        stays compliant for one window after the steward leaves. For an open
        visit the end moves forward with now.
        """
        raise NotImplementedError


# A stretch of time an area went without qualifying coverage. cleared_at is None
# while it is still overdue.
@dataclass(frozen=True)
class OverdueEpisode:
    overdue_at: datetime
    cleared_at: datetime | None

    def is_open(self) -> bool:
        """Tell whether the area is still overdue.

        True when no qualifying visit has ended the episode yet, which means
        cleared_at is None.
        """
        raise NotImplementedError

    def duration(self, now: datetime) -> timedelta:
        """How long the area has been, or was, overdue.

        cleared_at - overdue_at for a cleared episode, now - overdue_at for an
        open one. now is a parameter, so the result is repeatable.
        """
        raise NotImplementedError


# Coverage of one patrol area at as_of. Stores only facts; overdue_at,
# overdue_by and status are derived so they cannot contradict each other.
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
        """The deadline at which the area becomes overdue.

        None while covered_now, because a steward is patrolling right now.
        Otherwise the later of last_covered_at and baseline, plus window. None
        when both are None: the area was never patrolled and there is no shift
        start to count from, so there is no deadline. Derived, not stored, so
        it cannot disagree with the facts it comes from.
        """
        raise NotImplementedError

    @property
    def overdue_by(self) -> timedelta | None:
        """How far past the deadline the area is at as_of.

        as_of - overdue_at, never below zero, so a compliant area gives zero.
        None when overdue_at is None, because without a deadline the duration
        is unknown. The dashboard keeps counting between updates by itself.
        """
        raise NotImplementedError

    @property
    def status(self) -> CoverageStatus:
        """Whether the area is COMPLIANT or OVERDUE at as_of.

        OVERDUE when nobody is patrolling it now and either there is no
        deadline (never patrolled and no baseline, AC2) or as_of is past the
        deadline. Exactly at the deadline still counts as COMPLIANT.
        """
        raise NotImplementedError

    def state(self) -> tuple:
        """The fields that decide whether this area must be published again.

        Returns (covered_now, last_covered_at, status, current_steward_ids).
        The updater compares it with the last published value and only pushes
        when it differs. as_of, overdue_by and episodes are left out on purpose:
        as_of changes on every tick, so including it would republish every area
        every few seconds.
        """
        raise NotImplementedError


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
        raise NotImplementedError

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
