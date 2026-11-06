"""Trains stream payloads.

Defined by the positioning-interface contract
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TrainsUpdateTrain(BaseModel):
    """Update for a single train. Current steward IDs
    are the IDs of the stewards currently on the train."""

    train_id: UUID
    slug: str
    current_steward_ids: list[UUID]
    line: list[str]


class TrainsUpdate(BaseModel):
    """Update for all trains as defined in the contract."""

    manning_percent: float | None = None
    m1m2_manning_percent: float | None = None
    m3m4_manning_percent: float | None = None
    trains: list[TrainsUpdateTrain]
    time: datetime
