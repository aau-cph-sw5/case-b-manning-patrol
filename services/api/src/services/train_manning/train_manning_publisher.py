from typing import Protocol

from src.domain.train_manning import TrainManningReport


class TrainManningPublisher(Protocol):
    def publish(self, reports: list[TrainManningReport]) -> None: ...
