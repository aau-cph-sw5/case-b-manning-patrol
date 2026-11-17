"""Integration test for verifying a stored hash chain.

Saves events and their chain links in a real database, then edits or deletes
an event row directly, the way someone with database access could. The chain
is loaded again in a fresh session and verified, which must report the first
link that no longer matches its entry.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

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


def edit_adjustment(adjustment_id: UUID) -> Executable:
    """Return a statement that changes a hashed column of one adjustment."""
    return (
        update(Adjustment)
        .where(col(Adjustment.adjustment_id) == adjustment_id)
        .values(reason="tampered")
    )


async def test_untouched_chain_has_no_break(db_engine: AsyncEngine) -> None:
    await save_chain(db_engine)

    assert await verify_stored_chain(db_engine) is None


async def test_untouched_adjustments_chain_has_no_break(
    db_engine: AsyncEngine,
) -> None:
    await save_adjustments(db_engine)

    assert await verify_stored_chain(db_engine, ChainName.ADJUSTMENTS) is None


@pytest.mark.parametrize(
    ("save", "chain", "tamper", "reason"),
    [
        pytest.param(
            save_chain,
            ChainName.EVENTS,
            edit_event,
            ChainBreakReason.CONTENT_MISMATCH,
            id="event-edited",
        ),
        pytest.param(
            save_chain,
            ChainName.EVENTS,
            delete_event,
            ChainBreakReason.ENTRY_MISSING,
            id="event-deleted",
        ),
        pytest.param(
            save_adjustments,
            ChainName.ADJUSTMENTS,
            edit_adjustment,
            ChainBreakReason.CONTENT_MISMATCH,
            id="adjustment-edited",
        ),
    ],
)
async def test_tampered_row_breaks_the_chain_at_its_link(
    db_engine: AsyncEngine,
    save: Callable[[AsyncEngine], Awaitable[list[UUID]]],
    chain: ChainName,
    tamper: Callable[[UUID], Executable],
    reason: ChainBreakReason,
) -> None:
    record_ids = await save(db_engine)

    async with db_engine.begin() as conn:
        await conn.execute(tamper(record_ids[1]))

    result = await verify_stored_chain(db_engine, chain)

    assert result is not None
    assert result.link.record_id == record_ids[1]
    assert result.reason == reason
