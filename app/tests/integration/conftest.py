import asyncio
import os
from typing import Any, AsyncGenerator

from asgi_lifespan import LifespanManager
import boto3
from botocore.client import Config
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from config.config import settings
from infrastructure.db.db import get_db
from main import app as actual_app


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

def _join_root_path(root_path: str, path: str) -> str:
    root = (root_path or "").rstrip("/")
    if root == "/":
        root = ""
    if not path.startswith("/"):
        path = "/" + path
    return f"{root}{path}" if root else path


# Создаем асинхронный движок; каждый тест получает новый движок
@pytest.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()


# Фикстура, которая открывает соединение на время теста.
@pytest.fixture(scope="function")
async def async_connection(async_engine) -> AsyncGenerator[AsyncConnection, None]:
    connection = await async_engine.connect()
    yield connection
    await connection.close()


# Фикстура, создающая асинхронную сессию, привязанную к тому же соединению с применёнными миграциями.
@pytest.fixture(scope="function")
async def session(async_connection):
    async_session_factory = async_sessionmaker(bind=async_connection, expire_on_commit=False)
    async with async_session_factory() as session:
        # Create Tables
        from infrastructure.db.db import Base
        from infrastructure.db.models.book_orm import BookORM

        # Sync run because create_all is not async directly on connection easily without run_sync
        await async_connection.run_sync(Base.metadata.create_all)

        # Initialize FTS
        # We need to do this manually via raw SQL on the connection or session
        # Use underlying sync connection for sqlite3 specific fts creation if possible,
        # or just execute valid SQL via text()

        from sqlalchemy import text

        await session.execute(
            text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
                title, 
                author, 
                content='books', 
                content_rowid='id'
            );
        """)
        )
        await session.execute(text("INSERT INTO books_fts(books_fts) VALUES('rebuild');"))

        # Load Data from Fixture
        import json
        import os

        # Path relative to app/tests/integration/conftest.py?
        # app/tests/integration/../../tests/fixtures/akunin_books.json -> app/tests/fixtures/akunin_books.json
        # Running inside container, workdir /app. Fixtures are at /app/tests/fixtures if copied?
        # Dockerfile COPY app /app.
        # wait, app/tests/fixtures is inside app folder?
        # Yes, I created app/tests/fixtures.

        fixture_path = "/app/tests/fixtures/akunin_books.json"

        # Fallback for local run if path differs (optional)
        if not os.path.exists(fixture_path):
            # Try relative
            fixture_path = os.path.join(os.path.dirname(__file__), "../fixtures/akunin_books.json")

        if os.path.exists(fixture_path):
            with open(fixture_path, "r") as f:
                books_data = json.load(f)

            for b in books_data:
                # Filter out keys not in ORM (if any extra in DB extraction)
                # BookORM has specific fields.
                # extract_fixture.py did "select *", so columns should match.
                # However, BookORM might not have ALL columns if I missed some in definition?
                # I defined BookORM with all columns from 'schema books' output. Should be fine.
                book = BookORM(**b)
                session.add(book)
            await session.commit()

            # Update FTS after insert
            await session.execute(text("INSERT INTO books_fts(books_fts) VALUES('rebuild');"))
            await session.commit()

        yield session


@pytest.fixture(scope="function", autouse=True)
async def session_override(app, session) -> None:
    """Overriding session generator in the app"""

    async def get_db_session_override():
        """Generator with test session"""
        yield session

    app.dependency_overrides[get_db] = get_db_session_override


@pytest.fixture
async def app():
    async with LifespanManager(actual_app):
        yield actual_app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def api_url():
    def _api_url(path: str) -> str:
        return _join_root_path(settings.API_ROOT_PATH, path)

    return _api_url


@pytest.fixture(scope="session")
def s3_test_config() -> dict[str, str]:
    return {
        "endpoint": os.getenv("TEST_S3_ENDPOINT", settings.S3_ENDPOINT),
        "access_key": os.getenv("TEST_S3_ACCESS_KEY", settings.S3_ACCESS_KEY),
        "secret_key": os.getenv("TEST_S3_SECRET_KEY", settings.S3_SECRET_KEY),
        "bucket": os.getenv("TEST_S3_BUCKET", settings.S3_BUCKET),
        "region": os.getenv("TEST_S3_REGION", settings.S3_REGION),
    }


@pytest.fixture(scope="function")
async def ensure_s3_available(s3_test_config):
    def _client():
        return boto3.client(
            "s3",
            endpoint_url=s3_test_config["endpoint"],
            aws_access_key_id=s3_test_config["access_key"],
            aws_secret_access_key=s3_test_config["secret_key"],
            region_name=s3_test_config["region"],
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    last_err: Exception | None = None
    for _ in range(30):
        try:
            await asyncio.to_thread(_client().list_buckets)
            break
        except Exception as ex:  # noqa: BLE001
            last_err = ex
            await asyncio.sleep(1)
    else:
        raise RuntimeError(
            "MinIO недоступен. Подними его через `docker compose up -d minio` (или `docker compose up -d`)."
        ) from last_err

    bucket = s3_test_config["bucket"]

    def _ensure_bucket():
        cli = _client()
        try:
            cli.head_bucket(Bucket=bucket)
        except Exception:  # noqa: BLE001
            cli.create_bucket(Bucket=bucket)

    await asyncio.to_thread(_ensure_bucket)
