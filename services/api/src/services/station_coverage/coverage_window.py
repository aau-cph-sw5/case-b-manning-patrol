from datetime import datetime, timedelta

from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    OverdueEpisode,
    StewardPatrolInterval,
    TimeSpan,
)
from src.domain.patrol_area import AreaKind

TIME_UNTIL_NEXT_NEEDED_PATROL = timedelta(minutes=60)
MIN_QUALIFYING_DURATIONS = {
    AreaKind.PLATFORM: timedelta(seconds=10),
    AreaKind.CONCOURSE: timedelta(seconds=20),
}


class CoverageWindow:
    def __init__(
        self,
        time_until_next_needed_patrol: timedelta,
        min_qualifying_durations: dict[AreaKind, timedelta],
    ) -> None:
        self._time_until_next_needed_patrol = time_until_next_needed_patrol
        self._min_qualifying_durations = min_qualifying_durations

    def min_qualifying_duration(self, kind: AreaKind) -> timedelta:
        if kind not in self._min_qualifying_durations:
            raise KeyError(f"No min_qualifying_duration configured for {kind}")
        return self._min_qualifying_durations[kind]

    def evaluate(
        self,
        area: AreaReference,
        intervals: list[StewardPatrolInterval],
        shift_start_time: datetime | None,
        now: datetime,
    ) -> AreaCoverageReport:
        min_qualifying_duration = self.min_qualifying_duration(area.kind)

        spans: list[TimeSpan] = []
        for interval in intervals:
            span = interval.patrol_span(
                min_qualifying_duration, self._time_until_next_needed_patrol, now
            )
            if span is not None:
                spans.append(span)
        if shift_start_time is not None:
            spans.append(
                TimeSpan(
                    start=shift_start_time,
                    end=shift_start_time + self._time_until_next_needed_patrol,
                ),
            )

        merged = self._union(spans)
        start = merged[0].start if merged else now
        episodes = tuple(self._gaps(merged, start, now))

        finished_qualifying = [
            interval.ended_at
            for interval in intervals
            if interval.ended_at is not None
            and interval.qualifies_as_patrolled(min_qualifying_duration, now)
        ]
        covered_now = any(
            interval.is_patrolling()
            and interval.qualifies_as_patrolled(min_qualifying_duration, now)
            for interval in intervals
        )
        current_steward_ids = frozenset(
            interval.android_id for interval in intervals if interval.is_patrolling()
        )

        return AreaCoverageReport(
            area=area,
            last_covered_at=max(finished_qualifying) if finished_qualifying else None,
            covered_now=covered_now,
            shift_start_time=shift_start_time,
            current_steward_ids=current_steward_ids,
            episodes=episodes,
            time_until_next_needed_patrol=self._time_until_next_needed_patrol,
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

    def _gaps(
        self,
        spans: list[TimeSpan],
        start: datetime,
        until: datetime,
    ) -> list[OverdueEpisode]:
        episodes: list[OverdueEpisode] = []
        for current, following in zip(spans, spans[1:], strict=False):
            if current.end >= following.start:
                continue
            overdue_at = max(current.end, start)
            if overdue_at >= following.start:
                continue
            episodes.append(
                OverdueEpisode(overdue_at=overdue_at, cleared_at=following.start)
            )
        if spans and spans[-1].end < until:
            episodes.append(OverdueEpisode(overdue_at=spans[-1].end, cleared_at=None))
        return episodes
