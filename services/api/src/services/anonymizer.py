# src/services/anonymizer.py
from datetime import datetime, timedelta, UTC
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.adjustment_author import AdjustmentAuthor

RETENTION_PERIOD = timedelta(minutes=1) #days=5*365

async def anonymize_old_records(session: AsyncSession):
    """anonymize authors of adjustments older than retention period"""
    cutoff_date = datetime.now(UTC) - RETENTION_PERIOD

    statement = (
        update(AdjustmentAuthor)
        .where(AdjustmentAuthor.server_timestamp < cutoff_date)
        .where(AdjustmentAuthor.anonymized_at.is_(None))
        .values(
            author=None,
            anonymized_at=datetime.now(UTC)
        )
    )
    await session.exec(statement)
    await session.commit()