"""Queries for supervisor adjustments to recorded events."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    """Return the adjustment with this ID, or raise NoResultFound."""
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )
    return result.one()


async def get_adjustments(session: AsyncSession) -> list[Adjustment]:
    """Return all adjustments."""
    result = await session.exec(select(Adjustment))

    return list(result.all())


async def insert_adjustment(
    session: AsyncSession,
    adjustment: Adjustment,
) -> Adjustment:
    """Insert and commit the adjustment, then reload it from the database."""
    session.add(adjustment)
    await session.commit()
    await session.refresh(adjustment)
    return adjustment
