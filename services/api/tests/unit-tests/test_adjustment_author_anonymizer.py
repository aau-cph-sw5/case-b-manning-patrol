from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import NamedTuple
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import (
    Adjustment,
    AdjustmentAuthor,
    Event,
    ExpiredRecord,
    ExpiredTarget,
    StewardShiftIdentity,
)
from src.domain.event import EventType
from src.services.anonymizer import anonymize_old_records

OLD_TIMESTAMP = datetime(2020, 1, 1, tzinfo=UTC)
RECENT_TIMESTAMP = datetime(2025, 6, 1, tzinfo=UTC)
FAKE_NOW = datetime(2026, 1, 1, tzinfo=UTC)


class Correction(NamedTuple):
    """A stored chain of one identity, one event and a recent correction."""

    identity: StewardShiftIdentity
    adjustment_id: UUID
    author: AdjustmentAuthor


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


async def add_event(
    session: AsyncSession, steward_ref: UUID, device_timestamp: datetime
) -> UUID:
    event_id = uuid4()
    session.add(
        Event(
            event_id=event_id,
            event_type=EventType.CONNECT_EVENT,
            steward_ref=steward_ref,
            beacon_id=uuid4(),
            device_timestamp=device_timestamp,
            server_timestamp=device_timestamp,
            source="test",
        )
    )
    await session.commit()
    return event_id


async def add_adjustment(
    session: AsyncSession,
    target_event_id: UUID | None,
    corrected_occured_at: datetime,
    server_timestamp: datetime,
) -> UUID:
    adjustment_id = uuid4()
    session.add(
        Adjustment(
            adjustment_id=adjustment_id,
            target_event_id=target_event_id,
            server_timestamp=server_timestamp,
            source="test",
            corrected_fact_type=EventType.CONNECT_EVENT,
            corrected_beacon_id=uuid4(),
            corrected_occured_at=corrected_occured_at,
        )
    )
    await session.commit()
    return adjustment_id


async def add_author(
    session: AsyncSession, adjustment_id: UUID, server_timestamp: datetime
) -> AdjustmentAuthor:
    author = AdjustmentAuthor(
        adjustment_id=adjustment_id,
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


async def add_correction(
    session: AsyncSession,
    *,
    shift_start: datetime,
    event_at: datetime,
    corrected_at: datetime,
) -> Correction:
    """Insert a correction made now as one identity-event-adjustment chain.

    Only the three timestamps the caller passes vary; the adjustment and
    its author row are always recent, so the test that calls this controls
    exactly which rule of the anonymizer can fire.
    """
    identity = await add_identity(session, shift_start)
    event_id = await add_event(session, identity.steward_ref, event_at)
    adjustment_id = await add_adjustment(
        session,
        target_event_id=event_id,
        corrected_occured_at=corrected_at,
        server_timestamp=RECENT_TIMESTAMP,
    )
    author = await add_author(session, adjustment_id, RECENT_TIMESTAMP)
    return Correction(identity, adjustment_id, author)


@pytest.mark.asyncio
async def test_anonymize_author_after_five_years(session):
    author = await add_author(session, uuid4(), OLD_TIMESTAMP)

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(author)
    assert author.android_id is None
    assert author.reason is None
    assert author.author is None
    assert author.anonymized_at == FAKE_NOW


@pytest.mark.asyncio
async def test_author_anonymized_when_target_event_is_old(session):
    chain = await add_correction(
        session,
        shift_start=RECENT_TIMESTAMP,
        event_at=OLD_TIMESTAMP,
        corrected_at=RECENT_TIMESTAMP,
    )
    author = chain.author

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(author)
    assert author.android_id is None
    assert author.reason is None
    assert author.author is None
    assert author.anonymized_at == FAKE_NOW


@pytest.mark.asyncio
async def test_author_kept_when_target_event_is_recent(session):
    chain = await add_correction(
        session,
        shift_start=RECENT_TIMESTAMP,
        event_at=RECENT_TIMESTAMP,
        corrected_at=RECENT_TIMESTAMP,
    )
    author = chain.author
    android_id = author.android_id

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(author)
    assert author.android_id == android_id
    assert author.anonymized_at is None


@pytest.mark.asyncio
async def test_author_and_identity_expire_in_same_run(session):
    chain = await add_correction(
        session,
        shift_start=OLD_TIMESTAMP,
        event_at=OLD_TIMESTAMP,
        corrected_at=OLD_TIMESTAMP,
    )

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(chain.identity)
    await session.refresh(chain.author)
    assert chain.identity.anonymized_at == FAKE_NOW
    assert chain.author.anonymized_at == FAKE_NOW

    records = (await session.exec(select(ExpiredRecord))).all()
    assert {(r.target, r.record_id) for r in records} == {
        (ExpiredTarget.STEWARD_SHIFT_IDENTITY, chain.identity.steward_ref),
        (ExpiredTarget.ADJUSTMENT_AUTHOR, chain.adjustment_id),
    }

    await anonymize_at(session, datetime(2027, 1, 1, tzinfo=UTC))

    await session.refresh(chain.author)
    assert chain.author.anonymized_at == FAKE_NOW
    assert len((await session.exec(select(ExpiredRecord))).all()) == 2


@pytest.mark.asyncio
async def test_author_anonymized_when_corrected_fact_is_old(session):
    adjustment_id = await add_adjustment(
        session,
        target_event_id=None,
        corrected_occured_at=OLD_TIMESTAMP,
        server_timestamp=RECENT_TIMESTAMP,
    )
    author = await add_author(session, adjustment_id, RECENT_TIMESTAMP)

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(author)
    assert author.android_id is None
    assert author.reason is None
    assert author.author is None
    assert author.anonymized_at == FAKE_NOW


@pytest.mark.asyncio
async def test_author_kept_when_corrected_fact_is_recent(session):
    adjustment_id = await add_adjustment(
        session,
        target_event_id=None,
        corrected_occured_at=RECENT_TIMESTAMP,
        server_timestamp=RECENT_TIMESTAMP,
    )
    author = await add_author(session, adjustment_id, RECENT_TIMESTAMP)
    android_id = author.android_id

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(author)
    assert author.android_id == android_id
    assert author.anonymized_at is None
