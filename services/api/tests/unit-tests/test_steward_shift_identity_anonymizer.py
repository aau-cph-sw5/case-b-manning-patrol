from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Event, StewardShiftIdentity
from src.domain.event import EventType
from src.services.anonymizer import anonymize_old_records

OLD_SHIFT_START = datetime(2020, 1, 1, tzinfo=UTC)
RECENT_SHIFT_START = datetime(2025, 6, 1, tzinfo=UTC)
FAKE_NOW = datetime(2026, 1, 1, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


async def add_identity(
    session: AsyncSession, shift_start: datetime
) -> StewardShiftIdentity:
    identity = StewardShiftIdentity(android_id=uuid4(), shift_start=shift_start)
    session.add(identity)
    await session.commit()
    await session.refresh(identity)
    return identity


async def add_event(session: AsyncSession, steward_ref: UUID) -> UUID:
    event_id = uuid4()
    session.add(
        Event(
            event_id=event_id,
            event_type=EventType.CONNECT_EVENT,
            steward_ref=steward_ref,
            beacon_id=uuid4(),
            device_timestamp=OLD_SHIFT_START,
            server_timestamp=OLD_SHIFT_START,
            source="test",
        )
    )
    await session.commit()
    return event_id


async def anonymize_at(session: AsyncSession, now: datetime) -> None:
    with patch("src.services.anonymizer.datetime") as mock_dt:
        mock_dt.now.return_value = now
        mock_dt.UTC = UTC
        await anonymize_old_records(session)


@pytest.mark.asyncio
async def test_anonymize_steward_after_five_years(session):
    identity = await add_identity(session, OLD_SHIFT_START)

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(identity)
    assert identity.android_id is None
    assert identity.anonymized_at == FAKE_NOW


@pytest.mark.asyncio
async def test_steward_within_five_years_is_not_anonymized(session):
    identity = await add_identity(session, RECENT_SHIFT_START)
    android_id = identity.android_id

    await anonymize_at(session, FAKE_NOW)

    await session.refresh(identity)
    assert identity.android_id == android_id
    assert identity.anonymized_at is None


@pytest.mark.asyncio
async def test_anonymization_deletes_nothing(session):
    identity = await add_identity(session, OLD_SHIFT_START)
    steward_ref = identity.steward_ref
    event_id = await add_event(session, steward_ref)

    await anonymize_at(session, FAKE_NOW)

    identities = (await session.exec(select(StewardShiftIdentity))).all()
    events = (await session.exec(select(Event))).all()
    assert [i.steward_ref for i in identities] == [steward_ref]
    assert [e.event_id for e in events] == [event_id]


@pytest.mark.asyncio
async def test_events_still_belong_to_the_same_steward_after_anonymization(session):
    first_ref = (await add_identity(session, OLD_SHIFT_START)).steward_ref
    second_ref = (await add_identity(session, OLD_SHIFT_START)).steward_ref
    for steward_ref in (first_ref, first_ref, second_ref):
        await add_event(session, steward_ref)

    await anonymize_at(session, FAKE_NOW)

    events = (await session.exec(select(Event))).all()
    assert sorted(str(e.steward_ref) for e in events) == sorted(
        [str(first_ref), str(first_ref), str(second_ref)]
    )


@pytest.mark.asyncio
async def test_original_android_id_cannot_be_recovered(session):
    identity = await add_identity(session, OLD_SHIFT_START)
    android_id = identity.android_id
    await add_event(session, identity.steward_ref)

    await anonymize_at(session, FAKE_NOW)

    remaining = [
        *(await session.exec(select(StewardShiftIdentity))).all(),
        *(await session.exec(select(Event))).all(),
    ]
    stored_values = {
        str(value) for row in remaining for value in row.model_dump().values()
    }
    assert str(android_id) not in stored_values


@pytest.mark.asyncio
async def test_already_anonymized_steward_keeps_its_anonymization_time(session):
    identity = await add_identity(session, OLD_SHIFT_START)
    await anonymize_at(session, FAKE_NOW)

    await anonymize_at(session, datetime(2027, 1, 1, tzinfo=UTC))

    await session.refresh(identity)
    assert identity.anonymized_at == FAKE_NOW
