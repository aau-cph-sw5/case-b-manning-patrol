import asyncio

from src.services.coverage.coverage import StationCoverage
from src.services.coverage.coverage_publisher import CoveragePublisher


# Publishes coverage changes to every connected dashboard over SSE, with one
# queue per connection. In memory, so it only works in a single process.
class SseBroadcaster(CoveragePublisher):
    def __init__(self) -> None:
        """Start with no connected dashboards."""
        self._subscribers: set[asyncio.Queue[StationCoverage]] = set()

    def publish(self, changes: list[StationCoverage]) -> None:
        """Hand each changed station to every connected dashboard.

        put_nowait each station into each subscriber's queue. The stream route
        of that connection takes it from there. Never waits, so one slow
        dashboard cannot hold up the others or the updater.
        """
        raise NotImplementedError

    def subscribe(self) -> asyncio.Queue[StationCoverage]:
        """Register a new dashboard connection.

        Creates a queue, adds it to the subscribers and returns it. The stream
        route reads updates from this queue for as long as the connection is
        open.
        """
        raise NotImplementedError

    def unsubscribe(self, queue: asyncio.Queue[StationCoverage]) -> None:
        """Remove a dashboard connection that has closed.

        Drops its queue from the subscribers, so publish stops filling a queue
        that nobody reads.
        """
        raise NotImplementedError
