from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from composition import build_book_service
from domain.exceptions import (
    BooksNotFoundError,
    NotFoundError,
    StorageUnavailableError,
    TooManyResultsError,
    ValueException,
)
from domain.services.book_service import BookService
from infrastructure.db.db import sessionmanager

from .schemas import BooksSearchToolResponse, ExportBookToolResponse


mcp = FastMCP(
    name="Book Library MCP",
    instructions=(
        "Инструменты сервера ищут книги в библиотеке и экспортируют файлы книг в S3/MinIO. "
        "Для поиска нужно передать хотя бы один параметр: q, author или title."
    ),
)


@asynccontextmanager
async def book_service_context() -> AsyncIterator[BookService]:
    async with sessionmanager.session() as db:
        yield build_book_service(db)


def _normalize_query_part(value: str | None) -> str | None:
    normalized = value.strip() if value else None
    return normalized or None


@mcp.tool(
    name="search_books",
    description=(
        "Ищет книги по общему запросу, автору и названию. "
        "Поведение совпадает с GET /api/v1/books/search: широкие и пустые результаты возвращаются с пояснением."
    ),
    annotations={
        "title": "Поиск книг",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    },
)
async def search_books(
    q: Annotated[
        str | None,
        Field(
            description="Общий поисковый запрос по автору и названию. Предпочтительнее author/title.",
        ),
    ] = None,
    author: Annotated[
        str | None,
        Field(description="Поиск по автору"),
    ] = None,
    title: Annotated[
        str | None,
        Field(description="Поиск по названию"),
    ] = None,
) -> BooksSearchToolResponse:
    q_norm = _normalize_query_part(q)
    author_norm = _normalize_query_part(author)
    title_norm = _normalize_query_part(title)

    if not q_norm and not author_norm and not title_norm:
        return BooksSearchToolResponse(
            status="validation_error",
            detail="Нужно указать хотя бы один параметр поиска: q, author или title.",
        )

    async with book_service_context() as service:
        try:
            books = await service.search(q=q_norm, author=author_norm, title=title_norm)
        except TooManyResultsError as ex:
            return BooksSearchToolResponse(status="too_many_results", detail=str(ex))
        except BooksNotFoundError as ex:
            return BooksSearchToolResponse(status="no_results", detail=str(ex))

    return BooksSearchToolResponse(status="ok", books=books)


@mcp.tool(
    name="export_book_to_s3",
    description=(
        "Экспортирует файл книги в S3/MinIO по id книги. "
        "Поведение совпадает с POST /api/v1/books/{book_id}/export: возвращает bucket, key и existed."
    ),
    annotations={
        "title": "Экспорт книги в S3",
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def export_book_to_s3(
    book_id: Annotated[int, Field(description="ID книги в БД", ge=1)],
) -> ExportBookToolResponse:
    async with book_service_context() as service:
        try:
            data = await service.export_book_to_s3(book_id)
        except NotFoundError:
            return ExportBookToolResponse(status="not_found", detail="Книга не найдена")
        except ValueException as ex:
            return ExportBookToolResponse(status="invalid_book_data", detail=str(ex))
        except StorageUnavailableError as ex:
            return ExportBookToolResponse(status="storage_unavailable", detail=str(ex))

    return ExportBookToolResponse(status="ok", **data)


mcp_app = mcp.http_app()
