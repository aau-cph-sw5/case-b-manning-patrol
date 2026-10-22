from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import cast

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from src.api.v2.routers.coverage_stream import stream
from src.services.coverage.sse_broadcaster import SseBroadcaster


class FakeUpdater:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return self._snapshot


def make_request(updater, broadcaster):
    app = FastAPI()
    app.state.coverage_updater = updater
    app.state.sse_broadcaster = broadcaster
    return Request(scope={"type": "http", "app": app})


def open_stream(request) -> AsyncGenerator[ServerSentEvent]:
    # The route is annotated AsyncIterable because that is what FastAPI
    # accepts for SSE, but the tests need the generator interface.
    return cast(AsyncGenerator[ServerSentEvent], stream(request))


async def test_stream_sends_the_snapshot_first(station_report, now):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    broadcaster = SseBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster)

    generator = open_stream(request)
    first = await generator.__anext__()

    assert first.event == "coverage"
    assert [station["station_id"] for station in first.data] == ["marmorkirken"]
    await generator.aclose()


async def test_stream_sends_every_refresh_after_the_snapshot(station_report, now):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    live = [
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=None
        )
    ]
    broadcaster = SseBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster)

    generator = open_stream(request)
    await generator.__anext__()
    broadcaster.publish(live)
    second = await generator.__anext__()

    assert second.event == "coverage"
    assert [station["station_id"] for station in second.data] == ["kongens-nytorv"]
    await generator.aclose()


async def test_stream_unsubscribes_when_the_client_disconnects(station_report, now):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    broadcaster = SseBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster)

    generator = open_stream(request)
    await generator.__anext__()
    assert len(broadcaster._subscribers) == 1

    await generator.aclose()

    assert len(broadcaster._subscribers) == 0


async def test_stream_payload_matches_the_contract(station_report, now):
    snapshot = [
        station_report(
            "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv",
            covered_now=False,
            as_of=now,
            last_covered_at=now - timedelta(hours=2),
        ),
    ]
    broadcaster = SseBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster)

    generator = open_stream(request)
    first = await generator.__anext__()

    assert first.data == [
        {
            "station_id": "marmorkirken",
            "status": "compliant",
            "areas": [
                {
                    "area_id": "platform-1",
                    "type": "platform",
                    "covered_now": True,
                    "stewards_present": [],
                    "last_covered_at": now.isoformat(),
                    "status": "compliant",
                    "overdue_at": None,
                    "as_of": now.isoformat(),
                }
            ],
        },
        {
            "station_id": "kongens-nytorv",
            "status": "overdue",
            "areas": [
                {
                    "area_id": "platform-1",
                    "type": "platform",
                    "covered_now": False,
                    "stewards_present": [],
                    "last_covered_at": (now - timedelta(hours=2)).isoformat(),
                    "status": "overdue",
                    "overdue_at": (now - timedelta(hours=1)).isoformat(),
                    "as_of": now.isoformat(),
                }
            ],
        },
    ]
    await generator.aclose()
