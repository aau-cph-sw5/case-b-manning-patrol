"""Database table for the hash chain integrity log."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class IntegrityEntry(SQLModel, table=True):
    """One append to a named hash chain. Rows are only ever inserted.

    ``chain`` names the chain this link belongs to ("events" or
    "adjustments") and ``seq`` is the link's per-chain position; the pair
    is unique, so a link's place in the chain cannot be ambigous.
    ``record_type`` and ``record_id`` point at the committed row.
    ``prev_hash`` is the chain head before this append, ``content_hash``
    the digest of the committed record's fields alone and ``head_hash``
    the new head after the append. Editing or removing any row changes
    the head it produced, which no later ``prev_hash`` matches, so
    tampering anywhere in the chain is detectable (MET-B-021).
    """

    entry_id: UUID = Field(primary_key=True)
    chain: str = Field(max_length=32, index=True)
    seq: int
    record_type: str = Field(max_length=32)
    record_id: UUID
    prev_hash: str = Field(max_length=64)
    content_hash: str = Field(max_length=64)
    head_hash: str = Field(max_length=64)
    server_timestamp: datetime

    __table_args__ = (UniqueConstraint("chain", "seq"),)
