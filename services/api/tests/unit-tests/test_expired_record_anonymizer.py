from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import (
    AdjustmentAuthor,
    ExpiredRecord,
    ExpiredTarget,
    StewardShiftIdentity,
)
from src.services.anonymizer import anonymize_old_records

OLD_TIMESTAMP = datetime(2020, 1, 1, tzinfo=UTC)
RECENT_TIMESTAMP = datetime(2025, 6, 1, tzinfo=UTC)
FAKE_NOW = datetime(2026, 1, 1, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


async def anonymize_at(session: AsyncSession, now: datetime) -> None:
    with patch("src.services.anonymizer.datetime") as mock_dt:
        mock_dt.now.return_value = now
        mock_dt.UTC = UTC
        await anonymize_old_records(session)


async def add_identity(
    session: AsyncSession, shift_start: datetime
) -> StewardShiftIdentity:
    identity = StewardShiftIdentity(android_id=uuid4(), shift_start=shift_start)
    session.add(identity)
    await session.commit()
    await session.refresh(identity)
    return identity


async def add_author(
    session: AsyncSession, server_timestamp: datetime
) -> AdjustmentAuthor:
    author = AdjustmentAuthor(
        adjustment_id=uuid4(),
        android_id=uuid4(),
        reason="Test",
        author="Test",
        server_timestamp=server_timestamp,
        source="test",
    )
    session.add(author)
    await session.commit()
    await session.refresh(author)
    return author


@pytest.mark.asyncio
async def test_expired_record_written_for_old_identity(session):
    identity = await add_identity(session, OLD_TIMESTAMP)
    steward_ref = identity.steward_ref

    await anonymize_at(session, FAKE_NOW)

    records = (await session.exec(select(ExpiredRecord))).all()
    assert len(records) == 1
    assert records[0].target == ExpiredTarget.STEWARD_SHIFT_IDENTITY
    assert records[0].record_id == steward_ref
    assert records[0].server_timestamp == FAKE_NOW
    assert records[0].source == "anonymizer"


@pytest.mark.asyncio
async def test_expired_record_written_for_old_author(session):
    author = await add_author(session, OLD_TIMESTAMP)
    adjustment_id = author.adjustment_id

    await anonymize_at(session, FAKE_NOW)

    records = (await session.exec(select(ExpiredRecord))).all()
    assert len(records) == 1
    assert records[0].target == ExpiredTarget.ADJUSTMENT_AUTHOR
    assert records[0].record_id == adjustment_id


@pytest.mark.asyncio
async def test_no_expired_record_for_recent_records(session):
    await add_identity(session, RECENT_TIMESTAMP)
    await add_author(session, RECENT_TIMESTAMP)

    await anonymize_at(session, FAKE_NOW)

    assert (await session.exec(select(ExpiredRecord))).all() == []


@pytest.mark.asyncio
async def test_no_duplicate_expired_record_on_second_run(session):
    await add_identity(session, OLD_TIMESTAMP)

    await anonymize_at(session, FAKE_NOW)
    await anonymize_at(session, datetime(2027, 1, 1, tzinfo=UTC))

    assert len((await session.exec(select(ExpiredRecord))).all()) == 1


@pytest.mark.asyncio
async def test_expired_record_never_stores_android_id(session):
    identity = await add_identity(session, OLD_TIMESTAMP)
    android_id = str(identity.android_id)

    await anonymize_at(session, FAKE_NOW)

    records = (await session.exec(select(ExpiredRecord))).all()
    stored_values = {
        str(value) for row in records for value in row.model_dump().values()
        }
    assert android_id not in stored_values
