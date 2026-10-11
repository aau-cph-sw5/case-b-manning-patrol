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

from src.db.main import engine, init_db
from src.models.event import Adjustment, Event, EventType
from src.services.positioning_service import load_fixture

FIXTURE = "fixture-events-v1.json"
SOURCE = "seed"
SEED_NAMESPACE = uuid5(NAMESPACE_URL, "manning-patrol/seed")

FIXTURE_EVENT_TYPES = {
    "CONNECTED": EventType.CONNECT_EVENT,
    "DISCONNECTED": EventType.DISCONNECT_EVENT,
}


@dataclass
class SeedResult:
    events_inserted: int
    adjustments_inserted: int


def _seed_id(name: str) -> UUID:
    return uuid5(SEED_NAMESPACE, name)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_events(fixture: list[dict]) -> list[Event]:
    """Turn the fixture timeline into events, wrapped in a patrol session."""
    events = [
        Event(
            event_id=_seed_id(f"{FIXTURE}/{entry['debugging_number']}"),
            event_type=FIXTURE_EVENT_TYPES[entry["event"]],
            actor=entry["android_id"],
            beacon=entry["beacon_id"],
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
        ("start", EventType.START_EVENT, first, -timedelta(minutes=1)),
        ("stop", EventType.STOP_EVENT, last, timedelta(minutes=1)),
    ]
    for name, event_type, anchor, offset in session_bounds:
        timestamp = anchor.device_timestamp + offset
        events.append(
            Event(
                event_id=_seed_id(f"{FIXTURE}/{name}"),
                event_type=event_type,
                actor=anchor.actor,
                beacon=None,
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
        return []

    return [
        Adjustment(
            adjustment_id=_seed_id(f"{FIXTURE}/adjustment/10"),
            target_event_id=blip.event_id,
            actor=blip.actor,
            reason="Signal blip, steward did not leave the platform",
            author="seed-supervisor",
            server_timestamp=blip.server_timestamp + timedelta(hours=2),
            corrected_fact_type=EventType.CONNECT_EVENT,
            corrected_beacon_id=blip.beacon,
            corrected_occured_at=blip.device_timestamp,
            source=SOURCE,
        ),
    ]


async def seed(session: AsyncSession) -> SeedResult:
    events = build_events(load_fixture(FIXTURE))
    adjustments = build_adjustments(events)

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

    new_events = [e for e in events if e.event_id not in existing_events]
    new_adjustments = [
        a for a in adjustments if a.adjustment_id not in existing_adjustments
    ]
    session.add_all(new_events)
    session.add_all(new_adjustments)
    await session.commit()

    return SeedResult(
        events_inserted=len(new_events),
        adjustments_inserted=len(new_adjustments),
    )


async def _run() -> SeedResult:
    await init_db()
    try:
        async with AsyncSession(engine) as session:
            return await seed(session)
    finally:
        await engine.dispose()


def main():
    """Create tables if needed and insert the seed data."""
    result = asyncio.run(_run())
    print(
        f"Inserted {result.events_inserted} events and "
        f"{result.adjustments_inserted} adjustments.",
    )


if __name__ == "__main__":
    main()
