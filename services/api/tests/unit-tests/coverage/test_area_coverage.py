from datetime import timedelta

import pytest

from src.models.coverage import AreaCoverage, AreaRef
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
