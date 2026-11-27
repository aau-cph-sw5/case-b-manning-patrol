from collections.abc import AsyncGenerator
from typing import cast

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from src.api.v2.routers.dashboard_stream import stream
from src.api.v2.schemas.config import AtRiskThreshold
from src.api.v2.schemas.dashboard import Dashboard
from src.main import app as main_app
from src.security.current_user import User
from src.services.config.at_risk_threshold_broadcaster import AtRiskThresholdBroadcaster
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster

DEFAULT_THRESHOLD_MINUTES = 10


class FakeUpdater:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return self._snapshot

    def set_snapshot(self, snapshot):
        self._snapshot = snapshot


def make_request(
    presenter, coverage_updater=None, threshold_minutes=DEFAULT_THRESHOLD_MINUTES
):
    """Request whose app.state carries the updater, broadcasters and presenter."""
    app = FastAPI()
    app.state.coverage_updater = coverage_updater or FakeUpdater([])
    app.state.sse_broadcaster = SseCoverageBroadcaster()
    app.state.at_risk_threshold_broadcaster = AtRiskThresholdBroadcaster(
        threshold_minutes
    )
    app.state.dashboard_presenter = presenter
    return Request(scope={"type": "http", "app": app})


def open_stream(request) -> AsyncGenerator[ServerSentEvent]:
    # The route is annotated AsyncIterable because that is what FastAPI
    # accepts for SSE, but the tests need the generator interface.
    user = User(user_id="test", role="controlRoomOperator")
    return cast(AsyncGenerator[ServerSentEvent], stream(request, user))


def station_ids(event: ServerSentEvent) -> list[str]:
    dashboard = cast(Dashboard, event.data)
    return [station.station_id for station in dashboard.stations]


def threshold_minutes(event: ServerSentEvent) -> int:
    threshold = cast(AtRiskThreshold, event.data)
    return threshold.at_risk_threshold_minutes


async def read_initial_events(request) -> AsyncGenerator[ServerSentEvent]:
    """Open the stream and consume the two events sent on connect.

    Every new client first receives the full dashboard, then the current
    at-risk threshold.
    """
    generator = open_stream(request)
    first = await generator.__anext__()
    second = await generator.__anext__()
    assert first.event == "dashboard"
    assert second.event == "at-risk-threshold"
    return generator


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


async def test_stream_sends_the_current_threshold_on_connect(
    station_report, dashboard_presenter, now
):
    request = make_request(dashboard_presenter, threshold_minutes=25)

    generator = open_stream(request)
    await generator.__anext__()
    second = await generator.__anext__()

    assert second.event == "at-risk-threshold"
    assert threshold_minutes(second) == 25
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

    generator = await read_initial_events(request)
    broadcaster.publish(refreshed)
    third = await generator.__anext__()

    assert third.event == "dashboard"
    assert station_ids(third) == ["marmorkirken", "kongens-nytorv"]
    await generator.aclose()


async def test_stream_sends_the_new_threshold_when_it_changes(
    station_report, dashboard_presenter, now
):
    request = make_request(dashboard_presenter)
    threshold_broadcaster: AtRiskThresholdBroadcaster = (
        request.app.state.at_risk_threshold_broadcaster
    )

    generator = await read_initial_events(request)
    threshold_broadcaster.publish(30)
    third = await generator.__anext__()

    assert third.event == "at-risk-threshold"
    assert threshold_minutes(third) == 30
    await generator.aclose()


async def test_stream_sends_dashboard_and_threshold_when_both_change(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))
    coverage_broadcaster = request.app.state.sse_broadcaster
    threshold_broadcaster: AtRiskThresholdBroadcaster = (
        request.app.state.at_risk_threshold_broadcaster
    )

    generator = await read_initial_events(request)
    coverage_broadcaster.publish(snapshot)
    threshold_broadcaster.publish(45)

    third = await generator.__anext__()
    fourth = await generator.__anext__()

    assert third.event == "dashboard"
    assert fourth.event == "at-risk-threshold"
    assert threshold_minutes(fourth) == 45
    await generator.aclose()


async def test_stream_unsubscribes_from_the_broadcasters_on_disconnect(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))
    broadcaster = request.app.state.sse_broadcaster
    threshold_broadcaster: AtRiskThresholdBroadcaster = (
        request.app.state.at_risk_threshold_broadcaster
    )

    generator = open_stream(request)
    await generator.__anext__()
    assert len(broadcaster._subscribers) == 1
    assert len(threshold_broadcaster._subscribers) == 1

    await generator.aclose()

    assert len(broadcaster._subscribers) == 0
    assert len(threshold_broadcaster._subscribers) == 0


async def test_stream_payload_has_the_contract_fields(
    station_report, dashboard_presenter, now
):
    snapshot = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]
    request = make_request(dashboard_presenter, coverage_updater=FakeUpdater(snapshot))

    generator = open_stream(request)
    first = await generator.__anext__()
    payload = cast(Dashboard, first.data).model_dump(mode="json")

    assert set(payload) == {"stations", "time"}
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


async def test_threshold_event_payload_has_the_contract_fields(
    station_report, dashboard_presenter, now
):
    request = make_request(dashboard_presenter, threshold_minutes=12)

    generator = open_stream(request)
    await generator.__anext__()
    second = await generator.__anext__()
    payload = cast(AtRiskThreshold, second.data).model_dump(mode="json")

    assert set(payload) == {"at_risk_threshold_minutes"}
    assert payload["at_risk_threshold_minutes"] == 12
    await generator.aclose()
