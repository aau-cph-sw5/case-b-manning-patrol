"""Interface for pushing fresh train manning reports to listeners."""

from typing import Protocol

from src.domain.train_manning import TrainManningReport


class TrainManningPublisher(Protocol):
    """Anything that can receive the latest train manning reports."""

    def publish(self, reports: list[TrainManningReport]) -> None:
        """Deliver the latest train manning reports without blocking."""
        ...
