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

from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.repository import integrity_chain_link

TIMESTAMP = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


def make_link(
    chain: ChainName = ChainName.EVENTS,
    seq: int = 1,
    **overrides: Any,
) -> IntegrityChainLink:
    """Build one chain link; hashes are fixed so heads descend from prev."""
    fields: dict[str, Any] = {
        "entry_id": uuid4(),
        "chain": chain,
        "seq": seq,
        "record_id": uuid4(),
        "prev_hash": f"prev-{chain.value}-{seq}",
        "content_hash": f"content-{chain.value}-{seq}",
        "head_hash": f"head-{chain.value}-{seq}",
        "server_timestamp": TIMESTAMP,
    }
    return IntegrityChainLink(**(fields | overrides))


@pytest.mark.asyncio
async def test_head_hash_is_none_for_chain_without_links(
    session: AsyncSession,
) -> None:
    """An empty chain has no head, so the caller starts from genesis."""
    head = await integrity_chain_link.get_head_hash(session, ChainName.EVENTS)

    assert head is None


@pytest.mark.asyncio
async def test_head_hash_is_the_newest_link_of_the_chain(
    session: AsyncSession,
) -> None:
    """The head is the head_hash of the row with the highest seq."""
    for seq in (1, 2, 3):
        await integrity_chain_link.insert_link(session, make_link(seq=seq))

    head = await integrity_chain_link.get_head_hash(session, ChainName.EVENTS)

    assert head == "head-events-3"


@pytest.mark.asyncio
async def test_head_hash_is_per_chain(session: AsyncSession) -> None:
    """Appending to one chain never moves the head of another."""
    await integrity_chain_link.insert_link(session, make_link())
    await integrity_chain_link.insert_link(
        session, make_link(ChainName.ADJUSTMENTS, 1, head_hash="head-adjustments-1")
    )
    await integrity_chain_link.insert_link(session, make_link(seq=2))

    events_head = await integrity_chain_link.get_head_hash(session, ChainName.EVENTS)
    adjustments_head = await integrity_chain_link.get_head_hash(
        session, ChainName.ADJUSTMENTS
    )

    assert events_head == "head-events-2"
    assert adjustments_head == "head-adjustments-1"


@pytest.mark.asyncio
async def test_get_chain_returns_links_oldest_first(
    session: AsyncSession,
) -> None:
    """Verify walks the chain in append order, so it must come back sorted."""
    links = [make_link(seq=seq) for seq in (2, 3, 1)]
    for link in links:
        await integrity_chain_link.insert_link(session, link)

    chain = await integrity_chain_link.get_chain(session, ChainName.EVENTS)

    assert [link.seq for link in chain] == [1, 2, 3]
    assert chain == [links[2], links[0], links[1]]


@pytest.mark.asyncio
async def test_chain_and_seq_pair_must_be_unique(session: AsyncSession) -> None:
    """Two links cannot claim the same position in a chain."""
    await integrity_chain_link.insert_link(session, make_link())

    with pytest.raises(IntegrityError):
        await integrity_chain_link.insert_link(session, make_link())
    await session.rollback()

    head = await integrity_chain_link.get_head_hash(session, ChainName.EVENTS)
    assert head == "head-events-1"
