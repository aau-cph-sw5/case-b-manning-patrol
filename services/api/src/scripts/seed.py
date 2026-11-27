"""Seed the database with the fixture event timeline for local development.

Event IDs are derived from the fixture, so running the script again only
inserts rows that are missing and never rewrites existing ones.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine, upgrade_db
from src.db.models.adjustment import Adjustment
from src.db.models.adjustment_author import AdjustmentAuthor
from src.db.models.event import Event
from src.db.models.steward_shift_identity import StewardShiftIdentity
from src.domain.event import EventType
from src.services.positioning_service import load_fixture
from src.services.shared.shift_schedule import ShiftSchedule

FIXTURE = "fixture-events-v1.json"
SOURCE = "seed"
SEED_NAMESPACE = uuid5(NAMESPACE_URL, "manning-patrol/seed")
SHIFT_SCHEDULE = ShiftSchedule.from_file()

FIXTURE_EVENT_TYPES = {
    "CONNECTED": EventType.CONNECT_EVENT,
    "DISCONNECTED": EventType.DISCONNECT_EVENT,
}


@dataclass
class SeedResult:
    """How many rows a seed run inserted."""

    identities_inserted: int
    events_inserted: int
    adjustments_inserted: int


def _seed_id(name: str) -> UUID:
    return uuid5(SEED_NAMESPACE, name)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _shift_start(timestamp: datetime) -> datetime:
    return SHIFT_SCHEDULE.latest_shift(timestamp).start


def _steward_ref(android_id: str, timestamp: datetime) -> UUID:
    shift_start = _shift_start(timestamp).isoformat()
    return _seed_id(f"{FIXTURE}/steward/{android_id}/{shift_start}")


def build_steward_identities(fixture: list[dict]) -> list[StewardShiftIdentity]:
    """Return one steward identity per device and scheduled shift in the fixture.

    Shifts are assigned with the same schedule the event producer uses, and
    each ``steward_ref`` is derived from the device and shift so reruns reuse
    it.
    """
    shifts = {
        (entry["android_id"], _shift_start(_parse_timestamp(entry["timestamp"])))
        for entry in fixture
    }
    return [
        StewardShiftIdentity(
            steward_ref=_steward_ref(android_id, shift_start),
            android_id=UUID(android_id),
            shift_start=shift_start,
        )
        for android_id, shift_start in sorted(shifts)
    ]


def load_events(filename: str) -> list[Event]:
    """Load the fixture as events, failing loudly instead of seeding nothing."""
    fixture = load_fixture(filename)
    if not fixture:
        raise FileNotFoundError(f"Fixture {filename} is missing or empty")
    return build_events(fixture)


def build_events(fixture: list[dict]) -> list[Event]:
    """Turn the fixture timeline into events, wrapped in a patrol session.

    Events reference their device through the steward reference that
    ``build_steward_identities`` creates for its shift. The added session
    start and stop events share the reference of the event they wrap.
    """
    events = [
        Event(
            event_id=_seed_id(f"{FIXTURE}/{entry['debugging_number']}"),
            event_type=FIXTURE_EVENT_TYPES[entry["event"]],
            steward_ref=_steward_ref(
                entry["android_id"],
                _parse_timestamp(entry["timestamp"]),
            ),
            beacon_id=UUID(entry["beacon_id"]),
            device_timestamp=_parse_timestamp(entry["timestamp"]),
            server_timestamp=_parse_timestamp(entry["timestamp"]),
            source=SOURCE,
        )
        for entry in fixture
    ]
    if not events:
        return []

    first, last = events[0], events[-1]
    session_bounds = [
        ("shift_start", EventType.START_EVENT, first, -timedelta(minutes=1)),
        ("shift_stop", EventType.STOP_EVENT, last, timedelta(minutes=1)),
    ]
    for name, event_type, anchor, offset in session_bounds:
        timestamp = anchor.device_timestamp + offset
        events.append(
            Event(
                event_id=_seed_id(f"{FIXTURE}/{name}"),
                event_type=event_type,
                steward_ref=anchor.steward_ref,
                beacon_id=None,
                device_timestamp=timestamp,
                server_timestamp=timestamp,
                source=SOURCE,
            ),
        )

    return sorted(events, key=lambda event: event.device_timestamp)


def build_adjustments(events: list[Event]) -> list[Adjustment]:
    """Correct the station 4 signal blip (fixture event 10) as a supervisor."""
    blip_id = _seed_id(f"{FIXTURE}/10")
    blip = next((event for event in events if event.event_id == blip_id), None)
    if blip is None:
        raise ValueError(f"Fixture {FIXTURE} has no event 10 to adjust")

    return [
        Adjustment(
            adjustment_id=_seed_id(f"{FIXTURE}/adjustment/10"),
            target_event_id=blip.event_id,
            server_timestamp=blip.server_timestamp + timedelta(hours=2),
            corrected_fact_type=EventType.CONNECT_EVENT,
            corrected_beacon_id=blip.beacon_id,
            corrected_occured_at=blip.device_timestamp,
            source=SOURCE,
        ),
    ]


def build_adjustment_authors(
    fixture: list[dict], adjustments: list[Adjustment]
) -> list[AdjustmentAuthor]:
    """Record the seed supervisor as author of each seed adjustment.

    The device is taken from fixture event 10, the blip the adjustments
    correct, since stored events no longer hold the device ID.
    """
    blip = next(entry for entry in fixture if entry["debugging_number"] == 10)
    return [
        AdjustmentAuthor(
            adjustment_id=adjustment.adjustment_id,
            android_id=UUID(blip["android_id"]),
            reason="Signal blip, steward did not leave the platform",
            author="seed-supervisor",
            server_timestamp=adjustment.server_timestamp,
            source=SOURCE,
        )
        for adjustment in adjustments
    ]


async def seed(session: AsyncSession) -> SeedResult:
    """Insert the fixture identities, events and adjustment not stored yet.

    An adjustment's author row is inserted together with the adjustment.
    """
    identities = build_steward_identities(load_fixture(FIXTURE))
    events = load_events(FIXTURE)
    adjustments = build_adjustments(events)

    existing_identities = set(
        (
            await session.exec(
                select(StewardShiftIdentity.steward_ref).where(
                    col(StewardShiftIdentity.steward_ref).in_(
                        [i.steward_ref for i in identities],
                    ),
                ),
            )
        ).all(),
    )

    existing_events = set(
        (
            await session.exec(
                select(Event.event_id).where(
                    col(Event.event_id).in_([e.event_id for e in events]),
                ),
            )
        ).all(),
    )
    existing_adjustments = set(
        (
            await session.exec(
                select(Adjustment.adjustment_id).where(
                    col(Adjustment.adjustment_id).in_(
                        [a.adjustment_id for a in adjustments],
                    ),
                ),
            )
        ).all(),
    )

    new_identities = [i for i in identities if i.steward_ref not in existing_identities]
    new_events = [e for e in events if e.event_id not in existing_events]
    new_adjustments = [
        a for a in adjustments if a.adjustment_id not in existing_adjustments
    ]
    session.add_all(new_identities)
    await session.flush()
    session.add_all(new_events)
    session.add_all(new_adjustments)
    await session.flush()
    session.add_all(build_adjustment_authors(load_fixture(FIXTURE), new_adjustments))
    await session.commit()

    return SeedResult(
        identities_inserted=len(new_identities),
        events_inserted=len(new_events),
        adjustments_inserted=len(new_adjustments),
    )


async def _run() -> SeedResult:
    try:
        async with AsyncSession(engine) as session:
            return await seed(session)
    finally:
        await engine.dispose()


def main():
    """Apply pending migrations and insert the seed data."""
    upgrade_db()
    result = asyncio.run(_run())
    print(
        f"Inserted {result.identities_inserted} steward identities, "
        f"{result.events_inserted} events and "
        f"{result.adjustments_inserted} adjustments.",
    )


if __name__ == "__main__":
    main()
