"""Tests for POST /api/v2/patrol-session/stop (patrol-session-event)."""

from datetime import datetime
from uuid import UUID

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
TIMESTAMP = "2026-09-21T10:00:00+00:00"


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
    assert event["event_type"] == "stop"
    assert event["actor"] == ANDROID_ID
    assert event["beacon"] is None
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
