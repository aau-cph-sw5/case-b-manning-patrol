from datetime import datetime, timedelta
from uuid import UUID

import pytest

from src.models.coverage import AreaRefference, OverdueEpisode, StewardPatrolInterval
from src.models.patrol_area import AreaKind
from src.services.coverage.coverage_window import CoverageWindow

BASE = datetime(2026, 3, 2, 12, 0, 0)
WINDOW = timedelta(minutes=60)
PLATFORM_AREA = AreaRefference(
    station_id="STN-001", area_id="platform-1", kind=AreaKind.PLATFORM
)
CONCOURSE_AREA = AreaRefference(
    station_id="STN-001", area_id="concourse-1", kind=AreaKind.CONCOURSE
)
BEACON_ID = UUID("00000000-0000-0000-0000-000000000001")


def clock(hour, minute=0, second=0):
    return BASE.replace(hour=hour, minute=minute, second=second)


@pytest.fixture
def rule():
    return CoverageWindow(
        window=WINDOW,
        min_durations={
            AreaKind.PLATFORM: timedelta(seconds=4),
            AreaKind.CONCOURSE: timedelta(minutes=10),
        },
    )


def visit(started_at, ended_at, android_id="steward-1"):
    return StewardPatrolInterval(
        android_id=android_id,
        beacon_id=BEACON_ID,
        started_at=started_at,
        ended_at=ended_at,
    )


def test_min_duration_returns_the_configured_threshold_per_kind(rule):
    assert rule.min_duration(AreaKind.PLATFORM) == timedelta(seconds=4)
    assert rule.min_duration(AreaKind.CONCOURSE) == timedelta(minutes=10)


def test_min_duration_for_an_unconfigured_kind_is_a_configuration_error():
    rule = CoverageWindow(
        window=WINDOW,
        min_durations={AreaKind.PLATFORM: timedelta(seconds=4)},
    )
    with pytest.raises(KeyError):
        rule.min_duration(AreaKind.CONCOURSE)


def test_platform_visit_below_the_threshold_is_dropped(rule):
    too_short = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 0, 3))

    report = rule.evaluate(PLATFORM_AREA, [too_short], None, BASE)

    assert report.last_covered_at is None
    assert report.covered_now is False
    assert report.episodes == ()


def test_platform_visit_at_the_threshold_qualifies(rule):
    exactly_enough = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 0, 4))

    report = rule.evaluate(PLATFORM_AREA, [exactly_enough], None, clock(11, 0, 4))

    assert report.last_covered_at == clock(10, 0, 4)
    assert report.overdue_at == clock(11, 0, 4)
    assert report.coverage_status == "compliant"
    assert report.episodes == ()


def test_concourse_uses_its_own_threshold(rule):
    four_seconds = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 0, 4))
    ten_minutes = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0))

    below = rule.evaluate(CONCOURSE_AREA, [four_seconds], None, BASE)
    at_threshold = rule.evaluate(CONCOURSE_AREA, [ten_minutes], None, BASE)

    assert below.last_covered_at is None
    assert at_threshold.last_covered_at == clock(10, 10, 0)


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
        OverdueEpisode(overdue_at=clock(11, 10, 0), cleared_at=clock(13, 0, 4)),
    )
    assert report.last_covered_at == clock(13, 10, 0)


def test_overlapping_visits_by_two_stewards_merge_into_one_span(rule):
    steward_a = visit(
        started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0), android_id="steward-a"
    )
    steward_b = visit(
        started_at=clock(10, 5, 0), ended_at=clock(10, 15, 0), android_id="steward-b"
    )

    report = rule.evaluate(PLATFORM_AREA, [steward_a, steward_b], None, clock(11, 0, 0))

    assert report.episodes == ()
    assert report.last_covered_at == clock(10, 15, 0)


def test_spans_that_just_meet_are_merged(rule):
    first = visit(started_at=clock(10, 0, 0), ended_at=clock(10, 10, 0))
    second = visit(started_at=clock(11, 9, 56), ended_at=clock(11, 15, 0))

    report = rule.evaluate(PLATFORM_AREA, [first, second], None, clock(11, 30, 0))

    assert report.episodes == ()
    assert report.last_covered_at == clock(11, 15, 0)


def test_open_qualified_visit_covers_now(rule):
    patrolling = visit(
        started_at=clock(11, 50, 0), ended_at=None, android_id="steward-a"
    )

    report = rule.evaluate(PLATFORM_AREA, [patrolling], None, BASE)

    assert report.covered_now is True
    assert report.overdue_at is None
    assert report.coverage_status == "compliant"
    assert report.current_steward_ids == frozenset({"steward-a"})
    assert report.episodes == ()


def test_open_visits_count_as_present_even_when_unqualified(rule):
    patrolling = visit(
        started_at=clock(11, 50, 0), ended_at=None, android_id="steward-a"
    )
    just_arrived = visit(
        started_at=clock(11, 59, 58), ended_at=None, android_id="steward-b"
    )

    report = rule.evaluate(PLATFORM_AREA, [patrolling, just_arrived], None, BASE)

    assert report.covered_now is True
    assert report.current_steward_ids == frozenset({"steward-a", "steward-b"})


def test_baseline_extends_coverage_and_creates_its_own_deadline(rule):
    baseline = clock(10, 30, 0)

    report = rule.evaluate(PLATFORM_AREA, [], baseline, BASE)

    assert report.shift_start_time == baseline
    assert report.overdue_at == clock(11, 30, 0)
    assert report.coverage_status == "overdue"
    assert report.episodes == (
        OverdueEpisode(overdue_at=clock(11, 30, 0), cleared_at=None),
    )


def test_no_baseline_and_no_visits_gives_no_episodes(rule):
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
