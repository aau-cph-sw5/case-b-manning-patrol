from datetime import datetime

from src.api.v2.schemas.dashboard import Dashboard, DashboardArea, DashboardStation
from src.db.models import Station, StationLine
from src.domain.coverage import AreaCoverageReport, StationCoverageReport


class DashboardPresenter:
    def __init__(self, stations: list[Station], station_lines: list[StationLine]):
        self._names = {station.id: station.name for station in stations}
        lines: dict[str, list[str]] = {}
        for station_line in sorted(station_lines, key=lambda sl: sl.line_id):
            lines.setdefault(station_line.station_id, []).append(station_line.line_id)
        self._lines = lines

    def to_dashboard(
        self, reports: list[StationCoverageReport], sent_at: datetime
    ) -> Dashboard:
        return Dashboard(
            stations=[self._station(report) for report in reports],
            trains=[],
            time=sent_at,
        )

    def _station(self, report: StationCoverageReport) -> DashboardStation:
        lines = self._lines.get(report.station_id, [])
        return DashboardStation(
            station_id=report.station_id,
            name=self._names[report.station_id],
            areas=[self._area(area, lines) for area in report.areas],
        )

    @staticmethod
    def _area(report: AreaCoverageReport, lines: list[str]) -> DashboardArea:
        return DashboardArea(
            area_id=report.area.area_id,
            name=report.area.kind.value.capitalize(),
            line=lines,
            area_type=report.area.kind,
            covered_now=report.covered_now,
            overdue_at=report.overdue_at,
        )
