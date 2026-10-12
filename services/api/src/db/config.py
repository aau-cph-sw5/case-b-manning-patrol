from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./local.db"


class Settings(BaseSettings):
    DATABASE_URL: SecretStr = SecretStr(DEFAULT_DATABASE_URL)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
