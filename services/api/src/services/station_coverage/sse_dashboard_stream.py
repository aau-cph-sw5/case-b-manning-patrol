"""Server-sent events stream of station coverage for one dashboard client."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi.sse import ServerSentEvent

from src.domain.coverage import StationCoverageReport
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster


class SSEDashboardStream:
    """Send `dashboard` events to one client every time coverage is refreshed."""

    def __init__(
        self,
        broadcaster: SseCoverageBroadcaster,
        presenter: DashboardPresenter,
        updater: CoverageUpdater,
        queue: asyncio.Queue,
    ):
        self.broadcaster = broadcaster
        self.presenter = presenter
        self.updater = updater
        self.queue = queue

    async def run_stream(self) -> AsyncGenerator[ServerSentEvent]:
        """Yield the current coverage at once, then again after every refresh.

        Refreshes that pile up while the client is busy are sent as one event
        with the newest coverage. The queue is unsubscribed when the generator
        is closed.
        """
        try:
            yield self._dashboard_event(self.presenter, self.updater.snapshot())
            while True:
                await self._wait_for_refresh()
                yield self._dashboard_event(self.presenter, self.updater.snapshot())
        finally:
            self.broadcaster.unsubscribe(self.queue)

    async def _wait_for_refresh(self) -> None:
        task = asyncio.create_task(self.queue.get())
        try:
            await task
        finally:
            task.cancel()
        while not self.queue.empty():
            self.queue.get_nowait()

    def _dashboard_event(
        self,
        presenter: DashboardPresenter,
        station_reports: list[StationCoverageReport],
    ) -> ServerSentEvent:
        dashboard = presenter.to_dashboard(station_reports, sent_at=datetime.now(UTC))
        return ServerSentEvent(data=dashboard, event="dashboard")
