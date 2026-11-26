"""Build the historical compliance report payload sent to the web app."""

from src.api.v2.schemas.report import (
    ReportArea,
    ReportData,
    ReportStation,
    ReportTrain,
    ShiftBoundary,
)
from src.db.models import Station, StationLine
from src.domain.compliance import CompliancePicture
from src.domain.coverage import AreaCoverageReport, StationCoverageReport
from src.domain.train_manning import TrainManningReport
from src.services.train_manning.trains_update_presenter import TrainsUpdatePresenter


class ReportPresenter:
    """Add station names and lines to a compliance picture for the report.

    Station names and lines are read once at construction, so the presenter
    must be rebuilt if stations change.
    """

    def __init__(self, stations: list[Station], station_lines: list[StationLine]):
        """Build the station id-to-name and id-to-lines lookups from reference data."""
        self._names = {station.id: station.name for station in stations}
        lines: dict[str, list[str]] = {}
        for station_line in sorted(station_lines, key=lambda sl: sl.line_id):
            lines.setdefault(station_line.station_id, []).append(station_line.line_id)
        self._lines = lines

    def to_report(self, picture: CompliancePicture) -> ReportData:
        """Map a compliance picture to the report payload.

        The aggregate manning percentages come from the same presenter as the
        live trains stream, so the report and the dashboard always agree.
        """
        trains_update = TrainsUpdatePresenter([], []).to_trains_update(
            list(picture.trains), sent_at=picture.as_of
        )
        return ReportData(
            shift=ShiftBoundary(start=picture.shift.start, end=picture.shift.end),
            as_of=picture.as_of,
            known_at=picture.known_at,
            stations=[self._station(report) for report in picture.stations],
            trains=[self._train(report) for report in picture.trains],
            manning_percent=trains_update.manning_percent,
            m1m2_manning_percent=trains_update.m1m2_manning_percent,
            m3m4_manning_percent=trains_update.m3m4_manning_percent,
        )

    def _station(self, report: StationCoverageReport) -> ReportStation:
        """Map one station coverage report, adding the station's name and lines."""
        lines = self._lines.get(report.station_id, [])
        return ReportStation(
            station_id=report.station_id,
            name=self._names[report.station_id],
            line=lines,
            areas=[self._area(area, lines) for area in report.areas],
        )

    @staticmethod
    def _area(report: AreaCoverageReport, lines: list[str]) -> ReportArea:
        """Map one area coverage report, labelling the area by its kind."""
        return ReportArea(
            area_id=report.area.area_id,
            name=report.area.kind.value.capitalize(),
            line=lines,
            area_type=report.area.kind,
            covered_now=report.covered_now,
            overdue_at=report.overdue_at,
            last_covered_at=report.last_covered_at,
            coverage_status=report.coverage_status,
        )

    @staticmethod
    def _train(report: TrainManningReport) -> ReportTrain:
        """Map one train manning report; slug and lines need no lookup."""
        return ReportTrain(
            train_id=report.train.train_id,
            slug=report.train.slug,
            line=sorted(report.train.line_ids),
            manned_ratio=report.manned_ratio,
            manned_now=report.manned_now,
            manned_time=report.manned_time,
            running_time=report.running_time,
        )
