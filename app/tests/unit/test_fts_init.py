import pytest
from sqlalchemy import text

from infrastructure.db.fts import ensure_books_fts


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ensure_books_fts_creates_virtual_table(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT);"))
        await conn.execute(text("DELETE FROM books;"))
        await conn.execute(
            text("INSERT INTO books(id, title, author) VALUES (1, 'Азазель', 'Борис Акунин');")
        )

    await ensure_books_fts(async_engine)

    async with async_engine.connect() as conn:
        exists = (
            await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='books_fts' LIMIT 1;"))
        ).scalar_one_or_none()
        assert exists == "books_fts"

        # Проверяем, что rebuild действительно проиндексировал существующие записи.
        rows = (
            await conn.execute(text("SELECT rowid FROM books_fts WHERE books_fts MATCH 'Акунин';"))
        ).scalars().all()
        assert 1 in rows


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ensure_books_fts_idempotent(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT);"))
    await ensure_books_fts(async_engine)
    await ensure_books_fts(async_engine)
