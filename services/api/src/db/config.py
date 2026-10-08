from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: SecretStr

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
