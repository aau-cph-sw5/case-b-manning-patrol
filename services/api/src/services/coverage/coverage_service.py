from datetime import datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.events import get_events
from src.db.repository.patrol_area import get_patrol_areas
from src.models.coverage import (
    AreaCoverageReport,
    AreaRefference,
    StationCoverageReport,
    StewardPatrolInterval,
)
from src.services.coverage.coverage_window import CoverageWindow
from src.services.coverage.interval_builder import IntervalBuilder


# Query: computes the current coverage of every station. Reads only, never
# writes, logs or publishes.
class CoverageService:
    def __init__(self, builder: IntervalBuilder, rule: CoverageWindow) -> None:
        self._interval_builder = builder
        self._rule = rule

    async def compute_coverage_reports(
        self,
        session: AsyncSession,
        now: datetime,
        shift_start_time: datetime | None = None,
    ) -> list[StationCoverageReport]:
        events = await get_events(session)
        areas = await get_patrol_areas(session)

        intervals = self._interval_builder.build(events)
        intervals_by_beacon: dict[UUID, list[StewardPatrolInterval]] = {}
        for interval in intervals:
            intervals_by_beacon.setdefault(interval.beacon_id, []).append(interval)

        area_reports: list[AreaCoverageReport] = []
        for area in areas:
            area_refference = AreaRefference.from_patrol_area(area)
            area_intervals = (
                intervals_by_beacon.get(area.beacon_id, [])
                if area.beacon_id is not None
                else []
            )
            report = self._rule.evaluate(
                area_refference, area_intervals, shift_start_time, now
            )
            area_reports.append(report)

        by_station: dict[str, list[AreaCoverageReport]] = {}
        for report in area_reports:
            station_id = report.area.station_id or ""
            by_station.setdefault(station_id, []).append(report)

        sorted_stations = sorted(by_station.items())

        station_reports = []

        for id, area_reports in sorted_stations:
            station_reports.append(StationCoverageReport(id, tuple(area_reports)))

        return station_reports
