from datetime import timedelta

import pytest

from src.models.coverage import AreaCoverage, AreaRef, CoverageStatus, StationCoverage
from src.models.patrol_area import AreaKind


@pytest.fixture
def area_coverage_compliant(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE),
        covered_now=True,
        last_covered_at=now - timedelta(minutes=10),
        baseline=now - timedelta(minutes=15),
        episodes=(),
        window=timedelta(minutes=30),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


@pytest.fixture
def area_coverage_overdue(now):
    return AreaCoverage(
        area=AreaRef(station_id=None, area_id="platform", kind=AreaKind.PLATFORM),
        covered_now=False,
        last_covered_at=None,
        baseline=now - timedelta(minutes=15),
        episodes=(),
        window=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset(["steward1", "steward2"]),
    )


@pytest.fixture
def station_compliant(area_coverage_compliant):
    return StationCoverage("station_1", areas=(area_coverage_compliant,))


@pytest.fixture
def station_overdue(area_coverage_overdue) -> StationCoverage:
    return StationCoverage("station_1", areas=(area_coverage_overdue,))


def test_status_compliant(station_compliant):
    assert station_compliant.status == CoverageStatus.COMPLIANT


def test_status_overdue(station_overdue):
    assert station_overdue.status == CoverageStatus.OVERDUE
