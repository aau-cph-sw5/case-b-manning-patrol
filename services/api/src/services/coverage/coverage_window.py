from datetime import datetime, timedelta

from src.models.coverage import (
    AreaCoverageReport,
    AreaRefference,
    OverdueEpisode,
    StewardPatrolInterval,
    TimeSpan,
)
from src.models.patrol_area import AreaKind


# The patrol completion rule: decides the coverage of one area from its
# intervals. Holds only configuration, so the same inputs give the same result.
class CoverageWindow:
    def __init__(
        self,
        window: timedelta,
        min_durations: dict[AreaKind, timedelta],
    ) -> None:
        """Configure the rule.

        window is how long an area stays covered after a visit (60 min).
        min_durations is how long a visit must last per kind of area
        (placeholders: platform 4 s, concourse 10 min). Both are passed in, so
        they can change without changing the rule.
        """
        self._window = window
        self._min_durations = min_durations

    def min_duration(self, kind: AreaKind) -> timedelta:
        """How long a visit must last before it counts for this kind of area.

        Looks the kind up in min_durations. A kind without a configured
        threshold is a configuration error, not something to guess.
        """
        if kind not in self._min_durations:
            raise KeyError(f"No min_duration configured for {kind}")
        return self._min_durations[kind]

    def evaluate(
        self,
        area: AreaRefference,
        intervals: list[StewardPatrolInterval],
        baseline: datetime | None,
        now: datetime,
    ) -> AreaCoverageReport:
        """Work out the coverage of one patrol area at now.

        intervals are the visits at this area only.
        1. Ask each interval for its covered_span. Visits that are too short
           give None and are dropped.
        2. If a baseline (shift start) is given, add [baseline, baseline +
           window], so a shift starts covered. Today baseline is None.
        3. Merge the spans with _union.
        4. The gaps between them, up to now, are the overdue episodes (_gaps).
        5. Fill last_covered_at (end of the newest finished qualifying visit),
           covered_now (a qualifying visit is still open) and
           current_steward_ids (everyone present now, qualified or not).

        The same inputs and the same now always give the same result (AC5).
        """
        minimum = self.min_duration(area.kind)

        spans: list[TimeSpan] = []
        for interval in intervals:
            span = interval.patrol_span(minimum, self._window, now)
            if span is not None:
                spans.append(span)
        if baseline is not None:
            spans.append(TimeSpan(start=baseline, end=baseline + self._window))

        merged = self._union(spans)
        start = merged[0].start if merged else now
        episodes = tuple(self._gaps(merged, start, now))

        finished_qualifying = [
            interval.ended_at
            for interval in intervals
            if interval.ended_at is not None
            and interval.qualifies_as_patrolled(minimum, now)
        ]
        covered_now = any(
            interval.is_patrolling() and interval.qualifies_as_patrolled(minimum, now)
            for interval in intervals
        )
        current_steward_ids = frozenset(
            interval.android_id for interval in intervals if interval.is_patrolling()
        )

        return AreaCoverageReport(
            area=area,
            last_covered_at=max(finished_qualifying) if finished_qualifying else None,
            covered_now=covered_now,
            shift_start_time=baseline,
            current_steward_ids=current_steward_ids,
            episodes=episodes,
            time_until_next_needed_patrol=self._window,
            as_of=now,
        )

    def _union(self, spans: list[TimeSpan]) -> list[TimeSpan]:
        """Merge overlapping spans into a sorted list without overlaps.

        Sort by start, then walk the list and merge each span into the previous
        one while they touch. The result shows exactly when the area was
        covered, which makes the gaps easy to find.
        """
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
        """Find the stretches between start and until where nothing covered the area.

        spans must come from _union. Each gap becomes an OverdueEpisode that
        starts where a span ends (overdue_at, the deadline) and is cleared
        where the next span starts (qualified_at of the visit that ended it).
        A gap that reaches until is still open (cleared_at = None). start is
        the first covered moment, so time before the first patrol is never an
        episode.
        """
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
