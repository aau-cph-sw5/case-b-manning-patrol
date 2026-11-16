"""Integration test for verifying a stored hash chain.

Saves events and their chain links in a real database, then edits or deletes
an event row directly, the way someone with database access could. The chain
is loaded again in a fresh session and verified, which must report the first
link that no longer matches its entry.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.repository.event import insert_event
from src.db.repository.integrity_chain_link import get_head_hash, insert_link
from src.domain.event import EventType
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.chain_loader import ChainLoader
from src.services.hash_chain.chain_verifier import ChainBreakReason, ChainVerifier
from src.services.hash_chain.entry_hasher import GENESIS_HASH

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)


async def save_chain(db_engine: AsyncEngine, length: int = 3) -> list[UUID]:
    """Save ``length`` events with their chain links and return the event ids."""
    event_ids: list[UUID] = []
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        for seq in range(1, length + 1):
            event = await insert_event(
                session,
                Event(
                    event_id=uuid4(),
                    event_type=EventType.CONNECT_EVENT,
                    android_id=STEWARD,
                    beacon_id=BEACON,
                    device_timestamp=DEVICE_AT,
                    server_timestamp=SERVER_AT,
                    source="test",
                ),
            )
            prev_hash = await get_head_hash(session, ChainName.EVENTS) or GENESIS_HASH
            hashed = ChainLinker.link(event, prev_hash)
            await insert_link(
                session,
                IntegrityChainLink(
                    entry_id=uuid4(),
                    chain=ChainName.EVENTS,
                    seq=seq,
                    record_id=event.event_id,
                    prev_hash=hashed.prev_hash,
                    content_hash=hashed.content_hash,
                    head_hash=hashed.head_hash,
                    server_timestamp=SERVER_AT,
                ),
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
