from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.api.v2.schemas.adjustment import AdjustmentEventStored
from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.domain.event import EventRecord, EventType
from src.services.hash_chain.entry_stringifier import (
    ADJUSTMENT_FIELDS,
    EVENT_FIELDS,
    FORMAT_VERSION,
    EntryStringifier,
)
from src.services.shared.event_record_mapper import EventRecordMapper

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
ADJUSTMENT_ID = UUID("20000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
CORRECTED_AT = datetime(2026, 5, 30, 3, 10, tzinfo=UTC)
COPENHAGEN_SUMMER = timezone(timedelta(hours=2))

GOLDEN_EVENT = (
    '{"android_id":"660e8400-e29b-41d4-a716-446655440001",'
    '"beacon_id":"550e8400-e29b-41d4-a716-000000000002",'
    '"device_timestamp":"2026-05-30T03:00:00+00:00",'
    '"event_id":"10000000-0000-0000-0000-000000000001",'
    '"event_type":"connect",'
    '"kind":"event",'
    '"server_timestamp":"2026-05-30T03:00:05+00:00",'
    '"source":"test","v":1}'
)

GOLDEN_ADJUSTMENT = (
    '{"adjustment_id":"20000000-0000-0000-0000-000000000001",'
    '"android_id":"660e8400-e29b-41d4-a716-446655440001",'
    '"author":"supervisor",'
    '"corrected_beacon_id":null,'
    '"corrected_fact_type":"shift_stop",'
    '"corrected_occured_at":"2026-05-30T03:10:00+00:00",'
    '"kind":"adjustment",'
    '"reason":"missed stop",'
    '"server_timestamp":"2026-05-30T03:00:05+00:00",'
    '"source":"test",'
    '"target_event_id":"10000000-0000-0000-0000-000000000001","v":1}'
)


def make_event(
    event_type: EventType = EventType.CONNECT_EVENT,
    beacon_id: UUID | None = BEACON,
    device_timestamp: datetime = DEVICE_AT,
) -> Event:
    return Event(
        event_id=EVENT_ID,
        event_type=event_type,
        android_id=STEWARD,
        beacon_id=beacon_id,
        device_timestamp=device_timestamp,
        server_timestamp=SERVER_AT,
        source="test",
    )


def make_adjustment() -> Adjustment:
    return Adjustment(
        adjustment_id=ADJUSTMENT_ID,
        target_event_id=EVENT_ID,
        android_id=STEWARD,
        reason="missed stop",
        author="supervisor",
        server_timestamp=SERVER_AT,
        source="test",
        corrected_fact_type=EventType.STOP_EVENT,
        corrected_beacon_id=None,
        corrected_occured_at=CORRECTED_AT,
    )


def test_event_fields_cover_every_event_column():
    assert set(EVENT_FIELDS) == set(Event.model_fields)


def test_adjustment_fields_cover_every_adjustment_column():
    assert set(ADJUSTMENT_FIELDS) == set(Adjustment.model_fields)


def test_event_matches_the_golden_string():
    assert EntryStringifier.stringify_entry(make_event()) == GOLDEN_EVENT


def test_adjustment_matches_the_golden_string():
    assert EntryStringifier.stringify_entry(make_adjustment()) == GOLDEN_ADJUSTMENT


def test_same_entry_gives_the_same_string():
    assert EntryStringifier.stringify_entry(
        make_event()
    ) == EntryStringifier.stringify_entry(make_event())


def test_same_instant_in_another_time_zone_gives_the_same_string():
    local = make_event(device_timestamp=DEVICE_AT.astimezone(COPENHAGEN_SUMMER))

    assert EntryStringifier.stringify_entry(local) == EntryStringifier.stringify_entry(
        make_event()
    )


def test_none_beacon_id_is_written_as_null():
    session_start = make_event(event_type=EventType.START_EVENT, beacon_id=None)

    assert '"beacon_id":null' in EntryStringifier.stringify_entry(session_start)


def test_event_and_adjustment_are_tagged_with_their_kind():
    assert '"kind":"event"' in EntryStringifier.stringify_entry(make_event())
    assert '"kind":"adjustment"' in EntryStringifier.stringify_entry(make_adjustment())


def test_payload_is_tagged_with_the_format_version():
    assert f'"v":{FORMAT_VERSION}' in EntryStringifier.stringify_entry(make_event())
    assert f'"v":{FORMAT_VERSION}' in EntryStringifier.stringify_entry(
        make_adjustment()
    )


def test_naive_timestamp_is_rejected():
    naive = make_event(device_timestamp=DEVICE_AT.replace(tzinfo=None))

    with pytest.raises(ValueError, match="time zone"):
        EntryStringifier.stringify_entry(naive)


def test_domain_event_record_is_rejected():
    record: EventRecord = EventRecordMapper.to_record(make_event())

    with pytest.raises(TypeError, match="EventRecord"):
        EntryStringifier.stringify_entry(record)  # ty: ignore[invalid-argument-type]


def test_api_adjustment_schema_is_rejected():
    stored = AdjustmentEventStored.from_adjustment(make_adjustment())

    with pytest.raises(TypeError, match="AdjustmentEventStored"):
        EntryStringifier.stringify_entry(stored)  # ty: ignore[invalid-argument-type]
