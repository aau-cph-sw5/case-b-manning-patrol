from datetime import datetime, timedelta

from src.domain.coverage import StewardPatrolInterval, TimeSpan
from src.domain.train_manning import TrainManningReport, TrainReference


class TrainManningEvaluator:
    def evaluate(
        self,
        train: TrainReference,
        intervals: list[StewardPatrolInterval],
        shift_start_time: datetime,
        now: datetime,
    ) -> TrainManningReport:
        spans = [
            TimeSpan(start=interval.started_at, end=interval.ended_at or now)
            for interval in intervals
        ]
        manned_time = sum(
            (span.end - span.start for span in self._union(spans)),
            timedelta(0),
        )
        running_time = now - shift_start_time
        current_steward_ids = frozenset(
            interval.android_id for interval in intervals if interval.is_patrolling()
        )

        return TrainManningReport(
            train=train,
            running_time=running_time,
            manned_time=manned_time,
            manned_now=bool(current_steward_ids),
            current_steward_ids=current_steward_ids,
            as_of=now,
        )

    def _union(self, spans: list[TimeSpan]) -> list[TimeSpan]:
        merged: list[TimeSpan] = []
        for span in sorted(spans, key=lambda span: span.start):
            if merged and merged[-1].touches(span):
                merged[-1] = merged[-1].merge(span)
            else:
                merged.append(span)
        return merged
