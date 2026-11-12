"""Tests for the steward identity repository."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import StewardIdentity
from src.db.repository.steward_identity import get_or_create_steward_ref

ANNA = uuid4()
BO = uuid4()
NIGHT_1 = datetime(2026, 11, 11, 0, 0, tzinfo=UTC)
NIGHT_2 = datetime(2026, 11, 12, 0, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_same_steward_same_shift_gets_same_ref(session):
    first = await get_or_create_steward_ref(session, ANNA, NIGHT_1)
    second = await get_or_create_steward_ref(session, ANNA, NIGHT_1)

    assert first == second


@pytest.mark.asyncio
async def test_same_steward_new_shift_gets_new_ref(session):
    first_night = await get_or_create_steward_ref(session, ANNA, NIGHT_1)
    second_night = await get_or_create_steward_ref(session, ANNA, NIGHT_2)

    assert first_night != second_night


@pytest.mark.asyncio
async def test_different_stewards_same_shift_get_different_refs(session):
    anna = await get_or_create_steward_ref(session, ANNA, NIGHT_1)
    bo = await get_or_create_steward_ref(session, BO, NIGHT_1)

    assert anna != bo


@pytest.mark.asyncio
async def test_same_shift_creates_only_one_row(session):
    await get_or_create_steward_ref(session, ANNA, NIGHT_1)
    await get_or_create_steward_ref(session, ANNA, NIGHT_1)

    rows = (await session.exec(select(StewardIdentity))).all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_new_row_stores_android_id_and_is_not_anonymised(session):
    ref = await get_or_create_steward_ref(session, ANNA, NIGHT_1)

    row = await session.get(StewardIdentity, ref)
    assert row is not None
    assert row.android_id == ANNA
    assert row.shift_start == NIGHT_1
    assert row.anonymised_at is None
