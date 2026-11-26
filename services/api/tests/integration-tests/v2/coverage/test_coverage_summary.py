"""Tests for the episode onset summary endpoint."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.at_risk_log import AtRiskLogEntry
from src.db.models.overdue_log import OverdueLogEntry
from src.services.shared.shift_schedule import ShiftSchedule


def _overdue_row(
    entry_id: str,
    overdue_at: datetime,
    cleared_at: datetime | None,
    entry_type: str = "DETECTED",
):
    return OverdueLogEntry(
        entry_id=f"{entry_id}:{entry_type}",
        entry_type=entry_type,
        station_id="marmorkirken",
        area_id=f"{entry_id}-area",
        area_kind="station_level",
        overdue_at=overdue_at,
        detected_at=overdue_at + timedelta(minutes=1)
        if entry_type == "DETECTED"
        else None,
        last_covered_at=None,
        cleared_at=cleared_at,
        source="test",
    )


def _at_risk_row(
    entry_id: str, shift_start: datetime, at_risk_at: datetime, overdue_at: datetime
):
    return AtRiskLogEntry(
        entry_id=entry_id,
        station_id="marmorkirken",
        area_id=f"{entry_id}-area",
        area_kind="station_level",
        at_risk_at=at_risk_at,
        overdue_at=overdue_at,
        detected_at=overdue_at,
        shift_start=shift_start,
        source="test",
    )


@pytest_asyncio.fixture
async def seeded_session(db_engine) -> AsyncGenerator[AsyncSession]:
    """Yield a session seeded with episodes that begin at known shift offsets."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        schedule = ShiftSchedule.from_file()
        shift_start = schedule.latest_shift(datetime.now(UTC)).start
        other_shift_start = shift_start - timedelta(days=1)

        # Overdue one hour into the shift: bucket 1.
        session.add(
            _overdue_row(
                "overdue-1",
                shift_start + timedelta(hours=1),
                shift_start + timedelta(hours=1, seconds=30),
                "DETECTED",
            )
        )
        session.add(
            _overdue_row(
                "overdue-1",
                shift_start + timedelta(hours=1),
                shift_start + timedelta(hours=1, seconds=30),
                "CLEARED",
            )
        )
        # Overdue two hours into the shift: bucket 2.
        session.add(
            _overdue_row(
                "overdue-2",
                shift_start + timedelta(hours=2),
                shift_start + timedelta(hours=2, seconds=90),
                "DETECTED",
            )
        )
        session.add(
            _overdue_row(
                "overdue-2",
                shift_start + timedelta(hours=2),
                shift_start + timedelta(hours=2, seconds=90),
                "CLEARED",
            )
        )
        # Still open, but its onset is what counts: bucket 3.
        session.add(
            _overdue_row(
                "overdue-open", shift_start + timedelta(hours=3), None, "DETECTED"
            )
        )
        # Belongs to another shift, so omitted from the latest shift.
        session.add(
            _overdue_row(
                "overdue-old",
                other_shift_start + timedelta(hours=1),
                other_shift_start + timedelta(hours=1, seconds=30),
                "DETECTED",
            )
        )
        # At-risk one hour into the shift: bucket 1.
        session.add(
            _at_risk_row(
                "at-risk-1",
                shift_start,
                shift_start + timedelta(hours=1),
                shift_start + timedelta(hours=1, minutes=45),
            )
        )
        # Belongs to another shift, so omitted from the latest shift.
        session.add(
            _at_risk_row(
                "at-risk-old",
                other_shift_start,
                other_shift_start + timedelta(hours=1),
                other_shift_start + timedelta(hours=1, minutes=45),
            )
        )
        await session.commit()
        yield session


def test_summary_buckets_episode_onsets(client, seeded_session):
    response = client.get("/api/v2/coverage/summary")

    assert response.status_code == 200
    buckets = response.json()["buckets"]
    assert buckets[1] == {
        "label": "1:00-1:59",
        "overdue_count": 1,
        "at_risk_count": 1,
    }
    assert buckets[2] == {
        "label": "2:00-2:59",
        "overdue_count": 1,
        "at_risk_count": 0,
    }
    assert buckets[3] == {
        "label": "3:00-3:59",
        "overdue_count": 1,
        "at_risk_count": 0,
    }


def test_summary_zero_fills_and_stops_after_last_onset(client, seeded_session):
    response = client.get("/api/v2/coverage/summary")

    buckets = response.json()["buckets"]
    assert len(buckets) == 4
    assert buckets[0] == {
        "label": "0:00-0:59",
        "overdue_count": 0,
        "at_risk_count": 0,
    }


def test_summary_uses_the_requested_shift(client, seeded_session):
    schedule = ShiftSchedule.from_file()
    other_shift_start = schedule.latest_shift(datetime.now(UTC)).start - timedelta(
        days=1
    )

    response = client.get(
        "/api/v2/coverage/summary",
        params={"shift_start": other_shift_start.isoformat()},
    )

    buckets = response.json()["buckets"]
    assert len(buckets) == 2
    assert buckets[1] == {
        "label": "1:00-1:59",
        "overdue_count": 1,
        "at_risk_count": 1,
    }


def test_summary_has_no_buckets_without_episodes(client):
    response = client.get("/api/v2/coverage/summary")

    assert response.status_code == 200
    assert response.json()["buckets"] == []
