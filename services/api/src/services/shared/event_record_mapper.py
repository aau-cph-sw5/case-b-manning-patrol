"""Map database events to the domain event records used by the services."""

from src.db.models.event import Event
from src.domain.event import EventRecord


class EventRecordMapper:
    """Convert ``Event`` rows into ``EventRecord`` objects.

    Shared by the coverage and train manning services, which both compute
    their reports from the same event log.
    """

    @staticmethod
    def to_record(event: Event) -> EventRecord:
        """Return ``event`` as an ``EventRecord``, dropping storage-only fields."""
        return EventRecord(
            event_id=event.event_id,
            event_type=event.event_type,
            android_id=event.android_id,
            beacon_id=event.beacon_id,
            device_timestamp=event.device_timestamp,
            server_timestamp=event.server_timestamp,
        )
