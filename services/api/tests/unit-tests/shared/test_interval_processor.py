from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.domain.coverage import StewardPatrolInterval
from src.services.shared.interval_processor import IntervalProcessor

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON_A = UUID("550e8400-e29b-41d4-a716-000000000002")
BEACON_B = UUID("550e8400-e29b-41d4-a716-000000000004")

T0 = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SHIFT_START = T0
NOW = T0 + timedelta(hours=8)


def at(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


def make_interval(
    started_at: datetime,
    ended_at: datetime | None,
    beacon_id: UUID = BEACON_A,
) -> StewardPatrolInterval:
    return StewardPatrolInterval(
        android_id=STEWARD,
        beacon_id=beacon_id,
        started_at=started_at,
        ended_at=ended_at,
    )


def test_within_shift_drops_intervals_starting_after_now():
    intervals = [make_interval(at(9), None)]

    assert IntervalProcessor.within_shift(intervals, SHIFT_START, NOW) == []


def test_within_shift_drops_intervals_ended_before_the_shift_start():
    intervals = [make_interval(at(-2), at(-1))]

    assert IntervalProcessor.within_shift(intervals, SHIFT_START, NOW) == []


def test_within_shift_clips_the_start_up_to_the_shift_start():
    intervals = [make_interval(at(-1), at(2))]

    assert IntervalProcessor.within_shift(intervals, SHIFT_START, NOW) == [
        make_interval(SHIFT_START, at(2))
    ]


def test_within_shift_treats_an_end_after_now_as_still_open():
    intervals = [make_interval(at(1), at(12))]

    assert IntervalProcessor.within_shift(intervals, SHIFT_START, NOW) == [
        make_interval(at(1), None)
    ]


def test_group_by_beacon_groups_intervals_per_beacon():
    intervals = [
        make_interval(at(1), at(2), BEACON_A),
        make_interval(at(3), None, BEACON_B),
        make_interval(at(4), at(5), BEACON_A),
    ]

    grouped = IntervalProcessor.group_by_beacon(intervals)

    assert grouped == {
        BEACON_A: [intervals[0], intervals[2]],
        BEACON_B: [intervals[1]],
    }
