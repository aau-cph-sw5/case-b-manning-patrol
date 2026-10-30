from datetime import timedelta
from uuid import UUID

import pytest

from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    CoverageStatus,
    StationCoverageReport,
)
from src.domain.patrol_area import AreaKind

STEWARD_1 = UUID("00000000-0000-0000-0000-000000000001")
STEWARD_2 = UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def area_coverage_compliant(now):
    return AreaCoverageReport(
        area=AreaReference(
            station_id=None, area_id="concourse", kind=AreaKind.CONCOURSE
        ),
        covered_now=True,
        last_covered_at=now - timedelta(minutes=10),
        shift_start_time=now - timedelta(minutes=15),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=30),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
    )


@pytest.fixture
def area_coverage_overdue(now):
    return AreaCoverageReport(
        area=AreaReference(station_id=None, area_id="platform", kind=AreaKind.PLATFORM),
        covered_now=False,
        last_covered_at=None,
        shift_start_time=now - timedelta(minutes=15),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=5),
        as_of=now,
        current_steward_ids=frozenset([STEWARD_1, STEWARD_2]),
    )


@pytest.fixture
def station_compliant(area_coverage_compliant):
    return StationCoverageReport("station_1", areas=(area_coverage_compliant,))


@pytest.fixture
def station_overdue(area_coverage_overdue) -> StationCoverageReport:
    return StationCoverageReport("station_1", areas=(area_coverage_overdue,))


def test_status_compliant(station_compliant):
    assert station_compliant.coverage_status == CoverageStatus.COMPLIANT


def test_status_overdue(station_overdue):
    assert station_overdue.coverage_status == CoverageStatus.OVERDUE
