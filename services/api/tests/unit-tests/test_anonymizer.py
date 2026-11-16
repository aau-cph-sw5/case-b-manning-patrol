from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import AdjustmentAuthor
from src.services.anonymizer import anonymize_old_records


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_anonymize_author_after_five_years(session):
    old_timestamp = datetime(2020, 1, 1, tzinfo=UTC)
    author = AdjustmentAuthor(
        adjustment_id=uuid4(),
        android_id=uuid4(),
        reason="Test",
        author="Test",
        server_timestamp=old_timestamp,
        source="test",
        anonymized_at=None
    )
    session.add(author)
    await session.commit()

    fake_now = datetime(2026, 1, 1, tzinfo=UTC)

    with patch('src.services.anonymizer.datetime') as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.UTC = UTC
        await anonymize_old_records(session)

    await session.refresh(author)
    assert author.android_id is None
    assert author.reason is None
    assert author.author is None
    assert author.anonymized_at == fake_now
