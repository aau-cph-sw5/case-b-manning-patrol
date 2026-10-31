from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Event
from src.db.models.train_line import TrainLine
from src.db.repository.event import get_events
from src.db.repository.train import get_train_lines, get_trains
from src.domain.coverage import StewardPatrolInterval
from src.domain.event import EventRecord
from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.station_coverage.interval_builder import IntervalBuilder
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator


@dataclass
class TrainManningService:
    _interval_builder: IntervalBuilder
    _evaluator: TrainManningEvaluator

    async def compute_manning_reports(
        self,
        session: AsyncSession,
        now: datetime,
        shift_start_time: datetime | None = None,
    ) -> list[TrainManningReport]:
        events = await get_events(session)
        trains = await get_trains(session)
        train_lines = await get_train_lines(session)

        records = [_to_record(event) for event in events]
        intervals = self._interval_builder.build(records)
        if shift_start_time is not None:
            intervals = _within_shift(intervals, shift_start_time, now)
        intervals_by_beacon = _group_by_beacon(intervals)
        lines_by_train = _group_lines_by_train(train_lines)

        reports = []
        for train in trains:
            reference = TrainReference(
                id=train.id,
                slug=train.slug,
                beacon_id=train.beacon_id,
                line_ids=frozenset(lines_by_train.get(train.id, ())),
            )
            train_intervals = intervals_by_beacon.get(train.beacon_id, [])
            reports.append(
                self._evaluator.evaluate(
                    reference,
                    train_intervals,
                    shift_start_time if shift_start_time is not None else now,
                    now,
                )
            )
        return sorted(reports, key=lambda report: report.train.slug)


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
            )
        )
    return within


def _group_by_beacon(
    intervals: list[StewardPatrolInterval],
) -> dict[UUID, list[StewardPatrolInterval]]:
    intervals_by_beacon: dict[UUID, list[StewardPatrolInterval]] = {}
    for interval in intervals:
        intervals_by_beacon.setdefault(interval.beacon_id, []).append(interval)
    return intervals_by_beacon


def _group_lines_by_train(train_lines: list[TrainLine]) -> dict[UUID, set[str]]:
    lines_by_train: dict[UUID, set[str]] = {}
    for train_line in train_lines:
        lines_by_train.setdefault(train_line.train_id, set()).add(train_line.line_id)
    return lines_by_train


def _to_record(event: Event) -> EventRecord:
    return EventRecord(
        event_id=event.event_id,
        event_type=event.event_type,
        android_id=event.android_id,
        beacon_id=event.beacon_id,
        device_timestamp=event.device_timestamp,
        server_timestamp=event.server_timestamp,
    )
