"""Tests for GET /api/v2/record (patrol-record contract)."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from fastapi.testclient import TestClient

from src.api.v2.dependencies import get_async_db_session
from src.db.ingest import load_stations
from src.main import app

ANDROID_ID = "770e8400-e29b-41d4-a716-446655440001"
OTHER_ANDROID_ID = "770e8400-e29b-41d4-a716-446655440002"
BEACON_PLATFORM = "660e8400-e29b-41d4-a716-446655440001"  # STN-001 platform
BEACON_CONCOURSE = "660e8400-e29b-41d4-a716-446655440081"  # STN-001 concourse
BEACON_INTERCHANGE = "660e8400-e29b-41d4-a716-44665544000a"  # STN-010, M1+M2

SHIFT_START = datetime(2026, 10, 9, 10, 0, tzinfo=UTC)


@pytest_asyncio.fixture(autouse=True)
async def stations():
    get_test_session = app.dependency_overrides[get_async_db_session]
    async with asynccontextmanager(get_test_session)() as session:
        await load_stations(session)


def _post(
    client: TestClient,
    path: str,
    android_id: str,
    at: datetime,
    beacon_id: str | None = None,
):
    body = {"android_id": android_id, "timestamp": at.isoformat()}
    if beacon_id is not None:
        body["beacon_id"] = beacon_id
    response = client.post(f"/api/v2/{path}", json=body)
    assert response.status_code == 201
    return response


def _get_records(client: TestClient, android_id: str):
    return client.get("/api/v2/record", params={"android_id": android_id})


def test_get_records_rejects_missing_android_id(client):
    response = client.get("/api/v2/record")

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_get_records_rejects_malformed_android_id(client):
    response = client.get("/api/v2/record", params={"android_id": "not-a-uuid"})

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_get_records_empty_when_no_shift_started(client):
    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    body = response.json()
    assert body["records"] == []
    assert datetime.fromisoformat(body["time"])


def test_get_records_returns_pending_and_registered_most_recent_first(client):
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_PLATFORM,
    )
    _post(
        client,
        "connection/disconnect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=120),
        BEACON_PLATFORM,
    )
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=180),
        BEACON_CONCOURSE,
    )

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    body = response.json()
    assert datetime.fromisoformat(body["time"])
    records = body["records"]
    assert len(records) == 2

    pending = records[0]
    assert pending["android_id"] == ANDROID_ID
    assert pending["beacon_id"] == BEACON_CONCOURSE
    assert datetime.fromisoformat(pending["started_at"]) == SHIFT_START + timedelta(
        seconds=180
    )
    assert pending["ended_at"] is None
    assert pending["duration_secs"] is None
    assert pending["min_patrol_duration_secs"] == 20
    assert pending["patrolled"] is True
    assert pending["status"] == "pending"
    assert pending["area"] == {
        "area_id": "PA-001-C",
        "name": "Station 01 concourse",
        "line": ["M1"],
        "station_id": "STN-001",
        "area_type": "concourse",
    }

    registered = records[1]
    assert registered["beacon_id"] == BEACON_PLATFORM
    assert datetime.fromisoformat(registered["started_at"]) == SHIFT_START + timedelta(
        seconds=60
    )
    assert datetime.fromisoformat(registered["ended_at"]) == SHIFT_START + timedelta(
        seconds=120
    )
    assert registered["duration_secs"] == 60
    assert registered["min_patrol_duration_secs"] == 10
    assert registered["patrolled"] is True
    assert registered["status"] == "registered"
    assert registered["area"]["area_id"] == "PA-001-P"
    assert registered["area"]["name"] == "Station 01 platform"
    assert registered["area"]["area_type"] == "platform"


def test_get_records_registered_below_min_duration_is_not_patrolled(client):
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(client, "connection/connect", ANDROID_ID, SHIFT_START, BEACON_CONCOURSE)
    _post(
        client,
        "connection/disconnect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=15),
        BEACON_CONCOURSE,
    )

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    (record,) = response.json()["records"]
    assert record["status"] == "registered"
    assert record["duration_secs"] == 15
    assert record["min_patrol_duration_secs"] == 20
    assert record["patrolled"] is False


def test_get_records_excludes_events_before_current_shift(client):
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START - timedelta(hours=1),
        BEACON_PLATFORM,
    )
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_CONCOURSE,
    )

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 1
    assert records[0]["beacon_id"] == BEACON_CONCOURSE


def test_get_records_filtered_per_steward(client):
    _post(client, "patrol-session/start", OTHER_ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        OTHER_ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_PLATFORM,
    )
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_CONCOURSE,
    )

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 1
    assert records[0]["android_id"] == ANDROID_ID
    assert records[0]["beacon_id"] == BEACON_CONCOURSE


def test_get_records_after_shift_stop_returns_closed_records(client):
    stop_at = SHIFT_START + timedelta(hours=2)
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_PLATFORM,
    )
    _post(client, "patrol-session/stop", ANDROID_ID, stop_at)

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    (record,) = response.json()["records"]
    assert record["status"] == "registered"
    assert datetime.fromisoformat(record["ended_at"]) == stop_at
    assert record["duration_secs"] == 7140
    assert record["patrolled"] is True


def test_get_records_resolves_all_lines_of_interchange_area(client):
    _post(client, "patrol-session/start", ANDROID_ID, SHIFT_START)
    _post(
        client,
        "connection/connect",
        ANDROID_ID,
        SHIFT_START + timedelta(seconds=60),
        BEACON_INTERCHANGE,
    )

    response = _get_records(client, ANDROID_ID)

    assert response.status_code == 200
    (record,) = response.json()["records"]
    assert record["area"]["station_id"] == "STN-010"
    assert record["area"]["line"] == ["M1", "M2"]
    assert record["area"]["name"] == "Station 10 platform"
