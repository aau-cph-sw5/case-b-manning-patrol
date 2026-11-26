"""Anonymize steward identities and adjustment authors after five years."""

from datetime import UTC, datetime

from sqlalchemy import and_, or_
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment
from src.db.models.adjustment_author import AdjustmentAuthor
from src.db.models.event import Event
from src.db.models.expired_record import ExpiredRecord, ExpiredTarget
from src.db.models.steward_shift_identity import StewardShiftIdentity

RETENTION_YEARS = 5


def years_ago(now: datetime, years: int) -> datetime:
    """Return the datetime exactly `years` calendar years before `now`.

    This keeps month, day, time and timezone, so leap days inside the span
    are accounted for. If `now`is February 29 and the target year is not
    a leap year, the result falls back to February 28 of the target year.
    """

    try:
        return now.replace(year=now.year - years)
    except ValueError:
        return now.replace(year=now.year - years, day=28)


async def anonymize_old_records(session: AsyncSession):
    """Anonymize personal records past their retention period.

    An adjustment author row is anonymized when any of the following are true:
    * When adjustment targets are older than retention period
    * When the adjustment has no target event and the corrected fact is
    older than the retention period
    * When the author row itself is older than the retention period.
    Every anonymized row is an expiry action and gets oneExpiredRecord.
    """
    now = datetime.now(UTC)
    cutoff_date = years_ago(now, RETENTION_YEARS)

    identities = (
        await session.exec(
            select(StewardShiftIdentity)
            .where(col(StewardShiftIdentity.shift_start) <= cutoff_date)
            .where(col(StewardShiftIdentity.anonymized_at).is_(None))
        )
    ).all()
    for identity in identities:
        identity.android_id = None
        identity.anonymized_at = now
        session.add(
            ExpiredRecord(
                target=ExpiredTarget.STEWARD_SHIFT_IDENTITY,
                record_id=identity.steward_ref,
                server_timestamp=now,
                source="anonymizer",
            )
        )

    authors = (
        await session.exec(
            select(AdjustmentAuthor)
            .outerjoin(
                Adjustment,
                col(AdjustmentAuthor.adjustment_id) == col(Adjustment.adjustment_id),
            )
            .outerjoin(
                Event,
                col(Adjustment.target_event_id) == col(Event.event_id),
            )
            .where(col(AdjustmentAuthor.anonymized_at).is_(None))
            .where(
                or_(
                    col(Event.device_timestamp) <= cutoff_date,
                    and_(
                        col(Adjustment.target_event_id).is_(None),
                        col(Adjustment.corrected_occured_at) <= cutoff_date,
                    ),
                    col(AdjustmentAuthor.server_timestamp) <= cutoff_date,
                )
            )
        )
    ).all()
    for author in authors:
        author.android_id = None
        author.reason = None
        author.author = None
        author.anonymized_at = now
        session.add(
            ExpiredRecord(
                target=ExpiredTarget.ADJUSTMENT_AUTHOR,
                record_id=author.adjustment_id,
                server_timestamp=now,
                source="anonymizer",
            )
        )

    await session.commit()
