"""Database table for the hash chain integrity log."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, SQLModel


class ChainName(StrEnum):
    """The named chains whose records are committed link by link."""

    EVENTS = "events"
    ADJUSTMENTS = "adjustments"


class IntegrityChainLink(SQLModel, table=True):
    """One append to a named hash chain. Rows are only ever inserted.

    ``chain`` names the chain this link belongs to ("events" or
    "adjustments"), which also picks the table ``record_id`` points
    into. ``seq`` is a global autoincrement counter; links in a chain
    have increasing but non-consecutive values, so chain order is
    ``seq`` order. ``prev_hash`` is the head before this append,
    ``content_hash`` the digest of the committed record alone, and
    ``head_hash`` the new head. Integrity rests on each ``prev_hash``
    matching the ``head_hash`` of the same chain's previous ``seq``,
    not on ``seq`` being consecutive. Any edit or removal breaks that
    match and is detectable; tail deletion needs external anchoring
    of the head (MET-B-021).
    """

    seq: int | None = Field(default=None, primary_key=True)
    chain: ChainName = Field(index=True)
    record_id: UUID
    prev_hash: str = Field(max_length=64)
    content_hash: str = Field(max_length=64)
    head_hash: str = Field(max_length=64)
    server_timestamp: datetime
