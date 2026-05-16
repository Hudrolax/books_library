from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from composition import build_book_service
from domain.exceptions import (
    BooksNotFoundError,
    EmailSendError,
    NotFoundError,
    StorageUnavailableError,
    TooManyResultsError,
    ValueException,
)
from domain.services.book_service import BookService
from infrastructure.db.db import sessionmanager

from .schemas import BooksSearchToolResponse, ExportBookToolResponse, SendBookEmailToolResponse


mcp = FastMCP(
    name="Book Library MCP",
    instructions=(
        "Сервер ищет книги в библиотеке и доставляет их пользователю на e-mail.\n"
        "\n"
        "Обязательная последовательность действий (шаги нельзя пропускать или менять местами):\n"
        "1. search_books — найди книги по запросу пользователя. Если статус 'too_many_results' — "
        "уточни запрос и повтори поиск; если 'no_results' — расширь/измени запрос; "
        "если 'validation_error' — не задан ни один параметр поиска.\n"
        "2. Из списка результатов выбери РОВНО ОДНУ книгу (один id) — той логикой, которая "
        "лучше всего отвечает запросу пользователя. Никогда не экспортируй несколько книг сразу.\n"
        "3. export_book_to_s3 — выгрузи выбранную книгу в S3. Из ответа возьми bucket и key.\n"
        "4. send_book_to_email — отправь книгу на e-mail, передав bucket и file_key из ответа "
        "шага 3. Этот инструмент допустимо вызывать ТОЛЬКО после успешного export_book_to_s3.\n"
        "\n"
        "Не вызывай send_book_to_email до export_book_to_s3: книги ещё нет в S3 и отправка вернёт "
        "статус 'not_in_s3'."
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
        "Шаг 1 из 3. Ищет книги в библиотеке по общему запросу, автору и/или названию. "
        "Нужно передать хотя бы один из параметров: q, author или title.\n"
        "Статусы ответа:\n"
        "- 'ok' — в books список найденных книг; выбери из него РОВНО ОДНУ книгу (по её id) "
        "и переходи к export_book_to_s3.\n"
        "- 'too_many_results' — найдено слишком много книг (>50); уточни запрос "
        "(добавь автора/название) и вызови инструмент снова.\n"
        "- 'no_results' — ничего не найдено; упрости или измени запрос (часть фамилии "
        "автора, часть названия, без лишних символов) и попробуй снова.\n"
        "- 'validation_error' — не передан ни один параметр поиска."
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
            description=(
                "Общий поисковый запрос сразу по автору и названию. "
                "Используй, когда непонятно, где автор, а где название. "
                "Если их можно разделить — предпочитай author и title."
            ),
        ),
    ] = None,
    author: Annotated[
        str | None,
        Field(description="Поиск по автору (фамилия и/или имя, можно часть)."),
    ] = None,
    title: Annotated[
        str | None,
        Field(description="Поиск по названию книги (можно часть названия)."),
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
        "Шаг 2 из 3. Выгружает файл одной выбранной книги в S3/MinIO по её id "
        "(id берётся из результата search_books — ровно одна книга).\n"
        "При статусе 'ok' в ответе есть bucket, key и existed. Эти bucket и key "
        "ОБЯЗАТЕЛЬНЫ для следующего шага send_book_to_email (bucket -> bucket, key -> file_key).\n"
        "Статусы ответа:\n"
        "- 'ok' — книга в S3, можно вызывать send_book_to_email.\n"
        "- 'not_found' — книги с таким id нет; вернись к search_books.\n"
        "- 'invalid_book_data' — у книги нет данных для экспорта (архив/файл).\n"
        "- 'storage_unavailable' — S3/MinIO недоступен, повтори позже."
    ),
    annotations={
        "title": "Экспорт книги в S3",
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def export_book_to_s3(
    book_id: Annotated[
        int,
        Field(description="ID одной книги из результата search_books", ge=1),
    ],
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


@mcp.tool(
    name="send_book_to_email",
    description=(
        "Шаг 3 из 3. Отправляет уже выгруженную в S3 книгу на e-mail пользователя. "
        "Вызывать ТОЛЬКО после успешного export_book_to_s3.\n"
        "bucket и file_key бери из ответа export_book_to_s3 (bucket -> bucket, key -> file_key). "
        "to, subject и text — адрес и текст письма для пользователя.\n"
        "Сырой JSON-ответ n8n всегда пробрасывается в поле provider_response "
        "(и при успехе, и при ошибке) — опирайся на него, чтобы понять результат "
        "и при ошибке объяснить пользователю причину.\n"
        "Статусы ответа:\n"
        "- 'ok' — n8n принял запрос, письмо отправлено; detail = message от n8n.\n"
        "- 'not_in_s3' — файла нет в S3; сначала вызови export_book_to_s3.\n"
        "- 'storage_unavailable' — S3/MinIO недоступен при проверке файла.\n"
        "- 'email_send_failed' — n8n ответил ошибкой (причина в provider_response) "
        "или сервис недоступен (provider_response = null)."
    ),
    annotations={
        "title": "Отправка книги на e-mail",
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def send_book_to_email(
    bucket: Annotated[
        str,
        Field(description="S3 bucket из ответа export_book_to_s3", min_length=1),
    ],
    file_key: Annotated[
        str,
        Field(description="S3 object key (поле key из ответа export_book_to_s3)", min_length=1),
    ],
    to: Annotated[
        str,
        Field(description="E-mail получателя", min_length=3),
    ],
    subject: Annotated[
        str,
        Field(description="Тема письма", min_length=1),
    ],
    text: Annotated[
        str,
        Field(description="Текст письма", min_length=1),
    ],
) -> SendBookEmailToolResponse:
    async with book_service_context() as service:
        try:
            data = await service.send_book_to_email(
                bucket=bucket,
                file_key=file_key,
                to=to,
                subject=subject,
                text=text,
            )
        except ValueException as ex:
            return SendBookEmailToolResponse(status="not_in_s3", detail=str(ex))
        except StorageUnavailableError as ex:
            return SendBookEmailToolResponse(status="storage_unavailable", detail=str(ex))
        except EmailSendError as ex:
            return SendBookEmailToolResponse(status="email_send_failed", detail=str(ex))

    return SendBookEmailToolResponse(
        status="ok" if data["ok"] else "email_send_failed",
        detail=data["detail"],
        provider_response=data["provider_response"],
    )


mcp_app = mcp.http_app()
