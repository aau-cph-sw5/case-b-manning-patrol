from typing import Protocol

from src.domain.coverage import StationCoverageReport


class CoveragePublisher(Protocol):
    def publish(self, coverage: list[StationCoverageReport]) -> None: ...
