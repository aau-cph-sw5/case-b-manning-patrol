import asyncio

from src.domain.coverage import StationCoverageReport
from src.services.station_coverage.coverage_publisher import CoveragePublisher


class SseCoverageBroadcaster(CoveragePublisher):
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[list[StationCoverageReport]]] = set()

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        for queue in self._subscribers:
            queue.put_nowait(coverage)

    def subscribe(self) -> asyncio.Queue[list[StationCoverageReport]]:
        queue: asyncio.Queue[list[StationCoverageReport]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[StationCoverageReport]]) -> None:
        self._subscribers.discard(queue)
