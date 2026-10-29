"""
Repository of functions used to query the database related to Adjustments
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )
    return result.one()


async def get_adjustments(session: AsyncSession) -> list[Adjustment]:
    result = await session.exec(select(Adjustment))

    return list(result.all())


async def insert_adjustment(
    session: AsyncSession,
    adjustment: Adjustment,
) -> Adjustment:
    session.add(adjustment)
    await session.commit()
    await session.refresh(adjustment)
    return adjustment
