"""Tests for POST /api/v2/patrol-session/stop (patrol-session-event)."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.api.v2.dependencies import get_session
from src.db.repository import event
from src.domain.event import EventType
from src.main import app
from src.services.event_producer import EventProducer

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
TIMESTAMP = "2026-09-21T10:00:00+00:00"
STEWART_ANDROID_ID = UUID(ANDROID_ID)
BEACON_1_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
BEACON_2_ID = UUID("550e8400-e29b-41d4-a716-446655440002")
BEACON_3_ID = UUID("550e8400-e29b-41d4-a716-446655440003")


def test_patrol_session_stop_returns_201_for_valid_event(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 201


def test_patrol_session_stop_records_the_stop_event(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    event = response.json()
    assert event["event_type"] == "shift_stop"
    assert event["android_id"] == ANDROID_ID
    assert event["beacon_id"] is None
    assert UUID(event["event_id"])
    assert datetime.fromisoformat(event["server_timestamp"])
    device_timestamp = datetime.fromisoformat(event["device_timestamp"])
    assert device_timestamp == datetime.fromisoformat(TIMESTAMP)


def test_patrol_session_stop_rejects_missing_android_id(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"timestamp": TIMESTAMP},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_patrol_session_stop_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_patrol_session_stop_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID, "timestamp": "not-a-timestamp"},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


@pytest.mark.asyncio
async def test_patrol_session_stop_closes_open_connections(client: TestClient):
    started_at = datetime(2026, 10, 9, 10, 0, tzinfo=UTC)
    stopped_at = started_at + timedelta(hours=2)
    get_test_session = app.dependency_overrides[get_session]

    async with asynccontextmanager(get_test_session)() as session:
        producer = EventProducer(session, source="test")
        for beacon_id, timestamp in [
            (BEACON_1_ID, started_at),
            (BEACON_2_ID, started_at + timedelta(minutes=30)),
            (BEACON_3_ID, started_at - timedelta(hours=1)),
        ]:
            await producer.append_event(
                event_type=EventType.CONNECT_EVENT,
                android_id=STEWART_ANDROID_ID,
                beacon_id=beacon_id,
                device_timestamp=timestamp,
            )
        await producer.append_event(
            event_type=EventType.DISCONNECT_EVENT,
            android_id=STEWART_ANDROID_ID,
            beacon_id=BEACON_3_ID,
            device_timestamp=started_at,
        )

    response = client.post(
        "/api/v2/patrol-session/stop",
        json={
            "android_id": ANDROID_ID,
            "timestamp": stopped_at.isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json()["event_type"] == "shift_stop"

    async with asynccontextmanager(get_test_session)() as session:
        assert await event.get_open_connections(session, STEWART_ANDROID_ID) == []

        all_events = await event.get_events(session)
        disconnects = [
            event
            for event in all_events
            if event.event_type == EventType.DISCONNECT_EVENT
        ]
        closed = [
            disconnect_event
            for disconnect_event in disconnects
            if disconnect_event.beacon_id in {BEACON_1_ID, BEACON_2_ID}
        ]
        assert {closed_connection.beacon_id for closed_connection in closed} == {
            BEACON_1_ID,
            BEACON_2_ID,
        }
        assert all(
            closed_connection.device_timestamp.replace(tzinfo=None)
            == stopped_at.replace(tzinfo=None)
            for closed_connection in closed
        )
