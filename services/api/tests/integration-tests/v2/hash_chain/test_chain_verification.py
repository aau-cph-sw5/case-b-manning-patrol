"""Integration test for verifying a stored hash chain.

Saves events and their chain links in a real database, then edits or deletes
an event row directly, the way someone with database access could. The chain
is loaded again in a fresh session and verified, which must report the first
link that no longer matches its entry.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import Executable
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.adjustment import CorrectedFact
from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName
from src.db.repository.adjustment import get_adjustment
from src.db.repository.event import get_event
from src.domain.event import EventType
from src.services.event_store.event_producer import EventProducer
from src.services.hash_chain.chain_loader import ChainLoader
from src.services.hash_chain.chain_verifier import (
    ChainBreak,
    ChainBreakReason,
    ChainVerifier,
)

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


async def save_adjustments(db_engine: AsyncEngine) -> list[UUID]:
    """Append two adjustments through ``EventProducer`` and return their ids.

    The first corrects a saved event; the second has no target event and no
    beacon, so the nullable columns are stored and hashed too.
    """
    [target_event_id] = await save_chain(db_engine, length=1)
    fact = CorrectedFact(fact_type=EventType.STOP_EVENT, occurred_at=DEVICE_AT)
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        producer = EventProducer(session, source="test")
        targeted = await producer.append_adjustment(
            STEWARD, fact, "missed stop", "supervisor", target_event_id
        )
        untargeted = await producer.append_adjustment(
            STEWARD, fact, "late stop", "supervisor"
        )
    return [targeted.adjustment_id, untargeted.adjustment_id]


async def verify_stored_chain(
    db_engine: AsyncEngine, chain: ChainName = ChainName.EVENTS
) -> ChainBreak | None:
    """Load one chain in a fresh session and verify it."""
    async with AsyncSession(db_engine) as session:
        linked_entries = await ChainLoader.load(session, chain)
    return ChainVerifier.verify(linked_entries)


def edit_event(event_id: UUID) -> Executable:
    """Return a statement that changes a hashed column of one event."""
    return (
        update(Event).where(col(Event.event_id) == event_id).values(source="tampered")
    )


def delete_event(event_id: UUID) -> Executable:
    """Return a statement that removes one event row."""
    return delete(Event).where(col(Event.event_id) == event_id)


async def test_untouched_chain_has_no_break(db_engine: AsyncEngine) -> None:
    await save_chain(db_engine)

    assert await verify_stored_chain(db_engine) is None


async def stored_unlinked_count(
    db_engine: AsyncEngine, chain: ChainName = ChainName.EVENTS
) -> int:
    """Count the entries without a link in ``chain`` in a fresh session."""
    async with AsyncSession(db_engine) as session:
        return await ChainLoader.count_unlinked(session, chain)


async def test_untouched_chain_has_no_unlinked_entries(db_engine: AsyncEngine) -> None:
    await save_chain(db_engine)

    assert await stored_unlinked_count(db_engine) == 0


async def test_event_inserted_without_a_link_is_counted(
    db_engine: AsyncEngine,
) -> None:
    [event_id] = await save_chain(db_engine, length=1)
    async with AsyncSession(db_engine) as session:
        saved = await get_event(session, event_id)
        session.add(Event.model_validate(saved.model_dump() | {"event_id": uuid4()}))
        await session.commit()

    assert await stored_unlinked_count(db_engine) == 1


async def test_adjustment_inserted_without_a_link_is_counted(
    db_engine: AsyncEngine,
) -> None:
    [adjustment_id, _] = await save_adjustments(db_engine)
    async with AsyncSession(db_engine) as session:
        saved = await get_adjustment(session, adjustment_id)
        unlinked_copy = saved.model_dump() | {"adjustment_id": uuid4()}
        session.add(Adjustment.model_validate(unlinked_copy))
        await session.commit()

    assert await stored_unlinked_count(db_engine, ChainName.ADJUSTMENTS) == 1


async def test_untouched_adjustments_chain_has_no_break(
    db_engine: AsyncEngine,
) -> None:
    await save_adjustments(db_engine)

    assert await verify_stored_chain(db_engine, ChainName.ADJUSTMENTS) is None


@pytest.mark.parametrize(
    ("tamper", "reason"),
    [
        pytest.param(edit_event, ChainBreakReason.CONTENT_MISMATCH, id="edited"),
        pytest.param(delete_event, ChainBreakReason.ENTRY_MISSING, id="deleted"),
    ],
)
async def test_tampered_event_breaks_the_chain_at_its_link(
    db_engine: AsyncEngine,
    tamper: Callable[[UUID], Executable],
    reason: ChainBreakReason,
) -> None:
    event_ids = await save_chain(db_engine)

    async with db_engine.begin() as conn:
        await conn.execute(tamper(event_ids[1]))

    result = await verify_stored_chain(db_engine)

    assert result is not None
    assert result.link.record_id == event_ids[1]
    assert result.reason == reason
