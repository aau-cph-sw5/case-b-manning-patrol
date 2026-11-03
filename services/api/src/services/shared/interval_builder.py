"""Turn the raw steward event log into beacon visit intervals."""

import logging
from datetime import datetime
from uuid import UUID

from src.domain.coverage import StewardPatrolInterval
from src.domain.event import EventRecord, EventType

logger = logging.getLogger(__name__)


class IntervalBuilder:
    """Pair connect and disconnect events into steward patrol intervals."""

    def build(self, events: list[EventRecord]) -> list[StewardPatrolInterval]:
        """Replay the events in time order and return one interval per visit.

        Events are sorted by device timestamp, then server timestamp, then
        event ID. A visit is keyed by (android_id, beacon_id):

        - CONNECT opens a visit. A repeated CONNECT for an already open visit
          is ignored, so the earliest connect time is kept.
        - DISCONNECT closes the matching open visit. A DISCONNECT with no open
          visit is ignored.
        - STOP closes every open visit of that steward at the STOP time,
          regardless of beacon.
        - START is ignored; it carries no visit information.
        - CONNECT and DISCONNECT events without a beacon_id are skipped with a
          warning.

        Visits still open after the last event are returned with
        ``ended_at=None``, meaning the steward is still at the beacon.
        Closed intervals are returned in the order they were closed, followed
        by the open ones.
        """
        events = self._in_time_order(events)
        open_visits: dict[tuple[UUID, UUID], datetime] = {}
        intervals: list[StewardPatrolInterval] = []

        for event in events:
            if event.event_type == EventType.START_EVENT:
                continue

            if event.event_type == EventType.STOP_EVENT:
                stopped = [key for key in open_visits if key[0] == event.android_id]
                for key in stopped:
                    intervals.append(
                        self._close(key, open_visits.pop(key), event.device_timestamp),
                    )
                continue

            if event.beacon_id is None:
                logger.warning(
                    "Skipping %s event %s: no beacon_id",
                    event.event_type,
                    event.event_id,
                )
                continue
            key = (event.android_id, event.beacon_id)

            if event.event_type == EventType.CONNECT_EVENT:
                open_visits.setdefault(key, event.device_timestamp)

            elif event.event_type == EventType.DISCONNECT_EVENT:
                started_at = open_visits.pop(key, None)
                if started_at is not None:
                    intervals.append(
                        self._close(key, started_at, event.device_timestamp),
                    )

        for key, started_at in open_visits.items():
            intervals.append(self._close(key, started_at, None))

        return intervals

    @staticmethod
    def _close(
        key: tuple[UUID, UUID],
        started_at: datetime,
        ended_at: datetime | None,
    ) -> StewardPatrolInterval:
        android_id, beacon_id = key
        return StewardPatrolInterval(
            android_id=android_id,
            beacon_id=beacon_id,
            started_at=started_at,
            ended_at=ended_at,
        )

    @staticmethod
    def _in_time_order(events: list[EventRecord]) -> list[EventRecord]:
        return sorted(
            events,
            key=lambda event: (
                event.device_timestamp,
                event.server_timestamp,
                event.event_id,
            ),
        )
