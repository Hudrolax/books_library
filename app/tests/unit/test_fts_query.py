import pytest
from sqlalchemy import text

from infrastructure.db.fts import ensure_books_fts
from infrastructure.db.fts_query import build_fts5_match_query


@pytest.mark.asyncio
@pytest.mark.unit
async def test_build_fts5_match_query_handles_hyphenated_user_input(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT);"))
        await conn.execute(text("DELETE FROM books;"))
        await conn.execute(
            text("INSERT INTO books(id, title, author) VALUES (1, 'Весь мир театр', 'Борис Акунин');")
        )

    await ensure_books_fts(async_engine)

    q = build_fts5_match_query("Акунин - Весь мир театр")
    assert q

    async with async_engine.connect() as conn:
        rows = (
            await conn.execute(text("SELECT rowid FROM books_fts WHERE books_fts MATCH :q;"), {"q": q})
        ).scalars().all()

    assert 1 in rows


@pytest.mark.unit
def test_build_fts5_match_query_empty_input():
    assert build_fts5_match_query("") == ""
    assert build_fts5_match_query("   ") == ""

