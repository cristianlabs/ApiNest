from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApiNest"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://apinest:apinest@db:5432/apinest"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:3000"]

    rest_client_timeout_seconds: float = 15.0


settings = Settings()
