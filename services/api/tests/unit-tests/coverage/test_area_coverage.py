from datetime import timedelta

import pytest

from src.models.coverage import AreaCoverage, AreaRef, CoverageStatus
from src.models.patrol_area import AreaKind


@pytest.fixture
def area_coverage_covered_now(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE),
        covered_now=True,
        last_covered_at=now - timedelta(minutes=10),
        baseline=now - timedelta(minutes=15),
        episodes=(),
        window=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


@pytest.fixture
def area_coverage_overdue_never_covered(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE),
        covered_now=False,
        last_covered_at=None,
        baseline=now - timedelta(minutes=15),
        episodes=(),
        window=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


@pytest.fixture
def area_coverage_overdue_covered(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE),
        covered_now=False,
        last_covered_at=now - timedelta(minutes=30),
        baseline=now - timedelta(minutes=60),
        episodes=(),
        window=timedelta(minutes=60),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


@pytest.fixture
def area_coverage_overdue_shift_not_started(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE),
        covered_now=False,
        last_covered_at=None,
        baseline=None,
        episodes=(),
        window=timedelta(minutes=60),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


def test_overdue_at_covered_now(area_coverage_covered_now):
    assert area_coverage_covered_now.overdue_at is None


def test_area_coverage_overdue_at_never_covered(
    area_coverage_overdue_never_covered, now
):
    area_coverage = area_coverage_overdue_never_covered

    assert area_coverage.overdue_at == now - timedelta(minutes=10)


def test_area_coverage_overdue_at_covered(area_coverage_overdue_covered, now):
    ac = area_coverage_overdue_covered

    assert ac.overdue_at == now + timedelta(minutes=30)


def test_area_coverage_overdue_at_shift_not_started(
    area_coverage_overdue_shift_not_started, now
):
    ac = area_coverage_overdue_shift_not_started

    assert ac.overdue_at is None


def test_overdue_by_returns_none(area_coverage_overdue_shift_not_started, now):
    ac = area_coverage_overdue_shift_not_started

    assert ac.overdue_by is None


def test_overdue_by_returns_timedelta(area_coverage_overdue_covered, now):
    ac = area_coverage_overdue_covered

    assert ac.overdue_by == now - ac.overdue_at


def test_status_compliant(area_coverage_covered_now):
    ac = area_coverage_covered_now
    assert ac.status == CoverageStatus.COMPLIANT


def test_status_overdue(area_coverage_overdue_never_covered, now):
    ac = area_coverage_overdue_never_covered
    assert ac.status == CoverageStatus.OVERDUE


def test_status_compliant_with_future_overdue(area_coverage_overdue_covered, now):
    ac = area_coverage_overdue_covered
    assert ac.status == CoverageStatus.COMPLIANT


def test_state(area_coverage_covered_now):
    ac = area_coverage_covered_now
    expected_state = (
        ac.covered_now,
        ac.last_covered_at,
        ac.status,
        ac.current_steward_ids,
    )
    assert ac.state() == expected_state
