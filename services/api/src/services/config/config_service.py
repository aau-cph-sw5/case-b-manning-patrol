"""Read and update the system configuration stored in the database."""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.config import (
    get_or_create_config,
    set_at_risk_threshold_minutes,
)


class ConfigService:
    """Read and update backend settings kept in the single-row config table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_at_risk_threshold_minutes(self) -> int:
        """Return the at-risk threshold in minutes, using the default if unset."""
        config = await get_or_create_config(self._session)
        return config.at_risk_threshold_minutes

    async def set_at_risk_threshold_minutes(self, minutes: int) -> int:
        """Store the at-risk threshold in minutes and return the stored value."""
        config = await set_at_risk_threshold_minutes(self._session, minutes=minutes)
        return config.at_risk_threshold_minutes
