"""Authentication and RBAC checks on the v2 endpoints."""

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-09-21T10:00:00+00:00"

CONNECT_EVENT = {
    "android_id": ANDROID_ID,
    "beacon_id": BEACON_ID,
    "timestamp": TIMESTAMP,
}

ADJUSTMENT = {
    "android_id": ANDROID_ID,
    "corrected_fact": {
        "fact_type": "connect",
        "beacon_id": BEACON_ID,
        "occurred_at": TIMESTAMP,
    },
    "reason": "Signal blip, steward did not leave the platform",
    "author": "test-supervisor",
}


def test_ingestion_without_token_uses_default_dev_steward(client):
    response = client.post("/api/v2/connection/connect", json=CONNECT_EVENT)
    assert response.status_code == 201


def test_ingestion_with_unknown_token_is_401(client):
    response = client.post(
        "/api/v2/connection/connect",
        json=CONNECT_EVENT,
        headers={"Authorization": "Bearer nope"},
    )
    assert response.status_code == 401


def test_it_administrator_cannot_ingest_presence(client):
    response = client.post(
        "/api/v2/connection/connect",
        json=CONNECT_EVENT,
        headers={"Authorization": "Bearer dev-it-admin-token"},
    )
    assert response.status_code == 403


def test_steward_cannot_post_adjustments(client):
    response = client.post(
        "/api/v2/adjustment",
        json=ADJUSTMENT,
        headers={"Authorization": "Bearer dev-steward-token"},
    )
    assert response.status_code == 403


def test_supervisor_can_post_adjustments(client):
    response = client.post(
        "/api/v2/adjustment",
        json=ADJUSTMENT,
        headers={"Authorization": "Bearer dev-supervisor-token"},
    )
    assert response.status_code == 201
