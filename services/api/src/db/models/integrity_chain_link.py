"""Database table for the hash chain integrity log."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class ChainName(StrEnum):
    """The named chains whose records are committed link by link."""

    EVENTS = "events"
    ADJUSTMENTS = "adjustments"


class IntegrityChainLink(SQLModel, table=True):
    """One append to a named hash chain. Rows are only ever inserted.

    ``chain`` names the chain this link belongs to ("events" or
    "adjustments"), which also picks the table ``record_id`` points into,
    and ``seq`` is the link's position in the chain; the pair is unique,
    so a link's place in the chain cannot be ambiguous. ``prev_hash`` is
    the chain head before this append, ``content_hash`` the digest of
    the committed record's fields alone and ``head_hash`` the new head
    after the append. Editing or removing any row changes the head it
    produced, which no later ``prev_hash`` matches, so tampering
    anywhere in the chain is detectable (MET-B-021).
    """

    entry_id: UUID = Field(primary_key=True)
    chain: ChainName = Field(index=True)
    seq: int
    record_id: UUID
    prev_hash: str = Field(max_length=64)
    content_hash: str = Field(max_length=64)
    head_hash: str = Field(max_length=64)
    server_timestamp: datetime

    __table_args__ = (UniqueConstraint("chain", "seq"),)
