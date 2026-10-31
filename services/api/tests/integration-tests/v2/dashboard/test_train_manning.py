"""HTTP-driven tests for instantaneous train manning on the dashboard stream."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Line, Train, TrainLine
from src.main import app

ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001"
TRAIN_ID = "770e8400-e29b-41d4-a716-446655440001"
BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP = "2026-10-08T10:00:00+00:00"
LATER_TIMESTAMP = "2026-10-08T11:00:00+00:00"


async def insert_train(db_engine: AsyncEngine) -> None:
    async with AsyncSession(db_engine) as session:
        session.add(
            Train(
                id=UUID(TRAIN_ID),
                slug="a29",
                beacon_id=UUID(BEACON_ID),
            )
        )
        for line_id in ("M1", "M2"):
            session.add(Line(id=line_id, name=line_id))
            session.add(TrainLine(train_id=UUID(TRAIN_ID), line_id=line_id))
        await session.commit()


def train_snapshot():
    return app.state.train_manning_updater.snapshot()


def post_event(client, path: str, timestamp: str):
    return client.post(
        path,
        json={
            "android_id": ANDROID_ID,
            "beacon_id": BEACON_ID,
            "timestamp": timestamp,
        },
    )


OTHER_BEACON_ID = "550e8400-e29b-41d4-a716-446655440099"


async def test_train_without_events_is_unmanned(client, db_engine):
    await insert_train(db_engine)

    # An event on an unrelated beacon forces a refresh without touching the train.
    response = client.post(
        "/api/v2/connection/connect",
        json={
            "android_id": ANDROID_ID,
            "beacon_id": OTHER_BEACON_ID,
            "timestamp": TIMESTAMP,
        },
    )

    assert response.status_code == 201
    reports = train_snapshot()
    assert len(reports) == 1
    assert reports[0].manned_now is False
    assert reports[0].current_steward_ids == frozenset()
    assert reports[0].manned_time.total_seconds() == 0


async def test_connect_marks_the_train_manned(client, db_engine):
    await insert_train(db_engine)

    response = post_event(client, "/api/v2/connection/connect", TIMESTAMP)

    assert response.status_code == 201
    reports = train_snapshot()
    assert len(reports) == 1
    report = reports[0]
    assert str(report.train.id) == TRAIN_ID
    assert report.train.slug == "a29"
    assert report.train.line_ids == frozenset({"M1", "M2"})
    assert report.manned_now is True
    assert report.current_steward_ids == frozenset({UUID(ANDROID_ID)})


async def test_disconnect_makes_the_train_unmanned(client, db_engine):
    await insert_train(db_engine)
    post_event(client, "/api/v2/connection/connect", TIMESTAMP)

    response = post_event(client, "/api/v2/connection/disconnect", LATER_TIMESTAMP)

    assert response.status_code == 201
    reports = train_snapshot()
    assert reports[0].manned_now is False
    assert reports[0].current_steward_ids == frozenset()


async def test_dashboard_payload_exposes_train_with_line(client, db_engine):
    await insert_train(db_engine)
    post_event(client, "/api/v2/connection/connect", TIMESTAMP)

    presenter = app.state.dashboard_presenter
    dashboard = presenter.to_dashboard(
        app.state.coverage_updater.snapshot(),
        train_snapshot(),
        sent_at=datetime.now(UTC),
    )
    payload = dashboard.model_dump(mode="json")

    assert len(payload["trains"]) == 1
    train = payload["trains"][0]
    assert train["id"] == TRAIN_ID
    assert train["slug"] == "a29"
    assert train["line"] == ["M1", "M2"]
    assert train["current_steward_ids"] == [ANDROID_ID]
    assert isinstance(train["total_time_secs"], int)
    assert isinstance(train["manned_time_secs"], int)
    assert payload["stations"] is not None
