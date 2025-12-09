from pathlib import Path
from typing import ClassVar, Literal
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{(PROJECT_ROOT / 'librarry.db').as_posix()}"


class Settings(BaseSettings):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # DB Settings
    DATABASE_URL: str = Field(DEFAULT_DB_URL, description="DB URL")

    # TimeZone settings
    TZ: ZoneInfo = Field(ZoneInfo("UTC"), description="Временная зона")

    # Logging settings
    LOG_LEVEL: LogLevels = Field("INFO", description="Уровень логирования")

    @field_validator("TZ", mode="before")
    @classmethod
    def _parse_tz(cls, v):
        return ZoneInfo(v) if isinstance(v, str) else v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _default_sqlite_if_empty(cls, v: str | None):
        # Allow an empty env var to fall back to the bundled SQLite DB.
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return DEFAULT_DB_URL
        return v


settings = Settings()
