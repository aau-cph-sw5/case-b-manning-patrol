# src/services/anonymizer.py
from datetime import UTC, datetime, timedelta

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment_author import AdjustmentAuthor
from src.db.models.expired_record import ExpiredRecord, ExpiredTarget
from src.db.models.steward_shift_identity import StewardShiftIdentity

RETENTION_PERIOD = timedelta(days=5 * 365)


async def anonymize_old_records(session: AsyncSession):
    """Anonymize records older than the retention period.

    Every anonymized row is an expiry action and gets one ExpiredRecord.
    """
    now = datetime.now(UTC)
    cutoff_date = now - RETENTION_PERIOD

    authors = (
        await session.exec(
            select(AdjustmentAuthor)
            .where(col(AdjustmentAuthor.server_timestamp) <= cutoff_date)
            .where(col(AdjustmentAuthor.anonymized_at).is_(None))
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

    await session.commit()
