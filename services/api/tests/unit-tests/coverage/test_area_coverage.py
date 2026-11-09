from datetime import timedelta
from uuid import UUID

import pytest

from src.domain.coverage import AreaCoverageReport, AreaReference, CoverageStatus
from src.domain.patrol_area import AreaKind

STEWARD_1 = UUID("00000000-0000-0000-0000-000000000001")
STEWARD_2 = UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def area_coverage_covered_now(now):
    return AreaCoverageReport(
        area=AreaReference(
            station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE
        ),
        covered_now=True,
        last_covered_at=now - timedelta(minutes=10),
        shift_start_time=now - timedelta(minutes=15),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
    )


@pytest.fixture
def area_coverage_overdue_never_covered(now):
    return AreaCoverageReport(
        area=AreaReference(
            station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE
        ),
        covered_now=False,
        last_covered_at=None,
        shift_start_time=now - timedelta(minutes=15),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
    )


@pytest.fixture
def area_coverage_overdue_covered(now):
    return AreaCoverageReport(
        area=AreaReference(
            station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE
        ),
        covered_now=False,
        last_covered_at=now - timedelta(minutes=30),
        shift_start_time=now - timedelta(minutes=60),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=60),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
    )


@pytest.fixture
def area_coverage_overdue_shift_not_started(now):
    return AreaCoverageReport(
        area=AreaReference(
            station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE
        ),
        covered_now=False,
        last_covered_at=None,
        shift_start_time=None,
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=60),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
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
    assert ac.coverage_status == CoverageStatus.COMPLIANT


def test_status_overdue(area_coverage_overdue_never_covered, now):
    ac = area_coverage_overdue_never_covered
    assert ac.coverage_status == CoverageStatus.OVERDUE


def test_status_compliant_with_future_overdue(area_coverage_overdue_covered, now):
    ac = area_coverage_overdue_covered
    assert ac.coverage_status == CoverageStatus.COMPLIANT


def test_state(area_coverage_covered_now):
    ac = area_coverage_covered_now
    expected_state = (
        ac.covered_now,
        ac.last_covered_at,
        ac.coverage_status,
        ac.current_steward_ids,
    )
    assert ac.state() == expected_state
