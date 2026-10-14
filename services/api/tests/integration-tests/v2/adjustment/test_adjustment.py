"""Tests for POST /api/v2/adjustment (AdjustmentEventCreate)."""

from datetime import datetime
from uuid import UUID

from src.models.event import EventType

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
OCCURRED_AT = "2026-09-21T10:05:00+00:00"
AUTHOR_ID = "880e8400-e29b-41d4-a716-446655440003"
REASON = "Beacon never fired on arrival; steward confirms platform patrol."
TARGET_EVENT_ID = "770e8400-e29b-41d4-a716-446655440002"

VALID_ADJUSTMENT = {
    "android_id": ANDROID_ID,
    "corrected_fact": {
        "fact_type": EventType.CONNECT_EVENT,
        "beacon_id": BEACON_ID,
        "occurred_at": OCCURRED_AT,
    },
    "reason": REASON,
    "author": AUTHOR_ID,
}


def test_adjustment_returns_stored_adjustment(client):
    response = client.post("/api/v2/adjustment", json=VALID_ADJUSTMENT)

    assert response.status_code == 201
    adjustment = response.json()
    assert adjustment["android_id"] == ANDROID_ID
    assert datetime.fromisoformat(
        adjustment["corrected_fact"]["occurred_at"]) == datetime.fromisoformat(
        VALID_ADJUSTMENT["corrected_fact"]["occurred_at"])
    assert adjustment["reason"] == REASON
    assert adjustment["author"] == AUTHOR_ID
    assert adjustment["target_event_id"] is None
    assert UUID(adjustment["adjustment_id"])
    assert datetime.fromisoformat(adjustment["server_timestamp"])
    assert isinstance(adjustment["source"], str)


def test_adjustment_can_target_a_recorded_event(client):
    event = client.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": OCCURRED_AT,
        },
    ).json()
    payload = {**VALID_ADJUSTMENT, "target_event_id": event["event_id"]}

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 201
    assert response.json()["target_event_id"] == event["event_id"]


def test_adjustment_source_is_not_taken_from_request_body(client):
    payload = {**VALID_ADJUSTMENT, "source": "ANDROID"}

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 201
    assert response.json()["source"] != "ANDROID"


def test_adjustment_rejects_connect_fact_without_beacon(client):
    payload = {
        **VALID_ADJUSTMENT,
        "corrected_fact": {
            "fact_type": "connect",
            "beacon_id": None,
            "occurred_at": OCCURRED_AT,
        },
    }

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_disconnect_fact_without_beacon(client):
    payload = {
        **VALID_ADJUSTMENT,
        "corrected_fact": {
            "fact_type": "disconnect",
            "beacon_id": None,
            "occurred_at": OCCURRED_AT,
        },
    }

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_unknown_fact_type(client):
    payload = {
        **VALID_ADJUSTMENT,
        "corrected_fact": {
            "fact_type": "teleport",
            "beacon_id": BEACON_ID,
            "occurred_at": OCCURRED_AT,
        },
    }

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_missing_actor(client):
    payload = dict(VALID_ADJUSTMENT)
    del payload["android_id"]

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_missing_reason(client):
    payload = dict(VALID_ADJUSTMENT)
    del payload["reason"]

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_missing_author(client):
    payload = dict(VALID_ADJUSTMENT)
    del payload["author"]

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_missing_corrected_fact(client):
    payload = dict(VALID_ADJUSTMENT)
    del payload["corrected_fact"]

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 400
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)


def test_adjustment_rejects_unknown_target_event(client):
    payload = {**VALID_ADJUSTMENT, "target_event_id": TARGET_EVENT_ID}

    response = client.post("/api/v2/adjustment", json=payload)

    assert response.status_code == 404
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
