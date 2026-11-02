import logging
from datetime import datetime
from uuid import UUID

from src.domain.coverage import StewardPatrolInterval
from src.domain.event import EventRecord, EventType

logger = logging.getLogger(__name__)


class IntervalBuilder:
    def build(self, events: list[EventRecord]) -> list[StewardPatrolInterval]:
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
