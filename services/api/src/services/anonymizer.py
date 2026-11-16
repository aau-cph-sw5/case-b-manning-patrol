# src/services/anonymizer.py
from datetime import UTC, datetime, timedelta

from sqlmodel import col, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment_author import AdjustmentAuthor

RETENTION_PERIOD = timedelta(days=5 * 365)


async def anonymize_old_records(session: AsyncSession):
    """anonymize authors of adjustments older than retention period"""
    cutoff_date = datetime.now(UTC) - RETENTION_PERIOD

    statement = (
        update(AdjustmentAuthor)
        .where(col(AdjustmentAuthor.server_timestamp) <= cutoff_date)
        .where(col(AdjustmentAuthor.anonymized_at).is_(None))
        .values(
            android_id=None, reason=None, author=None, anonymized_at=datetime.now(UTC)
        )
    )
    await session.exec(statement)
    await session.commit()
