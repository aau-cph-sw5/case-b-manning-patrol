"""
Repository of functions used to query the database related to Events
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.event import Adjustment, AdjustmentModel, Event, EventModel


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_events(session: AsyncSession) -> list[Event]:
    result = await session.exec(select(Event))

    return list(result.all())


async def insert_event(session: AsyncSession, event: EventModel) -> Event:
    event_row = Event(**event.model_dump())
    session.add(event_row)
    await session.commit()
    return event_row


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )

    return result.one()


async def get_adjustments(session: AsyncSession) -> list[Adjustment]:
    result = await session.exec(select(Adjustment))

    return list(result.all())


async def insert_adjustment(
    session: AsyncSession,
    adjustment: AdjustmentModel,
) -> Adjustment:
    adjustment_row = Adjustment(
        **adjustment.model_dump(exclude={"corrected_fact"}),
        corrected_fact_type=adjustment.corrected_fact.fact_type,
        corrected_beacon_id=adjustment.corrected_fact.beacon_id,
        corrected_occured_at=adjustment.corrected_fact.occurred_at,
    )
    session.add(adjustment_row)
    await session.commit()
    return adjustment_row
