"""
Value objects for train manning (MET-B-011)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID


@dataclass(frozen=True)
class TrainReference:
    train_id: str
    beacon_id: UUID
    line_ids: frozenset[str]


@dataclass(frozen=True)
class TrainManningReport:
    train: TrainReference
    running_time: timedelta
    manned_time: timedelta
    manned_now: bool
    current_steward_ids: frozenset[UUID]
    required_ratio: float
    as_of: datetime

    @property
    def manned_ratio(self) -> float | None:
        if self.running_time <= timedelta(0):
            return None
        return self.manned_time / self.running_time

    def state(self) -> tuple:
        return (
            self.manned_now,
            self.current_steward_ids,
        )
