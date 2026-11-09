"""Settings read from environment variables and the .env file."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./local.db"


class SystemConfig(BaseSettings):
    """Backend settings; ``DATABASE_URL`` defaults to a local SQLite file."""

    DATABASE_URL: SecretStr = SecretStr(DEFAULT_DATABASE_URL)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


system_config = SystemConfig()
