import pytest
from sqlalchemy import text

from infrastructure.db.fts import ensure_books_fts
from infrastructure.db.fts_query import build_books_fts5_match_query, build_fts5_match_query


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


@pytest.mark.asyncio
@pytest.mark.unit
async def test_build_fts5_match_query_handles_yo_e_variants(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT);"))
        await conn.execute(text("DELETE FROM books;"))
        await conn.execute(
            text("INSERT INTO books(id, title, author) VALUES (1, 'Чёрный город', 'Борис Акунин');")
        )

    await ensure_books_fts(async_engine)

    q = build_fts5_match_query("Акунин Черный город")
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


@pytest.mark.asyncio
@pytest.mark.unit
async def test_build_books_fts5_match_query_supports_author_title_filters(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT);"))
        await conn.execute(text("DELETE FROM books;"))
        await conn.execute(text("INSERT INTO books(id, title, author) VALUES (1, 'Азазель', 'Борис Акунин');"))

    await ensure_books_fts(async_engine)

    q_title = build_books_fts5_match_query(title="Азазель")
    q_author_wrong = build_books_fts5_match_query(author="Азазель")
    q_combo = build_books_fts5_match_query(author="Акунин", title="Азазель")

    assert q_title
    assert q_author_wrong
    assert q_combo

    async with async_engine.connect() as conn:
        stmt = text("SELECT rowid FROM books_fts WHERE books_fts MATCH :q;")
        rows_title = (await conn.execute(stmt, {"q": q_title})).scalars().all()
        rows_author_wrong = (await conn.execute(stmt, {"q": q_author_wrong})).scalars().all()
        rows_combo = (await conn.execute(stmt, {"q": q_combo})).scalars().all()

    assert 1 in rows_title
    assert 1 not in rows_author_wrong
    assert 1 in rows_combo
