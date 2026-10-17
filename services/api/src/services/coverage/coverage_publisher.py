from typing import Protocol

from src.services.coverage.coverage import StationCoverage


# Where changed coverage is pushed. Keeps the transport (SSE today) replaceable.
class CoveragePublisher(Protocol):
    def publish(self, changes: list[StationCoverage]) -> None:
        """Send the stations whose coverage changed to the dashboards.

        Only changed stations are passed, never all of them. Synchronous on
        purpose: the updater calls it in a block without await, so no dashboard
        can connect halfway through a publish.
        """
        ...
