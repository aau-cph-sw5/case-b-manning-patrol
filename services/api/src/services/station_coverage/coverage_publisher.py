"""Interface for pushing fresh coverage reports to listeners."""

from typing import Protocol

from src.domain.coverage import StationCoverageReport


class CoveragePublisher(Protocol):
    """Anything that can receive the latest coverage reports."""

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Deliver the latest coverage reports without blocking."""
        ...
