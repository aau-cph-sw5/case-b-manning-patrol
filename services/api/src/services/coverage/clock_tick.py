from datetime import timedelta

from src.services.coverage.coverage_updater import CoverageUpdater


# Refreshes coverage on a timer, because window expiry and a threshold crossed
# mid-visit produce no event. Meant to run as a lifespan task (not wired yet).
class ClockTick:
    def __init__(self, updater: CoverageUpdater, interval: timedelta) -> None:
        """Hold the updater and how often to refresh.

        interval is passed in, so tests can use a short one.
        """
        self._updater = updater
        self._interval = interval

    async def run(self) -> None:
        """Refresh coverage on a fixed interval until the app shuts down.

        Loop: call updater.refresh(), then sleep for interval. Needed because
        two things change coverage without any event arriving: a window running
        out, and an open visit crossing its threshold. Stops cleanly when the
        lifespan cancels the task.
        """
        raise NotImplementedError
