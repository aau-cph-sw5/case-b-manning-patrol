"""Periodic background refresh of station coverage."""

import asyncio
import logging
from datetime import timedelta

from src.services.station_coverage.coverage_updater import CoverageUpdater

logger = logging.getLogger(__name__)


class CoverageClockTick:
    """Refresh coverage on a fixed interval so overdue areas appear without events.

    Coverage changes as time passes even when no steward events arrive, so
    the dashboard needs a clock-driven refresh in addition to event-driven
    ones.
    """

    def __init__(self, updater: CoverageUpdater, interval: timedelta) -> None:
        self._updater = updater
        self._interval = interval
        self._failed_ticks = 0

    async def run(self) -> None:
        """Call ``updater.refresh()`` forever, sleeping ``interval`` between calls.

        A failing refresh never stops the loop. The first failure in a row is
        logged with its traceback, later consecutive failures only at debug
        level, and the first success afterwards logs a recovery message.
        Only cancellation ends the loop.
        """
        while True:
            try:
                await self._updater.refresh()
            except asyncio.CancelledError:
                raise
            except Exception:
                self._failed_ticks += 1
                if self._failed_ticks == 1:
                    logger.exception("Clock tick refresh failed; will keep retrying")
                else:
                    logger.debug(
                        "Clock tick refresh failed again (%d in a row)",
                        self._failed_ticks,
                    )
            else:
                if self._failed_ticks:
                    logger.info(
                        "Clock tick refresh recovered after %d failed ticks",
                        self._failed_ticks,
                    )
                    self._failed_ticks = 0
            await asyncio.sleep(self._interval.total_seconds())
