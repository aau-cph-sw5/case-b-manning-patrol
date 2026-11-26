"""Unit tests for ReportPresenter mapping CompliancePicture to ReportData."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.db.models import Station, StationLine
from src.domain.compliance import CompliancePicture
from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    StationCoverageReport,
)
from src.domain.patrol_area import AreaKind
from src.domain.shift import Shift
from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.report.report_presenter import ReportPresenter

AS_OF = datetime(2026, 10, 9, 6, 0, tzinfo=UTC)
SHIFT = Shift(
    start=datetime(2026, 10, 8, 22, 0, tzinfo=UTC),
    end=datetime(2026, 10, 9, 21, 59, tzinfo=UTC),
)
STEWARD = UUID("880e8400-e29b-41d4-a716-446655440001")


def make_area(covered_now: bool = True) -> AreaCoverageReport:
    """Build one covered platform area report at station STN-001."""
    return AreaCoverageReport(
        area=AreaReference(
            station_id="STN-001", area_id="PA-001-P", kind=AreaKind.PLATFORM
        ),
        last_covered_at=AS_OF - timedelta(hours=1) if covered_now else None,
        covered_now=covered_now,
        shift_start_time=SHIFT.start,
        current_steward_ids=frozenset({STEWARD}) if covered_now else frozenset(),
        episodes=(),
        time_until_next_needed_patrol=timedelta(minutes=60),
        as_of=AS_OF,
    )


def make_train(
    line_ids: frozenset[str], running: timedelta, manned: timedelta
) -> TrainManningReport:
    """Build one train manning report."""
    return TrainManningReport(
        train=TrainReference(
            train_id=UUID("770e8400-e29b-41d4-a716-446655440101"),
            slug="train-1",
            beacon_id=UUID("660e8400-e29b-41d4-a716-446655440101"),
            line_ids=line_ids,
        ),
        running_time=running,
        manned_time=manned,
        manned_now=manned > timedelta(0),
        current_steward_ids=frozenset(),
        as_of=AS_OF,
    )


def make_picture(
    stations: tuple[StationCoverageReport, ...] = (),
    trains: tuple[TrainManningReport, ...] = (),
) -> CompliancePicture:
    """Build a compliance picture for the fixed shift and AS_OF."""
    return CompliancePicture(
        shift=SHIFT, as_of=AS_OF, known_at=None, stations=stations, trains=trains
    )


def make_presenter() -> ReportPresenter:
    """Build a presenter with one station on M1 and M2."""
    return ReportPresenter(
        stations=[Station(id="STN-001", name="Vestamager")],
        station_lines=[
            StationLine(station_id="STN-001", line_id="M2"),
            StationLine(station_id="STN-001", line_id="M1"),
        ],
    )


def test_station_names_lines_and_areas_are_mapped():
    picture = make_picture(
        stations=(StationCoverageReport(station_id="STN-001", areas=(make_area(),)),)
    )

    report = make_presenter().to_report(picture)

    (station,) = report.stations
    assert station.station_id == "STN-001"
    assert station.name == "Vestamager"
    assert station.line == ["M1", "M2"]
    (area,) = station.areas
    assert area.area_id == "PA-001-P"
    assert area.name == "Platform"
    assert area.area_type == AreaKind.PLATFORM
    assert area.covered_now is True
    assert area.overdue_at is None
    assert area.coverage_status == "compliant"
    assert report.shift.start == SHIFT.start
    assert report.as_of == AS_OF
    assert report.known_at is None


def test_uncovered_area_reports_overdue_status():
    picture = make_picture(
        stations=(
            StationCoverageReport(
                station_id="STN-001",
                areas=(make_area(False),),
            ),
        )
    )

    report = make_presenter().to_report(picture)

    (area,) = report.stations[0].areas
    assert area.covered_now is False
    assert area.coverage_status == "overdue"
    assert area.overdue_at == SHIFT.start + timedelta(minutes=60)


def test_train_fields_are_mapped_without_lookup():
    picture = make_picture(
        trains=(
            make_train(frozenset({"M2", "M1"}), timedelta(hours=4), timedelta(hours=3)),
        )
    )

    report = make_presenter().to_report(picture)

    (train,) = report.trains
    assert train.slug == "train-1"
    assert train.line == ["M1", "M2"]
    assert train.manned_ratio == 0.75
    assert train.manned_now is True
    assert train.manned_time == timedelta(hours=3)
    assert train.running_time == timedelta(hours=4)


def test_manned_ratio_is_none_without_running_time():
    picture = make_picture(
        trains=(make_train(frozenset({"M1"}), timedelta(0), timedelta(0)),)
    )

    report = make_presenter().to_report(picture)

    assert report.trains[0].manned_ratio is None
    assert report.manning_percent is None
    assert report.m1m2_manning_percent is None
    assert report.m3m4_manning_percent is None


def test_aggregate_percents_are_split_by_line_group():
    picture = make_picture(
        trains=(
            make_train(frozenset({"M1"}), timedelta(hours=4), timedelta(hours=1)),
            make_train(frozenset({"M3"}), timedelta(hours=2), timedelta(0)),
        )
    )

    report = make_presenter().to_report(picture)

    assert report.manning_percent == pytest.approx(100 / 6)
    assert report.m1m2_manning_percent == 25.0
    assert report.m3m4_manning_percent == 0.0
