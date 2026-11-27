"""Queries for supervisor adjustments to recorded events."""

from datetime import datetime
from uuid import UUID

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    """Return the adjustment with this ID, or raise NoResultFound."""
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )
    return result.one()


async def get_adjustments(
    session: AsyncSession,
    *,
    known_at: datetime | None = None,
) -> list[Adjustment]:
    """Return the stored adjustments, in no particular order.

    With ``known_at``, only adjustments recorded by then
    (``server_timestamp <= known_at``) are returned. ``None`` returns every
    adjustment.
    """
    statement = select(Adjustment)
    if known_at is not None:
        statement = statement.where(col(Adjustment.server_timestamp) <= known_at)
    result = await session.exec(statement)

    return list(result.all())


async def count_unlinked_adjustments(session: AsyncSession) -> int:
    """Return how many adjustments have no link in the adjustments hash chain.

    ``insert_adjustment`` saves every adjustment together with its link, so
    this is 0 unless rows were written to the database directly.
    """
    linked_ids = select(IntegrityChainLink.record_id).where(
        IntegrityChainLink.chain == ChainName.ADJUSTMENTS
    )
    result = await session.exec(
        select(func.count())
        .select_from(Adjustment)
        .where(col(Adjustment.adjustment_id).not_in(linked_ids))
    )

    return result.one()


async def insert_adjustment(
    session: AsyncSession,
    adjustment: Adjustment,
    chain_link: IntegrityChainLink,
) -> Adjustment:
    """Insert and commit the adjustment, then reload it from the database."""
    session.add(adjustment)
    session.add(chain_link)
    await session.commit()
    await session.refresh(adjustment)
    await session.refresh(chain_link)
    return adjustment
