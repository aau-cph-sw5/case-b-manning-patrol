import asyncio
import logging
from datetime import timedelta

from src.services.train_manning.train_manning_updater import TrainManningUpdater

logger = logging.getLogger(__name__)


class TrainManningClockTick:
    def __init__(self, updater: TrainManningUpdater, interval: timedelta) -> None:
        self._updater = updater
        self._interval = interval
        self._failed_ticks = 0

    async def run(self) -> None:
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
