from pathlib import Path
from typing import ClassVar, Literal
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LogLevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{(PROJECT_ROOT / 'librarry.db').as_posix()}"
DEFAULT_BOOKS_ARCHIVES_PATH = PROJECT_ROOT / "books"


class Settings(BaseSettings):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App path settings
    API_ROOT_PATH: str = Field("/api", description="Базовый путь приложения (FastAPI root_path), например '/api'")

    # DB Settings
    DATABASE_URL: str = Field(DEFAULT_DB_URL, description="DB URL")

    # TimeZone settings
    TZ: ZoneInfo = Field(ZoneInfo("UTC"), description="Временная зона")

    # Logging settings
    LOG_LEVEL: LogLevels = Field("INFO", description="Уровень логирования")

    # Local books archive settings
    BOOKS_ARCHIVES_PATH: Path = Field(DEFAULT_BOOKS_ARCHIVES_PATH, description="Путь до папки с архивами книг")

    # S3 / MinIO settings
    S3_ENDPOINT: str = Field("http://minio:9000", description="S3 endpoint URL (например, MinIO)")
    S3_ACCESS_KEY: str = Field("minioadmin", description="S3 access key")
    S3_SECRET_KEY: str = Field("minioadmin", description="S3 secret key")
    S3_BUCKET: str = Field("book-library", description="S3 bucket name")
    S3_REGION: str = Field("us-east-1", description="S3 region name (для SigV4)")

    @field_validator("S3_ENDPOINT", mode="before")
    @classmethod
    def _parse_s3_endpoint(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            return v

        normalized = v.strip()
        if (normalized.startswith('"') and normalized.endswith('"')) or (
            normalized.startswith("'") and normalized.endswith("'")
        ):
            normalized = normalized[1:-1].strip()

        # Частая ошибка в env: S3_ENDPOINT=minio:9000 (без схемы).
        if normalized and "://" not in normalized:
            normalized = "http://" + normalized

        return normalized.rstrip("/")

    @field_validator("TZ", mode="before")
    @classmethod
    def _parse_tz(cls, v):
        return ZoneInfo(v) if isinstance(v, str) else v

    @field_validator("API_ROOT_PATH", mode="before")
    @classmethod
    def _parse_api_root_path(cls, v):
        if v is None:
            return "/api"
        if not isinstance(v, str):
            return v

        normalized = v.strip()
        if (normalized.startswith('"') and normalized.endswith('"')) or (
            normalized.startswith("'") and normalized.endswith("'")
        ):
            normalized = normalized[1:-1].strip()

        if normalized in ("", "/"):
            return ""

        if not normalized.startswith("/"):
            normalized = "/" + normalized

        return normalized.rstrip("/")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _default_sqlite_if_empty(cls, v: str | None):
        # Allow an empty env var to fall back to the bundled SQLite DB.
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return DEFAULT_DB_URL
        return v

    @field_validator("BOOKS_ARCHIVES_PATH", mode="before")
    @classmethod
    def _parse_books_archives_path(cls, v):
        # В docker-compose/.env значения иногда задают в кавычках (например, BOOKS_ARCHIVES_PATH="/books").
        # В контейнер/настройки это может приехать буквально с кавычками, и Path будет указывать на несуществующий путь.
        if isinstance(v, Path):
            normalized = str(v).strip()
        elif isinstance(v, str):
            normalized = v.strip()
        else:
            return v

        if (normalized.startswith('"') and normalized.endswith('"')) or (
            normalized.startswith("'") and normalized.endswith("'")
        ):
            normalized = normalized[1:-1].strip()

        return Path(normalized)


settings = Settings()
