"""Tests for GET /api/v2/trains/stream (trains SSE endpoint)."""

import json
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Line, Train, TrainLine

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
TRAIN_ID = "770e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
OTHER_BEACON_ID = "550e8400-e29b-41d4-a716-446655440099"
TIMESTAMP = "2026-10-08T10:00:00+00:00"
LATER_TIMESTAMP = "2026-10-08T11:00:00+00:00"


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


async def insert_train(db_engine: AsyncEngine) -> None:
    async with AsyncSession(db_engine) as session:
        session.add(
            Train(
                train_id=UUID(TRAIN_ID),
                slug="a29",
                beacon_id=UUID(BEACON_ID),
            )
        )
        for line_id in ("M1", "M2"):
            session.add(Line(id=line_id, name=line_id))
            session.add(TrainLine(train_id=UUID(TRAIN_ID), line_id=line_id))
        await session.commit()


def post_event(http: httpx.Client, path: str, beacon_id: str, timestamp: str) -> None:
    response = http.post(
        path,
        json={
            "android_id": ANDROID_ID,
            "beacon_id": beacon_id,
            "timestamp": timestamp,
        },
    )
    assert response.status_code == 201


async def test_trains_stream_lists_the_train_unmanned(live_base_url, db_engine):
    await insert_train(db_engine)
    with httpx.Client(base_url=live_base_url, timeout=5.0) as http:
        # An event on an unrelated beacon forces a refresh without manning.
        post_event(http, "/api/v2/connection/connect", OTHER_BEACON_ID, TIMESTAMP)

        with http.stream("GET", "/api/v2/trains/stream") as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            event_name, payload = read_sse_event(response.iter_lines())

    assert event_name == "trains"
    assert set(payload) == {
        "trains",
        "manning_percent",
        "m1m2_manning_percent",
        "m3m4_manning_percent",
        "time",
    }
    assert len(payload["trains"]) == 1
    train = payload["trains"][0]
    assert set(train) == {"train_id", "slug", "current_steward_ids", "line"}
    assert train["train_id"] == TRAIN_ID
    assert train["slug"] == "a29"
    assert train["line"] == ["M1", "M2"]
    assert train["current_steward_ids"] == []


async def test_trains_stream_shows_the_manned_train_after_connect(
    live_base_url, db_engine
):
    await insert_train(db_engine)
    with httpx.Client(base_url=live_base_url, timeout=5.0) as http:
        post_event(http, "/api/v2/connection/connect", BEACON_ID, TIMESTAMP)

        with http.stream("GET", "/api/v2/trains/stream") as response:
            _, payload = read_sse_event(response.iter_lines())

    assert payload["trains"][0]["current_steward_ids"] == [ANDROID_ID]


async def test_trains_stream_reemits_unmanned_train_after_disconnect(
    live_base_url, db_engine
):
    await insert_train(db_engine)
    with httpx.Client(base_url=live_base_url, timeout=5.0) as http:
        with httpx.Client(base_url=live_base_url, timeout=5.0) as poster:
            post_event(poster, "/api/v2/connection/connect", BEACON_ID, TIMESTAMP)

            with http.stream("GET", "/api/v2/trains/stream") as response:
                lines = response.iter_lines()
                read_sse_event(lines)

                post_event(
                    poster, "/api/v2/connection/disconnect", BEACON_ID, LATER_TIMESTAMP
                )

                event_name, payload = read_sse_event(lines)

    assert event_name == "trains"
    assert payload["trains"][0]["current_steward_ids"] == []
