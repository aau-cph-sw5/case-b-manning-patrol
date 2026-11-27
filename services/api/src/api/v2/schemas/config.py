"""Payloads of the config endpoints and the dashboard stream's threshold event.

Defined by the positioning-interface contract
(contracts/api/v2/positioning-interface).
"""

from pydantic import BaseModel, Field


class AtRiskThreshold(BaseModel):
    """Minutes left before an area is overdue at which it counts as at risk."""

    at_risk_threshold_minutes: int = Field(ge=1)
