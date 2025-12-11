import logging
from typing import List

from ..interfaces.book_ifaces import IBookRepoProtocol, IBookService
from ..models.book import Book, BookDict


logger = logging.getLogger(__name__)


class BookService(IBookService):
    repository: IBookRepoProtocol

    def __init__(self, repository: IBookRepoProtocol) -> None:
        self.repository = repository

    async def read(self, filters: BookDict) -> Book:
        return await self.repository.read(filters=filters)

    async def list(self, filters: BookDict) -> List[Book]:
        return await self.repository.list(filters=filters)

    async def search(self, query: str) -> List[Book]:
        limit = 20
        # Запрашиваем на 1 больше, чтобы понять, есть ли еще результаты
        books = await self.repository.search(query=query, limit=limit + 1)

        if len(books) > limit:
            from domain.exceptions import TooManyResultsError

            raise TooManyResultsError("Found too many matching books. Please refine your search.")

        return books
