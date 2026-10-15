from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.routers.patrol_session import (
    PatrolSessionEvent,
    patrol_session_stop_event,
)
from src.db.repository import events
from src.main import app
from src.models.event import EventType
from src.services.producer import MainProducer


def test_connection_event_returns_created_event():
    client = TestClient(app)

    connection_response = client.post(
        app.url_path_for("connection_event"),
        json={
            "android_id": "android-1",
            "beacon_id": "beacon-1",
            "timestamp": "2026-10-02T10:00:00+00:00",
        },
    )

    disconnection_response = client.post(
        app.url_path_for("disconnection_event"),
        json={
            "android_id": "android-1",
            "beacon_id": "beacon-1",
            "timestamp": "2026-10-02T10:00:00+00:00",
        },
    )

    start_response = client.post(
        app.url_path_for("patrol_session_start_event"),
        json={
            "android_id": "android-1",
            "timestamp": "2026-10-02T10:00:00+00:00",
        },
    )

    stop_response = client.post(
        app.url_path_for("patrol_session_stop_event"),
        json={
            "android_id": "android-1",
            "timestamp": "2026-10-02T10:00:00+00:00",
        },
    )

    adjustment_response = client.post(
        app.url_path_for("adjustment_event"),
        json={
            "android_id": "android-1",
            "corrected_fact": {
                "fact_type": "connect",
                "beacon_id": "beacon-1",
                "occurred_at": "2026-10-02T10:00:00+00:00",
            },
            "reason": "Adjusted something",
            "author": "Controller-1",
        },
    )

    # Asserting Connection
    assert connection_response.status_code == 201
    connection_event = connection_response.json()
    assert connection_event["event_type"] == "connect"
    assert connection_event["actor"] == "android-1"
    assert connection_event["beacon"] == "beacon-1"
    assert connection_event["device_timestamp"] == "2026-10-02T10:00:00Z"
    assert connection_event["server_timestamp"]
    assert connection_event["event_id"]

    # Asserting Disconnection
    assert disconnection_response.status_code == 201
    disconnection_event = disconnection_response.json()
    assert disconnection_event["event_type"] == "disconnect"
    assert disconnection_event["actor"] == "android-1"
    assert disconnection_event["beacon"] == "beacon-1"
    assert disconnection_event["device_timestamp"] == "2026-10-02T10:00:00Z"
    assert disconnection_event["server_timestamp"]
    assert disconnection_event["event_id"]

    # Asserting Patrol Session Start
    assert start_response.status_code == 201
    start_event = start_response.json()
    assert start_event["event_type"] == "start"
    assert start_event["actor"] == "android-1"
    assert start_event["beacon"] is None
    assert start_event["device_timestamp"] == "2026-10-02T10:00:00Z"
    assert start_event["server_timestamp"]
    assert start_event["event_id"]

    # Asserting Patrol Session Stop
    assert stop_response.status_code == 201
    stop_event = stop_response.json()
    assert stop_event["event_type"] == "stop"
    assert stop_event["actor"] == "android-1"
    assert stop_event["beacon"] is None
    assert stop_event["device_timestamp"] == "2026-10-02T10:00:00Z"
    assert stop_event["server_timestamp"]
    assert stop_event["event_id"]

    # Asserting Adjustment
    assert adjustment_response.status_code == 201
    adjustment_event = adjustment_response.json()
    assert adjustment_event["actor"] == "android-1"
    assert adjustment_event["corrected_fact"] == {
        "fact_type": "connect",
        "beacon_id": "beacon-1",
        "occurred_at": "2026-10-02T10:00:00Z",
    }
    assert adjustment_event["reason"] == "Adjusted something"
    assert adjustment_event["server_timestamp"]
    assert adjustment_event["adjustment_id"]
    assert adjustment_event["author"] == "Controller-1"
    assert adjustment_event["target_event_id"] is None


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


async def test_patrol_session_stop_closes_open_connections(db_session):
    started_at = datetime(2026, 10, 9, 10, 0, tzinfo=UTC)
    stopped_at = started_at + timedelta(hours=2)

    for beacon_id, timestamp in [
        ("beacon-1", started_at),
        ("beacon-2", started_at + timedelta(minutes=30)),
        ("beacon-3", started_at - timedelta(hours=1)),
    ]:
        await MainProducer.append_event(
            session=db_session,
            event_type=EventType.CONNECT_EVENT,
            actor="android-1",
            beacon=beacon_id,
            device_timestamp=timestamp,
            source="test",
        )
    await MainProducer.append_event(
        session=db_session,
        event_type=EventType.DISCONNECT_EVENT,
        actor="android-1",
        beacon="beacon-3",
        device_timestamp=started_at,
        source="test",
    )

    stop_event = await patrol_session_stop_event(
        PatrolSessionEvent(android_id="android-1", timestamp=stopped_at),
        db_session,
    )

    assert stop_event.event_type == EventType.STOP_EVENT
    assert await events.get_open_connections(db_session, "android-1") == []

    all_events = await events.get_events(db_session)
    disconnects = [
        event for event in all_events if event.event_type == EventType.DISCONNECT_EVENT
    ]
    closed = [
        disconnect_event
        for disconnect_event in disconnects
        if disconnect_event.beacon in {"beacon-1", "beacon-2"}
    ]
    assert {closed_connection.beacon for closed_connection in closed} == {
        "beacon-1",
        "beacon-2",
    }
    assert all(
        closed_connection.device_timestamp.replace(tzinfo=None)
        == stopped_at.replace(tzinfo=None)
        for closed_connection in closed
    )
