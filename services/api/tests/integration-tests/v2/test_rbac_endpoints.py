"""Authentication and RBAC checks on the v2 endpoints.

The `client` fixture authenticates as controlRoomOperator by default
(see conftest.py); these tests override the Authorization header per request
or use `anon_client` to exercise 401/403 paths.
"""

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
OTHER_ANDROID_ID = "11111111-2222-3333-4444-555555555555"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-09-21T10:00:00+00:00"

STEWARD = {"Authorization": "Bearer steward"}
CRO = {"Authorization": "Bearer controlRoomOperator"}
OPS_ADMIN = {"Authorization": "Bearer operations_administrator"}
IT_ADMIN = {"Authorization": "Bearer it_administrator"}

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
    "reason": "Signal blip",
    "author": "test-supervisor",
}


def test_missing_authorization_header_is_401(anon_client):
    assert anon_client.get("/api/v2/coverage/at-risk-count").status_code == 401
    assert (
        anon_client.post("/api/v2/connection/connect", json=CONNECT_EVENT).status_code
        == 401
    )


def test_malformed_authorization_header_is_401(anon_client):
    response = anon_client.get(
        "/api/v2/coverage/at-risk-count", headers={"Authorization": "Token steward"}
    )
    assert response.status_code == 401


def test_steward_can_send_connection_events(client):
    response = client.post(
        "/api/v2/connection/connect", json=CONNECT_EVENT, headers=STEWARD
    )
    assert response.status_code == 201


def test_it_administrator_cannot_send_connection_events(client):
    response = client.post(
        "/api/v2/connection/connect", json=CONNECT_EVENT, headers=IT_ADMIN
    )
    assert response.status_code == 403


def test_steward_cannot_read_at_risk_count_but_cro_can(client):
    assert (
        client.get("/api/v2/coverage/at-risk-count", headers=STEWARD).status_code == 403
    )
    assert client.get("/api/v2/coverage/at-risk-count", headers=CRO).status_code == 200


def test_steward_reads_only_own_record(client):
    own = client.get(
        f"/api/v2/record?android_id={ANDROID_ID}",
        headers={**STEWARD, "X-Android-Id": ANDROID_ID},
    )
    assert own.status_code == 200

    other = client.get(
        f"/api/v2/record?android_id={OTHER_ANDROID_ID}",
        headers={**STEWARD, "X-Android-Id": ANDROID_ID},
    )
    assert other.status_code == 403

    no_device = client.get(f"/api/v2/record?android_id={ANDROID_ID}", headers=STEWARD)
    assert no_device.status_code == 403


def test_control_room_operator_reads_any_record(client):
    response = client.get(f"/api/v2/record?android_id={ANDROID_ID}", headers=CRO)
    assert response.status_code == 200


def test_it_administrator_cannot_read_records(client):
    response = client.get(f"/api/v2/record?android_id={ANDROID_ID}", headers=IT_ADMIN)
    assert response.status_code == 403


def test_config_threshold_requires_permission(client):
    steward_get = client.get("/api/v2/config/at-risk-threshold", headers=STEWARD)
    assert steward_get.status_code == 403
    cro_get = client.get("/api/v2/config/at-risk-threshold", headers=CRO)
    assert cro_get.status_code == 200

    denied = client.post(
        "/api/v2/config/at-risk-threshold",
        json={"at_risk_threshold_minutes": 15},
        headers=STEWARD,
    )
    assert denied.status_code == 403

    allowed = client.post(
        "/api/v2/config/at-risk-threshold",
        json={"at_risk_threshold_minutes": 15},
        headers=OPS_ADMIN,
    )
    assert allowed.status_code == 200
    assert allowed.json() == {"at_risk_threshold_minutes": 15}


def test_adjustment_requires_permission(client):
    denied = client.post("/api/v2/adjustment", json=ADJUSTMENT, headers=STEWARD)
    assert denied.status_code == 403

    allowed = client.post("/api/v2/adjustment", json=ADJUSTMENT, headers=CRO)
    assert allowed.status_code == 201
