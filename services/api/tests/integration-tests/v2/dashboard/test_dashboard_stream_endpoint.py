"""Tests for GET /api/v2/dashboard/stream (dashboard SSE endpoint)."""

import json

import httpx2

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-10-08T10:00:00+00:00"


def read_sse_event(lines) -> tuple[str | None, dict]:
    """Read one `event:`/`data:` block from an SSE line iterator.

    A response only allows a single line iterator, so tests share one.
    """
    event_name = None
    data_lines: list[str] = []
    for line in lines:
        if line == "":
            if data_lines:
                return event_name, json.loads("\n".join(data_lines))
            continue
        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
    raise AssertionError("stream closed before an event was sent")


def post_connect(http: httpx2.Client) -> None:
    response = http.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )
    assert response.status_code == 201


def test_dashboard_stream_sends_a_stations_only_dashboard_event(live_base_url):
    with httpx2.Client(
        base_url=live_base_url,
        timeout=5.0,
        headers={"Authorization": "Bearer controlRoomOperator"},
    ) as http:
        with http.stream("GET", "/api/v2/dashboard/stream") as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            event_name, payload = read_sse_event(response.iter_lines())

    assert event_name == "dashboard"
    assert set(payload) == {"stations", "time"}
    assert payload["stations"] == []


def test_dashboard_stream_sends_the_current_threshold_on_connect(live_base_url):
    with httpx2.Client(
        base_url=live_base_url,
        timeout=5.0,
        headers={"Authorization": "Bearer controlRoomOperator"},
    ) as http:
        with http.stream("GET", "/api/v2/dashboard/stream") as response:
            assert response.status_code == 200
            lines = response.iter_lines()

            dashboard_event, dashboard_payload = read_sse_event(lines)
            threshold_event, threshold_payload = read_sse_event(lines)

    assert dashboard_event == "dashboard"
    assert set(dashboard_payload) == {"stations", "time"}
    assert threshold_event == "at-risk-threshold"
    assert set(threshold_payload) == {"at_risk_threshold_minutes"}
    assert threshold_payload["at_risk_threshold_minutes"] >= 1


def test_dashboard_stream_emits_at_risk_threshold_when_it_is_changed(
    live_base_url, client
):
    with httpx2.Client(
        base_url=live_base_url,
        timeout=5.0,
        headers={"Authorization": "Bearer controlRoomOperator"},
    ) as http:
        with http.stream("GET", "/api/v2/dashboard/stream") as response:
            lines = response.iter_lines()
            read_sse_event(lines)
            read_sse_event(lines)

            response = client.post(
                "/api/v2/config/at-risk-threshold",
                json={"at_risk_threshold_minutes": 20},
            )
            assert response.status_code == 200

            event_name, payload = read_sse_event(lines)

    assert event_name == "at-risk-threshold"
    assert payload == {"at_risk_threshold_minutes": 20}


def test_dashboard_stream_reemits_when_coverage_is_recomputed(live_base_url):
    with httpx2.Client(
        base_url=live_base_url,
        timeout=5.0,
        headers={"Authorization": "Bearer controlRoomOperator"},
    ) as http:
        with httpx2.Client(
            base_url=live_base_url,
            timeout=5.0,
            headers={"Authorization": "Bearer controlRoomOperator"},
        ) as poster:
            with http.stream("GET", "/api/v2/dashboard/stream") as response:
                lines = response.iter_lines()
                read_sse_event(lines)
                read_sse_event(lines)

                post_connect(poster)

                event_name, payload = read_sse_event(lines)

    assert event_name == "dashboard"
    assert set(payload) == {"stations", "time"}
