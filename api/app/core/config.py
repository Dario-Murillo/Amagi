from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Amagi"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(..., alias="DATABASE_URL")
    secret_key: SecretStr = Field(..., alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Login attempts allowed per window, counted per client address and per
    # username. Generous enough that a person retrying a typo never notices.
    login_max_attempts: int = 10
    login_window_seconds: int = 60

    # Origins allowed to call the API. The frontend is served statically, so the
    # loopback host it is opened with has to match one of these exactly.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
    ]


settings = Settings()
