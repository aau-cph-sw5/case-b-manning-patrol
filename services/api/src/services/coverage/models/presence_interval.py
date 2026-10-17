# One steward's presence at one beacon: a CONNECT and the DISCONNECT or STOP that
# closed it. ended_at is None while the visit is still open.
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.services.coverage.models.covered_time_span import CoveredTimeSpan


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
        return self.ended_at is None

    def duration(self, now: datetime) -> timedelta:
        """How long the steward has been, or was, at the beacon.

        ended_at - started_at for a closed visit. An open visit has no end yet,
        so it is measured up to now. now is passed in instead of read from the
        clock, so the result is repeatable (AC5).
        """
        if self.ended_at is not None:
            return self.ended_at - self.started_at
        return now - self.started_at

    def qualifies(self, min_duration: timedelta, now: datetime) -> bool:
        """Tell whether the visit is long enough to count as a patrol.

        True when duration(now) is at least min_duration, the threshold for the
        area's kind (platform 4 s, concourse 10 min). A shorter visit, such as
        walking through, never counts. An open visit can cross the threshold
        while it is still going on, which is one reason for the clock tick.
        """
        if self.duration(now) >= min_duration:
            return True
        return False

    def qualified_at(self, min_duration: timedelta) -> datetime:
        """The moment the visit started to count as a patrol.

        started_at + min_duration. Coverage begins here, not at started_at,
        because before this moment the visit was not long enough yet. It is
        also the moment an overdue episode ends when this visit clears it.
        """

        return self.started_at + min_duration
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
        return CoveredTimeSpan(
            start=self.qualified_at(min_duration),
            end=(self.ended_at or now) + window,
        )
