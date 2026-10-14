"""Endpoint tests for the v2 Positioning Ingestion contract.

One explicit test per endpoint in
contracts/api/v2/positioning-ingestion/schema.json. Payload values are the
contract's example values; when the contract changes, update these tests.
"""

from datetime import datetime
from uuid import UUID

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-09-21T10:00:00+00:00"


def test_connect_records_connection_event(client):
    response = client.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    assert response.status_code == 201
    event = response.json()
    assert event["event_type"] == "connect"
    assert event["actor"] == ANDROID_ID
    assert event["beacon"] == BEACON_ID
    assert UUID(event["event_id"])
    assert datetime.fromisoformat(event["server_timestamp"])
    device_timestamp = datetime.fromisoformat(event["device_timestamp"])
    assert device_timestamp == datetime.fromisoformat(TIMESTAMP)


def test_connect_rejects_missing_android_id(client):
    response = client.post(
        "/api/v2/connection/connect",
        json={"beacon_id": BEACON_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 422


def test_connect_rejects_missing_beacon_id(client):
    response = client.post(
        "/api/v2/connection/connect",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 422


def test_connect_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/connection/connect",
        json={"android_id": ANDROID_ID, "beacon_id": BEACON_ID},
    )

    assert response.status_code == 422


def test_connect_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": "not-a-timestamp",
        },
    )

    assert response.status_code == 422


def test_disconnect_records_disconnection_event(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    assert response.status_code == 201
    event = response.json()
    assert event["event_type"] == "disconnect"
    assert event["actor"] == ANDROID_ID
    assert event["beacon"] == BEACON_ID
    assert UUID(event["event_id"])
    assert datetime.fromisoformat(event["server_timestamp"])
    device_timestamp = datetime.fromisoformat(event["device_timestamp"])
    assert device_timestamp == datetime.fromisoformat(TIMESTAMP)


def test_disconnect_rejects_missing_android_id(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"beacon_id": BEACON_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 422


def test_disconnect_rejects_missing_beacon_id(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 422


def test_disconnect_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={"android_id": ANDROID_ID, "beacon_id": BEACON_ID},
    )

    assert response.status_code == 422


def test_disconnect_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/connection/disconnect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": "not-a-timestamp",
        },
    )

    assert response.status_code == 422


def test_patrol_session_start_records_start_event(client):
    response = client.post(
        "/api/v2/patrol-session/start",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 201
    event = response.json()
    assert event["event_type"] == "start"
    assert event["actor"] == ANDROID_ID
    assert event["beacon"] is None
    assert UUID(event["event_id"])
    assert datetime.fromisoformat(event["server_timestamp"])
    device_timestamp = datetime.fromisoformat(event["device_timestamp"])
    assert device_timestamp == datetime.fromisoformat(TIMESTAMP)


def test_patrol_session_start_rejects_missing_android_id(client):
    response = client.post(
        "/api/v2/patrol-session/start",
        json={"timestamp": TIMESTAMP},
    )

    assert response.status_code == 422


def test_patrol_session_start_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/start",
        json={"android_id": ANDROID_ID},
    )

    assert response.status_code == 422


def test_patrol_session_start_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/start",
        json={"android_id": ANDROID_ID, "timestamp": "not-a-timestamp"},
    )

    assert response.status_code == 422


def test_patrol_session_stop_records_stop_event(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID, "timestamp": TIMESTAMP},
    )

    assert response.status_code == 201
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

    assert response.status_code == 422


def test_patrol_session_stop_rejects_missing_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID},
    )

    assert response.status_code == 422


def test_patrol_session_stop_rejects_malformed_timestamp(client):
    response = client.post(
        "/api/v2/patrol-session/stop",
        json={"android_id": ANDROID_ID, "timestamp": "not-a-timestamp"},
    )

    assert response.status_code == 422


def test_patrol_session_lifecycle_appends_distinct_events(client):
    connection = {
        "android_id": ANDROID_ID,
        "beacon_id": BEACON_ID,
        "timestamp": TIMESTAMP,
    }
    patrol_session = {"android_id": ANDROID_ID, "timestamp": TIMESTAMP}
    steps = [
        ("/api/v2/patrol-session/start", patrol_session),
        ("/api/v2/connection/connect", connection),
        ("/api/v2/connection/disconnect", connection),
        ("/api/v2/patrol-session/stop", patrol_session),
    ]

    event_ids = set()
    for path, payload in steps:
        response = client.post(path, json=payload)
        assert response.status_code == 201
        event_ids.add(response.json()["event_id"])

    assert len(event_ids) == len(steps)
