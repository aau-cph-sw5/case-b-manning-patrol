"""Post-processing operations on built steward patrol intervals."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from src.domain.coverage import StewardPatrolInterval


class IntervalProcessor:
    """Shared operations on intervals after ``IntervalBuilder`` built them.

    Used by both the coverage and the train manning services, which compute
    from the same event log.
    """

    @staticmethod
    def within_shift(
        intervals: list[StewardPatrolInterval],
        shift_start_time: datetime,
        now: datetime,
    ) -> list[StewardPatrolInterval]:
        """Clip ``intervals`` to the window ``[shift_start_time, now]``.

        Intervals starting after ``now`` or ending at or before the shift
        start are dropped, start times are moved up to the shift start, and
        intervals ending after ``now`` are treated as still open.
        """
        within: list[StewardPatrolInterval] = []
        for interval in intervals:
            if interval.started_at > now:
                continue
            if interval.ended_at is not None and interval.ended_at <= shift_start_time:
                continue
            ended_at = interval.ended_at
            if ended_at is not None and ended_at > now:
                ended_at = None
            within.append(
                replace(
                    interval,
                    started_at=max(interval.started_at, shift_start_time),
                    ended_at=ended_at,
                ),
            )
        return within

    @staticmethod
    def group_by_beacon(
        intervals: list[StewardPatrolInterval],
    ) -> dict[UUID, list[StewardPatrolInterval]]:
        """Group ``intervals`` by the beacon they were recorded at."""
        intervals_by_beacon: dict[UUID, list[StewardPatrolInterval]] = {}
        for interval in intervals:
            intervals_by_beacon.setdefault(interval.beacon_id, []).append(interval)
        return intervals_by_beacon
