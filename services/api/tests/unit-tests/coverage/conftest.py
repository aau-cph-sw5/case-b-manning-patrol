import datetime
from collections.abc import Callable
from datetime import timedelta

import pytest

from src.models import Station, StationLine
from src.models.coverage import (
    AreaCoverageReport,
    AreaReference,
    StationCoverageReport,
)
from src.models.patrol_area import AreaKind
from src.services.station_coverage.dashboard_presenter import DashboardPresenter


@pytest.fixture
def now():
    return datetime.datetime.now()


@pytest.fixture
def dashboard_presenter() -> DashboardPresenter:
    """Presenter knowing the stations the station_report factory is used with."""
    return DashboardPresenter(
        stations=[
            Station(id="marmorkirken", name="Marmorkirken"),
            Station(id="kongens-nytorv", name="Kongens Nytorv"),
        ],
        station_lines=[
            StationLine(station_id="marmorkirken", line_id="M3"),
            StationLine(station_id="kongens-nytorv", line_id="M2"),
            StationLine(station_id="kongens-nytorv", line_id="M1"),
        ],
    )


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
