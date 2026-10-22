from datetime import datetime

from src.models import Station, StationLine
from src.models.coverage import AreaCoverageReport, StationCoverageReport
from src.models.dashboard import Dashboard, DashboardArea, DashboardStation

LINE_SEPARATOR = " & "


# Turns coverage reports into the Dashboard of the positioning-interface contract.
# Holds the station reference data the reports do not carry: names and lines.
class DashboardPresenter:
    def __init__(self, stations: list[Station], station_lines: list[StationLine]):
        """Index the station names and the lines serving each station.

        The dataset has no line per area, so an area gets its station's lines.
        """
        self._names = {station.id: station.name for station in stations}
        lines: dict[str, list[str]] = {}
        for station_line in sorted(station_lines, key=lambda sl: sl.line_id):
            lines.setdefault(station_line.station_id, []).append(station_line.line_id)
        self._lines = {
            station_id: LINE_SEPARATOR.join(line_ids)
            for station_id, line_ids in lines.items()
        }

    def present(
        self, reports: list[StationCoverageReport], sent_at: datetime
    ) -> Dashboard:
        """The Dashboard for the given stations, sent at sent_at.

        No train is tracked by the backend yet, so trains is always empty.
        """
        return Dashboard(
            stations=[self._station(report) for report in reports],
            trains=[],
            time=sent_at,
        )

    def _station(self, report: StationCoverageReport) -> DashboardStation:
        line = self._lines.get(report.station_id, "")
        return DashboardStation(
            station_id=report.station_id,
            name=self._names[report.station_id],
            areas=[self._area(area, line) for area in report.areas],
        )

    @staticmethod
    def _area(report: AreaCoverageReport, line: str) -> DashboardArea:
        # The dataset has no area names. A station has at most one area of each
        # kind, so the kind names the area within its station.
        return DashboardArea(
            area_id=report.area.area_id,
            name=report.area.kind.value.capitalize(),
            line=line,
            area_type=report.area.kind,
            covered_now=report.covered_now,
            overdue_at=report.overdue_at,
        )
