from typing import Any, AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from infrastructure.db.db import get_db
from main import app as actual_app


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


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
