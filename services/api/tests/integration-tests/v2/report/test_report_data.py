"""Tests for GET /api/v2/report_data (historical compliance report endpoint).

The night shift starting 2026-10-08 runs 00:00-23:59 Europe/Copenhagen
(UTC+2), i.e. 2026-10-07T22:00:00Z to 2026-10-08T21:59:00Z.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.ingest import load_stations
from src.db.models import Event, StewardShiftIdentity, Train, TrainLine
from src.domain.event import EventType

OPS_ADMIN = {"Authorization": "Bearer operations_administrator"}

TRAIN_ID = UUID("770e8400-e29b-41d4-a716-446655440101")
TRAIN_BEACON = UUID("660e8400-e29b-41d4-a716-446655440101")
STEWARD_REF = UUID("880e8400-e29b-41d4-a716-446655440001")
ANDROID_ID = UUID("660e8400-e29b-41d4-a716-446655440002")
EVENT_ID = UUID("990e8400-e29b-41d4-a716-446655440001")

SHIFT_DAY = "2026-10-08"
SHIFT_START = datetime(2026, 10, 7, 22, 0, tzinfo=UTC)
SHIFT_END_KNOWN_AT = "2026-10-08T23:59:00+02:00"


async def seed_train_manned_all_shift(db_engine: AsyncEngine) -> None:
    """Load the station reference data and add one M1 train with a steward
    connected to its beacon from the shift start, never disconnected."""
    async with AsyncSession(db_engine) as session:
        await load_stations(session)
        session.add(Train(train_id=TRAIN_ID, slug="train-1", beacon_id=TRAIN_BEACON))
        session.add(TrainLine(train_id=TRAIN_ID, line_id="M1"))
        session.add(
            StewardShiftIdentity(
                steward_ref=STEWARD_REF,
                android_id=ANDROID_ID,
                shift_start=SHIFT_START,
            )
        )
        session.add(
            Event(
                event_id=EVENT_ID,
                event_type=EventType.CONNECT_EVENT,
                steward_ref=STEWARD_REF,
                beacon_id=TRAIN_BEACON,
                device_timestamp=SHIFT_START,
                server_timestamp=SHIFT_START,
                source="test",
            )
        )
        await session.commit()


def test_empty_database_returns_empty_report(client):
    """An empty database yields an empty report; 2020-01-01 00:00 in
    Europe/Copenhagen (UTC+1 in January) is 2019-12-31T23:00:00Z."""
    response = client.get(
        "/api/v2/report_data", params={"date": "2020-01-01"}, headers=OPS_ADMIN
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stations"] == []
    assert body["trains"] == []
    assert body["manning_percent"] is None
    assert body["m1m2_manning_percent"] is None
    assert body["m3m4_manning_percent"] is None
    assert body["known_at"] is None
    assert body["shift"]["start"] == "2019-12-31T23:00:00Z"


def test_known_at_without_timezone_offset_is_400(client):
    response = client.get(
        "/api/v2/report_data",
        params={"date": "2020-01-01", "known_at": "2020-01-01T12:00:00"},
        headers=OPS_ADMIN,
    )

    assert response.status_code == 400
    error = response.json()
    assert error["code"] == "400"
    assert "timezone offset" in error["message"]


def test_shift_that_has_not_started_is_400(client):
    response = client.get(
        "/api/v2/report_data", params={"date": "2999-01-01"}, headers=OPS_ADMIN
    )

    assert response.status_code == 400
    assert "had not started" in response.json()["message"]


async def test_report_contains_station_names_and_train_manning(client, db_engine):
    await seed_train_manned_all_shift(db_engine)

    response = client.get(
        "/api/v2/report_data",
        params={"date": SHIFT_DAY, "known_at": SHIFT_END_KNOWN_AT},
        headers=OPS_ADMIN,
    )

    assert response.status_code == 200
    body = response.json()
    station = next(s for s in body["stations"] if s["station_id"] == "STN-001")
    assert station["name"] == "Vestamager"
    assert station["line"] == ["M1"]
    assert station["areas"], "station areas are part of the report"
    (train,) = body["trains"]
    assert train["slug"] == "train-1"
    assert train["line"] == ["M1"]
    assert train["manned_ratio"] == 1.0
    assert train["manned_now"] is True
    assert train["manned_time"] == train["running_time"]
    assert body["manning_percent"] == 100.0
    assert body["m1m2_manning_percent"] == 100.0
    assert body["m3m4_manning_percent"] is None
    assert body["known_at"] == SHIFT_END_KNOWN_AT
