from datetime import datetime

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

        intervals_by_beacon = {}
        for interval in intervals:
            if interval.beacon_id not in intervals_by_beacon:
                intervals_by_beacon[interval.beacon_id] = []
            intervals_by_beacon[interval.beacon_id].append(interval)

        area_reports = []
        for area in areas:
            patrol_intervals: list[StewardPatrolInterval] = []
            area_reference = AreaRefference.from_patrol_area(area)
            if area.beacon_id is None:
                patrol_intervals = []
            else:
                patrol_intervals = intervals_by_beacon.get(area.beacon_id, [])
            area_report = self._rule.evaluate(
                area_reference, patrol_intervals, shift_start_time, now
            )
            area_reports.append(area_report)

        area_reports_by_station = self._get_area_reports_by_station(area_reports)

        station_ids = sorted(area_reports_by_station.keys())

        station_reports = []
        for station_id in station_ids:
            station_reports.append(
                StationCoverageReport(
                    station_id, tuple(area_reports_by_station[station_id])
                )
            )

        return station_reports

    def _get_area_reports_by_station(
        self, area_reports: list[AreaCoverageReport]
    ) -> dict[str, list[AreaCoverageReport]]:
        area_reports_by_station = {}
        for area_report in area_reports:
            if area_report.area.station_id is None:
                station_id = ""
            else:
                station_id = area_report.area.station_id
            if station_id not in area_reports_by_station:
                area_reports_by_station[station_id] = []
            area_reports_by_station[station_id].append(area_report)
        return area_reports_by_station
