import logging
from datetime import datetime
from uuid import UUID

from src.models.coverage import StewardPatrolInterval
from src.models.event import Event, EventType

logger = logging.getLogger(__name__)


class IntervalBuilder:
    def build(self, events: list[Event]) -> list[StewardPatrolInterval]:
        """Turn the stored events into presence intervals, one per visit.

        1. Sort the events by device_timestamp (the phone's time), because
           events can arrive out of order.
        2. A CONNECT opens a visit for (actor, beacon). The next DISCONNECT for
           the same pair closes it.
        3. A STOP closes all of that actor's open visits at the STOP time,
           because the phone sends no DISCONNECT when a patrol session stops.
        4. Visits still open at the end keep ended_at = None. Their length is
           measured later against now.
        5. START has no effect here.

        Event.beacon is a string. It is converted to UUID once, and invalid
        values are skipped and logged. No database and no clock, so the same
        events always give the same intervals.
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

        return intervals

    @staticmethod
    def _close(
        key: tuple[UUID, UUID],
        started_at: datetime,
        ended_at: datetime,
    ) -> StewardPatrolInterval:
        android_id, beacon_id = key
        return StewardPatrolInterval(
            android_id=str(android_id),
            beacon_id=beacon_id,
            started_at=started_at,
            ended_at=ended_at,
        )

    @staticmethod
    def _in_time_order(events: list[Event]) -> list[Event]:
        return sorted(
            events,
            key=lambda event: (
                event.device_timestamp,
                event.server_timestamp,
                event.event_id,
            ),
        )
