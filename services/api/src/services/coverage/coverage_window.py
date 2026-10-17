from datetime import datetime, timedelta

from src.models.patrol_area import AreaKind
from src.services.coverage.models.area_coverage import AreaCoverage
from src.services.coverage.models.area_ref import AreaRef
from src.services.coverage.models.covered_time_span import CoveredTimeSpan
from src.services.coverage.models.overdue_episode import OverdueEpisode
from src.services.coverage.models.presence_interval import PresenceInterval


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
        raise NotImplementedError

    def evaluate(
        self,
        area: AreaRef,
        intervals: list[PresenceInterval],
        baseline: datetime | None,
        now: datetime,
    ) -> AreaCoverage:
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
        raise NotImplementedError

    def _union(self, spans: list[CoveredTimeSpan]) -> list[CoveredTimeSpan]:
        """Merge overlapping spans into a sorted list without overlaps.

        Sort by start, then walk the list and merge each span into the previous
        one while they touch. The result shows exactly when the area was
        covered, which makes the gaps easy to find.
        """
        raise NotImplementedError

    def _gaps(
        self,
        spans: list[CoveredTimeSpan],
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
        raise NotImplementedError
