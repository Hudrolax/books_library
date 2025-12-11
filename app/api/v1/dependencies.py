from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.book import Book
from domain.services.book_service import BookService
from infrastructure.db.db import get_db
from infrastructure.db.models.book_orm import BookORM
from infrastructure.repositories.book_repo import BookRepo


async def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    repo = BookRepo(db, Book, BookORM)
    return BookService(repo)
