"""Fan out coverage reports to connected dashboard SSE streams."""

import asyncio

from src.domain.coverage import StationCoverageReport
from src.services.station_coverage.coverage_publisher import CoveragePublisher


class SseCoverageBroadcaster(CoveragePublisher):
    """Give each server-sent-events client its own queue of coverage updates."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[list[StationCoverageReport]]] = set()

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Put the reports on every subscriber's queue.

        Queues are unbounded, so a client that stops reading accumulates
        updates until it unsubscribes.
        """
        for queue in self._subscribers:
            queue.put_nowait(coverage)

    def subscribe(self) -> asyncio.Queue[list[StationCoverageReport]]:
        """Register a new client and return the queue it should read from."""
        queue: asyncio.Queue[list[StationCoverageReport]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[StationCoverageReport]]) -> None:
        """Stop sending updates to ``queue``; unknown queues are ignored."""
        self._subscribers.discard(queue)
