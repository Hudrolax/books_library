from typing import Generic

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from domain.exceptions import RepositoryException
from domain.models.base_domain_model import TDomain, TTypedDict
from domain.models.book import BookDict, BookFields

from ..db.models.base_model_orm import TOrm
from .sqlalchemy_mixins import ListMixin, ReadMixin


class BookRepo(
    ReadMixin[TDomain, TOrm, BookDict],
    ListMixin[TDomain, TOrm, BookDict, BookFields],
    Generic[TDomain, TOrm, TTypedDict],
):
    async def search(self, query: str) -> list[TDomain]:
        # Используем FTS5 поиск с сортировкой по релевантности (rank)
        # books_fts - это виртуальная таблица
        stmt = select(self.orm_class).from_statement(
            text("""
            SELECT books.* FROM books
            JOIN books_fts ON books.id = books_fts.rowid
            WHERE books_fts MATCH :query
            ORDER BY rank
        """)
        )

        try:
            result = await self.db.execute(stmt, {"query": query})
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))

        rows = result.scalars().all()
        return [self.domain_model.model_validate(row) for row in rows]
