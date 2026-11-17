"""Unit tests for ChainLinker against a real in-memory database session.

``ChainLinker`` reads the chain's current head hash from the database itself,
so each test runs against an in-memory SQLite database seeded through
``insert_link``.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.repository.integrity_chain_link import insert_link
from src.domain.event import EventRecord, EventType
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.entry_hasher import EntryHasher
from src.services.hash_chain.entry_stringifier import EntryStringifier
from src.services.shared.event_record_mapper import EventRecordMapper

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
ADJUSTMENT_ID = UUID("20000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
CORRECTED_AT = datetime(2026, 5, 30, 3, 10, tzinfo=UTC)
OTHER_HEAD_HASH = "f" * 64

GOLDEN_CONTENT_HASH = "c6fabbf488b9a9bc5826dab2b88c7083bd2aab7accbefa34cbb3702071621ee6"
"""Content hash of make_event(); same as in test_entry_hasher.py."""
GOLDEN_HEAD_HASH = "23d96ff06016161032a1777d37ef10893849f45aadc451364df21cad7c34f44e"
"""Head hash of make_event() linked onto EntryHasher.GENESIS_HASH."""
GOLDEN_HEAD_HASH_AFTER_F = (
    "96c40c6591f7f0960244ca958580a93e8a24c291f1d377aea929c312a4667b2b"
)
"""Head hash of make_event() linked onto OTHER_HEAD_HASH, as in test_entry_hasher.py."""


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


def make_event(source: str = "test") -> Event:
    return Event(
        event_id=EVENT_ID,
        event_type=EventType.CONNECT_EVENT,
        android_id=STEWARD,
        beacon_id=BEACON,
        device_timestamp=DEVICE_AT,
        server_timestamp=SERVER_AT,
        source=source,
    )


def make_adjustment() -> Adjustment:
    return Adjustment(
        adjustment_id=ADJUSTMENT_ID,
        target_event_id=EVENT_ID,
        android_id=STEWARD,
        reason="missed stop",
        author="supervisor",
        server_timestamp=SERVER_AT,
        source="test",
        corrected_fact_type=EventType.STOP_EVENT,
        corrected_beacon_id=None,
        corrected_occured_at=CORRECTED_AT,
    )


def make_stored_link(chain: ChainName, head_hash: str) -> IntegrityChainLink:
    """Build a link row as the database would store it, to seed a chain head."""
    return IntegrityChainLink(
        chain=chain,
        record_id=uuid4(),
        prev_hash=EntryHasher.GENESIS_HASH,
        content_hash="c" * 64,
        head_hash=head_hash,
        server_timestamp=SERVER_AT,
    )


async def test_event_on_an_empty_chain_matches_the_golden_hashes(
    session: AsyncSession,
) -> None:
    link = await ChainLinker(session, make_event()).link(source="test")

    assert link.chain == ChainName.EVENTS
    assert link.record_id == EVENT_ID
    assert link.prev_hash == EntryHasher.GENESIS_HASH
    assert link.content_hash == GOLDEN_CONTENT_HASH
    assert link.head_hash == GOLDEN_HEAD_HASH


async def test_link_hashes_the_stringified_entry(session: AsyncSession) -> None:
    adjustment = make_adjustment()
    expected = EntryHasher.hash_text(
        EntryStringifier.stringify_entry(adjustment), EntryHasher.GENESIS_HASH
    )

    link = await ChainLinker(session, adjustment).link(source="test")

    assert link.chain == ChainName.ADJUSTMENTS
    assert link.record_id == ADJUSTMENT_ID
    assert link.prev_hash == expected.prev_hash
    assert link.content_hash == expected.content_hash
    assert link.head_hash == expected.head_hash


async def test_same_input_gives_the_same_link(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ChainLinker, "_now_utc", staticmethod(lambda: SERVER_AT))

    first = await ChainLinker(session, make_event()).link(source="test")
    second = await ChainLinker(session, make_event()).link(source="test")

    assert first == second


async def test_changing_a_field_changes_the_hashes(session: AsyncSession) -> None:
    original = await ChainLinker(session, make_event()).link(source="test")
    tampered = await ChainLinker(session, make_event(source="tampered")).link(
        source="test"
    )

    assert tampered.content_hash != original.content_hash
    assert tampered.head_hash != original.head_hash


async def test_link_chains_onto_the_current_head(session: AsyncSession) -> None:
    await insert_link(session, make_stored_link(ChainName.EVENTS, OTHER_HEAD_HASH))

    link = await ChainLinker(session, make_event()).link(source="test")

    assert link.prev_hash == OTHER_HEAD_HASH
    assert link.content_hash == GOLDEN_CONTENT_HASH
    assert link.head_hash == GOLDEN_HEAD_HASH_AFTER_F


async def test_head_hash_is_read_per_chain(session: AsyncSession) -> None:
    await insert_link(session, make_stored_link(ChainName.EVENTS, OTHER_HEAD_HASH))

    event_link = await ChainLinker(session, make_event()).link(source="test")
    adjustment_link = await ChainLinker(session, make_adjustment()).link(source="test")

    assert event_link.prev_hash == OTHER_HEAD_HASH
    assert adjustment_link.prev_hash == EntryHasher.GENESIS_HASH


async def test_server_timestamp_is_now_in_utc(session: AsyncSession) -> None:
    before = datetime.now(UTC)

    link = await ChainLinker(session, make_event()).link(source="test")

    assert before <= link.server_timestamp <= datetime.now(UTC)


async def test_domain_event_record_is_rejected(session: AsyncSession) -> None:
    record: EventRecord = EventRecordMapper.to_record(make_event())
    linker = ChainLinker(session, record)  # ty: ignore[invalid-argument-type]

    with pytest.raises(TypeError, match="EventRecord"):
        await linker.link(source="test")


async def test_malformed_stored_head_hash_is_rejected(session: AsyncSession) -> None:
    await insert_link(session, make_stored_link(ChainName.EVENTS, "abc"))

    with pytest.raises(ValueError, match="prev_hash"):
        await ChainLinker(session, make_event()).link(source="test")
