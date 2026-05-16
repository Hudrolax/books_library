from typing import Any, Literal

from pydantic import BaseModel, Field

from domain.models.book import Book


class BooksSearchToolResponse(BaseModel):
    status: Literal["ok", "validation_error", "no_results", "too_many_results"] = Field(
        ...,
        description="Статус выполнения поиска",
    )
    books: list[Book] = Field(default_factory=list, description="Найденные книги")
    detail: str | None = Field(None, description="Пояснение для статусов без результата")


class ExportBookToolResponse(BaseModel):
    status: Literal["ok", "not_found", "invalid_book_data", "storage_unavailable"] = Field(
        ...,
        description="Статус экспорта книги",
    )
    bucket: str | None = Field(None, description="S3 bucket. Передай его как bucket в send_book_to_email.")
    key: str | None = Field(None, description="S3 object key. Передай его как file_key в send_book_to_email.")
    existed: bool | None = Field(None, description="Был ли файл уже в S3")
    detail: str | None = Field(None, description="Пояснение для ошибочного статуса")


class SendBookEmailToolResponse(BaseModel):
    status: Literal["ok", "not_in_s3", "storage_unavailable", "email_send_failed"] = Field(
        ...,
        description=(
            "Статус отправки книги на e-mail. "
            "'ok' — n8n принял и письмо отправлено; 'email_send_failed' — n8n ответил ошибкой "
            "(детали в provider_response) или сервис недоступен; "
            "'not_in_s3' — файла нет в S3, сначала нужен export_book_to_s3."
        ),
    )
    detail: str | None = Field(None, description="Краткое человекочитаемое пояснение (обычно message от n8n)")
    provider_response: dict[str, Any] | None = Field(
        None,
        description=(
            "Сырой JSON-ответ n8n как есть (и при успехе, и при ошибке). "
            "null, если n8n недоступен или ответ не в формате JSON-объекта. "
            "Используй его, чтобы понять, что именно произошло с отправкой."
        ),
    )
