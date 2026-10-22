from typing import Protocol

from src.models.coverage import StationCoverageReport


# Where the current coverage is pushed. Keeps the transport (SSE today)
# replaceable.
class CoveragePublisher(Protocol):
    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Send the current coverage of every station to the dashboards.

        Every refresh passes the full coverage, the same payload a dashboard
        receives on connect, so a client can always replace its whole state.
        Synchronous on purpose: the updater calls it in a block without await,
        so no dashboard can connect halfway through a publish.
        """
        ...
