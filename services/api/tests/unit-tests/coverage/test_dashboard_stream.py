from collections.abc import AsyncGenerator
from typing import cast

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from src.api.v2.routers.dashboard_stream import stream
from src.main import app as main_app
from src.models.dashboard import Dashboard
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster


class FakeUpdater:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return self._snapshot


def make_request(updater, broadcaster, presenter):
    app = FastAPI()
    app.state.coverage_updater = updater
    app.state.sse_broadcaster = broadcaster
    app.state.dashboard_presenter = presenter
    return Request(scope={"type": "http", "app": app})


def open_stream(request) -> AsyncGenerator[ServerSentEvent]:
    # The route is annotated AsyncIterable because that is what FastAPI
    # accepts for SSE, but the tests need the generator interface.
    return cast(AsyncGenerator[ServerSentEvent], stream(request))


def station_ids(event: ServerSentEvent) -> list[str]:
    dashboard = cast(Dashboard, event.data)
    return [station.station_id for station in dashboard.stations]


def test_stream_is_served_at_the_contract_path():
    assert "/api/v2/dashboard/stream" in main_app.openapi()["paths"]


async def test_stream_sends_every_station_first(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report(
            "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=None
        ),
    ]
    broadcaster = SseCoverageBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster, dashboard_presenter)

    generator = open_stream(request)
    first = await generator.__anext__()

    assert first.event == "dashboard"
    assert station_ids(first) == ["marmorkirken", "kongens-nytorv"]
    await generator.aclose()


async def test_stream_sends_every_station_on_each_refresh(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report(
            "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=True, as_of=now, last_covered_at=now
        ),
    ]
    refreshed = [
        station_report(
            "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=now
        ),
    ]
    broadcaster = SseCoverageBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster, dashboard_presenter)

    generator = open_stream(request)
    await generator.__anext__()
    broadcaster.publish(refreshed)
    second = await generator.__anext__()

    assert second.event == "dashboard"
    assert station_ids(second) == ["marmorkirken", "kongens-nytorv"]
    await generator.aclose()


async def test_stream_unsubscribes_when_the_client_disconnects(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    broadcaster = SseCoverageBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster, dashboard_presenter)

    generator = open_stream(request)
    await generator.__anext__()
    assert len(broadcaster._subscribers) == 1

    await generator.aclose()

    assert len(broadcaster._subscribers) == 0


async def test_stream_payload_has_the_contract_fields(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    broadcaster = SseCoverageBroadcaster()
    request = make_request(FakeUpdater(snapshot), broadcaster, dashboard_presenter)

    generator = open_stream(request)
    first = await generator.__anext__()
    payload = cast(Dashboard, first.data).model_dump(mode="json")

    assert set(payload) == {"stations", "trains", "time"}
    assert payload["trains"] == []
    station = payload["stations"][0]
    assert set(station) == {"station_id", "name", "areas"}
    assert set(station["areas"][0]) == {
        "area_id",
        "name",
        "line",
        "area_type",
        "covered_now",
        "overdue_at",
    }
    await generator.aclose()
