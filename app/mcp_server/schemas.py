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
    bucket: str | None = Field(None, description="S3 bucket")
    key: str | None = Field(None, description="S3 object key")
    existed: bool | None = Field(None, description="Был ли файл уже в S3")
    detail: str | None = Field(None, description="Пояснение для ошибочного статуса")
