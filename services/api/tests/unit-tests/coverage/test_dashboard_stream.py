from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from src.api.v2.routers.dashboard_stream import stream
from src.api.v2.schemas.dashboard import Dashboard
from src.domain.train_manning import TrainManningReport, TrainReference
from src.main import app as main_app
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)

TRAIN_ID = UUID("10000000-0000-0000-0000-000000000001")
TRAIN_BEACON = UUID("00000000-0000-0000-0000-00000000a001")
STEWARD = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")


class FakeUpdater:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return self._snapshot

    def set_snapshot(self, snapshot):
        self._snapshot = snapshot


def make_request(presenter, coverage_updater=None, train_updater=None):
    """Request whose app.state carries both updaters and both broadcasters."""
    app = FastAPI()
    app.state.coverage_updater = coverage_updater or FakeUpdater([])
    app.state.sse_broadcaster = SseCoverageBroadcaster()
    app.state.dashboard_presenter = presenter
    app.state.train_manning_updater = train_updater or FakeUpdater([])
    app.state.train_manning_broadcaster = SseTrainManningBroadcaster()
    return Request(scope={"type": "http", "app": app})


def train_report(manned_now: bool = False) -> TrainManningReport:
    now = datetime.now(UTC)
    return TrainManningReport(
        train=TrainReference(
            id=TRAIN_ID,
            slug="a29",
            beacon_id=TRAIN_BEACON,
            line_ids=frozenset({"M1", "M2"}),
        ),
        running_time=timedelta(hours=1),
        manned_time=timedelta(minutes=30) if manned_now else timedelta(0),
        manned_now=manned_now,
        current_steward_ids=frozenset({STEWARD}) if manned_now else frozenset(),
        as_of=now,
    )


def open_stream(request) -> AsyncGenerator[ServerSentEvent]:
    # The route is annotated AsyncIterable because that is what FastAPI
    # accepts for SSE, but the tests need the generator interface.
    return cast(AsyncGenerator[ServerSentEvent], stream(request))


def station_ids(event: ServerSentEvent) -> list[str]:
    dashboard = cast(Dashboard, event.data)
    return [station.station_id for station in dashboard.stations]


def train_ids(event: ServerSentEvent) -> list[UUID]:
    dashboard = cast(Dashboard, event.data)
    return [train.id for train in dashboard.trains]


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
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))

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
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))
    broadcaster = request.app.state.sse_broadcaster

    generator = open_stream(request)
    await generator.__anext__()
    broadcaster.publish(refreshed)
    second = await generator.__anext__()

    assert second.event == "dashboard"
    assert station_ids(second) == ["marmorkirken", "kongens-nytorv"]
    await generator.aclose()


async def test_stream_merges_trains_into_every_dashboard_event(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(
        dashboard_presenter,
        coverage_updater=FakeUpdater(snapshot),
        train_updater=FakeUpdater([train_report(manned_now=True)]),
    )

    generator = open_stream(request)
    first = await generator.__anext__()

    assert first.event == "dashboard"
    assert station_ids(first) == ["marmorkirken"]
    assert train_ids(first) == [TRAIN_ID]
    train = cast(Dashboard, first.data).trains[0]
    assert train.current_steward_ids == [STEWARD]
    assert train.line == ["M1", "M2"]
    await generator.aclose()


async def test_train_refresh_re_emits_stations_and_trains(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    train_updater = FakeUpdater([train_report(manned_now=True)])
    request = make_request(
        dashboard_presenter,
        coverage_updater=FakeUpdater(snapshot),
        train_updater=train_updater,
    )

    generator = open_stream(request)
    await generator.__anext__()
    train_updater.set_snapshot([train_report(manned_now=False)])
    request.app.state.train_manning_broadcaster.publish([train_report()])
    second = await generator.__anext__()

    dashboard = cast(Dashboard, second.data)
    assert station_ids(second) == ["marmorkirken"]
    assert train_ids(second) == [TRAIN_ID]
    assert dashboard.trains[0].current_steward_ids == []
    await generator.aclose()


async def test_stream_unsubscribes_from_both_broadcasters_on_disconnect(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))
    broadcaster = request.app.state.sse_broadcaster
    train_broadcaster = request.app.state.train_manning_broadcaster

    generator = open_stream(request)
    await generator.__anext__()
    assert len(broadcaster._subscribers) == 1
    assert len(train_broadcaster._subscribers) == 1

    await generator.aclose()

    assert len(broadcaster._subscribers) == 0
    assert len(train_broadcaster._subscribers) == 0


async def test_stream_payload_has_the_contract_fields(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(
        dashboard_presenter,
        coverage_updater=FakeUpdater(snapshot),
        train_updater=FakeUpdater([train_report()]),
    )

    generator = open_stream(request)
    first = await generator.__anext__()
    payload = cast(Dashboard, first.data).model_dump(mode="json")

    assert set(payload) == {"stations", "trains", "time"}
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
    assert set(payload["trains"][0]) == {
        "id",
        "slug",
        "total_time_secs",
        "manned_time_secs",
        "current_steward_ids",
        "line",
    }
    await generator.aclose()
