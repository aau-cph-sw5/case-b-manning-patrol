"""
Repository of functions used to query the database related to Train
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Train, TrainLine


async def get_trains(session: AsyncSession) -> list[Train]:
    result = await session.exec(select(Train))

    return list(result.all())


async def get_train_lines(session: AsyncSession) -> list[TrainLine]:
    result = await session.exec(select(TrainLine))

    return list(result.all())
