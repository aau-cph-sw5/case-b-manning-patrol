from typing import Protocol

from src.models.coverage import StationCoverageReport


class CoveragePublisher(Protocol):
    def publish(self, coverage: list[StationCoverageReport]) -> None: ...
