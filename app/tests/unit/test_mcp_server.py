from contextlib import asynccontextmanager

import pytest

from domain.exceptions import BooksNotFoundError, EmailSendError, NotFoundError, ValueException
from domain.models.book import Book
from main import app
from mcp_server import server


class _SearchService:
    def __init__(self) -> None:
        self.search_kwargs: dict[str, str | None] | None = None

    async def search(self, *, q: str | None = None, author: str | None = None, title: str | None = None):
        self.search_kwargs = {"q": q, "author": author, "title": title}
        return [
            Book(
                id=1,
                author="Акунин Борис",
                title="Азазель",
                archive_name="books.zip",
                file_name="azazel.fb2",
                file_size_mb=1.5,
            )
        ]


class _NoResultsService:
    async def search(self, *, q: str | None = None, author: str | None = None, title: str | None = None):
        raise BooksNotFoundError("Нет результатов")


class _ExportService:
    async def export_book_to_s3(self, book_id: int):
        return {"bucket": "books", "key": f"{book_id}_book.fb2", "existed": False}


class _NotFoundExportService:
    async def export_book_to_s3(self, book_id: int):
        raise NotFoundError


class _EmailService:
    def __init__(self) -> None:
        self.kwargs: dict[str, str] | None = None

    async def send_book_to_email(self, *, bucket: str, file_key: str, to: str, subject: str, text: str):
        self.kwargs = {
            "bucket": bucket,
            "file_key": file_key,
            "to": to,
            "subject": subject,
            "text": text,
        }
        return {"detail": "The file has been successfully sent to email."}


class _NotInS3EmailService:
    async def send_book_to_email(self, *, bucket: str, file_key: str, to: str, subject: str, text: str):
        raise ValueException("Файл книги не найден в S3. Сначала вызови export_book_to_s3.")


class _FailingEmailService:
    async def send_book_to_email(self, *, bucket: str, file_key: str, to: str, subject: str, text: str):
        raise EmailSendError("Сервис отправки писем недоступен")


def _service_context(service):
    @asynccontextmanager
    async def _context():
        yield service

    return _context


@pytest.mark.asyncio
async def test_mcp_search_books_trims_and_delegates(monkeypatch):
    service = _SearchService()
    monkeypatch.setattr(server, "book_service_context", _service_context(service))

    result = await server.search_books(author="  Акунин  ", title=" Азазель ")

    assert result.status == "ok"
    assert result.books[0].id == 1
    assert service.search_kwargs == {"q": None, "author": "Акунин", "title": "Азазель"}


@pytest.mark.asyncio
async def test_mcp_search_books_returns_validation_error_without_query():
    result = await server.search_books(q=" ", author=None, title=None)

    assert result.status == "validation_error"
    assert result.detail == "Нужно указать хотя бы один параметр поиска: q, author или title."


@pytest.mark.asyncio
async def test_mcp_search_books_maps_no_results(monkeypatch):
    monkeypatch.setattr(server, "book_service_context", _service_context(_NoResultsService()))

    result = await server.search_books(title="нет")

    assert result.status == "no_results"
    assert result.detail == "Нет результатов"


@pytest.mark.asyncio
async def test_mcp_export_book_to_s3_returns_export_data(monkeypatch):
    monkeypatch.setattr(server, "book_service_context", _service_context(_ExportService()))

    result = await server.export_book_to_s3(42)

    assert result.status == "ok"
    assert result.bucket == "books"
    assert result.key == "42_book.fb2"
    assert result.existed is False


@pytest.mark.asyncio
async def test_mcp_export_book_to_s3_maps_not_found(monkeypatch):
    monkeypatch.setattr(server, "book_service_context", _service_context(_NotFoundExportService()))

    result = await server.export_book_to_s3(404)

    assert result.status == "not_found"
    assert result.detail == "Книга не найдена"


@pytest.mark.asyncio
async def test_mcp_send_book_to_email_returns_ok(monkeypatch):
    service = _EmailService()
    monkeypatch.setattr(server, "book_service_context", _service_context(service))

    result = await server.send_book_to_email(
        bucket="books",
        file_key="103582_akunin-boris_azazel_0_39.fb2",
        to="hudro795@gmail.com",
        subject="Ваша книга",
        text="Получи свою книгу!",
    )

    assert result.status == "ok"
    assert result.detail == "The file has been successfully sent to email."
    assert service.kwargs == {
        "bucket": "books",
        "file_key": "103582_akunin-boris_azazel_0_39.fb2",
        "to": "hudro795@gmail.com",
        "subject": "Ваша книга",
        "text": "Получи свою книгу!",
    }


@pytest.mark.asyncio
async def test_mcp_send_book_to_email_maps_not_in_s3(monkeypatch):
    monkeypatch.setattr(server, "book_service_context", _service_context(_NotInS3EmailService()))

    result = await server.send_book_to_email(
        bucket="books",
        file_key="missing.fb2",
        to="hudro795@gmail.com",
        subject="Ваша книга",
        text="Получи свою книгу!",
    )

    assert result.status == "not_in_s3"
    assert "export_book_to_s3" in (result.detail or "")


@pytest.mark.asyncio
async def test_mcp_send_book_to_email_maps_email_send_failed(monkeypatch):
    monkeypatch.setattr(server, "book_service_context", _service_context(_FailingEmailService()))

    result = await server.send_book_to_email(
        bucket="books",
        file_key="103582_akunin-boris_azazel_0_39.fb2",
        to="hudro795@gmail.com",
        subject="Ваша книга",
        text="Получи свою книгу!",
    )

    assert result.status == "email_send_failed"
    assert result.detail == "Сервис отправки писем недоступен"


def test_mcp_http_route_registered_at_top_level():
    mcp_routes = [
        route
        for route in app.routes
        if type(route).__name__ == "Route" and getattr(route, "path", None) == "/mcp"
    ]

    assert mcp_routes
