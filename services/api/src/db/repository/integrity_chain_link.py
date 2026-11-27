"""Queries for the hash chain integrity log."""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink


async def get_head_hash(session: AsyncSession, chain: ChainName) -> str | None:
    """Return the head hash the next append must link onto, or None.

    The chain's head is the ``head_hash`` of its newest link, the row with
    the highest ``seq`` for that chain. None means the chain has no links
    yet, so the caller starts from the chain's genesis hash.
    """
    result = await session.exec(
        select(col(IntegrityChainLink.head_hash))
        .where(IntegrityChainLink.chain == chain)
        .order_by(col(IntegrityChainLink.seq).desc())
    )

    return result.first()


async def get_chain(
    session: AsyncSession, chain: ChainName
) -> list[IntegrityChainLink]:
    """Return every link of the chain, oldest first, to verify the chain."""
    result = await session.exec(
        select(IntegrityChainLink)
        .where(IntegrityChainLink.chain == chain)
        .order_by(col(IntegrityChainLink.seq))
    )

    return list(result.all())

