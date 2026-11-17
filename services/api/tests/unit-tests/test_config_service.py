"""Unit tests for ConfigService."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db import models  # noqa: F401  registers table metadata
from src.db.models.config import DEFAULT_AT_RISK_THRESHOLD_MINUTES
from src.services.config.config_service import ConfigService


@pytest_asyncio.fixture
async def service() -> AsyncGenerator[ConfigService]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield ConfigService(session)
    await engine.dispose()


async def test_get_returns_default_when_unset(service: ConfigService):
    assert (
        await service.get_at_risk_threshold_minutes()
        == DEFAULT_AT_RISK_THRESHOLD_MINUTES
    )


async def test_set_persists_value(service: ConfigService):
    assert await service.set_at_risk_threshold_minutes(15) == 15
    assert await service.get_at_risk_threshold_minutes() == 15
