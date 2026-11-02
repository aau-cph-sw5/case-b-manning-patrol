"""Payload of the trains stream.

Defined by the positioning-interface contract
(contracts/api/v2/positioning-interface).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Train(BaseModel):
    """Manned state of one train."""

    train_id: UUID
    slug: str
    total_time_secs: int
    manned_time_secs: int
    current_steward_ids: list[UUID]
    line: list[str]


class TrainsUpdate(BaseModel):
    """The trains sent on every `trains` stream event; `time` is when it was sent."""

    trains: list[Train]
    time: datetime
