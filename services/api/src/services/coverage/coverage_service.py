from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.coverage.coverage import StationCoverage
from src.services.coverage.coverage_window import CoverageWindow
from src.services.coverage.interval_builder import IntervalBuilder


# Query: computes the current coverage of every station. Reads only, never
# writes, logs or publishes.
class CoverageService:
    def __init__(self, builder: IntervalBuilder, rule: CoverageWindow) -> None:
        """Hold the interval builder and the coverage rule.

        Both are passed in, so tests can supply their own configuration, for
        example shorter thresholds.
        """
        self._builder = builder
        self._rule = rule

    async def compute(
        self,
        session: AsyncSession,
        now: datetime,
        baseline: datetime | None = None,
    ) -> list[StationCoverage]:
        """Compute the coverage of every station at now, without changing anything.

        1. Load all events and all patrol areas, once each.
        2. Build a beacon_id -> AreaRef lookup. Events at unknown beacons are
           skipped and logged.
        3. Build the intervals once and group them per area.
        4. Evaluate every patrol area, including areas with no visits at all,
           so a never patrolled area shows as OVERDUE instead of disappearing.
        5. Group the results per station.

        Read only: it writes nothing and publishes nothing. baseline is the
        shift start once shifts exist; None today.
        """
        raise NotImplementedError
