"""Queries for the single-row system configuration."""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Config
from src.db.models.config import DEFAULT_AT_RISK_THRESHOLD_MINUTES

CONFIG_ROW_ID = 1


async def get_or_create_config(session: AsyncSession) -> Config:
    config = await session.get(Config, CONFIG_ROW_ID)
    if config is None:
        config = Config(
            id=CONFIG_ROW_ID,
            at_risk_threshold_minutes=DEFAULT_AT_RISK_THRESHOLD_MINUTES,
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)
    return config


async def set_at_risk_threshold_minutes(session: AsyncSession, minutes: int) -> Config:
    config = await get_or_create_config(session)
    config.at_risk_threshold_minutes = minutes
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config
