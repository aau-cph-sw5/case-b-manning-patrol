from typing import Protocol

from src.models.coverage import StationCoverageReport


# Where the current coverage is pushed. Keeps the transport (SSE today)
# replaceable.
class CoveragePublisher(Protocol):
    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Send the coverage of the stations that changed to the dashboards.

        A dashboard already holds every station from the snapshot it received
        on connect, and replaces its copy of each station it receives here.
        Synchronous on purpose: the updater calls it in a block without await,
        so no dashboard can connect halfway through a publish.
        """
        ...
