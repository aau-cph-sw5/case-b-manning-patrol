from fastapi.testclient import TestClient

from src.main import app


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
        app.url_path_for("shift_start_event"),
        json={
            "android_id": "android-1",
            "timestamp": "2026-10-02T10:00:00+00:00",
        },
    )

    stop_response = client.post(
        app.url_path_for("shift_stop_event"),
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
                "beacon_id": "12345",
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

    # Asserting Shift Start
    assert start_response.status_code == 201
    start_event = start_response.json()
    assert start_event["event_type"] == "start"
    assert start_event["actor"] == "android-1"
    assert start_event["beacon"] is None
    assert start_event["device_timestamp"] == "2026-10-02T10:00:00Z"
    assert start_event["server_timestamp"]
    assert start_event["event_id"]

    # Asserting Shift Stop
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
        "beacon_id": "12345",
        "occurred_at": "2026-10-02T10:00:00Z",
    }
    assert adjustment_event["reason"] == "Adjusted something"
    assert adjustment_event["server_timestamp"]
    assert adjustment_event["adjustment_id"]
    assert adjustment_event["author"] == "Controller-1"
    assert adjustment_event["target_event_id"] is None
