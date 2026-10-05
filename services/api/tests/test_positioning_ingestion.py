"""The ingestion endpoints of contracts/positioning-ingestion/v1: each endpoint
records one action, and the payloads carry no status field — the endpoint says
what happened. These are the 20% of cases that cover the whole contract."""

import pytest
from fastapi.testclient import TestClient

from src.main import API_PREFIX, app
from src.services import ingestion_service

client = TestClient(app)

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-000000000002"
TIMESTAMP = "2026-05-30T03:08:13.000Z"


def post_connection(action: str, **overrides):
    payload = {"android_id": ANDROID_ID, "beacon_id": BEACON_ID, "timestamp": TIMESTAMP}
    payload.update(overrides)
    return client.post(f"{API_PREFIX}/connection/{action}", json=payload)


@pytest.fixture(autouse=True)
def clean_logs():
    ingestion_service.connection_log.clear()
    ingestion_service.shift_log.clear()


def test_connect_returns_201_and_logs_connected():
    response = post_connection("connect")

    assert response.status_code == 201
    assert ingestion_service.connection_log == [
        {
            "event": "CONNECTED",
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": "2026-05-30T03:08:13+00:00",
        }
    ]


def test_disconnect_returns_201_and_logs_disconnected():
    response = post_connection("disconnect")

    assert response.status_code == 201
    assert ingestion_service.connection_log == [
        {
            "event": "DISCONNECTED",
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": "2026-05-30T03:08:13+00:00",
        }
    ]


def test_events_accumulate_in_order():
    post_connection("connect")
    post_connection("disconnect")

    assert [event["event"] for event in ingestion_service.connection_log] == [
        "CONNECTED",
        "DISCONNECTED",
    ]


@pytest.mark.parametrize("action", ["start", "stop"])
def test_shift_endpoints_return_201_and_log_the_action(action):
    response = client.post(f"{API_PREFIX}/shift/{action}", json={"id": ANDROID_ID})

    expected_event = "SHIFT_STARTED" if action == "start" else "SHIFT_STOPPED"
    assert response.status_code == 201
    assert ingestion_service.shift_log == [
        {"event": expected_event, "android_id": ANDROID_ID}
    ]


def test_connection_without_beacon_id_is_rejected():
    response = post_connection("connect", beacon_id="")

    assert response.status_code == 422
    assert ingestion_service.connection_log == []


def test_connection_with_bad_timestamp_is_rejected():
    response = post_connection("connect", timestamp="yesterday")

    assert response.status_code == 422
    assert ingestion_service.connection_log == []
