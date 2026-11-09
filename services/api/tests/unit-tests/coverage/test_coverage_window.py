from datetime import datetime, timedelta
from uuid import UUID

import pytest

from src.domain.coverage import AreaReference, OverdueEpisode, StewardPatrolInterval
from src.domain.patrol_area import AreaKind
from src.services.station_coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)

BASE = datetime(2026, 3, 2, 12, 0, 0)
WINDOW = TIME_UNTIL_NEXT_NEEDED_PATROL
PLATFORM_THRESHOLD = MIN_QUALIFYING_DURATIONS[AreaKind.PLATFORM]
CONCOURSE_THRESHOLD = MIN_QUALIFYING_DURATIONS[AreaKind.CONCOURSE]
ONE_SECOND = timedelta(seconds=1)
PLATFORM_AREA = AreaReference(
    station_id="STN-001", area_id="platform-1", kind=AreaKind.PLATFORM
)
CONCOURSE_AREA = AreaReference(
    station_id="STN-001", area_id="concourse-1", kind=AreaKind.CONCOURSE
)
BEACON_ID = UUID("00000000-0000-0000-0000-000000000001")
STEWARD_A = UUID("00000000-0000-0000-0000-0000000000a1")
STEWARD_B = UUID("00000000-0000-0000-0000-0000000000b1")


def clock(hour, minute=0, second=0):
    return BASE.replace(hour=hour, minute=minute, second=second)


@pytest.fixture
def rule():
    return CoverageWindow(
        time_until_next_needed_patrol=WINDOW,
        min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
    )


def visit(started_at, ended_at, android_id=STEWARD_A):
    return StewardPatrolInterval(
        android_id=android_id,
        beacon_id=BEACON_ID,
        started_at=started_at,
        ended_at=ended_at,
    )


def test_min_qualifying_duration_returns_the_configured_threshold_per_kind(rule):
    assert rule.min_qualifying_duration(AreaKind.PLATFORM) == timedelta(seconds=10)
    assert rule.min_qualifying_duration(AreaKind.CONCOURSE) == timedelta(seconds=20)


def test_min_qualifying_duration_for_an_unconfigured_kind_is_a_configuration_error():
    rule = CoverageWindow(
        time_until_next_needed_patrol=WINDOW,
        min_qualifying_durations={AreaKind.PLATFORM: PLATFORM_THRESHOLD},
    )
    with pytest.raises(KeyError):
        rule.min_qualifying_duration(AreaKind.CONCOURSE)


def test_platform_visit_below_the_threshold_is_dropped(rule):
    started_at = clock(10, 0, 0)
    too_short = visit(
        started_at=started_at, ended_at=started_at + PLATFORM_THRESHOLD - ONE_SECOND
    )

    report = rule.evaluate(PLATFORM_AREA, [too_short], None, BASE)

    assert report.last_covered_at is None
    assert report.covered_now is False
    assert report.episodes == ()


def test_platform_visit_at_the_threshold_qualifies(rule):
    started_at = clock(10, 0, 0)
    ended_at = started_at + PLATFORM_THRESHOLD
    exactly_enough = visit(started_at=started_at, ended_at=ended_at)

    report = rule.evaluate(PLATFORM_AREA, [exactly_enough], None, ended_at + WINDOW)

    assert report.last_covered_at == ended_at
    assert report.overdue_at == ended_at + WINDOW
    assert report.coverage_status == "compliant"
    assert report.episodes == ()


def test_concourse_uses_its_own_threshold(rule):
    started_at = clock(10, 0, 0)
    platform_long = visit(
        started_at=started_at, ended_at=started_at + PLATFORM_THRESHOLD
    )
    concourse_long = visit(
        started_at=started_at, ended_at=started_at + CONCOURSE_THRESHOLD
    )

    below = rule.evaluate(CONCOURSE_AREA, [platform_long], None, BASE)
    at_threshold = rule.evaluate(CONCOURSE_AREA, [concourse_long], None, BASE)

    assert below.last_covered_at is None
    assert at_threshold.last_covered_at == started_at + CONCOURSE_THRESHOLD


def test_expired_coverage_is_overdue_with_an_open_episode(rule):
    earlier = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0))

    report = rule.evaluate(PLATFORM_AREA, [earlier], None, BASE)

    assert report.coverage_status == "overdue"
    assert report.overdue_at == clock(11, 10, 0)
    assert report.overdue_by == timedelta(minutes=50)
    assert report.episodes == (
        OverdueEpisode(overdue_at=clock(11, 10, 0), cleared_at=None),
    )


def test_a_gap_becomes_an_episode_cleared_by_the_next_visit(rule):
    first = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0))
    second = visit(started_at=clock(13, 0, 0), ended_at=clock(13, 10, 0))

    report = rule.evaluate(PLATFORM_AREA, [first, second], None, clock(14, 0, 0))

    assert report.episodes == (
        OverdueEpisode(
            overdue_at=clock(11, 10, 0),
            cleared_at=clock(13, 0, 0) + PLATFORM_THRESHOLD,
        ),
    )
    assert report.last_covered_at == clock(13, 10, 0)


def test_overlapping_visits_by_two_stewards_merge_into_one_span(rule):
    steward_a = visit(
        started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0), android_id=STEWARD_A
    )
    steward_b = visit(
        started_at=clock(10, 5, 0), ended_at=clock(10, 15, 0), android_id=STEWARD_B
    )

    report = rule.evaluate(PLATFORM_AREA, [steward_a, steward_b], None, clock(11, 0, 0))

    assert report.episodes == ()
    assert report.last_covered_at == clock(10, 15, 0)


def test_spans_that_just_meet_are_merged(rule):
    first = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0))
    # The second visit qualifies at 11:10:00, the moment the first span ends.
    second = visit(
        started_at=clock(11, 10, 0) - PLATFORM_THRESHOLD, ended_at=clock(11, 15, 0)
    )

    report = rule.evaluate(PLATFORM_AREA, [first, second], None, clock(11, 30, 0))

    assert report.episodes == ()
    assert report.last_covered_at == clock(11, 15, 0)


def test_open_qualified_visit_covers_now(rule):
    patrolling = visit(started_at=clock(11, 50, 0), ended_at=None, android_id=STEWARD_A)

    report = rule.evaluate(PLATFORM_AREA, [patrolling], None, BASE)

    assert report.covered_now is True
    assert report.overdue_at is None
    assert report.coverage_status == "compliant"
    assert report.current_steward_ids == frozenset({STEWARD_A})
    assert report.episodes == ()


def test_open_visits_count_as_present_even_when_unqualified(rule):
    patrolling = visit(started_at=clock(11, 50, 0), ended_at=None, android_id=STEWARD_A)
    just_arrived = visit(
        started_at=clock(11, 59, 58), ended_at=None, android_id=STEWARD_B
    )

    report = rule.evaluate(PLATFORM_AREA, [patrolling, just_arrived], None, BASE)

    assert report.covered_now is True
    assert report.current_steward_ids == frozenset({STEWARD_A, STEWARD_B})


def test_shift_start_time_extends_coverage_and_creates_its_own_deadline(rule):
    shift_start_time = clock(10, 30, 0)

    report = rule.evaluate(PLATFORM_AREA, [], shift_start_time, BASE)

    assert report.shift_start_time == shift_start_time
    assert report.overdue_at == clock(11, 30, 0)
    assert report.coverage_status == "overdue"
    assert report.episodes == (
        OverdueEpisode(overdue_at=clock(11, 30, 0), cleared_at=None),
    )


def test_no_shift_start_time_and_no_visits_gives_no_episodes(rule):
    report = rule.evaluate(PLATFORM_AREA, [], None, BASE)

    assert report.shift_start_time is None
    assert report.last_covered_at is None
    assert report.episodes == ()
    assert report.overdue_at is None


def test_evaluate_is_deterministic(rule):
    intervals = [
        visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0)),
        visit(started_at=clock(13, 0, 0), ended_at=clock(13, 10, 0)),
    ]

    first = rule.evaluate(PLATFORM_AREA, intervals, None, BASE)
    second = rule.evaluate(PLATFORM_AREA, intervals, None, BASE)

    assert first == second
    assert first.state() == second.state()
