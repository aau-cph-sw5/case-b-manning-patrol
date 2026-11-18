"""Integration guard for the fields the hash chain stringifies.

``EntryStringifier`` hashes exactly the columns of the ``Event`` and
``Adjustment`` tables plus a ``kind`` and a ``"v"`` tag. These tests post real
events through the API into a real database and check that the stringified
rows match the live database columns and the API response, so changing the
models, the API schemas or the field lists in the stringifier fails here
instead of silently changing hashes.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.v2.dependencies import get_async_db_session
from src.api.v2.schemas.ingestion import StoredEvent
from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName
from src.db.repository.adjustment import get_adjustments
from src.db.repository.event import get_event, get_events
from src.db.repository.integrity_chain_link import get_chain
from src.main import app
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.entry_hasher import EntryHasher
from src.services.hash_chain.entry_stringifier import (
    ADJUSTMENT_FIELDS,
    EVENT_FIELDS,
    FORMAT_VERSION,
    EntryStringifier,
)

API_VERSION = "v2"
"""Version of the API under test; change here if the routes are bumped."""

API_BASE = f"/api/{API_VERSION}"
"""Base path every call below goes through."""

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
AUTHOR_ID = "880e8400-e29b-41d4-a716-446655440003"
DEVICE_AT = "2026-10-09T10:00:00+00:00"


async def _live_columns(db_engine: AsyncEngine, table: str) -> set[str]:
    """Return the columns of ``table`` as created in the test database."""
    async with db_engine.connect() as conn:
        return await conn.run_sync(
            lambda sync_conn: {
                column["name"] for column in inspect(sync_conn).get_columns(table)
            }
        )


async def test_stringified_event_covers_exactly_the_live_event_columns(
    client: TestClient, db_engine: AsyncEngine
) -> None:
    """A posted event stringifies to exactly the columns the database has."""
    response = client.post(
        f"{API_BASE}/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": DEVICE_AT,
        },
    )
    assert response.status_code == 201

    event_table = Event.__table__.name  # ty: ignore[unresolved-attribute]
    columns = await _live_columns(db_engine, event_table)
    get_test_session = app.dependency_overrides[get_async_db_session]
    async with asynccontextmanager(get_test_session)() as session:
        events = await get_events(session)

    assert len(events) == 1
    payload = json.loads(EntryStringifier.stringify_entry(events[0]))
    assert set(payload) == columns | {"kind", "v"}
    assert set(EVENT_FIELDS) == columns
    assert payload["kind"] == "event"
    assert payload["v"] == FORMAT_VERSION


async def test_stringified_adjustment_covers_exactly_the_live_columns(
    client: TestClient, db_engine: AsyncEngine
) -> None:
    """A posted adjustment stringifies to exactly the columns the database has."""
    response = client.post(
        f"{API_BASE}/adjustment",
        json={
            "android_id": ANDROID_ID,
            "corrected_fact": {
                "fact_type": "connect",
                "beacon_id": BEACON_ID,
                "occurred_at": DEVICE_AT,
            },
            "reason": "Beacon never fired on arrival.",
            "author": AUTHOR_ID,
        },
    )
    assert response.status_code == 201

    adjustment_table = Adjustment.__table__.name  # ty: ignore[unresolved-attribute]
    columns = await _live_columns(db_engine, adjustment_table)
    get_test_session = app.dependency_overrides[get_async_db_session]
    async with asynccontextmanager(get_test_session)() as session:
        adjustments = await get_adjustments(session)

    assert len(adjustments) == 1
    payload = json.loads(EntryStringifier.stringify_entry(adjustments[0]))
    assert set(payload) == columns | {"kind", "v"}
    assert set(ADJUSTMENT_FIELDS) == columns
    assert payload["kind"] == "adjustment"
    assert payload["v"] == FORMAT_VERSION


async def test_posted_disconnect_response_row_and_hash_agree(
    client: TestClient,
) -> None:
    """The 201 response, the stored row and its chain link carry the same fields."""
    response = client.post(
        f"{API_BASE}/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": DEVICE_AT,
        },
    )
    assert response.status_code == 201
    stored = response.json()
    assert set(stored) == set(StoredEvent.model_fields)

    get_test_session = app.dependency_overrides[get_async_db_session]
    async with asynccontextmanager(get_test_session)() as session:
        row = await get_event(session, UUID(stored["event_id"]))
        stored_links = await get_chain(session, ChainName.EVENTS)
        relinked = await ChainLinker(session, row).link(source=stored["source"])

    payload = json.loads(EntryStringifier.stringify_entry(row))
    assert set(payload) == set(EVENT_FIELDS) | {"kind", "v"}
    assert payload["event_id"] == stored["event_id"]
    assert payload["event_type"] == stored["event_type"]
    assert payload["steward_ref"] == str(row.steward_ref)
    assert stored["android_id"] == ANDROID_ID
    assert payload["beacon_id"] == stored["beacon_id"]
    assert payload["source"] == stored["source"]
    assert datetime.fromisoformat(
        payload["device_timestamp"]
    ) == datetime.fromisoformat(stored["device_timestamp"])
    assert datetime.fromisoformat(
        payload["server_timestamp"]
    ) == datetime.fromisoformat(stored["server_timestamp"])

    stored_link = next(link for link in stored_links if link.record_id == row.event_id)
    assert stored_link.chain == ChainName.EVENTS
    assert stored_link.prev_hash == EntryHasher.GENESIS_HASH
    assert (
        stored_link.content_hash
        == EntryHasher.hash_text(
            EntryStringifier.stringify_entry(row), EntryHasher.GENESIS_HASH
        ).content_hash
    )
    assert len(stored_link.head_hash) == 64

    assert relinked.record_id == row.event_id
    assert relinked.prev_hash == stored_link.head_hash
    assert relinked.content_hash == stored_link.content_hash
    assert (
        relinked.head_hash
        == EntryHasher.hash_text(
            EntryStringifier.stringify_entry(row), stored_link.head_hash
        ).head_hash
    )
