import datetime
from collections.abc import Callable
from datetime import timedelta

import pytest

from src.models.coverage import (
    AreaCoverageReport,
    AreaReference,
    StationCoverageReport,
)
from src.models.patrol_area import AreaKind


@pytest.fixture
def now():
    return datetime.datetime.now()


@pytest.fixture
def station_report() -> Callable[..., StationCoverageReport]:
    """Factory for a one-area station report, so tests only spell out the
    fields that matter for the push path."""

    def _make(
        station_id: str,
        *,
        covered_now: bool,
        as_of: datetime.datetime,
        last_covered_at: datetime.datetime | None,
    ) -> StationCoverageReport:
        return StationCoverageReport(
            station_id=station_id,
            areas=(
                AreaCoverageReport(
                    area=AreaReference(
                        station_id=station_id,
                        area_id="platform-1",
                        kind=AreaKind.PLATFORM,
                    ),
                    last_covered_at=last_covered_at,
                    covered_now=covered_now,
                    shift_start_time=None,
                    current_steward_ids=frozenset(),
                    episodes=(),
                    time_until_next_needed_patrol=timedelta(minutes=60),
                    as_of=as_of,
                ),
            ),
        )

    return _make
