from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from src.api.v2.routers.trains_stream import stream
from src.api.v2.schemas.trains import TrainsUpdate
from src.domain.train_manning import TrainManningReport, TrainReference
from src.main import app as main_app
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
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


def make_request(updater, broadcaster):
    app = FastAPI()
    app.state.train_manning_updater = updater
    app.state.train_manning_broadcaster = broadcaster
    app.state.dashboard_presenter = DashboardPresenter(stations=[], station_lines=[])
    return Request(scope={"type": "http", "app": app})


def train_report(manned_now: bool = False) -> TrainManningReport:
    now = datetime.now(UTC)
    return TrainManningReport(
        train=TrainReference(
            train_id=TRAIN_ID,
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


def train_ids(event: ServerSentEvent) -> list[UUID]:
    update = cast(TrainsUpdate, event.data)
    return [train.train_id for train in update.trains]


def test_stream_is_served_at_the_contract_path():
    assert "/api/v2/trains/stream" in main_app.openapi()["paths"]


async def test_stream_sends_every_train_first():
    broadcaster = SseTrainManningBroadcaster()
    updater = FakeUpdater([train_report(manned_now=True)])
    request = make_request(updater, broadcaster)

    generator = open_stream(request)
    first = await generator.__anext__()

    assert first.event == "trains"
    assert train_ids(first) == [TRAIN_ID]
    train = cast(TrainsUpdate, first.data).trains[0]
    assert train.current_steward_ids == [STEWARD]
    assert train.line == ["M1", "M2"]
    await generator.aclose()


async def test_stream_sends_trains_on_each_refresh():
    broadcaster = SseTrainManningBroadcaster()
    updater = FakeUpdater([train_report(manned_now=True)])
    request = make_request(updater, broadcaster)

    generator = open_stream(request)
    await generator.__anext__()
    updater.set_snapshot([train_report(manned_now=False)])
    broadcaster.publish([train_report(manned_now=False)])
    second = await generator.__anext__()

    update = cast(TrainsUpdate, second.data)
    assert second.event == "trains"
    assert train_ids(second) == [TRAIN_ID]
    assert update.trains[0].current_steward_ids == []
    await generator.aclose()


async def test_stream_unsubscribes_when_the_client_disconnects():
    broadcaster = SseTrainManningBroadcaster()
    request = make_request(FakeUpdater([]), broadcaster)

    generator = open_stream(request)
    await generator.__anext__()
    assert len(broadcaster._subscribers) == 1

    await generator.aclose()

    assert len(broadcaster._subscribers) == 0


async def test_stream_payload_has_the_contract_fields():
    broadcaster = SseTrainManningBroadcaster()
    request = make_request(FakeUpdater([train_report()]), broadcaster)

    generator = open_stream(request)
    first = await generator.__anext__()
    payload = cast(TrainsUpdate, first.data).model_dump(mode="json")

    assert set(payload) == {"trains", "time"}
    assert set(payload["trains"][0]) == {
        "train_id",
        "slug",
        "total_time_secs",
        "manned_time_secs",
        "current_steward_ids",
        "line",
    }
    await generator.aclose()
