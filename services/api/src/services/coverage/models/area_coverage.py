# Coverage of one patrol area at as_of. Stores only facts; overdue_at,
# overdue_by and status are derived so they cannot contradict each other.
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.services.coverage.coverage import CoverageStatus
from src.services.coverage.models.area_ref import AreaRef
from src.services.coverage.models.overdue_episode import OverdueEpisode


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

        if self.covered_now:
            return None

        if self.last_covered_at is None and self.baseline is None:
            return None  # shift hasn't started yet

        if self.last_covered_at is None and self.baseline is not None:
            return self.baseline + self.window

        if self.last_covered_at is not None and self.baseline is None:
            return self.last_covered_at + self.window

        return None

    @property
    def overdue_by(self) -> timedelta | None:
        """How far past the deadline the area is at as_of.
        as_of - overdue_at, never below zero, so a compliant area gives zero.
        None when overdue_at is None, because without a deadline the duration
        is unknown. The dashboard keeps counting between updates by itself.
        """
        if self.overdue_at is None:
            return None
        return datetime.now() - self.overdue_at

    @property
    def status(self) -> CoverageStatus:
        """Whether the area is COMPLIANT or OVERDUE at as_of.

        OVERDUE when nobody is patrolling it now and either there is no
        deadline (never patrolled and no baseline, AC2) or as_of is past the
        deadline. Exactly at the deadline still counts as COMPLIANT.
        """
        if self.overdue_at is None:
            return CoverageStatus.COMPLIANT
        if self.as_of > self.overdue_at:
            return CoverageStatus.OVERDUE
        return CoverageStatus.COMPLIANT

    def state(self) -> tuple:
        """The fields that decide whether this area must be published again.

        Returns (covered_now, last_covered_at, status, current_steward_ids).
        The updater compares it with the last published value and only pushes
        when it differs. as_of, overdue_by and episodes are left out on purpose:
        as_of changes on every tick, so including it would republish every area
        every few seconds.
        """
        return (
            self.covered_now,
            self.last_covered_at,
            self.status,
            self.current_steward_ids,
        )
