"""Compute train manning from the event log."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.train_line import TrainLine
from src.db.repository.event import get_events
from src.db.repository.train import get_train_lines, get_trains
from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.shared.event_record_mapper import EventRecordMapper
from src.services.shared.interval_builder import IntervalBuilder
from src.services.shared.interval_processor import IntervalProcessor
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator


@dataclass
class TrainManningService:
    """Build a manning report for every train from steward visits to its beacon."""

    _interval_builder: IntervalBuilder
    _evaluator: TrainManningEvaluator

    async def compute_manning_reports(
        self,
        session: AsyncSession,
        now: datetime,
        shift_start_time: datetime | None = None,
        known_at: datetime | None = None,
    ) -> list[TrainManningReport]:
        """Return the manning of every train as of ``now``, sorted by slug.

        ``shift_start_time`` is the scheduled shift start; when given,
        intervals are clipped to ``[shift_start_time, now]`` and running time
        is counted from it. When ``None``, running time starts at ``now``.

        ``known_at`` limits the calculation to events the backend had
        received by then (by ``server_timestamp``), so manning can be
        reproduced as it was known at that moment. When ``None``, every
        stored event is used, including ones that arrived late.
        """
        events = await get_events(session, known_at=known_at)
        trains = await get_trains(session)
        train_lines = await get_train_lines(session)

        records = [EventRecordMapper.to_record(event) for event in events]
        intervals = self._interval_builder.build(records)
        if shift_start_time is not None:
            intervals = IntervalProcessor.within_shift(intervals, shift_start_time, now)
        intervals_by_beacon = IntervalProcessor.group_by_beacon(intervals)
        lines_by_train = TrainManningService._group_lines_by_train(train_lines)

        reports = []
        for train in trains:
            reference = TrainReference(
                train_id=train.train_id,
                slug=train.slug,
                beacon_id=train.beacon_id,
                line_ids=frozenset(lines_by_train.get(train.train_id, ())),
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

    @staticmethod
    def _group_lines_by_train(train_lines: list[TrainLine]) -> dict[UUID, set[str]]:
        lines_by_train: dict[UUID, set[str]] = {}
        for train_line in train_lines:
            lines_by_train.setdefault(train_line.train_id, set()).add(
                train_line.line_id
            )
        return lines_by_train
