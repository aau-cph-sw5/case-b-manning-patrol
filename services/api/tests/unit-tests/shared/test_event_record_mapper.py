from datetime import UTC, datetime
from uuid import UUID

from src.db.models.event import Event
from src.domain.event import EventRecord, EventType
from src.services.shared.event_record_mapper import EventRecordMapper

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)


def make_event() -> Event:
    return Event(
        event_id=EVENT_ID,
        event_type=EventType.CONNECT_EVENT,
        android_id=STEWARD,
        beacon_id=BEACON,
        device_timestamp=DEVICE_AT,
        server_timestamp=SERVER_AT,
        source="test",
    )


def test_to_record_copies_the_event_fields():
    record = EventRecordMapper.to_record(make_event())

    assert record == EventRecord(
        event_id=EVENT_ID,
        event_type=EventType.CONNECT_EVENT,
        android_id=STEWARD,
        beacon_id=BEACON,
        device_timestamp=DEVICE_AT,
        server_timestamp=SERVER_AT,
    )


def test_to_record_keeps_a_none_beacon_id():
    event = make_event()
    event.beacon_id = None

    assert EventRecordMapper.to_record(event).beacon_id is None
