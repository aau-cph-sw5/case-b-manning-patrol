"""Queries for the hash chain integrity log."""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.integrity_entry import IntegrityEntry


async def get_head_hash(session: AsyncSession, chain: str) -> str | None:
    """Return the head hash the next append must link onto, or None.

    The chain's head is the ``head_hash`` of its newest link, the row with
    the highest ``seq`` for that chain. None means the chain has no links
    yet, so the caller starts from the chain's genesis hash.
    """
    result = await session.exec(
        select(col(IntegrityEntry.head_hash))
        .where(IntegrityEntry.chain == chain)
        .order_by(col(IntegrityEntry.seq).desc())
    )

    return result.first()


async def get_chain(session: AsyncSession, chain: str) -> list[IntegrityEntry]:
    """Return every link of the chain, oldest first, to verify the chain."""
    result = await session.exec(
        select(IntegrityEntry)
        .where(IntegrityEntry.chain == chain)
        .order_by(col(IntegrityEntry.seq))
    )

    return list(result.all())


async def insert_entry(
    session: AsyncSession,
    entry: IntegrityEntry,
) -> IntegrityEntry:
    """Insert and commit the entry, then reload it from the database."""
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
