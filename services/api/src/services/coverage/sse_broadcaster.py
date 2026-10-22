import asyncio

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_publisher import CoveragePublisher


# Publishes the current coverage of every station to every connected
# dashboard over SSE, with one queue per connection. In memory, so it only
# works in a single process.
class SseBroadcaster(CoveragePublisher):
    def __init__(self) -> None:
        """Start with no connected dashboards."""
        self._subscribers: set[asyncio.Queue[list[StationCoverageReport]]] = set()

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Hand the current coverage to every connected dashboard.

        put_nowait the whole list into each subscriber's queue, as one message
        per refresh with the same shape as the snapshot a dashboard receives on
        connect. The stream route of that connection takes it from there.
        Never waits, so one slow dashboard cannot hold up the others or the
        updater.
        """
        for queue in self._subscribers:
            queue.put_nowait(coverage)

    def subscribe(self) -> asyncio.Queue[list[StationCoverageReport]]:
        """Register a new dashboard connection.

        Creates a queue, adds it to the subscribers and returns it. The stream
        route reads updates from this queue for as long as the connection is
        open.
        """
        queue: asyncio.Queue[list[StationCoverageReport]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[StationCoverageReport]]) -> None:
        """Remove a dashboard connection that has closed.

        Drops its queue from the subscribers, so publish stops filling a queue
        that nobody reads.
        """
        self._subscribers.discard(queue)
