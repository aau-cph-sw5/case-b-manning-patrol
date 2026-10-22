import datetime
from uuid import uuid4

import pytest

from src.models.coverage import StewardPatrolInterval


@pytest.fixture
def open_interval():
    now = datetime.datetime.now()
    started_at = now - datetime.timedelta(minutes=5)
    return StewardPatrolInterval(
        android_id=uuid4(), beacon_id=uuid4(), started_at=started_at, ended_at=None
    )


@pytest.fixture
def closed_interval():
    now = datetime.datetime.now()
    started_at = now - datetime.timedelta(minutes=5)
    ended_at = now - datetime.timedelta(minutes=1)
    return StewardPatrolInterval(
        android_id=uuid4(), beacon_id=uuid4(), started_at=started_at, ended_at=ended_at
    )


def test_is_open(open_interval, closed_interval):
    assert open_interval.is_patrolling() is True
    assert closed_interval.is_patrolling() is False


def test_duration(open_interval, closed_interval, now):
    assert open_interval.patrol_duration(now) == now - open_interval.started_at
    assert closed_interval.patrol_duration(now) == datetime.timedelta(minutes=4)


def test_qualifies_with_shorter_min_qualifying_duration(
    open_interval, closed_interval, now
):
    min_qualifying_duration = datetime.timedelta(minutes=3)
    assert open_interval.qualifies_as_patrolled(min_qualifying_duration, now) is True
    assert closed_interval.qualifies_as_patrolled(min_qualifying_duration, now) is True


def test_qualifies_with_equal_min_qualifying_duration(
    open_interval, closed_interval, now
):
    min_qualifying_duration = datetime.timedelta(minutes=5)
    assert open_interval.qualifies_as_patrolled(min_qualifying_duration, now) is True
    assert closed_interval.qualifies_as_patrolled(min_qualifying_duration, now) is False


def test_qualifies_with_longer_min_qualifying_duration(
    open_interval, closed_interval, now
):
    min_qualifying_duration = datetime.timedelta(minutes=6)
    assert open_interval.qualifies_as_patrolled(min_qualifying_duration, now) is False
    assert closed_interval.qualifies_as_patrolled(min_qualifying_duration, now) is False


def test_qualified_at(open_interval):
    min_qualifying_duration = datetime.timedelta(minutes=4)
    qualified_at = open_interval.started_at + min_qualifying_duration
    assert (
        open_interval.qualified_as_patrolled_at(min_qualifying_duration) == qualified_at
    )


def test_covered_span_open(open_interval, closed_interval, now):
    min_qualifying_duration = datetime.timedelta(minutes=4)
    window = datetime.timedelta(minutes=1)

    covered_span_open = open_interval.patrol_span(min_qualifying_duration, window, now)
    assert covered_span_open is not None
    assert covered_span_open.start == open_interval.qualified_as_patrolled_at(
        min_qualifying_duration,
    )
    assert covered_span_open.end == now + window


def test_covered_span_closed(open_interval, closed_interval, now):
    min_qualifying_duration = datetime.timedelta(minutes=4)
    window = datetime.timedelta(minutes=1)
    covered_span_closed = closed_interval.patrol_span(
        min_qualifying_duration, window, now
    )
    assert covered_span_closed is not None
    assert covered_span_closed.start == closed_interval.qualified_as_patrolled_at(
        min_qualifying_duration,
    )
    assert covered_span_closed.end == closed_interval.ended_at + window


def test_covered_span_non_qualifying(open_interval, closed_interval, now):
    window = datetime.timedelta(minutes=1)
    min_qualifying_duration_long = datetime.timedelta(minutes=6)
    covered_span_non_qualifying = open_interval.patrol_span(
        min_qualifying_duration_long, window, now
    )
    assert covered_span_non_qualifying is None
