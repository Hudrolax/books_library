import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine


logger = logging.getLogger(__name__)


async def ensure_books_fts(engine: AsyncEngine) -> None:
    if engine.dialect.name != "sqlite":
        logger.info("Инициализация FTS пропущена: dialect=%s", engine.dialect.name)
        return

    async with engine.begin() as conn:
        try:
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='books_fts' LIMIT 1;")
                )
            ).scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Не удалось проверить существование таблицы books_fts")
            raise

        if exists:
            return

        logger.info("Создаю FTS5 виртуальную таблицу books_fts (первый запуск на этой БД)")

        try:
            await conn.execute(
                text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
                    title,
                    author,
                    content='books',
                    content_rowid='id'
                );
            """)
            )
            await conn.execute(text("INSERT INTO books_fts(books_fts) VALUES('rebuild');"))

            await conn.execute(
                text("""
                CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
                  INSERT INTO books_fts(rowid, title, author) VALUES (new.id, new.title, new.author);
                END;
            """)
            )
            await conn.execute(
                text("""
                CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, author) VALUES('delete', old.id, old.title, old.author);
                END;
            """)
            )
            await conn.execute(
                text("""
                CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, author) VALUES('delete', old.id, old.title, old.author);
                  INSERT INTO books_fts(rowid, title, author) VALUES (new.id, new.title, new.author);
                END;
            """)
            )
        except SQLAlchemyError:
            logger.exception("Не удалось создать books_fts или триггеры FTS")
            raise
