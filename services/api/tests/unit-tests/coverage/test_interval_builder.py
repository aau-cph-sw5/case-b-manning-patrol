import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.domain.event import EventRecord, EventType
from src.services.station_coverage.interval_builder import IntervalBuilder

STEWARD_1 = UUID("660e8400-e29b-41d4-a716-446655440001")
STEWARD_2 = UUID("660e8400-e29b-41d4-a716-446655440002")
STATION_2 = UUID("550e8400-e29b-41d4-a716-000000000002")
STATION_4 = UUID("550e8400-e29b-41d4-a716-000000000004")
TRAIN_50 = UUID("550e8400-e29b-41d4-a716-000000000050")

T0 = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)


def at(seconds: int) -> datetime:
    return T0 + timedelta(seconds=seconds)


def make_event(
    event_type: EventType,
    seconds: int,
    android_id: UUID = STEWARD_1,
    beacon_id: UUID | None = STATION_2,
) -> EventRecord:
    return EventRecord(
        event_id=uuid4(),
        event_type=event_type,
        android_id=android_id,
        beacon_id=beacon_id,
        device_timestamp=at(seconds),
        server_timestamp=at(seconds),
    )


def connect(seconds: int, **kwargs) -> EventRecord:
    return make_event(EventType.CONNECT_EVENT, seconds, **kwargs)


def disconnect(seconds: int, **kwargs) -> EventRecord:
    return make_event(EventType.DISCONNECT_EVENT, seconds, **kwargs)


def start(seconds: int, android_id: UUID = STEWARD_1) -> EventRecord:
    return make_event(EventType.START_EVENT, seconds, android_id, beacon_id=None)


def stop(seconds: int, android_id: UUID = STEWARD_1) -> EventRecord:
    return make_event(EventType.STOP_EVENT, seconds, android_id, beacon_id=None)


def spans(intervals) -> set[tuple[UUID, UUID, datetime, datetime | None]]:
    return {(i.android_id, i.beacon_id, i.started_at, i.ended_at) for i in intervals}


@pytest.fixture
def builder() -> IntervalBuilder:
    return IntervalBuilder()


def test_no_events_gives_no_intervals(builder):
    assert builder.build([]) == []


def test_connect_then_disconnect_gives_one_closed_interval(builder):
    intervals = builder.build([connect(0), disconnect(30)])

    assert spans(intervals) == {(STEWARD_1, STATION_2, at(0), at(30))}


def test_events_are_sorted_by_device_timestamp(builder):
    intervals = builder.build([disconnect(30), connect(0)])

    assert spans(intervals) == {(STEWARD_1, STATION_2, at(0), at(30))}


def test_blip_gives_two_separate_intervals(builder):
    intervals = builder.build(
        [
            connect(0, beacon_id=STATION_4),
            disconnect(60, beacon_id=STATION_4),
            connect(67, beacon_id=STATION_4),
            disconnect(600, beacon_id=STATION_4),
        ],
    )

    assert spans(intervals) == {
        (STEWARD_1, STATION_4, at(0), at(60)),
        (STEWARD_1, STATION_4, at(67), at(600)),
    }


def test_connect_without_disconnect_stays_open(builder):
    intervals = builder.build(
        [connect(0, beacon_id=STATION_4), connect(10, beacon_id=STATION_2)],
    )

    assert spans(intervals) == {
        (STEWARD_1, STATION_4, at(0), None),
        (STEWARD_1, STATION_2, at(10), None),
    }
    assert all(interval.is_patrolling() for interval in intervals)


def test_overlapping_beacons_for_one_steward(builder):
    intervals = builder.build(
        [
            connect(0, beacon_id=TRAIN_50),
            connect(10, beacon_id=STATION_2),
            disconnect(20, beacon_id=STATION_2),
            disconnect(30, beacon_id=TRAIN_50),
        ],
    )

    assert spans(intervals) == {
        (STEWARD_1, TRAIN_50, at(0), at(30)),
        (STEWARD_1, STATION_2, at(10), at(20)),
    }


def test_stop_closes_all_open_visits_of_that_steward(builder):
    intervals = builder.build(
        [
            start(0),
            connect(10, beacon_id=STATION_2),
            connect(20, beacon_id=TRAIN_50),
            stop(100),
        ],
    )

    assert spans(intervals) == {
        (STEWARD_1, STATION_2, at(10), at(100)),
        (STEWARD_1, TRAIN_50, at(20), at(100)),
    }


def test_stop_leaves_other_stewards_open(builder):
    intervals = builder.build(
        [
            connect(0, android_id=STEWARD_1),
            connect(5, android_id=STEWARD_2),
            stop(100, android_id=STEWARD_1),
        ],
    )

    assert spans(intervals) == {
        (STEWARD_1, STATION_2, at(0), at(100)),
        (STEWARD_2, STATION_2, at(5), None),
    }


def test_disconnect_after_stop_is_ignored(builder):
    intervals = builder.build([connect(0), stop(100), disconnect(120)])

    assert spans(intervals) == {(STEWARD_1, STATION_2, at(0), at(100))}


def test_start_alone_gives_no_intervals(builder):
    assert builder.build([start(0)]) == []


def test_two_stewards_at_the_same_beacon_at_once(builder):
    intervals = builder.build(
        [
            connect(0, android_id=STEWARD_1),
            connect(10, android_id=STEWARD_2),
            disconnect(20, android_id=STEWARD_1),
            disconnect(40, android_id=STEWARD_2),
        ],
    )

    assert spans(intervals) == {
        (STEWARD_1, STATION_2, at(0), at(20)),
        (STEWARD_2, STATION_2, at(10), at(40)),
    }


def test_disconnect_without_connect_is_ignored(builder):
    assert builder.build([disconnect(30)]) == []


def test_second_connect_keeps_the_first_start(builder):
    intervals = builder.build([connect(0), connect(10), disconnect(30)])

    assert spans(intervals) == {(STEWARD_1, STATION_2, at(0), at(30))}


def test_connect_without_beacon_is_skipped_and_logged(builder, caplog):
    with caplog.at_level(logging.WARNING):
        intervals = builder.build([connect(0, beacon_id=None), disconnect(30)])

    assert intervals == []
    assert "no beacon_id" in caplog.text


def test_same_events_give_same_intervals(builder):
    events = [connect(0), connect(5, beacon_id=TRAIN_50), disconnect(30), stop(60)]

    assert builder.build(events) == builder.build(list(reversed(events)))
