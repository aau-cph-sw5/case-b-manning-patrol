"""Database table linking a steward to the events of one shift."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class StewardShiftIdentity(SQLModel, table=True):
    """One steward's identity for one shift.

    Events will point here through ``steward_ref`` instead of storing
    ``android_id``, so the person is only stored in this table. Each steward
    gets a new random ``steward_ref`` every shift, so old and new records
    cannot be linked to each other. Anonymisation after 5 years
    sets ``android_id`` to None and sets ``anonymised_at``.
    Rows are never deleted.
    """

    __tablename__ = "steward_identity"
    __table_args__ = (UniqueConstraint("android_id", "shift_start"),)

    steward_ref: UUID = Field(default_factory=uuid4, primary_key=True)
    android_id: UUID | None
    shift_start: datetime
    anonymised_at: datetime | None = None
