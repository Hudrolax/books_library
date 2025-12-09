from typing import Literal

from pydantic import Field

from .base_domain_model import BaseCreateDict, BaseDomainModel


class Book(BaseDomainModel):
    id: int = Field(..., description="ID в БД")
    author: str | None = Field(None, description="Автор (поле author)")
    title: str | None = Field(None, description="Название (поле title)")
    archive_name: str | None = Field(None, description="Имя архива")
    file_name: str | None = Field(None, description="Имя файла внутри архива")
    file_size_mb: float | None = Field(None, description="Размер файла в мегабайтах")
    genre: str | None = Field(None, description="Жанр")
    author_first_name: str | None = Field(None, description="Имя автора")
    author_last_name: str | None = Field(None, description="Фамилия автора")
    book_title: str | None = Field(None, description="Название книги (поле book_title)")
    annotation: str | None = Field(None, description="Аннотация")
    lang: str | None = Field(None, description="Язык")
    publish_book_name: str | None = Field(None, description="Издательская серия/название")
    publisher: str | None = Field(None, description="Издательство")
    city: str | None = Field(None, description="Город издания")
    year: str | None = Field(None, description="Год издания (как в БД)")
    isbn: str | None = Field(None, description="ISBN")


class BookDict(BaseCreateDict, total=False):
    id: int
    author: str | None
    title: str | None
    archive_name: str | None
    file_name: str | None
    file_size_mb: float | None
    genre: str | None
    author_first_name: str | None
    author_last_name: str | None
    book_title: str | None
    annotation: str | None
    lang: str | None
    publish_book_name: str | None
    publisher: str | None
    city: str | None
    year: str | None
    isbn: str | None


BookFields = Literal[
    "id",
    "author",
    "title",
    "archive_name",
    "file_name",
    "file_size_mb",
    "genre",
    "author_first_name",
    "author_last_name",
    "book_title",
    "annotation",
    "lang",
    "publish_book_name",
    "publisher",
    "city",
    "year",
    "isbn",
]
