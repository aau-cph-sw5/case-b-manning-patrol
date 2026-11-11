from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.integrity_entry import IntegrityEntry
from src.db.repository import integrity_entry

TIMESTAMP = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


def make_entry(chain: str, seq: int, **overrides: Any) -> IntegrityEntry:
    """Build one chain link; hashes are fixed so heads descend from prev."""
    fields: dict[str, Any] = {
        "entry_id": uuid4(),
        "chain": chain,
        "seq": seq,
        "record_type": "event",
        "record_id": uuid4(),
        "prev_hash": f"prev-{chain}-{seq}",
        "content_hash": f"content-{chain}-{seq}",
        "head_hash": f"head-{chain}-{seq}",
        "server_timestamp": TIMESTAMP,
    }
    return IntegrityEntry(**(fields | overrides))


@pytest.mark.asyncio
async def test_head_hash_is_none_for_chain_without_links(
    session: AsyncSession,
) -> None:
    """An empty chain has no head, so the caller starts from genesis."""
    head = await integrity_entry.get_head_hash(session, "events")

    assert head is None


@pytest.mark.asyncio
async def test_head_hash_is_the_newest_link_of_the_chain(
    session: AsyncSession,
) -> None:
    """The head is the head_hash of the row with the highest seq."""
    for seq in (1, 2, 3):
        await integrity_entry.insert_entry(session, make_entry("events", seq))

    head = await integrity_entry.get_head_hash(session, "events")

    assert head == "head-events-3"


@pytest.mark.asyncio
async def test_head_hash_is_per_chain(session: AsyncSession) -> None:
    """Appending to one chain never moves the head of another."""
    await integrity_entry.insert_entry(session, make_entry("events", 1))
    await integrity_entry.insert_entry(
        session, make_entry("adjustments", 1, head_hash="head-adjustments-1")
    )
    await integrity_entry.insert_entry(session, make_entry("events", 2))

    events_head = await integrity_entry.get_head_hash(session, "events")
    adjustments_head = await integrity_entry.get_head_hash(session, "adjustments")

    assert events_head == "head-events-2"
    assert adjustments_head == "head-adjustments-1"


@pytest.mark.asyncio
async def test_get_chain_returns_links_oldest_first(
    session: AsyncSession,
) -> None:
    """Verify walks the chain in append order, so it must come back sorted."""
    links = [make_entry("events", seq) for seq in (2, 3, 1)]
    for link in links:
        await integrity_entry.insert_entry(session, link)

    chain = await integrity_entry.get_chain(session, "events")

    assert [entry.seq for entry in chain] == [1, 2, 3]
    assert chain == [links[2], links[0], links[1]]


@pytest.mark.asyncio
async def test_chain_and_seq_pair_must_be_unique(session: AsyncSession) -> None:
    """Two links cannot claim the same position in a chain."""
    await integrity_entry.insert_entry(session, make_entry("events", 1))

    with pytest.raises(IntegrityError):
        await integrity_entry.insert_entry(session, make_entry("events", 1))
    await session.rollback()

    head = await integrity_entry.get_head_hash(session, "events")
    assert head == "head-events-1"
