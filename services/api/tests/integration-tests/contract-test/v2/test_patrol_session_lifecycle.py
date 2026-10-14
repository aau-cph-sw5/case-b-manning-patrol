"""Scenario test: a steward's patrol session across ingestion endpoints."""

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-09-21T10:00:00+00:00"


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
