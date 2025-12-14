from pathlib import Path

from config.config import Settings


def test_books_archives_path_strips_wrapping_quotes():
    settings = Settings(BOOKS_ARCHIVES_PATH='"/books"')
    assert settings.BOOKS_ARCHIVES_PATH == Path("/books")


def test_books_archives_path_keeps_unquoted_value():
    settings = Settings(BOOKS_ARCHIVES_PATH="/books")
    assert settings.BOOKS_ARCHIVES_PATH == Path("/books")
