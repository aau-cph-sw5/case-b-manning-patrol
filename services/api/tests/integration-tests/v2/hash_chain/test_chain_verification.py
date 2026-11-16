"""Integration test for verifying a stored hash chain.

Saves events and their chain links in a real database, then edits or deletes
an event row directly, the way someone with database access could. The chain
is loaded again in a fresh session and verified, which must report the first
link that no longer matches its entry.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName
from src.domain.event import EventType
from src.services.event_store.event_producer import EventProducer
from src.services.hash_chain.chain_loader import ChainLoader
from src.services.hash_chain.chain_verifier import ChainBreakReason, ChainVerifier

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)


async def save_chain(db_engine: AsyncEngine, length: int = 3) -> list[UUID]:
    """Append ``length`` events through ``EventProducer`` and return their ids."""
    event_ids: list[UUID] = []
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        producer = EventProducer(session, source="test")
        for _ in range(length):
            event = await producer.append_event(
                event_type=EventType.CONNECT_EVENT,
                android_id=STEWARD,
                beacon_id=BEACON,
                device_timestamp=DEVICE_AT,
            )
            event_ids.append(event.event_id)
    return event_ids


async def verify_stored_chain(db_engine: AsyncEngine):
    """Load the events chain in a fresh session and verify it."""
    async with AsyncSession(db_engine) as session:
        linked_entries = await ChainLoader.load(session, ChainName.EVENTS)
    return ChainVerifier.verify(linked_entries)


async def test_untouched_chain_has_no_break(db_engine: AsyncEngine) -> None:
    await save_chain(db_engine)

    assert await verify_stored_chain(db_engine) is None


async def test_event_edited_in_the_database_breaks_the_chain_at_its_link(
    db_engine: AsyncEngine,
) -> None:
    event_ids = await save_chain(db_engine)

    async with db_engine.begin() as conn:
        await conn.execute(
            update(Event)
            .where(col(Event.event_id) == event_ids[1])
            .values(source="tampered")
        )

    result = await verify_stored_chain(db_engine)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.CONTENT_MISMATCH


async def test_event_deleted_from_the_database_breaks_the_chain_at_its_link(
    db_engine: AsyncEngine,
) -> None:
    event_ids = await save_chain(db_engine)

    async with db_engine.begin() as conn:
        await conn.execute(delete(Event).where(col(Event.event_id) == event_ids[1]))

    result = await verify_stored_chain(db_engine)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.ENTRY_MISSING
