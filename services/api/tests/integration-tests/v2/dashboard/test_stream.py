"""Tests for GET /api/v2/dashboard/stream (SSE Dashboard stream)."""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import cast

from fastapi.sse import ServerSentEvent
from starlette.requests import Request

from src.api.v2.routers.dashboard_stream import stream
from src.main import app

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-09-21T10:00:00+00:00"


def _make_request() -> Request:
    return Request(scope={"type": "http", "app": app})


def _open_stream(request: Request) -> AsyncGenerator[ServerSentEvent]:
    # The route is annotated AsyncIterable because that is what FastAPI
    # accepts for SSE, but the tests need the generator interface.
    return cast(AsyncGenerator[ServerSentEvent], stream(request))


def _post_connect_event(client):
    client.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )


async def test_stream_first_event_is_named_dashboard(client):
    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    assert first.event == "dashboard"


async def test_stream_first_event_matches_dashboard_contract(client):
    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    assert set(dashboard.keys()) == {"stations", "trains", "time"}
    assert isinstance(dashboard["stations"], list)
    assert isinstance(dashboard["trains"], list)
    assert datetime.fromisoformat(dashboard["time"])


async def test_stream_includes_seeded_station(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    assert len(dashboard["stations"]) == 1
    station = dashboard["stations"][0]
    assert set(station.keys()) == {"station_id", "name", "areas"}
    assert station["station_id"] == seeded_station_id
    assert isinstance(station["name"], str)
    assert isinstance(station["areas"], list)
    assert len(station["areas"]) == 1


async def test_stream_station_area_matches_contract(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    area = dashboard["stations"][0]["areas"][0]
    assert set(area.keys()) == {
        "area_id",
        "name",
        "line",
        "area_type",
        "covered_now",
        "overdue_at",
    }
    assert isinstance(area["area_id"], str)
    assert isinstance(area["name"], str)
    assert isinstance(area["line"], str)
    assert area["area_type"] in ("platform", "concourse")
    assert isinstance(area["covered_now"], bool)
    assert area["overdue_at"] is None or isinstance(area["overdue_at"], str)
    if area["overdue_at"] is not None:
        datetime.fromisoformat(area["overdue_at"])


async def test_stream_area_types_are_valid(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    area = dashboard["stations"][0]["areas"][0]
    assert area["area_type"] == "platform"


async def test_stream_covered_now_is_boolean(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    area = dashboard["stations"][0]["areas"][0]
    assert isinstance(area["covered_now"], bool)


async def test_stream_trains_is_empty_array(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    assert dashboard["trains"] == []


async def test_stream_time_is_iso_datetime(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    parsed = datetime.fromisoformat(dashboard["time"])
    assert parsed.tzinfo is not None


async def test_stream_station_id_matches_contract_type(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    station = dashboard["stations"][0]
    assert isinstance(station["station_id"], str)


async def test_stream_area_id_matches_contract_type(client, seeded_station_id):
    _post_connect_event(client)

    generator = _open_stream(_make_request())
    first = await generator.__anext__()
    await generator.aclose()

    dashboard = first.data.model_dump(mode="json")
    area = dashboard["stations"][0]["areas"][0]
    assert isinstance(area["area_id"], str)
