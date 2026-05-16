from typing import Literal

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
            "'not_in_s3' — файл не найден в S3, сначала нужен export_book_to_s3."
        ),
    )
    detail: str | None = Field(None, description="Сообщение от сервиса отправки или пояснение ошибки")
