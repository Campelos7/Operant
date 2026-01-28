from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPERANT_", case_sensitive=False)

    env: str = "local"
    database_url: str = "postgresql+psycopg2://operant:operant@localhost:5432/operant"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 15 * 60
    jwt_refresh_ttl_seconds: int = 30 * 24 * 60 * 60

    password_bcrypt_rounds: int = 12


settings = Settings()


