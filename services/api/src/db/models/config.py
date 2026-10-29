from sqlmodel import Field, SQLModel

DEFAULT_AT_RISK_THRESHOLD_MINUTES = 10


class Config(SQLModel, table=True):
    __tablename__ = "config"

    id: int | None = Field(default=None, primary_key=True)
    at_risk_threshold_minutes: int = Field(default=DEFAULT_AT_RISK_THRESHOLD_MINUTES)
