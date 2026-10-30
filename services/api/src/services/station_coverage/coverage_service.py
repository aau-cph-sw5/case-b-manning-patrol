"""Compute per-station patrol coverage from the event log."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Event
from src.db.models.patrol_area import PatrolArea
from src.db.repository.event import get_events
from src.db.repository.patrol_area import get_patrol_areas
from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    StationCoverageReport,
    StewardPatrolInterval,
)
from src.domain.event import EventRecord
from src.services.station_coverage.coverage_window import CoverageWindow
from src.services.station_coverage.interval_builder import IntervalBuilder


class CoverageService:
    """Build coverage reports for every patrol area, grouped by station."""

    def __init__(self, builder: IntervalBuilder, rule: CoverageWindow) -> None:
        self._interval_builder = builder
        self._rule = rule

    async def compute_coverage_reports(
        self,
        session: AsyncSession,
        now: datetime,
        shift_start_time: datetime | None = None,
    ) -> list[StationCoverageReport]:
        """Return the coverage of all stations as of ``now``.

        Loads every event and patrol area, builds visit intervals and
        evaluates each area with the coverage rule. ``now`` is passed in
        instead of read from the clock so results are deterministic and
        testable.

        ``shift_start_time`` is the scheduled shift start from
        ``ShiftSchedule``, never a START event. When given, intervals are
        clipped to ``[shift_start_time, now]``: intervals that start after
        ``now`` or end at or before the shift start are dropped, start times
        are moved up to the shift start, and intervals ending after ``now``
        are treated as still open. When ``None``, no clipping is done.

        Areas without a beacon get no intervals, areas without a station are
        left out, and stations and their areas are sorted by ID.
        """
        events = await get_events(session)
        areas = await get_patrol_areas(session)

        records = [_to_record(event) for event in events]
        intervals = self._interval_builder.build(records)
        if shift_start_time is not None:
            intervals = self._within_shift(intervals, shift_start_time, now)
        intervals_by_beacon = self._group_by_beacon(intervals)
        area_reports = [
            self._evaluate_area(area, intervals_by_beacon, shift_start_time, now)
            for area in areas
        ]
        return self._group_by_station(area_reports)

    def _evaluate_area(
        self,
        area: PatrolArea,
        intervals_by_beacon: dict[UUID, list[StewardPatrolInterval]],
        shift_start_time: datetime | None,
        now: datetime,
    ) -> AreaCoverageReport:
        intervals = (
            intervals_by_beacon.get(area.beacon_id, [])
            if area.beacon_id is not None
            else []
        )
        return self._rule.evaluate(
            _to_area_reference(area), intervals, shift_start_time, now
        )

    @staticmethod
    def _within_shift(
        intervals: list[StewardPatrolInterval],
        shift_start_time: datetime,
        now: datetime,
    ) -> list[StewardPatrolInterval]:
        within: list[StewardPatrolInterval] = []
        for interval in intervals:
            if interval.started_at > now:
                continue
            if interval.ended_at is not None and interval.ended_at <= shift_start_time:
                continue
            ended_at = interval.ended_at
            if ended_at is not None and ended_at > now:
                ended_at = None
            within.append(
                replace(
                    interval,
                    started_at=max(interval.started_at, shift_start_time),
                    ended_at=ended_at,
                ),
            )
        return within

    @staticmethod
    def _group_by_beacon(
        intervals: list[StewardPatrolInterval],
    ) -> dict[UUID, list[StewardPatrolInterval]]:
        intervals_by_beacon: dict[UUID, list[StewardPatrolInterval]] = {}
        for interval in intervals:
            intervals_by_beacon.setdefault(interval.beacon_id, []).append(interval)
        return intervals_by_beacon

    @staticmethod
    def _group_by_station(
        area_reports: list[AreaCoverageReport],
    ) -> list[StationCoverageReport]:
        reports_by_station: dict[str, list[AreaCoverageReport]] = {}
        for report in area_reports:
            station_id = report.area.station_id
            if station_id is None:
                continue
            reports_by_station.setdefault(station_id, []).append(report)

        return [
            StationCoverageReport(
                station_id=station_id,
                areas=tuple(sorted(reports, key=lambda report: report.area.area_id)),
            )
            for station_id, reports in sorted(reports_by_station.items())
        ]


def _to_record(event: Event) -> EventRecord:
    return EventRecord(
        event_id=event.event_id,
        event_type=event.event_type,
        android_id=event.android_id,
        beacon_id=event.beacon_id,
        device_timestamp=event.device_timestamp,
        server_timestamp=event.server_timestamp,
    )


def _to_area_reference(area: PatrolArea) -> AreaReference:
    return AreaReference(area.station_id, area.area_id, area.area_kind)
