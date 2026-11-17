"""Tests for POST /api/v2/connection/disconnect (connection-event)."""

from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

import pytest_asyncio

from src.api.v2.dependencies import get_async_db_session
from src.db.ingest import load_reference_data
from src.main import app

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "660e8400-e29b-41d4-a716-446655440002"  # STN-002 platform
TIMESTAMP = "2026-09-21T10:00:00+00:00"


@pytest_asyncio.fixture(autouse=True)
async def reference_data():
    get_test_session = app.dependency_overrides[get_async_db_session]
    async with asynccontextmanager(get_test_session)() as session:
        await load_reference_data(session)


def test_disconnect_returns_201_for_valid_connection_event(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    assert response.status_code == 201


def test_disconnect_records_the_disconnection_event(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    event = response.json()
    assert event["event_type"] == "disconnect"
    assert event["android_id"] == ANDROID_ID
    assert event["beacon_id"] == BEACON_ID
    assert UUID(event["event_id"])
    assert datetime.fromisoformat(event["server_timestamp"])
    device_timestamp = datetime.fromisoformat(event["device_timestamp"])
    assert device_timestamp == datetime.fromisoformat(TIMESTAMP)


def test_disconnect_rejects_missing_android_id(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"beacon_id": BEACON_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_disconnect_rejects_missing_beacon_id(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_disconnect_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"android_id": ANDROID_ID, "beacon_id": BEACON_ID},
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_disconnect_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": "not-a-timestamp",
        },
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_disconnect_rejects_non_uuid_android_id(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": "not-a-uuid",
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
